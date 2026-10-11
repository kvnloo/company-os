#!/usr/bin/env python3
"""Capture actual Chromium frames of the lab; encode local view-only tour.
No synthesized telemetry, no audio capture, no user browser attachment.
"""
import argparse
import base64
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import time
from playwright.sync_api import sync_playwright


def capture(base, artifacts):
    artifacts.mkdir(parents=True,exist_ok=True)
    frames=[];chapters=[];errors=[]
    with tempfile.TemporaryDirectory(prefix='motion-lab-frames-',dir=os.environ['TMPDIR']) as temporary:
        root=Path(temporary)
        with sync_playwright() as p:
            browser=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox','--disable-dev-shm-usage'])
            context=browser.new_context(viewport={'width':1440,'height':1400},device_scale_factor=1,reduced_motion='no-preference')
            page=context.new_page();page.on('pageerror',lambda e:errors.append(str(e)))
            page.goto(base+'/motion-lab',wait_until='networkidle');page.evaluate('document.fonts.ready')
            assert page.evaluate('window.motionReceipt.transport')=='connected'
            page.locator('.lane-row[data-source=z0_outcomes]').click()
            page.locator('#play').click()  # pause the selection-triggered reveal
            page.locator('#scrub').evaluate('(e)=>{e.value="0";e.dispatchEvent(new Event("input",{bubbles:true}));}')
            page.evaluate('scrollTo(0,0)')
            cdp=context.new_cdp_session(page)
            def frame(event):
                content=base64.b64decode(event['data'])
                filename=f'frame-{len(frames):05d}.jpg'
                (root/filename).write_bytes(content)
                frames.append({'file':filename,'timestamp':event['metadata']['timestamp'],'sha256':hashlib.sha256(content).hexdigest()})
                cdp.send('Page.screencastFrameAck',{'sessionId':event['sessionId']})
            cdp.on('Page.screencastFrame',frame)
            cdp.send('Page.startScreencast',{'format':'jpeg','quality':88,'maxWidth':1440,'maxHeight':1400,'everyNthFrame':2})
            def chapter(name):chapters.append({'name':name,'at':time.time(),'scene':page.evaluate('window.motionReceipt')})
            chapter('Evidence trace: source selection to bound fact and provenance')
            page.locator('#play').click();page.wait_for_timeout(6800)
            page.locator('#source-challenge').click();page.wait_for_timeout(1100)
            page.locator('#source-challenge').click()
            page.locator('#enter-lens').click()
            page.locator('[data-variant=focus]').click();page.evaluate('scrollTo(0,0)')
            chapter('Context lens: selected source separates, scope stays explicit')
            page.wait_for_timeout(6800)
            page.locator('[data-variant=compare]').click();page.locator('#capture-anchor').click()
            page.locator('#scrub').evaluate('(e)=>{e.value="0";e.dispatchEvent(new Event("input",{bubbles:true}));}')
            page.locator('#play').click();page.evaluate('scrollTo(0,0)')
            chapter('Time lens: explicitly captured A and latest received B')
            page.wait_for_timeout(6800)
            page.locator('#hypothesis').check();chapter('Illustrative branch: evidence withheld, no causal prediction')
            page.wait_for_timeout(1800)
            page.locator('#restore').click();page.evaluate('scrollTo(0,0)');chapter('Restore original cockpit')
            page.wait_for_timeout(900)
            cdp.send('Page.stopScreencast')
            context.close();browser.close()
        assert not errors,errors
        assert len(frames)>30,'Need real animation frames'
        # Retain the observed frame intervals; do not fabricate intermediate images.
        lines=[]
        for i,f in enumerate(frames):
            lines.append("file '"+str(root/f['file'])+"'")
            duration=frames[i+1]['timestamp']-f['timestamp'] if i+1<len(frames) else .1
            lines.append(f'duration {max(.001,min(duration,3)):.6f}')
        lines.append("file '"+str(root/frames[-1]['file'])+"'")
        timeline=root/'frames.ffconcat';timeline.write_text('\n'.join(lines)+'\n')
        ffmpeg=shutil.which('ffmpeg')
        if not ffmpeg:raise RuntimeError('ffmpeg unavailable')
        result=subprocess.run([ffmpeg,'-y','-hide_banner','-loglevel','warning','-f','concat','-safe','0','-i',str(timeline),'-an','-fps_mode','vfr','-c:v','libvpx-vp9','-b:v','0','-crf','32','-deadline','good','-cpu-used','4',str(artifacts/'motion-tour.webm')],capture_output=True,text=True,timeout=180)
        if result.returncode:raise RuntimeError(result.stderr)
    video=artifacts/'motion-tour.webm'
    receipt={'captured_at':datetime.now(timezone.utc).isoformat(),'base':base,'mode':'actual CDP browser screencast; no audio','frames':frames,'frame_count':len(frames),'chapters':chapters,'video':{'file':video.name,'bytes':video.stat().st_size,'sha256':hashlib.sha256(video.read_bytes()).hexdigest()},'page_errors':errors}
    (artifacts/'motion-tour-receipt.json').write_text(json.dumps(receipt,indent=2))
    manifest_path=artifacts/'gallery.json'
    if manifest_path.exists():
        manifest=json.loads(manifest_path.read_text());manifest['video']='motion-tour.webm';manifest_path.write_text(json.dumps(manifest,indent=2))
    print(json.dumps({'frame_count':len(frames),'video':str(video),'bytes':video.stat().st_size,'errors':errors},indent=2))

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base',default='http://127.0.0.1:18750')
    parser.add_argument('--artifacts',type=Path,default=Path('/workspace/zer0/data/operations/company-os-recovery/motion-prototypes'))
    args=parser.parse_args();capture(args.base,args.artifacts)
