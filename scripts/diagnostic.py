"""Diagnostic browser gate using the installed Hermes registry/SDK sources.
No full Hermes startup (which can bootstrap credentials/runtimes), profile edits,
or GUI auto-open. A small owned FastAPI server mounts the production router.
"""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import tempfile
import threading

from fastapi import FastAPI
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
import uvicorn

ROOT = Path(__file__).resolve().parents[1]


def make_app(assets):
    spec = importlib.util.spec_from_file_location('company_os_diagnostic', ROOT / 'hermes-plugin/dashboard/plugin_api.py')
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)
    app.include_router(module.router, prefix='/api/plugins/company-os')
    app.mount('/dashboard-plugins/company-os', StaticFiles(directory=ROOT / 'hermes-plugin/dashboard'), name='company-os')
    @app.get('/api/dashboard/plugins')
    def manifests():
        return [json.loads((ROOT / 'hermes-plugin/dashboard/manifest.json').read_text())]
    @app.get('/company-os-network')
    def page():
        return HTMLResponse('<!doctype html><html><head><meta charset="utf-8"><title>CompanyOS isolated diagnostic</title></head><body><div id="root"></div><script src="/diagnostic-host.js"></script></body></html>', headers={'Cache-Control': 'no-store'})
    @app.get('/diagnostic-host.js')
    def host_bundle():
        return FileResponse(assets / 'diagnostic-host.js', media_type='text/javascript')
    return app


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--hermes-root', required=True, type=Path)
    parser.add_argument('--artifacts', required=True, type=Path)
    parser.add_argument('--port', type=int, default=0)
    parser.add_argument('--test-browser', action='store_true')
    parser.add_argument('--chromium', default='/usr/bin/chromium')
    args = parser.parse_args()
    args.artifacts.mkdir(parents=True, exist_ok=True)
    subprocess.run(['node', str(ROOT / 'scripts/build-diagnostic.mjs'), str(args.hermes_root), str(args.artifacts)], check=True)
    import socket
    sock = socket.socket()
    sock.bind(('127.0.0.1', args.port))
    port = sock.getsockname()[1]
    sock.listen(128)
    app = make_app(args.artifacts)
    server = uvicorn.Server(uvicorn.Config(app, log_level='warning', lifespan='off'))
    url = f'http://127.0.0.1:{port}'
    print(json.dumps({'url': url + '/company-os-network', 'api': url + '/api/plugins/company-os/snapshot', 'mode': 'isolated-diagnostic'}), flush=True)
    if not args.test_browser:
        server.run(sockets=[sock])
        return
    thread = threading.Thread(target=server.run, kwargs={'sockets': [sock]}, daemon=True)
    thread.start()
    try:
        import time
        import urllib.request
        deadline = time.monotonic() + 15
        while not server.started:
            if not thread.is_alive() or time.monotonic() >= deadline:
                raise RuntimeError('diagnostic server not ready')
            time.sleep(.05)
        with urllib.request.urlopen(url + '/api/plugins/company-os/snapshot', timeout=20) as response:
            snapshot = json.load(response)
        (args.artifacts / 'live-snapshot.json').write_text(json.dumps(snapshot, indent=2))
        with urllib.request.urlopen(url + '/api/plugins/company-os/health', timeout=20) as response:
            health = json.load(response)
        assert health['schema'] == 'company_os.snapshot.v1'
        (args.artifacts / 'live-health.json').write_text(json.dumps(health, indent=2))
        # Pin actual installed host input bytes; Git HEAD alone can hide dirt.
        host_inputs = ['web/src/plugins/registry.ts', 'web/src/plugins/usePlugins.ts',
                       'web/src/plugins/PluginPage.tsx', 'web/src/lib/api.ts']
        host_evidence = {p: hashlib.sha256((args.hermes_root / p).read_bytes()).hexdigest() for p in host_inputs}
        from playwright.sync_api import sync_playwright
        with sync_playwright() as pw:
            browser = pw.chromium.launch(executable_path=args.chromium, headless=True, args=['--disable-dev-shm-usage'])
            page = browser.new_page(viewport={'width': 1440, 'height': 1000})
            errors, requests = [], []
            page.on('pageerror', lambda e: errors.append(str(e)))
            page.on('request', lambda req: requests.append({'method': req.method, 'path': req.url.removeprefix(url)}))
            page.goto(url + '/company-os-network')
            page.wait_for_selector('.cos-status', timeout=15000)
            page.wait_for_function("document.querySelector('.cos-clock')?.textContent.includes('snapshot 20')", timeout=20000)
            assert page.evaluate("window.__COMPANY_OS_DIAGNOSTIC__.registered") is True
            assert page.locator('.cos-node.live').count() == 0
            assert 'unknown' in page.locator('.cos-foot').inner_text()
            clock = page.locator('.cos-clock').inner_text()
            page.wait_for_function('(old) => document.querySelector(".cos-clock").textContent !== old', arg=page.locator('.cos-clock').text_content(), timeout=20000)
            page.get_by_role('button', name='inspect trace').click()
            page.get_by_text('inspect service metrics (not economics)', exact=True).click()
            assert page.locator('#cos-flow-detail details').filter(has=page.get_by_text('inspect service metrics (not economics)', exact=True)).get_attribute('open') is not None
            page.get_by_text('Qualification gaps — audit context, not live deployment', exact=True).click()
            assert 'FAIL / DISCARD' in page.locator('#cos-flow-detail').inner_text()
            page.locator('.cos-sources summary').filter(has_text='z0_health:').click()
            page.wait_for_function("Array.from(document.querySelectorAll('.cos-sources details')).some(d => d.open && d.innerText.toLowerCase().includes('source revision sha256:'))")
            assert 'source revision sha256:' in page.locator('.cos-sources').inner_text().lower()
            page.locator('.cos').evaluate('(el) => {el.scrollTop=0;el.scrollLeft=0}')
            page.locator('.cos-map').evaluate('(el) => {el.scrollTop=0;el.scrollLeft=0}')
            page.screenshot(path=str(args.artifacts / 'browser-live.png'), full_page=True)
            page.locator('.cos').evaluate('(el) => {el.scrollTop=el.scrollHeight}')
            page.screenshot(path=str(args.artifacts / 'browser-details.png'), full_page=True)
            # Inert hostile fixture, read by the production API in this owned
            # process only. This is a negative control, not live capacity.
            with tempfile.TemporaryDirectory(prefix='cos-private-', dir=os.environ['TMPDIR']) as temp:
                marker = 'PRIVATE_SENTINEL_/home/private_prompt_credentials'
                alias = 'ref-' + hashlib.sha256(marker.encode()).hexdigest()[:16]
                fixture = Path(temp) / 'capacity.json'
                fixture.write_text(json.dumps({'schema':'z0.capacity.snapshot.v1', 'observed_at':time.time()-500,
                    'hosts':[{'host_id':marker,'label':marker,'observed_at':time.time()-500,
                              'resources':{'cpu_logical':{'secret':marker},'gpus':[{'name':marker}]}}],
                    'sources':{'tern':{'status':{'secret':marker},'private':marker}}}))
                previous = os.environ.get('COMPANY_OS_Z0_CAPACITY_SNAPSHOT')
                os.environ['COMPANY_OS_Z0_CAPACITY_SNAPSHOT'] = str(fixture)
                try:
                    with urllib.request.urlopen(url + '/api/plugins/company-os/snapshot', timeout=20) as response:
                        negative = response.read().decode()
                    assert marker not in negative and '/home/private' not in negative
                    assert json.loads(negative)['sources']['z0_capacity']['freshness'] == 'stale'
                    (args.artifacts / 'privacy-control-snapshot.json').write_text(negative)
                    page.wait_for_function('(alias) => document.querySelector(".cos-tree").textContent.includes(alias)', arg=alias, timeout=25000)
                    visible = page.locator('.cos').text_content()
                    assert visible and marker not in visible and '/home/private' not in visible
                    assert page.locator('.cos-node.live').count() == 0
                finally:
                    if previous is None:
                        os.environ.pop('COMPANY_OS_Z0_CAPACITY_SNAPSHOT', None)
                    else:
                        os.environ['COMPANY_OS_Z0_CAPACITY_SNAPSHOT'] = previous
            # Controlled consumer outage only. No live service is stopped or changed.
            page.route('**/api/plugins/company-os/snapshot', lambda route: route.fulfill(status=503, body='unavailable'))
            page.wait_for_function("document.querySelector('.cos-status')?.textContent.includes('stale')", timeout=20000)
            assert page.locator('.cos-node.live').count() == 0
            assert 'last known' in page.locator('.cos-sources').inner_text().lower()
            page.locator('.cos').evaluate('(el) => {el.scrollTop=0;el.scrollLeft=0}')
            page.screenshot(path=str(args.artifacts / 'browser-outage.png'), full_page=True)
            (args.artifacts / 'browser-dom.txt').write_text(page.locator('.cos').inner_text())
            receipt = {'registered': True, 'sdk_version': page.evaluate('window.__HERMES_PLUGIN_SDK__.sdkVersion'),
                       'privacy_control': 'PASS: inert hostile file through production API and real DOM; not live capacity',
                       'source_revision': snapshot['implementation'], 'initial_clock': clock, 'outage_visible': True,
                       'requests': requests, 'page_errors': errors, 'host_inputs_sha256': host_evidence,
                       'hermes_head': subprocess.check_output(['git', '-C', str(args.hermes_root), 'rev-parse', 'HEAD'], text=True).strip(),
                       'profile_scope': 'inherited server environment; no profile configuration edited',
                       'scope': 'installed Hermes loader + registry + PluginPage + fetchJSON; isolated diagnostic, not deployed profile'}
            (args.artifacts / 'browser-receipt.json').write_text(json.dumps(receipt, indent=2))
            assert not errors, errors
            assert all(r['method'] == 'GET' for r in requests)
            assert all(r['path'].startswith(('/company-os-network', '/diagnostic-host.js', '/dashboard-plugins/company-os/', '/api/plugins/company-os/snapshot', '/api/dashboard/plugins')) for r in requests)
            browser.close()
            print(json.dumps({'browser': 'PASS', 'registered': True, 'outage': 'stale', 'errors': errors}), flush=True)
    finally:
        server.should_exit = True
        thread.join(timeout=15)
        sock.close()
        if thread.is_alive():
            raise RuntimeError('owned server did not stop')


if __name__ == '__main__':
    main()
