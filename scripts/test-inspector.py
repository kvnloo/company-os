"""One-command live GET + headless interaction gate; owns and reaps its server."""
import argparse
import copy
import hashlib
import json
import os
import socket
import subprocess
import threading
import time
import tempfile
import urllib.request
from pathlib import Path

import uvicorn
from diagnostic import ROOT, make_app


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--hermes-root', required=True, type=Path)
    parser.add_argument('--artifacts', required=True, type=Path)
    parser.add_argument('--port', default=0, type=int)
    parser.add_argument('--chromium', default='/usr/bin/chromium')
    args = parser.parse_args()
    args.artifacts.mkdir(parents=True, exist_ok=True)
    subprocess.run(['node', str(ROOT / 'scripts/build-browser.mjs')], check=True)
    subprocess.run(['node', str(ROOT / 'scripts/build-diagnostic.mjs'), str(args.hermes_root), str(args.artifacts)], check=True)
    sock = socket.socket()
    sock.bind(('127.0.0.1', args.port))
    sock.listen(128)
    base = f'http://127.0.0.1:{sock.getsockname()[1]}'
    server = uvicorn.Server(uvicorn.Config(make_app(args.artifacts), log_level='warning', lifespan='off'))
    thread = threading.Thread(target=server.run, kwargs={'sockets':[sock]}, daemon=True)
    thread.start()
    try:
        deadline = time.monotonic() + 15
        while not server.started:
            if not thread.is_alive() or time.monotonic() > deadline:
                raise RuntimeError('owned diagnostic failed to start')
            time.sleep(.05)
        attempts=[]; snapshot={}
        for attempt in range(4):
            with urllib.request.urlopen(base+'/api/plugins/company-os/snapshot', timeout=25) as response:
                snapshot=json.load(response)
            attempts.append({name:source['status'] for name,source in snapshot['sources'].items()})
            if all(attempts[-1].get(name)=='ok' for name in ('z0_health','z0_readiness','z0_metrics','z0_bridge','z0_outcomes','z0_evaluation')):
                break
            if attempt<3:time.sleep(2)
        (args.artifacts/'initial-source-attempts.json').write_text(json.dumps(attempts,indent=2))
        (args.artifacts/'live-snapshot.json').write_text(json.dumps(snapshot,indent=2))
        assert snapshot['z0_service'].get('bridge_capabilities',{}).get('schema')=='agentweb.z0.bridge.capabilities.v1', snapshot['sources']['z0_bridge']
        assert snapshot['z0_service'].get('randomized_evidence',{}).get('schema')=='z0int.agentweb_randomized_outcome_evidence.v1', snapshot['sources']['z0_evaluation']
        from playwright.sync_api import sync_playwright
        with sync_playwright() as pw:
            browser=pw.chromium.launch(executable_path=args.chromium,headless=True,args=['--disable-dev-shm-usage'])
            try:
                page=browser.new_page(viewport={'width':1440,'height':1000})
                errors=[]; requests=[]
                page.on('pageerror',lambda e:errors.append(str(e)))
                page.on('request',lambda r:requests.append({'method':r.method,'path':r.url.removeprefix(base)}))
                page.goto(base+'/company-os-network')
                page.wait_for_selector('.cos-inspector',timeout=12000)
                page.wait_for_function("document.querySelector('.cos-clock')?.textContent.includes('snapshot 20')",timeout=25000)
                assert page.locator('.cos-inspect-card').count()==10
                assert page.evaluate('window.__COMPANY_OS_DIAGNOSTIC__.registered') is True
                page.screenshot(path=str(args.artifacts/'overview.png'),full_page=True)
                card=lambda node:page.locator('button[data-node='+json.dumps(node)+']')
                detail=page.locator('.cos-inspector-detail')
                card('services').click()
                card('service:health').click()
                assert detail.get_attribute('data-selected')=='service:health'
                assert 'not establish' in detail.inner_text()
                assert '/healthz' in detail.inner_text()
                card('service:metrics').focus()
                page.keyboard.press('ArrowRight')
                assert (page.evaluate('document.activeElement?.getAttribute("data-node")') or '').startswith('metric:'), 'keyboard drill lost focus'
                page.keyboard.press('ArrowLeft')
                assert page.evaluate('document.activeElement?.getAttribute("data-node")')=='service:metrics', 'keyboard back did not restore group focus'
                page.keyboard.press('ArrowRight')
                assert page.locator('.cos-inspect-card').count()<=8
                first=page.locator('.cos-inspect-card').first
                first.focus(); page.keyboard.press('Enter')
                selected=detail.get_attribute('data-selected')
                assert selected is not None and selected.startswith('metric:')
                assert page.locator('.cos-inspect-card[aria-pressed="true"]').count()==1
                old=page.locator('.cos-clock').text_content()
                page.wait_for_function('(old)=>document.querySelector(".cos-clock").textContent!==old',arg=old,timeout=20000)
                assert detail.get_attribute('data-selected')==selected
                assert page.evaluate('document.activeElement?.getAttribute("data-node")')==selected, 'polling stole keyboard focus'
                page.get_by_role('button',name='Collapse children',exact=True).click()
                assert page.locator('.cos-inspect-card').count()==0
                page.get_by_role('button',name='Expand children',exact=True).click()
                assert page.locator('.cos-inspect-card').count()>0
                if page.get_by_role('button',name='Next children',exact=True).is_enabled():
                    page.get_by_role('button',name='Next children',exact=True).click()
                    assert detail.get_attribute('data-selected')==selected
                page.screenshot(path=str(args.artifacts/'metric-detail.png'),full_page=True)
                # Poll replacement and removal are browser-only controls.
                # Last-known detail must retain the latest successful poll,
                # not the older value from when the operator first clicked.
                changed=copy.deepcopy(snapshot)
                for metric in changed['z0_service']['metrics']:
                    metric['value']=123456789
                page.route('**/api/plugins/company-os/snapshot',lambda route:route.fulfill(json=changed))
                page.wait_for_function("document.querySelector('.cos-inspector-detail')?.textContent.includes('123456789')",timeout=20000)
                assert detail.get_attribute('data-selected')==selected
                changed['z0_service']['metrics']=[]
                page.wait_for_function("document.querySelector('.cos-inspector-detail')?.textContent.includes('No longer in latest')",timeout=20000)
                assert '123456789' in detail.inner_text(), 'last-known detail reverted to click-time state'
                page.unroute('**/api/plugins/company-os/snapshot')
                page.locator('.cos-breadcrumbs').get_by_role('button',name='Network',exact=True).click()
                card('work').focus(); page.keyboard.press('Space')
                card('cluster:tasks').click()
                assert 'not all local work' in detail.inner_text()
                card('stage:AODL').click()
                assert 'Unobserved' in detail.inner_text()
                assert page.locator('.cos-node.live').count()==0
                page.keyboard.press('Escape')
                assert detail.get_attribute('data-selected')=='work'
                page.get_by_role('button',name='Back',exact=True).click()
                assert detail.get_attribute('data-selected')=='network'
                card('evidence').click(); card('window:1h').click()
                assert 'assessment' in detail.inner_text().lower()
                page.locator('.cos-breadcrumbs').get_by_role('button',name='Network',exact=True).click()
                card('evaluation').click()
                assert 'promotion permission' in detail.inner_text()
                page.screenshot(path=str(args.artifacts/'evaluation-detail.png'),full_page=True)
                # Inert file exercises the production privacy/freshness boundary,
                # never writes an existing source or impersonates live telemetry.
                with tempfile.TemporaryDirectory(prefix='cos-inspector-',dir=os.environ['TMPDIR']) as temp:
                    marker='PRIVATE_SENTINEL_/home/private_prompt_credentials'
                    alias='ref-'+hashlib.sha256(marker.encode()).hexdigest()[:16]
                    fixture=Path(temp)/'capacity.json'
                    fixture.write_text(json.dumps({'schema':'z0.capacity.snapshot.v1','observed_at':time.time()-500,
                        'hosts':[{'host_id':marker,'label':marker,'observed_at':time.time()-500,
                                  'resources':{'cpu_logical':{'secret':marker},'gpus':[{'name':marker}]}}]}))
                    old_capacity=os.environ.get('COMPANY_OS_Z0_CAPACITY_SNAPSHOT')
                    os.environ['COMPANY_OS_Z0_CAPACITY_SNAPSHOT']=str(fixture)
                    try:
                        with urllib.request.urlopen(base+'/api/plugins/company-os/snapshot',timeout=25) as response:
                            negative=response.read().decode()
                        assert marker not in negative
                        assert json.loads(negative)['sources']['z0_capacity']['freshness']=='stale'
                        page.locator('.cos-breadcrumbs').get_by_role('button',name='Network',exact=True).click()
                        card('resources').click()
                        page.wait_for_function("document.querySelector('[data-node=hosts]')?.textContent.includes('1 projected children')",timeout=20000)
                        card('hosts').click(); card('host:'+alias).click()
                        assert marker not in page.locator('.cos').inner_text()
                        assert 'stale' in detail.inner_text()
                    finally:
                        if old_capacity is None:os.environ.pop('COMPANY_OS_Z0_CAPACITY_SNAPSHOT',None)
                        else:os.environ['COMPANY_OS_Z0_CAPACITY_SNAPSHOT']=old_capacity
                page.locator('.cos-breadcrumbs').get_by_role('button',name='Network',exact=True).click()
                card('agents').click()
                processes=page.locator('.cos-inspect-card[data-node^="process:"]')
                removal=False
                if processes.count():
                    processes.first.click(); selected=detail.get_attribute('data-selected')
                    removed=copy.deepcopy(snapshot); removed['fleet']=[]; removed['generated_at']=time.time()
                    # Browser-only failure/removal control, not source telemetry.
                    page.route('**/api/plugins/company-os/snapshot',lambda route:route.fulfill(json=removed))
                    page.wait_for_function("document.querySelector('.cos-inspector-detail')?.textContent.includes('No longer in latest')",timeout=20000)
                    assert detail.get_attribute('data-selected')==selected
                    assert 'not proof of completion' in detail.inner_text()
                    removal=True
                    page.unroute('**/api/plugins/company-os/snapshot')
                page.route('**/api/plugins/company-os/snapshot',lambda route:route.fulfill(status=503,body='unavailable'))
                page.wait_for_function("document.querySelector('.cos-status')?.textContent.includes('stale')",timeout=20000)
                assert 'last known' in detail.inner_text().lower()
                page.screenshot(path=str(args.artifacts/'outage-detail.png'),full_page=True)
                assert not errors, errors
                assert all(r['method']=='GET' for r in requests)
                assert all(r['path'].startswith(('/company-os-network','/diagnostic-host.js','/dashboard-plugins/company-os/','/api/plugins/company-os/snapshot','/api/dashboard/plugins')) for r in requests)
                (args.artifacts/'browser-dom.txt').write_text(page.locator('.cos').inner_text())
                receipt={'result':'PASS','head':subprocess.check_output(['git','-C',str(ROOT),'rev-parse','HEAD'],text=True).strip(),
                    'backend_sha256':hashlib.sha256((ROOT/'hermes-plugin/dashboard/plugin_api.py').read_bytes()).hexdigest(),
                    'ui_sha256':hashlib.sha256((ROOT/'plugin/plugin.js').read_bytes()).hexdigest(),
                    'requests':requests,'errors':errors,'live_get_schemas':True,'keyboard':['ArrowRight','ArrowLeft','Enter','Space','Escape'],
                    'keyboard_drill_back_focus':True,
                    'initial_source_attempts':attempts,
                    'poll_selection_preserved':True,'collapse_expand':True,'breadcrumbs_back':True,
                    'latest_successful_detail_retained':True,'production_privacy_stale_control':True,
                    'cluster_live_get':snapshot.get('hermes_cluster') is not None,
                    'missing_selection_control':removal,'outage_detail':'last known',
                    'scope':'actual installed Hermes loader; headless owned diagnostic; browser-only removal/outage fixtures'}
                (args.artifacts/'receipt.json').write_text(json.dumps(receipt,indent=2))
                print(json.dumps({k:v for k,v in receipt.items() if k!='requests'}))
            finally:
                browser.close()
    finally:
        server.should_exit=True
        thread.join(timeout=20)
        sock.close()
        if thread.is_alive():raise RuntimeError('owned server did not exit')


if __name__=='__main__':main()
