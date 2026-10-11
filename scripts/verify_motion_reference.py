#!/usr/bin/env python3
"""Real isolated Chromium acceptance; owns only its ephemeral loopback server."""
import argparse, json, threading, io, time
from pathlib import Path
from urllib.request import urlopen
from playwright.sync_api import sync_playwright
from PIL import Image,ImageChops
from reference_motion import make_server,ROOT

def verify(out):
    out.mkdir(parents=True,exist_ok=True);checks=[]
    def check(name,truth):
        assert truth,name
        checks.append({'name':name,'passed':True})
    with make_server(0) as server:
        thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
        base=f'http://127.0.0.1:{server.server_port}'
        try:
            with urlopen(base+'/motion-reference',timeout=3) as response:
                check('exact motion-reference route is served',response.status==200 and b'replica.js' in response.read())
            with sync_playwright() as p:
                browser=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox','--disable-dev-shm-usage'])
                page=browser.new_page(viewport={'width':1496,'height':1350},device_scale_factor=1,reduced_motion='reduce')
                errors=[];requests=[]
                def wait_state(predicate):
                    deadline=time.monotonic()+2
                    while time.monotonic()<deadline:
                        if page.evaluate(predicate):return
                        page.wait_for_timeout(30)
                    raise AssertionError({'predicate':predicate,'state':page.evaluate('window.motionReference.state()'),'errors':errors})
                page.on('pageerror',lambda x:errors.append(str(x)))
                page.on('request',lambda x:requests.append(x.url))
                page.goto(base+'/video-replica?native=1',wait_until='networkidle');page.evaluate('document.fonts.ready')
                check('full-clip scrub control exists',page.locator('#motion-scrub').count()==1)
                check('starts paused under reduced motion',not page.evaluate('window.motionReference.state().playing'))
                page.locator('#stage-holder').screenshot(path=str(out/'browser-000.000.png'))
                initial=page.locator('#replica-frame').screenshot()
                for t in [0.5,2.5,4,5,6,7,8.5,9,10.5,11,12,14,15.133333]:
                    page.locator('#motion-scrub').fill(str(t))
                    page.wait_for_timeout(65)
                    check(f'scrub reaches {t}s',abs(page.evaluate('window.motionReference.state().time')-t)<.002)
                    page.locator('#stage-holder').screenshot(path=str(out/f'browser-{t:07.3f}.png'))
                page.locator('#motion-scrub').focus();page.locator('#motion-scrub').press('Home');page.locator('#motion-scrub').press('ArrowRight')
                page.locator('#motion-scrub').fill('11')
                check('observed late summary is not frozen to first frame',page.locator('#lane-totals b').all_text_contents()==['19','22','9,531','0','4'])
                check('observed lane reorder is replayed', 'ltg-m6-fix-wolfxl-xlsx-render-png-crash' in page.locator('.lane-column').first.locator('.lane-name').first.inner_text())
                page.locator('#motion-scrub').focus();page.locator('#motion-scrub').press('Home');page.locator('#motion-scrub').press('ArrowRight')
                check('keyboard scrub advances one measured sample and retains focus',page.evaluate('Math.abs(window.motionReference.state().time-.05)<1e-6 && document.activeElement.id==="motion-scrub"'))
                page.locator('#motion').click();wait_state('window.motionReference.state().time>.1')
                check('play advances reference timeline',page.evaluate('window.motionReference.state().time>.1'))
                page.locator('#motion').click();frozen=page.evaluate('window.motionReference.state().time');page.wait_for_timeout(120)
                check('pause freezes the entire timeline',page.evaluate('window.motionReference.state().time')==frozen)
                page.locator('#motion-scrub').fill('2.5')
                zoom=page.locator('#camera-layer').get_attribute('style')
                page.locator('#camera-toggle').click()
                check('camera can be removed independently',zoom!=page.locator('#camera-layer').get_attribute('style'))
                page.locator('#stage-holder').screenshot(path=str(out/'camera-separated-002.500.png'))
                page.locator('#camera-toggle').click()
                page.emulate_media(reduced_motion='no-preference');page.locator('#motion').click();page.emulate_media(reduced_motion='reduce');page.wait_for_timeout(40)
                check('preference change pauses',not page.evaluate('window.motionReference.state().playing'))
                page.locator('#motion-scrub').fill('15.1');page.locator('#motion').click();wait_state('!window.motionReference.state().playing && window.motionReference.state().time>15.13')
                check('end stops without inventing a periodic loop',page.evaluate('!window.motionReference.state().playing && window.motionReference.state().time>15.13'))
                page.locator('#reset').click();page.evaluate('document.activeElement.blur()')
                reset_pixels=page.locator('#replica-frame').screenshot(path=str(out/'browser-reset.png'))
                reset_diff=ImageChops.difference(Image.open(io.BytesIO(initial)).convert('RGB'),Image.open(io.BytesIO(reset_pixels)).convert('RGB'))
                reset_diff.save(out/'reset-difference.png')
                import numpy as np
                diff=np.array(reset_diff)
                reset_metrics={'changed_pixels':int((diff.max(2)>0).sum()),'max_channel_error':int(diff.max())}
                (out/'reset-metrics.json').write_text(json.dumps(reset_metrics))
                check('reset restores exact initial component pixels',reset_metrics['changed_pixels']==0)
                check('reset restores exact clock and initial summary state',page.evaluate('window.motionReference.state().time===0 && !window.motionReference.state().playing') and page.locator('#lane-totals b').all_text_contents()==['18','16','9,847','0','3'])
                page.locator('button[data-view=side]').click();page.screenshot(path=str(out/'browser-side-by-side.png'))
                check('side-by-side fits both full frames',page.locator('#side-reference').bounding_box()['x']+page.locator('#side-reference').bounding_box()['width']<=1496)
                page.locator('#motion-scrub').fill('2.5')
                wait_state('document.querySelector("#side-moving-reference").readyState>=2 && !document.querySelector("#side-moving-reference").seeking')
                check('comparison-only source video seeks to same time',abs(page.locator('#side-moving-reference').evaluate('(v)=>v.currentTime')-2.5)<.02)
                page.screenshot(path=str(out/'browser-synchronized-source.png'))
                page.locator('button[data-view=original]').click()
                wait_state('document.querySelector("#moving-reference").readyState>=2 && !document.querySelector("#moving-reference").seeking')
                check('moving original comparison visible outside replica root',page.locator('#moving-reference').is_visible() and page.locator('#replica-frame video').count()==0)
                check('composition raster restriction remains intact',page.locator('#replica-frame img').count()==1 and (page.locator('#replica-frame img').get_attribute('src') or '').endswith('tahoe-day.jpg'))
                check('no operational or external requests',all(x.startswith(base+'/video-replica') for x in requests))
                check('no page errors',not errors)
                receipt={'checks':checks,'count':len(checks),'errors':errors,'requests':requests,'browser':browser.version,'source':'real isolated Chromium; no everyday browser attached','jev':'no_key; deterministic acceptance harness'}
                (out/'browser-tests.json').write_text(json.dumps(receipt,indent=2));print(json.dumps({'passed':len(checks),'errors':errors}));browser.close()
        finally:server.shutdown();thread.join(3)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);verify(p.parse_args().out)
