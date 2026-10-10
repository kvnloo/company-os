"""Static preview contract, exercised through HTTP and real Chromium.
Run with the installed test environment; no plugin/profile installation.
"""
import importlib.util
import json
import os
from pathlib import Path
import threading
import urllib.error
import urllib.request

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope='module')
def preview_url():
    spec = importlib.util.spec_from_file_location('company_os_style_preview', ROOT / 'scripts/style_preview.py')
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    server = module.make_server(0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f'http://127.0.0.1:{server.server_port}/style-preview/'
    finally:
        server.shutdown()
        server.server_close()
        thread.join(5)
        assert not thread.is_alive()


def test_preview_route_is_explicitly_static_not_telemetry(preview_url):
    try:
        with urllib.request.urlopen(preview_url) as response:
            status, html = response.status, response.read().decode()
    except urllib.error.HTTPError as error:
        status, html = error.code, error.read().decode()
    assert status == 200, 'the dedicated style-preview route must exist'
    assert 'Static architecture' in html
    assert 'Not live telemetry' in html
    assert 'No microphone' in html
    assert '<title>CompanyOS — v3 style preview</title>' in html


def test_real_browser_theme_choice_is_local_persistent_and_accessible(preview_url):
    from playwright.sync_api import sync_playwright
    with sync_playwright() as pw:
        browser = pw.chromium.launch(executable_path='/usr/bin/chromium', headless=True,
                                    args=['--disable-dev-shm-usage'])
        page = browser.new_page(viewport={'width': 1536, 'height': 1024})
        requests, errors = [], []
        page.on('request', lambda req: requests.append((req.method, req.url)))
        page.on('pageerror', lambda error: errors.append(str(error)))
        page.goto(preview_url)
        assert page.locator('html').get_attribute('data-hud-theme') == 'dark'
        page.get_by_role('button', name='Light', exact=True).click()
        assert page.locator('html').get_attribute('data-hud-theme') == 'light'
        assert page.get_by_role('button', name='Light', exact=True).get_attribute('aria-pressed') == 'true'
        page.reload()
        assert page.locator('html').get_attribute('data-hud-theme') == 'light'
        page.get_by_role('button', name='Dark', exact=True).click()
        assert page.locator('html').get_attribute('data-hud-theme') == 'dark'
        assert all(method == 'GET' and url.startswith(preview_url.split('/style-preview/')[0]) for method, url in requests)
        assert not errors
        browser.close()


def test_browser_render_matrix_and_read_only_controls(preview_url, tmp_path):
    from playwright.sync_api import sync_playwright
    artifacts = Path(os.environ.get('STYLE_PREVIEW_ARTIFACTS', str(tmp_path)))
    artifacts.mkdir(parents=True, exist_ok=True)
    rows = []
    with sync_playwright() as pw:
        browser = pw.chromium.launch(executable_path='/usr/bin/chromium', headless=True,
                                    args=['--disable-dev-shm-usage'])
        for width, height in [(1536, 1024), (1440, 900), (1024, 768), (768, 1024), (390, 844), (320, 740)]:
            page = browser.new_page(viewport={'width': width, 'height': height}, reduced_motion='reduce')
            errors, requests, responses = [], [], []
            page.on('pageerror', lambda error: errors.append(str(error)))
            page.on('console', lambda msg: errors.append(msg.text) if msg.type == 'error' else None)
            page.on('request', lambda req: requests.append({'method': req.method, 'url': req.url}))
            page.on('response', lambda res: responses.append({'status': res.status, 'url': res.url}))
            page.goto(preview_url)
            page.evaluate('document.fonts.ready')
            for theme in ['dark', 'light']:
                page.get_by_role('button', name=theme.capitalize(), exact=True).click()
                page.evaluate('window.scrollTo(0,0)')
                layout = page.evaluate('''() => ({
                    width: innerWidth, scrollWidth: document.documentElement.scrollWidth,
                    animations: document.getAnimations().length,
                    fonts: Array.from(document.fonts).map(f => ({family:f.family,status:f.status})),
                    variables: Object.fromEntries(['--hud-bg','--hud-panel','--hud-fg','--hud-muted','--hud-faint'].map(k=>[k,getComputedStyle(document.documentElement).getPropertyValue(k).trim()]))
                })''')
                assert layout['scrollWidth'] <= width, (width, theme, layout)
                assert layout['animations'] == 0, 'no decorative activity animation'
                assert all(font['status'] == 'loaded' for font in layout['fonts'])
                assert page.get_by_role('progressbar').count() == 0
                # Corner highlights must survive the subtle rail edge, as in v3.
                if width == 1536:
                    import io
                    from PIL import Image
                    panel = Image.open(io.BytesIO(page.locator('.hud-panel').first.screenshot())).convert('RGB')
                    corner, edge = panel.getpixel((2, 0)), panel.getpixel((20, 0))
                    assert isinstance(corner, tuple) and isinstance(edge, tuple)
                    assert sum(abs(a-b) for a,b in zip(corner, edge)) > 60, (corner, edge)
                for fg in ['--hud-fg', '--hud-muted', '--hud-faint']:
                    for bg in ['--hud-bg', '--hud-panel']:
                        assert contrast(layout['variables'][fg], layout['variables'][bg]) >= 4.5
                filename = f'{theme}-{width}x{height}.png'
                page.screenshot(path=str(artifacts / filename), full_page=True)
                if width == 1536:
                    page.screenshot(path=str(artifacts / f'{theme}-desktop-viewport.png'))
                rows.append({'theme':theme, 'viewport':{'width':width, 'height':height}, 'screenshot':filename, **layout})
            # Native keyboard disclosure; content stays non-authoritative.
            summary = page.locator('.hud-lane summary').first
            summary.focus()
            page.keyboard.press('Enter')
            assert page.locator('.hud-lane').first.get_attribute('open') is not None
            assert page.get_by_text('One owner per product or project.', exact=False).is_visible()
            page.get_by_role('link', name='Inspect architecture & source notes').click()
            assert page.url.endswith('#source-notes')
            assert page.get_by_role('heading', name='The surface, not a second system.').is_visible()
            page.get_by_role('link', name='Back to map').click()
            assert page.url.endswith('#cockpit')
            assert not errors, errors
            assert all(row['status'] == 200 for row in responses), responses
            assert all(row['method'] == 'GET' and '/api/' not in row['url'] and row['url'].startswith(preview_url.split('/style-preview/')[0]) for row in requests)
            (artifacts / f'network-{width}.json').write_text(json.dumps({'requests':requests,'responses':responses,'errors':errors}, indent=2))
            page.close()
        browser.close()
    (artifacts / 'render-matrix.json').write_text(json.dumps(rows, indent=2))
    assert len(rows) == 12


def contrast(first, second):
    def luminance(value):
        channels = [int(value[i:i+2], 16) / 255 for i in (1, 3, 5)]
        linear = [c / 12.92 if c <= .04045 else ((c + .055) / 1.055) ** 2.4 for c in channels]
        return sum(c * w for c, w in zip(linear, [.2126, .7152, .0722]))
    bright, dark = sorted([luminance(first), luminance(second)], reverse=True)
    return (bright + .05) / (dark + .05)


def test_theme_storage_denied_and_scriptless_architecture_still_work(preview_url):
    from playwright.sync_api import sync_playwright
    with sync_playwright() as pw:
        browser = pw.chromium.launch(executable_path='/usr/bin/chromium', headless=True)
        page = browser.new_page()
        page.add_init_script("Object.defineProperty(window, 'localStorage', {get() {throw new Error('disabled')}})")
        page.goto(preview_url)
        page.get_by_role('button', name='Light', exact=True).click()
        assert page.locator('html').get_attribute('data-hud-theme') == 'light'
        page.close()
        page = browser.new_page(java_script_enabled=False)
        page.goto(preview_url)
        assert page.get_by_text('Static architecture', exact=True).is_visible()
        page.locator('.hud-lane summary').first.click()
        assert page.locator('.hud-lane').first.get_attribute('open') is not None
        browser.close()


def test_preview_server_cli_is_loopback_only_and_owns_no_api():
    import select
    import subprocess
    import sys
    runner = ROOT / 'scripts/style_preview.py'
    help_result = subprocess.run([sys.executable, str(runner), '--help'], capture_output=True, text=True)
    assert help_result.returncode == 0, 'the owned preview server CLI must be available'
    process = subprocess.Popen([sys.executable, str(runner), '--port', '0'], stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE, text=True)
    try:
        assert process.stdout is not None
        assert select.select([process.stdout], [], [], 10)[0], 'server did not announce its actual bound port'
        receipt = json.loads(process.stdout.readline())
        assert receipt['mode'] == 'static-style-preview'
        assert receipt['pid'] == process.pid
        assert receipt['url'].startswith('http://127.0.0.1:')
        with urllib.request.urlopen(receipt['url']) as response:
            assert response.status == 200
            assert response.headers['Content-Security-Policy'].find("connect-src 'none'") >= 0
        origin = receipt['url'].split('/style-preview/')[0]
        for path in ['/api/plugins/company-os/snapshot', '/index.html', '/fonts/', '/../README.md']:
            with pytest.raises(urllib.error.HTTPError) as error:
                urllib.request.urlopen(origin + path)
            assert error.value.code == 404
        with pytest.raises(urllib.error.HTTPError) as error:
            urllib.request.urlopen(urllib.request.Request(receipt['url'], data=b'{}', method='POST'))
        assert error.value.code == 405
        # Occupancy must fail without attaching to or killing the first server.
        second = subprocess.run([sys.executable, str(runner), '--port', str(receipt['port'])],
                                capture_output=True, text=True, timeout=10)
        assert second.returncode != 0
        assert process.poll() is None
        with urllib.request.urlopen(receipt['url']) as response:
            assert response.status == 200
    finally:
        process.terminate()
        process.communicate(timeout=10)
