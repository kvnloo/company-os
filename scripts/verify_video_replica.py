#!/usr/bin/env python3
"""One-command, real-browser proof on an owned ephemeral loopback listener.

Requires Playwright + Pillow. Uses system Chromium; never attaches to Zen,
never contacts a live snapshot, never kills another listener. Artifact output is
explicit and outside the implementation worktree by default.
"""
from pathlib import Path
from urllib.request import urlopen, Request
from urllib.error import HTTPError
import argparse
import io
import json
import threading
from PIL import Image, ImageChops
from playwright.sync_api import sync_playwright
from video_replica import make_server, ROOT


def verify(artifacts):
    artifacts.mkdir(parents=True,exist_ok=True)
    checks=[]
    def bounds(locator):
        rect=locator.bounding_box()
        assert rect is not None, 'Expected visible geometry'
        return rect
    def check(name,condition):
        if not condition: raise AssertionError(name)
        checks.append({'name':name,'passed':True})
    with make_server(0) as server:
        thread=threading.Thread(target=server.serve_forever,daemon=True)
        thread.start()
        base=f'http://127.0.0.1:{server.server_port}'
        try:
            with urlopen(base+'/video-replica',timeout=5) as response:
                check('owned server HTTP readiness',response.status==200)
            for path,method,expected in [('/api/plugins/company-os/snapshot','GET',404),('/video-replica','POST',405),('/video-replica/%2e%2e/%2e%2e/README.md','GET',404)]:
                try:
                    urlopen(Request(base+path,method=method),timeout=5)
                    raise AssertionError(f'{method} {path} unexpectedly allowed')
                except HTTPError as error:
                    check(f'{method} {path} returns {expected}',error.code==expected)
                    error.close()
            with sync_playwright() as p:
                browser=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox','--disable-dev-shm-usage'])
                page=browser.new_page(viewport={'width':1496,'height':1230},device_scale_factor=1,reduced_motion='reduce')
                errors=[];requests=[]
                page.on('pageerror',lambda error:errors.append(str(error)))
                page.on('console',lambda message: errors.append(message.text) if message.type=='error' else None)
                page.on('request',lambda request:requests.append(request.url))
                page.goto(base+'/video-replica?native=1',wait_until='networkidle')
                page.evaluate('document.fonts.ready')
                frame=page.locator('#replica-frame')
                box=bounds(frame)
                check('native 1496 x 1080 geometry',box['width']==1496 and box['height']==1080)
                check('14 lanes, 6 metric cards, 10 priority labels',page.locator('.lane-row').count()==14 and page.locator('.metric-card').count()==6 and page.locator('.priority').count()==10)
                check('reference-only receipt',page.evaluate('window.replicaReceipt.mode==="reference-fixture" && window.replicaReceipt.liveConnected===false'))
                check('fixture label outside composition',not frame.locator('.fixture-notice').count() and 'NOT live CompanyOS' in page.locator('.fixture-notice').inner_text())
                check('only separate photo raster inside composition',frame.locator('img').count()==1 and (frame.locator('img').get_attribute('src') or '').endswith('tahoe-day.jpg'))
                check('reduced motion starts paused',page.locator('#motion').get_attribute('aria-pressed')=='false' and frame.get_attribute('data-motion-seconds')=='0.000')
                page.locator('#stage-holder').screenshot(path=str(artifacts/'browser-native.png'))
                page.locator('button[data-view=original]').click()
                original=page.locator('#stage-holder').screenshot(path=str(artifacts/'browser-original-control.png'))
                check('original control shows exact source pixels',ImageChops.difference(Image.open(io.BytesIO(original)).convert('RGB'),Image.open(ROOT/'web/video-replica/assets/original-frame.png').convert('RGB')).getbbox() is None)
                page.locator('button[data-view=overlay]').click()
                check('overlay control shows reference at 50 percent',page.locator('#original-overlay').is_visible() and page.locator('#original-overlay').evaluate('(e)=>getComputedStyle(e).opacity')=='0.5')
                slider=page.locator('#overlay-opacity');slider.focus();slider.press('Home')
                for _ in range(20):slider.press('ArrowRight')
                check('overlay opacity keyboard control',page.locator('#original-overlay').evaluate('(e)=>getComputedStyle(e).opacity')=='0.2')
                page.locator('#stage-holder').screenshot(path=str(artifacts/'browser-overlay-control.png'))
                page.locator('button[data-view=side]').click()
                left=bounds(page.locator('#stage-holder'));right=bounds(page.locator('#side-reference'))
                check('side by side displays both full frames even from native mode',left['width']==right['width'] and right['x']+right['width']<=1496)
                page.screenshot(path=str(artifacts/'browser-side-by-side.png'))
                page.locator('#reset').click()
                check('reset hides reference and restores native frame',not page.locator('#original-overlay').is_visible() and bounds(frame)['width']==1496)
                # The P4 tooltip was directly visible in the recording. Test both
                # its pointer entry and accessible keyboard-equivalent exposure.
                page.evaluate('scrollTo(0,0)')
                page.mouse.move(582,360)
                check('observed P4 pointer tooltip',page.locator('#ring-tooltip').is_visible() and '68.6% done' in page.locator('#ring-tooltip').inner_text())
                page.locator('#stage-holder').screenshot(path=str(artifacts/'browser-p4-tooltip.png'))
                page.mouse.move(730,620)
                check('tooltip closes on pointer leave',not page.locator('#ring-tooltip').is_visible())
                page.locator('.ring-hit').focus()
                check('tooltip keyboard focus equivalent',page.locator('#ring-tooltip').is_visible())
                page.locator('.ring-hit').press('Escape')
                check('Escape closes tooltip',not page.locator('#ring-tooltip').is_visible())
                before=page.locator('[data-flight]').first.get_attribute('transform')
                frozen=page.locator('#metric-strip').inner_text()
                page.locator('#motion').click()
                page.wait_for_timeout(220)
                after=page.locator('[data-flight]').first.get_attribute('transform')
                check('measured flight tracks move during play',before!=after)
                check('motion does not alter fixture metrics or scene geometry',page.locator('#metric-strip').inner_text()==frozen and bounds(frame)['width']==1496)
                page.locator('#motion').click()
                paused=page.locator('[data-flight]').first.get_attribute('transform')
                page.wait_for_timeout(130)
                check('pause freezes flight phase',page.locator('[data-flight]').first.get_attribute('transform')==paused)
                page.emulate_media(reduced_motion='no-preference')
                page.locator('#motion').click()
                page.emulate_media(reduced_motion='reduce')
                page.wait_for_timeout(60)
                check('new reduced-motion preference pauses playback',page.locator('#motion').get_attribute('aria-pressed')=='false')
                page.locator('#reset').click()
                check('reset returns exact initial flight phase',page.locator('[data-flight]').first.get_attribute('transform')==before and frame.get_attribute('data-motion-seconds')=='0.000')
                page.goto(base+'/video-replica',wait_until='networkidle')
                page.set_viewport_size({'width':1280,'height':900})
                page.wait_for_timeout(50)
                page.screenshot(path=str(artifacts/'browser-fit-with-controls.png'))
                check('fit mode shows full composition without reflow',bounds(frame)['width']<=1280 and bounds(frame)['height']<900 and page.locator('.fixture-notice').is_visible())
                check('seven issue-defined unconnected binding rows',page.locator('#binding-map article').count()==7)
                check('no external or snapshot network requests',all(url.startswith(base+'/video-replica') for url in requests) and not any('/api/' in url for url in requests))
                check('no console/page errors',not errors)
                receipt={'checks':checks,'check_count':len(checks),'browser':browser.version,'viewport_native':[1496,1080],'dpr':1,'requests':requests,'errors':errors,'mode':'reference-only','source_authority':'none','gui_gate':'Jev returned no_key; deterministic owned-browser acceptance harness, no user browser attached'}
                (artifacts/'executed-browser-tests.json').write_text(json.dumps(receipt,indent=2))
                print(json.dumps({'passed':len(checks),'failed':0,'browser':browser.version,'artifacts':str(artifacts)},indent=2))
                browser.close()
        finally:
            server.shutdown();thread.join(3)
            if thread.is_alive():raise RuntimeError('Owned test server did not shut down')

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--artifacts',type=Path,default=Path('/workspace/zer0/data/operations/company-os-recovery/video-replica'))
    verify(parser.parse_args().artifacts)
