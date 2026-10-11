#!/usr/bin/env python3
"""Regenerate publication, run actual-source tests and real browser receipts."""
from pathlib import Path
import argparse,json,os,subprocess,sys
p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);a=p.parse_args()
out=a.out.resolve();root=Path(__file__).resolve().parents[1];tracks=out/'tracks.json'
source=json.loads(tracks.read_text())['source'];env={**os.environ,'MOTION_SOURCE':source,'MOTION_TRACKS':str(tracks)}
commands=[
 [sys.executable,'scripts/motion_publish.py','--tracks',str(tracks),'--out',str(out),'--module','web/video-replica/motion-timeline.mjs'],
 [sys.executable,'-m','pytest','tests/test_motion_analysis.py','tests/test_motion_publish.py','tests/test_reference_motion_server.py','tests/test_video_replica.py','-q'],
 ['node','--test','tests/motion-model.test.mjs','tests/video-replica-bindings.test.mjs'],
 [sys.executable,'scripts/verify_motion_reference.py','--out',str(out/'browser')],
 [sys.executable,'scripts/measure_motion_fidelity.py','--out',str(out)],
 [sys.executable,'scripts/motion_summary.py','--out',str(out)],
]
results=[]
for cmd in commands:
    print('RUN',cmd,flush=True)
    r=subprocess.run(cmd,cwd=root,env=env,text=True,capture_output=True,timeout=300)
    results.append({'command':cmd,'cwd':str(root),'exit_code':r.returncode,'stdout':r.stdout,'stderr':r.stderr})
    (out/'test-runs.json').write_text(json.dumps(results,indent=2))
    print(r.stdout+r.stderr,flush=True)
    if r.returncode:sys.exit(r.returncode)
print(json.dumps({'all_passed':True,'commands':len(results)}))
