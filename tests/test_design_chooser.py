"""Owned loopback proxy and real-browser chooser acceptance. No live writes."""
import importlib.util
import json
import os
from pathlib import Path
import threading
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest

ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = Path(os.environ.get('CHOOSER_ARTIFACTS', '/workspace/zer0/data/operations/company-os-recovery/design-chooser'))
API = '/api/plugins/company-os/'


def load_server():
    path = ROOT / 'scripts/design_chooser.py'
    assert path.is_file(), 'the owned read-only chooser server must exist'
    spec = importlib.util.spec_from_file_location('design_chooser_server', path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class Running:
    def __init__(self, server):
        self.server = server
        self.thread = threading.Thread(target=server.serve_forever, daemon=True)
        self.url = f'http://127.0.0.1:{server.server_port}'
    def __enter__(self):
        self.thread.start()
        return self
    def __exit__(self, *_):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(5)
        assert not self.thread.is_alive()


def read(url, method='GET', headers=None):
    try:
        with urllib.request.urlopen(urllib.request.Request(url, method=method, headers=headers or {}), timeout=30) as response:
            return response.status, response.read(), response.headers
    except urllib.error.HTTPError as error:
        return error.code, error.read(), error.headers


def test_fixed_get_proxy_preserves_bytes_and_rejects_writes():
    module = load_server()
    calls = []
    # Protocol fixture, not operational data. Browser acceptance uses real 18743.
    payload = b'{"contract_test":true,"unknown":null,"zero":0,"flag":false}'
    class Upstream(BaseHTTPRequestHandler):
        def do_GET(self):
            calls.append((self.command, self.path, dict(self.headers)))
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(payload)
        def log_message(self, *_):
            pass
    with Running(ThreadingHTTPServer(('127.0.0.1', 0), Upstream)) as upstream:
        with Running(module.make_server(0, upstream=upstream.url, artifacts=ARTIFACTS)) as chooser:
            for endpoint in ('snapshot', 'health'):
                status, data, headers = read(chooser.url + API + endpoint, headers={'Cookie':'test-only', 'Authorization':'test-only'})
                assert status == 200
                assert data == payload, 'proxy must not recalculate or coerce the projection'
                assert headers['Cache-Control'] == 'no-store'
                assert 'Access-Control-Allow-Origin' not in headers
            assert len(calls) == 2
            assert all('Cookie' not in headers and 'Authorization' not in headers for _, _, headers in calls)
            for method in ('POST', 'PUT', 'PATCH', 'DELETE', 'OPTIONS', 'HEAD'):
                assert read(chooser.url + API + 'snapshot', method)[0] == 405
            for path in (API + 'snapshot?refresh=1', API + 'dispatch', '/../../README.md', '/fonts/', '/.git/config'):
                assert read(chooser.url + path)[0] == 404
            assert read(chooser.url + API + 'snapshot', headers={'Host':'attacker.invalid'})[0] == 403
            assert read(chooser.url + API + 'snapshot', headers={'Origin':'https://attacker.invalid'})[0] == 403
            assert len(calls) == 2, 'rejected calls must not reach the upstream'
    for origin in ('https://127.0.0.1:18743', 'http://localhost:18743', 'http://example.com', 'http://127.0.0.1:18743/path'):
        with pytest.raises(ValueError):
            module.make_server(0, upstream=origin, artifacts=ARTIFACTS)


@pytest.fixture(scope='module')
def chooser_url(integrated_server):
    return integrated_server['url'].split('/design-chooser/')[0]


@pytest.fixture(scope='module')
def browser():
    from playwright.sync_api import sync_playwright
    with sync_playwright() as pw:
        instance = pw.chromium.launch(executable_path='/usr/bin/chromium', headless=True, args=['--disable-dev-shm-usage'])
        yield instance
        instance.close()


def open_live(page, chooser_url):
    with page.expect_response('**' + API + 'snapshot', timeout=30000) as pending:
        page.goto(chooser_url + '/design-chooser/')
    response = pending.value
    assert response.status == 200, 'real critical-path backend must be running'
    snapshot = response.json()
    page.wait_for_selector('[data-loaded="true"]')
    return snapshot


def test_spatial_cockpit_consumes_real_sources_and_inspects_without_coercion(chooser_url, browser):
    page = browser.new_page(viewport={'width':1536, 'height':1024})
    errors, requests = [], []
    page.on('pageerror', lambda e: errors.append(str(e)))
    page.on('request', lambda r: requests.append({'method':r.method,'url':r.url}))
    snapshot = open_live(page, chooser_url)
    assert snapshot['schema'] == 'company_os.snapshot.v1'
    assert page.locator('#workspace').get_attribute('data-layout') == 'spatial'
    for title in ('Services', 'Providers', 'Kubernetes', 'Source freshness', 'Coverage & gaps'):
        assert page.get_by_role('heading', name=title, exact=True).is_visible()
    assert page.locator('.source-list [data-source]').count() == len(snapshot['sources'])
    assert page.locator('[data-economics="observed_cost_usd"]').inner_text() == 'unknown'
    assert page.locator('#snapshot-status').inner_text().lower().startswith(snapshot['status'])
    page.get_by_role('button', name='Inspect source z0_health', exact=True).click()
    assert page.locator('#inspect-title').inner_text() == 'z0_health'
    assert snapshot['sources']['z0_health']['source_version'] in page.locator('#inspect-body').inner_text()
    assert 'unknown' in page.locator('#inspect-body').inner_text()
    assert 'not model or deployment acceptance' in page.locator('#workspace').inner_text()
    assert 'Presence is not governed work' in page.locator('#workspace').inner_text()
    assert page.locator('.k8s-list [data-pod]').count() == len(snapshot['k8s'].get('pods', []))
    assert not errors
    assert all(r['method'] == 'GET' and r['url'].startswith(chooser_url) for r in requests)
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    (ARTIFACTS / 'spatial-source-receipt.json').write_text(json.dumps({'snapshot':snapshot,'requests':requests,'errors':errors}, indent=2))
    page.close()


def test_all_layouts_theme_and_local_choice_survive_reload_and_download(chooser_url, browser, tmp_path):
    page = browser.new_page(viewport={'width':1536,'height':1024}, accept_downloads=True)
    open_live(page, chooser_url)
    layouts = [('spatial','Spatial cockpit'),('balanced','Operations split'),('dense','Instrument desk')]
    rows = []
    for key, title in layouts:
        page.get_by_role('tab', name=title, exact=True).click()
        assert page.locator('#workspace').get_attribute('data-layout') == key
        assert page.get_by_role('tab', name=title, exact=True).get_attribute('aria-selected') == 'true'
        for theme in ('Light','Dark'):
            page.get_by_role('button', name=theme, exact=True).click()
            assert page.locator('html').get_attribute('data-hud-theme') == theme.lower()
            page.get_by_role('button', name='Inspect source z0_metrics', exact=True).click()
            assert page.locator('#inspect-title').inner_text() == 'z0_metrics'
            assert page.locator('.k8s-list [data-pod]').count() > 0
            rows.append({'layout':key,'theme':theme.lower(),'detail':'z0_metrics'})
        page.get_by_role('button', name='Save as default view', exact=True).click()
        assert title in page.locator('#choice-state').inner_text()
        assert 'Saved locally' in page.locator('#choice-state').inner_text()
        page.reload()
        page.wait_for_selector('[data-loaded="true"]')
        assert page.locator('#workspace').get_attribute('data-layout') == key
        assert page.locator('html').get_attribute('data-hud-theme') == 'dark'
        assert title in page.locator('#choice-state').inner_text()
    with page.expect_download() as pending:
        page.get_by_role('button', name='Download preference', exact=True).click()
    dest = tmp_path / 'selection.json'
    pending.value.save_as(dest)
    choice = json.loads(dest.read_text())
    assert choice['design'] == 'dense'
    assert choice['theme'] == 'dark'
    assert choice['scope'] == 'local-design-preference'
    assert choice['production_changed'] is False
    page.get_by_role('button', name='Collapse sections', exact=True).click()
    assert page.locator('.desk-section[open]').count() == 0
    page.get_by_role('button', name='Expand sections', exact=True).click()
    assert page.locator('.desk-section[open]').count() == 3
    tab = page.get_by_role('tab', name='Spatial cockpit', exact=True)
    tab.focus()
    page.keyboard.press('ArrowRight')
    assert page.get_by_role('tab', name='Operations split', exact=True).get_attribute('aria-selected') == 'true'
    page.keyboard.press('Home')
    assert page.locator('#workspace').get_attribute('data-layout') == 'spatial'
    assert page.locator('#choice-state').inner_text().startswith('Saved locally: Instrument desk')
    assert page.locator('#choice-controls').inner_text().find('Save as default view') >= 0
    (ARTIFACTS / 'choice-receipt.json').write_text(json.dumps({'matrix':rows,'download':choice},indent=2))
    assert len(rows) == 6
    page.close()


def test_polling_outage_retains_last_known_and_recovers_without_losing_inspection(chooser_url, browser):
    page = browser.new_page(viewport={'width':1536,'height':1024})
    errors=[]
    page.on('pageerror', lambda error: errors.append(str(error)))
    snapshot=open_live(page, chooser_url)
    previous=page.locator('#snapshot-time').inner_text()
    page.wait_for_function('(before) => document.querySelector("#snapshot-time").textContent !== before', arg=previous, timeout=25000)
    page.get_by_role('button',name='Inspect service metrics',exact=True).click()
    assert 'Not cost, task totals or quality' in page.locator('#inspect-body').inner_text()
    metric=page.locator('#inspect-body').get_by_text('dispatch_active',exact=True)
    while not metric.is_visible() and page.get_by_role('button',name='Next children',exact=True).is_enabled():
        page.get_by_role('button',name='Next children',exact=True).click()
    assert metric.is_visible(), 'the bounded counter pages must expose the actual dispatch gauge'
    page.get_by_role('button',name='Inspect source z0_health',exact=True).click()
    page.locator('#raw-summary').click()
    page.route('**' + API + 'snapshot', lambda route: route.abort('connectionrefused'))
    last=page.locator('#snapshot-time').inner_text()
    page.get_by_role('button',name='Refresh snapshot',exact=True).click()
    page.wait_for_function('() => document.querySelector("#workspace").dataset.transport === "stale"')
    assert page.locator('#snapshot-time').inner_text() == last
    assert 'last-known' in page.locator('#outage-banner').inner_text()
    assert page.locator('#inspect-title').inner_text() == 'z0_health'
    assert page.locator('#inspect-body details.raw').get_attribute('open') is not None
    for title in ('Spatial cockpit','Operations split','Instrument desk'):
        page.get_by_role('tab',name=title,exact=True).click()
        assert 'stale' in page.locator('#snapshot-status').inner_text().lower()
        assert 'last known' in page.locator('.source-list').inner_text().lower()
    page.screenshot(path=str(ARTIFACTS / 'outage-last-known.png'),full_page=True)
    page.unroute('**' + API + 'snapshot')
    with page.expect_response('**' + API + 'snapshot') as response:
        page.get_by_role('button',name='Refresh snapshot',exact=True).click()
    assert response.value.status == 200
    page.wait_for_function('() => document.querySelector("#workspace").dataset.transport === "connected"')
    assert not page.locator('#outage-banner').is_visible()
    page.get_by_role('button',name='Pause updates',exact=True).click()
    assert 'paused' in page.locator('#snapshot-status').inner_text().lower()
    assert page.get_by_role('button',name='Resume updates',exact=True).is_visible()
    assert not errors
    (ARTIFACTS / 'outage-receipt.json').write_text(json.dumps({'controlled_consumer_outage':True,'live_service_stopped':False,'retained_snapshot_time':last,'recovery':True,'errors':errors},indent=2))
    page.close()


def test_cold_outage_storage_denial_and_unknowns_remain_usable(chooser_url,browser):
    page=browser.new_page()
    errors=[]
    page.on('pageerror',lambda error:errors.append(str(error)))
    page.add_init_script("Object.defineProperty(window,'localStorage',{get(){throw new Error('denied')}})")
    page.route('**'+API+'snapshot',lambda route:route.abort('connectionrefused'))
    page.goto(chooser_url+'/design-chooser/')
    page.wait_for_function('document.querySelector("#snapshot-status").textContent.includes("unavailable")')
    assert 'No snapshot' in page.locator('#workspace').inner_text()
    assert page.locator('#workspace [data-source]').count() == 0
    page.get_by_role('tab',name='Instrument desk',exact=True).click()
    page.get_by_role('button',name='Light',exact=True).click()
    page.get_by_role('button',name='Save as default view',exact=True).click()
    assert 'storage unavailable' in page.locator('#choice-state').inner_text()
    assert page.get_by_role('button',name='Download preference',exact=True).is_enabled()
    assert not errors
    page.close()


def test_render_all_six_designs_responsive_without_overflow_or_browser_errors(chooser_url,browser):
    matrices=[]
    layouts=[('spatial','Spatial cockpit'),('balanced','Operations split'),('dense','Instrument desk')]
    dimensions=[(1536,1100),(1440,900),(1024,768),(768,1024),(390,844),(320,740)]
    for width,height in dimensions:
        page=browser.new_page(viewport={'width':width,'height':height},reduced_motion='reduce')
        errors=[]
        requests=[]
        page.on('pageerror',lambda e:errors.append(str(e)))
        page.on('console',lambda m:errors.append(m.text) if m.type=='error' else None)
        page.on('request',lambda r:requests.append({'method':r.method,'url':r.url}))
        open_live(page,chooser_url)
        page.evaluate('document.fonts.ready')
        for layout,title in layouts:
            page.get_by_role('tab',name=title,exact=True).click()
            for theme in ('dark','light'):
                page.get_by_role('button',name=theme.title(),exact=True).click()
                page.evaluate('window.scrollTo(0,0)')
                geometry=page.evaluate('''() => ({width:innerWidth,scrollWidth:document.documentElement.scrollWidth,
                    overflowing:Array.from(document.querySelectorAll('#workspace *')).filter(e=>e.getBoundingClientRect().right>innerWidth+1).map(e=>({tag:e.tagName,cls:e.className,width:e.getBoundingClientRect().width})),
                    animations:document.getAnimations().length,fonts:Array.from(document.fonts).map(f=>({family:f.family,status:f.status}))})''')
                assert geometry['scrollWidth']<=width, (layout,theme,width,geometry)
                assert not geometry['overflowing'], (layout,theme,width,geometry)
                assert geometry['animations']==0
                assert all(font['status']=='loaded' for font in geometry['fonts'])
                assert page.get_by_role('progressbar').count()==0
                filename=f'{layout}-{theme}.png' if width==1536 else f'{layout}-{theme}-{width}.png'
                page.screenshot(path=str(ARTIFACTS/filename),full_page=True)
                snapshot=page.request.get(chooser_url+API+'snapshot').json()
                row={'layout':layout,'theme':theme,'file':filename,'viewport':{'width':width,'height':height},'snapshot_generated_at':snapshot['generated_at'],'geometry':geometry}
                if width==1536:
                    (ARTIFACTS/f'{layout}-{theme}-snapshot.json').write_text(json.dumps(snapshot,indent=2))
                matrices.append(row)
                (ARTIFACTS/'render-matrix.json').write_text(json.dumps(matrices,indent=2))
        assert not errors,errors
        assert all(req['method']=='GET' and req['url'].startswith(chooser_url) for req in requests)
        (ARTIFACTS/f'network-{width}.json').write_text(json.dumps({'requests':requests,'errors':errors},indent=2))
        page.close()
    assert len(matrices)==len(layouts)*2*len(dimensions)


def test_gallery_links_six_real_captures_to_live_layouts(chooser_url,browser):
    page=browser.new_page(viewport={'width':1536,'height':1100})
    open_live(page,chooser_url)
    page.get_by_role('button',name='Compare images',exact=True).click()
    page.wait_for_selector('#gallery img')
    assert page.locator('#gallery img').count()==6
    assert page.locator('#gallery').inner_text().find('Captured views, not current telemetry')>=0
    assert page.locator('#gallery img').evaluate_all('(images)=>images.every(i=>i.complete && i.naturalWidth>=1440)')
    for layout,title in [('spatial','Spatial cockpit'),('balanced','Operations split'),('dense','Instrument desk')]:
        for theme in ('dark','light'):
            page.get_by_role('button',name=f'Open {title} / {theme} live view',exact=True).click()
            assert page.locator('#workspace').is_visible()
            assert page.locator('#workspace').get_attribute('data-layout')==layout
            assert page.locator('html').get_attribute('data-hud-theme')==theme
            assert page.locator('#choice-state').inner_text().startswith('All three views available')
            page.get_by_role('button',name='Compare images',exact=True).click()
    page.screenshot(path=str(ARTIFACTS/'gallery.png'),full_page=True)
    response=page.request.get(chooser_url+'/design-chooser/gallery.json')
    manifest=response.json()
    assert len(manifest['images'])==6
    assert all(entry['sha256'] and entry['bytes']>10000 for entry in manifest['images'])
    page.close()


def test_dense_desk_places_instruments_side_by_side(chooser_url,browser):
    page=browser.new_page(viewport={'width':1536,'height':1100})
    open_live(page,chooser_url)
    page.get_by_role('tab',name='Instrument desk',exact=True).click()
    provider=page.locator('[data-section="Providers"]').bounding_box()
    processes=page.locator('[data-section="Process presence"]').bounding_box()
    assert provider and processes
    assert abs(provider['y']-processes['y'])<=1, 'dense desk uses parallel instruments, not a long stacked list'
    assert processes['x']>provider['x']
    page.locator('.provider-list button').first.click()
    assert page.locator('#inspect-title').is_visible()
    page.get_by_role('button',name='Return to selected row',exact=True).click()
    assert page.evaluate('document.activeElement.dataset.kind')=='provider'
    page.close()


def test_group_hierarchy_drilldown_breadcrumbs_and_poll_preservation(chooser_url,browser):
    page=browser.new_page(viewport={'width':1536,'height':1100})
    snapshot=open_live(page,chooser_url)
    for title in ('Spatial cockpit','Operations split','Instrument desk'):
        page.get_by_role('tab',name=title,exact=True).click()
        page.get_by_role('button',name='Browse Resources group',exact=True).click()
        assert page.locator('#inspect-title').inner_text()=='Resources'
        assert page.get_by_role('navigation',name='Inspection breadcrumb').is_visible()
        page.get_by_role('button',name='Inspect Kubernetes pods',exact=True).click()
        assert page.locator('#inspect-body [data-child-id^="pod:"]').count()==min(8,len(snapshot['k8s']['pods']))
        assert f"of {len(snapshot['k8s']['pods'])} projected children" in page.locator('#child-page').inner_text()
        first=page.locator('#inspect-body [data-child-id^="pod:"]').first
        name=first.locator('strong').inner_text()
        first.focus()
        page.keyboard.press('Enter')
        assert page.locator('#inspect-title').inner_text()==name
        assert 'workload ready' in page.locator('#inspect-body').inner_text()
        page.locator('#inspect-body .provenance summary').click()
        old=page.locator('#snapshot-time').inner_text()
        page.get_by_role('button',name='Refresh snapshot',exact=True).click()
        page.wait_for_function('(old)=>document.querySelector("#snapshot-time").textContent !== old',arg=old,timeout=25000)
        assert page.locator('#inspect-title').inner_text()==name
        assert page.locator('#inspect-body .provenance').get_attribute('open') is not None
        assert 'Kubernetes pods' in page.get_by_role('navigation',name='Inspection breadcrumb').inner_text()
        page.get_by_role('button',name='Back one level',exact=True).click()
        assert page.locator('#inspect-title').inner_text()=='Kubernetes pods'
        page.get_by_role('navigation',name='Inspection breadcrumb').get_by_role('button',name='Network',exact=True).click()
        assert page.locator('.child-list [data-child-id]').count()==8
        assert 'of 10 projected children' in page.locator('#child-page').inner_text()
        page.get_by_role('button',name='Inspect Capacity',exact=True).click()
        page.get_by_role('button',name='Inspect Capacity offers',exact=True).click()
        assert 'Optional and unqualified' in page.locator('#inspect-body').inner_text()
        assert 'unknown' in page.locator('#inspect-body').inner_text()
    page.get_by_role('button',name='Browse Capacity group',exact=True).click()
    latest=page.request.get(chooser_url+API+'snapshot').json()
    if latest['z0_service'].get('providers'):
        assert page.locator('#inspect-body [data-child-id^="provider:"]').count()==len(latest['z0_service']['providers'])
    else:
        assert 'unknown provider admission rows' in page.locator('#inspect-body').inner_text()
    page.screenshot(path=str(ARTIFACTS/'hierarchy-inspector.png'),full_page=True)
    page.close()


def test_spatial_nodes_are_keyboard_operable_groups(chooser_url,browser):
    page=browser.new_page()
    open_live(page,chooser_url)
    page.get_by_role('button',name='Inspect network groups',exact=True).focus()
    page.keyboard.press('Enter')
    assert page.locator('#inspect-title').inner_text()=='Network'
    for selector,title in [('.orbit-top','Services'),('.orbit-left','Capacity'),('.orbit-right','Resources'),('.orbit-bottom','Sources & gaps')]:
        page.locator(selector).click()
        assert page.locator('#inspect-title').inner_text()==title
        assert page.locator('#inspect-body').inner_text()
    page.close()


def test_server_cli_collision_and_read_only_failure_paths(tmp_path):
    import select
    import subprocess
    import sys
    runner=ROOT/'scripts/design_chooser.py'
    assert subprocess.run([sys.executable,str(runner),'--help'],capture_output=True).returncode==0
    process=subprocess.Popen([sys.executable,str(runner),'--port','0','--artifacts',str(tmp_path)],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
    try:
        assert process.stdout and select.select([process.stdout],[],[],10)[0]
        receipt=json.loads(process.stdout.readline())
        assert receipt['pid']==process.pid
        assert receipt['url'].startswith('http://127.0.0.1:')
        status,_,headers=read(receipt['url'])
        assert status==200
        assert "connect-src 'self'" in headers['Content-Security-Policy']
        collision=subprocess.run([sys.executable,str(runner),'--port',str(receipt['port'])],capture_output=True,timeout=10)
        assert collision.returncode!=0
        assert read(receipt['url'])[0]==200
        origin=receipt['url'].split('/design-chooser/')[0]
        assert json.loads(read(origin+'/design-chooser/gallery.json')[1])['images']==[]
        assert read(origin+'/design-chooser/gallery/../../README.md')[0]==404
    finally:
        process.terminate()
        process.communicate(timeout=10)
    assert process.returncode==0
    with pytest.raises(urllib.error.URLError):
        urllib.request.urlopen(receipt['url'],timeout=2)
    module=load_server()
    with Running(module.make_server(0,upstream=origin,artifacts=tmp_path)) as owned:
        status,body,_=read(owned.url+API+'snapshot')
        assert status==502
        assert json.loads(body)['error']=='read-only source unavailable'
    (ARTIFACTS/'server-cli-receipt.json').write_text(json.dumps({'loopback':True,'collision_failed':True,'cleanup':True,'upstream_outage_status':status},indent=2))


def test_invalid_local_design_id_is_not_treated_as_a_layout(chooser_url,browser):
    page=browser.new_page()
    errors=[]
    page.on('pageerror',lambda e:errors.append(str(e)))
    page.goto(chooser_url+'/design-chooser/?design=constructor&theme=unexpected')
    page.wait_for_selector('[data-loaded="true"]')
    assert page.locator('#workspace').get_attribute('data-layout')=='spatial'
    assert page.locator('html').get_attribute('data-hud-theme')=='dark'
    assert not errors
    page.close()


def test_keyboard_disclosure_focus_and_pause_survive_refresh(chooser_url,browser):
    page=browser.new_page()
    open_live(page,chooser_url)
    page.get_by_role('tab',name='Instrument desk',exact=True).click()
    summary=page.locator('[data-section="Providers"] > summary')
    summary.focus()
    page.keyboard.press('Enter')
    assert not page.locator('[data-section="Providers"]').evaluate('(el)=>el.open')
    old=page.locator('#snapshot-time').inner_text()
    page.wait_for_function('(before)=>document.querySelector("#snapshot-time").textContent!==before',arg=old,timeout=25000)
    assert summary.evaluate('(el)=>el===document.activeElement')
    assert not page.locator('[data-section="Providers"]').evaluate('(el)=>el.open')
    page.keyboard.press('Enter')
    assert page.locator('[data-section="Providers"]').evaluate('(el)=>el.open')
    page.get_by_role('button',name='Browse Sources & gaps group',exact=True).click()
    page.get_by_role('button',name='Inspect source z0_health',exact=True).last.click()
    raw=page.locator('#inspect-body .raw > summary')
    raw.focus()
    page.keyboard.press('Enter')
    old=page.locator('#snapshot-time').inner_text()
    page.wait_for_function('(before)=>document.querySelector("#snapshot-time").textContent!==before',arg=old,timeout=25000)
    assert raw.evaluate('(el)=>el===document.activeElement')
    assert page.locator('#inspect-body .raw').evaluate('(el)=>el.open')
    page.get_by_role('button',name='Pause updates',exact=True).focus()
    page.keyboard.press('Enter')
    assert page.get_by_role('button',name='Resume updates',exact=True).evaluate('(el)=>el===document.activeElement')
    page.keyboard.press('Enter')
    assert page.get_by_role('button',name='Pause updates',exact=True).is_visible()
    page.close()
