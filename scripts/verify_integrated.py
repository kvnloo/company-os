#!/usr/bin/env python3
"""Read-only proof of an already-running integrated chooser; owned headless browser only."""
import argparse
import hashlib
from importlib.metadata import version
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time
import urllib.request

ROOT=Path(__file__).resolve().parents[1]


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--url',required=True,help='exact http://127.0.0.1:PORT origin')
    parser.add_argument('--artifacts',type=Path,required=True)
    args=parser.parse_args()
    if not re.fullmatch(r'http://127\.0\.0\.1:[0-9]{1,5}',args.url):
        parser.error('exact loopback origin required')
    args.artifacts.mkdir(parents=True,exist_ok=True)
    os.environ['CHOOSER_ARTIFACTS']=str(args.artifacts)
    sys.path.insert(0,str(ROOT/'tests'))
    from playwright.sync_api import sync_playwright
    import importlib
    interactions=importlib.import_module('test_integrated_interactions')
    chooser_tests=importlib.import_module('test_design_chooser')
    opener=urllib.request.build_opener(urllib.request.ProxyHandler({}))
    def get(path):
        with opener.open(args.url+path,timeout=30) as response:
            assert response.status==200
            return response.read()
    files={
        '/design-chooser/':'web/design-chooser/index.html',
        '/design-chooser/chooser.js':'web/design-chooser/chooser.js',
        '/design-chooser/chooser.css':'web/design-chooser/chooser.css',
        '/design-chooser/inspection-model.mjs':'plugin/inspection-model.mjs',
        '/hud-v3.css':'web/hud-v3.css',
        '/fonts/ibm-plex-mono-regular.ttf':'web/fonts/ibm-plex-mono-regular.ttf',
        '/fonts/ibm-plex-sans-regular.ttf':'web/fonts/ibm-plex-sans-regular.ttf',
    }
    hashes={}
    for route,path in files.items():
        data=get(route)
        assert data==(ROOT/path).read_bytes(),path
        hashes[path]=hashlib.sha256(data).hexdigest()
    snapshot=json.loads(get('/api/plugins/company-os/snapshot'))
    assert snapshot['implementation']['content_sha256']==hashlib.sha256((ROOT/'hermes-plugin/dashboard/plugin_api.py').read_bytes()).hexdigest()
    assert {'z0_bridge','z0_evaluation','hermes_cluster'}<=snapshot['sources'].keys()
    health=json.loads(get('/api/plugins/company-os/health'))
    (args.artifacts/'live-snapshot.json').write_text(json.dumps(snapshot,indent=2))
    (args.artifacts/'live-health.json').write_text(json.dumps(health,indent=2))
    with sync_playwright() as pw:
        browser=pw.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--disable-dev-shm-usage'])
        try:
            interactions.test_six_live_layout_theme_inspections_paging_and_focus(args.url,browser)
            download=args.artifacts/'test-owned-choice';download.mkdir(exist_ok=True)
            chooser_tests.test_all_layouts_theme_and_local_choice_survive_reload_and_download(args.url,browser,download)
            interactions.test_latest_detail_and_provenance_survive_replacement_removal_and_source_failure(args.url,browser)
        finally:
            browser.close()
    matrix=json.loads((args.artifacts/'integrated-browser-matrix.json').read_text())
    assert len({(r['layout'],r['theme']) for r in matrix})==6
    receipt={'status':'PASS','url':args.url+'/design-chooser/','verified_at':time.time(),
             'head':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
             'git_status':subprocess.check_output(['git','status','--porcelain'],cwd=ROOT,text=True),
             'static_sha256':hashes,'backend_sha256':snapshot['implementation']['content_sha256'],
             'layout_theme_combinations':len(matrix),'groups_per_combination':10,
             'choice_scope':'isolated test browser; not user preference','playwright':version('playwright'),
             'source_statuses':{k:v['status'] for k,v in snapshot['sources'].items()}}
    (args.artifacts/'receipt.json').write_text(json.dumps(receipt,indent=2))
    print(json.dumps(receipt,indent=2))


if __name__=='__main__':
    main()
