#!/usr/bin/env python3
"""Owned headless-browser acceptance. Normal captures use real read-only GET data.
Negative injection cases are explicitly test fixtures, never demonstration data.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import threading
import time
from playwright.sync_api import sync_playwright
from motion_lab import make_server


def verify(artifacts, base=None):
    artifacts.mkdir(parents=True, exist_ok=True)
    server=thread=None
    checks=[]
    def check(name, condition):
        if not condition: raise AssertionError(name)
        checks.append({'name':name,'passed':True})
    if base is None:
        server=make_server(0,artifacts=artifacts)
        thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
        base=f'http://127.0.0.1:{server.server_port}'
    try:
        with sync_playwright() as p:
            browser=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox','--disable-dev-shm-usage'])
            context=browser.new_context(viewport={'width':1600,'height':1200},device_scale_factor=1,reduced_motion='reduce')
            page=context.new_page()
            errors=[];console=[];requests=[]
            page.on('pageerror',lambda e:errors.append(str(e)))
            page.on('console',lambda m:console.append(m.text) if m.type=='error' else None)
            context.on('request',lambda r:requests.append({'url':r.url,'method':r.method}))
            def receipt(): return page.evaluate('window.motionReceipt')
            def wait_state(status):
                deadline=time.monotonic()+35
                while time.monotonic()<deadline:
                    if receipt()['transport']==status and not page.locator('#refresh').is_disabled():return
                    page.wait_for_timeout(80)
                raise AssertionError(f'Expected {status}, got {receipt()}')
            def wait_ready(): wait_state('connected')
            def refresh(): page.locator('#refresh').click();wait_ready()
            page.goto(base+'/motion-lab',wait_until='networkidle');wait_ready()
            page.evaluate('document.fonts.ready')
            check('three distinct creative variants',page.locator('[data-variant]').count()==3)
            check('ten rings, six cards, fourteen binding lanes',page.locator('.ring-control').count()==10 and page.locator('.metric-card').count()==6 and page.locator('.lane-row').count()==14)
            check('reduced motion begins off and paused',receipt()['motionOff'] and not receipt()['playing'] and page.locator('#play').is_disabled())
            check('safe source actually connected, no fixture fallback',receipt()['transport']=='connected' and receipt()['snapshotAt'] is not None)
            for row in page.locator('.lane-row').all():
                source=row.get_attribute('data-source');assert source is not None;row.click()
                check('linked source identity: '+source,page.locator('#evidence').get_attribute('data-source')==source and page.locator('.metric-card[aria-pressed=true]').get_attribute('data-bound-source')==source)
            for ring in page.locator('.ring-control').all():
                source=ring.get_attribute('data-source');assert source is not None;ring.focus();ring.press('Enter')
                check('keyboard ring selection: '+source,receipt()['selected']==source)
            page.locator('.lane-row[data-source=z0_outcomes]').click()
            check('exact path shown, not inferred causal relationship','z0_service.outcome_coverage' in page.locator('#facts').inner_text())
            for variant in ['trace','focus','compare']:
                page.locator(f'[data-variant={variant}]').click()
                check('switch '+variant+' preserves selection',receipt()['variant']==variant and receipt()['selected']=='z0_outcomes')
                page.locator('#scrub').focus();page.locator('#scrub').press('Home')
                check(variant+' scrub Home',receipt()['phase']==0)
                page.locator('#scrub').press('End')
                check(variant+' scrub End',receipt()['phase']==1)
                page.locator('#cockpit').screenshot(path=str(artifacts/(variant+'.png')))
            page.locator('[data-variant=trace]').click()
            page.locator('#source-challenge').click()
            check('source provenance is explicit',page.locator('#provenance').get_attribute('open') is not None and 'source_digest' in page.locator('#source-meta').inner_text())
            selected=receipt()['selected']
            focused=page.locator(f'.lane-row[data-source={selected}]');focused.focus()
            page.evaluate('document.querySelector("#refresh").click()')
            focused.focus();wait_ready()
            check('GET rebind preserves actual focus and disclosure',page.evaluate('document.activeElement.dataset.source')==selected and receipt()['selected']==selected and page.locator('#provenance').get_attribute('open') is not None)
            page.evaluate('window.scrollTo(0,130)')
            page.locator('#enter-lens').click();before=page.evaluate('scrollY')
            page.locator('[data-variant=focus]').click();page.locator('.lane-row[data-source=hermes_cluster]').click()
            page.locator('#source-challenge').click()
            page.locator('#pin').click()
            pin=json.loads(page.evaluate('localStorage.getItem("companyos.motion-lab.pin.v1")'))
            check('explicit pin stores only presentation recipe',set(pin)=={'schema','selected','variant'} and pin['selected']=='hermes_cluster' and pin['variant']=='focus')
            page.locator('#restore').click()
            check('restore recovers original selection and mode',receipt()['selected']==selected and receipt()['variant']=='trace' and not receipt()['lens'])
            check('restore recovers disclosure and reading position',page.locator('#provenance').get_attribute('open') is not None and abs(page.evaluate('scrollY')-before)<3)
            page.locator('#recall').click()
            check('recall enters a private lens, not production state',receipt()['lens'] and receipt()['variant']=='focus' and receipt()['selected']=='hermes_cluster')
            page.locator('.lane-row[data-source=z0_readiness]').click();page.locator('#back').click()
            check('Back recovers previous stable source',receipt()['selected']=='hermes_cluster')
            page.keyboard.press('Escape')
            check('Escape restores lens',not receipt()['lens'] and receipt()['selected']==selected)
            page.reload(wait_until='networkidle');wait_ready()
            check('pin survives reload without auto-changing cockpit',receipt()['pin']['selected']=='hermes_cluster' and receipt()['selected']=='z0_readiness' and not receipt()['lens'])
            page.locator('[data-variant=compare]').click()
            check('no historical anchor invented',receipt()['anchorAt'] is None and 'Capture A' in page.locator('#compare-note').inner_text())
            page.locator('.lane-row[data-source=z0_outcomes]').click()
            page.locator('#capture-anchor').click()
            check('A capture is explicit, memory-only',receipt()['anchorAt']==receipt()['snapshotAt'] and receipt()['lens'])
            a=receipt()['anchorAt'];refresh()
            check('refresh updates B without rewriting A',receipt()['anchorAt']==a and 'matched field' in page.locator('#compare-note').inner_text())
            page.locator('#hypothesis').check()
            check('counterfactual withholds evidence, never invents outcomes',receipt()['hypothesis'] and page.locator('#compare-rows').inner_text().count('withheld · hypothesis')>0 and 'ILLUSTRATIVE BRANCH' in page.locator('#compare-note').inner_text())
            page.locator('#cockpit').screenshot(path=str(artifacts/'hypothesis.png'))
            page.locator('#hypothesis').uncheck()
            page.locator('#cockpit').screenshot(path=str(artifacts/'compare.png'))
            page.locator('#discard').click()
            check('discard erases comparison but retains cockpit',receipt()['anchorAt'] is None and not receipt()['hypothesis'] and not receipt()['lens'])
            page.locator('[data-variant=trace]').click()
            page.emulate_media(reduced_motion='no-preference');page.locator('#motion-off').click()
            page.locator('#play').click();page.wait_for_timeout(210)
            moving=receipt()['phase'];check('play advances actual reveal frames',0<moving<1 and receipt()['playing'])
            page.locator('#play').click();paused=receipt()['phase'];page.wait_for_timeout(180)
            check('pause freezes animation phase',receipt()['phase']==paused and not receipt()['playing'])
            page.locator('#scrub').focus();page.locator('#scrub').press('Home');page.locator('#play').click()
            page.emulate_media(reduced_motion='reduce');page.wait_for_timeout(80)
            check('OS reduced motion stops an active reveal',receipt()['motionOff'] and not receipt()['playing'])
            page.locator('[data-variant=focus]').click();page.locator('.lane-row[data-source=z0_outcomes]').click()
            check('motion off retains all interactions',receipt()['variant']=='focus' and receipt()['selected']=='z0_outcomes' and receipt()['phase']==1)
            page.locator('#equal-table').click()
            check('static alternative exposes equal source fields',page.locator('#static-table article').count()==14 and 'z0_service.outcome_coverage' in page.locator('#static-table').inner_text())
            page.locator('#equal-table').click()
            page.locator('#source-challenge').click()
            if page.locator('#provenance').get_attribute('open') is not None:page.locator('#source-challenge').click()
            page.locator('#cockpit').screenshot(path=str(artifacts/'focus.png'))
            page.locator('[data-variant=trace]').click()
            page.locator('#scrub').evaluate('(e)=>{e.value="560";e.dispatchEvent(new Event("input",{bubbles:true}));}')
            page.locator('#cockpit').screenshot(path=str(artifacts/'trace.png'))
            page.screenshot(path=str(artifacts/'overview.png'),full_page=True)
            # Real native capture of unchanged reference, not a screenshot background.
            reference=context.new_page();reference.set_viewport_size({'width':1496,'height':1230})
            reference.goto(base+'/video-replica?native=1',wait_until='networkidle');reference.evaluate('document.fonts.ready')
            reference.locator('#replica-frame').screenshot(path=str(artifacts/'baseline.png'))
            check('faithful baseline is reference-only',reference.evaluate('window.replicaReceipt.mode')=='reference-fixture')
            reference.close()
            page.locator('#baseline-toggle').click()
            frame=page.frame_locator('#reference-frame')
            frame.locator('.lane-row').first.wait_for()
            check('side-by-side baseline actually renders',frame.locator('.lane-row').count()==14 and frame.locator('.metric-card').count()==6)
            page.screenshot(path=str(artifacts/'side-by-side.png'),full_page=True)
            page.locator('#baseline-toggle').click()
            matrix=[]
            for width in [390,768,1280,1600]:
                page.set_viewport_size({'width':width,'height':1000})
                for variant in ['trace','focus','compare']:
                    page.locator(f'[data-variant={variant}]').click()
                    dims=page.evaluate('({width:innerWidth,scroll:document.documentElement.scrollWidth})')
                    check(f'no clipping {variant} {width}px',dims['scroll']<=dims['width'])
                    matrix.append({'variant':variant,'width':width,'document_width':dims['scroll']})
                    if width==390:page.screenshot(path=str(artifacts/(variant+'-390.png')),full_page=True)
            page.set_viewport_size({'width':1600,'height':1200})
            # Gallery manifest references ONLY actual captured files.
            manifest={'captured_at':datetime.now(timezone.utc).isoformat(),'images':[{'file':name+'.png','sha256':hashlib.sha256((artifacts/(name+'.png')).read_bytes()).hexdigest(),'bytes':(artifacts/(name+'.png')).stat().st_size} for name in ['baseline','trace','focus','compare']]}
            if (artifacts/'motion-tour.webm').is_file():manifest['video']='motion-tour.webm'
            (artifacts/'gallery.json').write_text(json.dumps(manifest,indent=2))
            page.locator('#gallery summary').click();page.locator('#capture-gallery img').first.wait_for()
            check('four actual capture choices',page.locator('#capture-gallery img').count()==4)
            if manifest.get('video'):
                video=page.locator('#capture-gallery video')
                video.evaluate('(e)=>e.load()')
                deadline=time.monotonic()+12
                while video.evaluate('(e)=>e.readyState')<2 and time.monotonic()<deadline:page.wait_for_timeout(80)
                check('served screencast decodes in Chromium',video.evaluate('(e)=>Number.isFinite(e.duration)&&e.duration>10&&e.videoWidth>0'))
                video.evaluate('(e)=>e.play()');page.wait_for_timeout(380)
                check('served screencast really plays',video.evaluate('(e)=>e.currentTime>0&&!e.paused'))
                video.evaluate('(e)=>e.pause()')
                video.screenshot(path=str(artifacts/'video-playing.png'))
            page.locator('#gallery').screenshot(path=str(artifacts/'gallery.png'))
            check('normal path has no console or page errors',not errors and not console)
            normal_console=list(console)
            # Outage: a local presentation-only fault and a genuine network denial.
            page.locator('#outage').click();old=receipt()['snapshotAt']
            check('warm outage retains last received, marks NOT current',old is not None and 'NOT current' in page.locator('#transport').inner_text())
            page.screenshot(path=str(artifacts/'outage.png'),full_page=True)
            page.locator('#outage').click();wait_ready()
            check('outage recovers through same GET',receipt()['transport']=='connected')
            page.locator('[data-variant=compare]').click();page.locator('#capture-anchor').click()
            page.route('**/api/plugins/company-os/snapshot',lambda route:route.fulfill(status=403,content_type='application/json',body='{"test_fixture":"access denied"}'))
            page.locator('#refresh').click();wait_state('denied')
            check('denial clears current and held snapshots',receipt()['snapshotAt'] is None and receipt()['anchorAt'] is None)
            page.locator('#restore').click()
            check('restore cannot resurrect revoked facts',receipt()['snapshotAt'] is None and not page.locator('#facts b:not([data-value=null])').count())
            page.unroute('**/api/plugins/company-os/snapshot');refresh()
            # Privacy fixture: source text can never become executable/retained content.
            actual=context.request.get(base+'/api/plugins/company-os/snapshot').json()
            actual['raw_private_prompt']='PRIVATE-CANARY-DO-NOT-RENDER'
            actual['sources']['z0_readiness']['coverage']={'scope':'<img src=https://example.invalid/tracker>'}
            actual['sources']['z0_readiness']['status']='denied'
            actual.setdefault('z0_service',{}).setdefault('readiness',{})['max_active']=919191
            privacy=browser.new_context(viewport={'width':1000,'height':900},reduced_motion='reduce')
            privatepage=privacy.new_page();privatepage.on('pageerror',lambda e:errors.append(str(e)))
            privatepage.route('**/api/plugins/company-os/snapshot',lambda route:route.fulfill(status=200,content_type='application/json',body=json.dumps(actual)))
            privatepage.goto(base+'/motion-lab',wait_until='networkidle')
            body=privatepage.locator('body').inner_text()
            check('private payload and denied fields absent from DOM','PRIVATE-CANARY' not in body and '919191' not in body and 'example.invalid' not in body)
            privatepage.locator('#enter-lens').click();privatepage.locator('#pin').click()
            check('browser storage has only approved pin keys',privatepage.evaluate('Object.keys(localStorage)')==['companyos.motion-lab.pin.v1'] and 'PRIVATE' not in privatepage.evaluate('JSON.stringify(localStorage)'))
            actual['sources']['z0_readiness']['status']='ok'
            actual['z0_service']['readiness']['max_active']=42
            privatepage.reload(wait_until='networkidle')
            privatepage.locator('[data-variant=compare]').click();privatepage.locator('#capture-anchor').click()
            check('test-only comparison anchor created',privatepage.evaluate('window.motionReceipt.anchorAt') is not None)
            actual['sources']['z0_readiness']['status']='denied'
            privatepage.locator('#refresh').click()
            for _ in range(50):
                if privatepage.evaluate('window.motionReceipt.anchorAt') is None:break
                privatepage.wait_for_timeout(50)
            check('source-level revocation clears an older held anchor',privatepage.evaluate('window.motionReceipt.anchorAt') is None and '42' not in privatepage.locator('#compare-rows b').all_inner_texts())
            privacy.close()
            # Cold outage and storage denial are isolated test-only browser contexts.
            for fault in ['cold-outage','storage-denied']:
                ctx=browser.new_context(reduced_motion='reduce');pg=ctx.new_page();pg.on('pageerror',lambda e:errors.append(str(e)))
                if fault=='cold-outage':pg.route('**/api/plugins/company-os/snapshot',lambda route:route.fulfill(status=502,content_type='application/json',body='{"test_fixture":"offline"}'))
                else:pg.add_init_script('Storage.prototype.setItem=function(){throw new DOMException("denied","SecurityError")}')
                pg.goto(base+'/motion-lab',wait_until='networkidle')
                if fault=='cold-outage':check('cold outage has unknown fields, no fixtures',pg.evaluate('window.motionReceipt.snapshotAt') is None and not pg.locator('#facts b:not([data-value=null])').count())
                else:
                    pg.locator('#enter-lens').click();pg.locator('#pin').click();check('storage-denied pin stays in memory without crash','this tab only' in pg.locator('#notice').inner_text())
                ctx.close()
            check('all app page errors absent, including negative cases',not errors)
            check('browser requests are same-origin and GET-only',all(r['method']=='GET' and r['url'].startswith(base+'/') for r in requests))
            check('matrix count reconciles',len(matrix)==12 and len({(x['variant'],x['width']) for x in matrix})==12)
            receipt_data={'checks':checks,'count':len(checks),'matrix':matrix,'requests':requests,'page_errors':errors,'normal_console_errors':normal_console,'expected_fault_console':console[len(normal_console):],'browser':browser.version,'base':base,'gui_gate':'Jev unavailable no_key; deterministic owned headless acceptance, no user browser','data_policy':'Normal captures: real safe GET. Fault payloads: explicitly isolated test fixtures.'}
            (artifacts/'browser-tests.json').write_text(json.dumps(receipt_data,indent=2))
            context.close();browser.close()
            print(json.dumps({'passed':len(checks),'failed':0,'matrix':len(matrix),'artifacts':str(artifacts)},indent=2))
    finally:
        if server:
            server.shutdown()
            assert thread is not None
            thread.join(3);server.server_close()
            if thread.is_alive():raise RuntimeError('Owned test server not stopped')

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--artifacts',type=Path,default=Path('/workspace/zer0/data/operations/company-os-recovery/motion-prototypes'))
    parser.add_argument('--base')
    args=parser.parse_args();verify(args.artifacts,args.base)
