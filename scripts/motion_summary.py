#!/usr/bin/env python3
"""Aggregate measured observations without upgrading them into causal events."""
from pathlib import Path
import json,statistics,hashlib,argparse
parser=argparse.ArgumentParser();parser.add_argument('--out',type=Path,required=True);p=parser.parse_args().out
raw=json.loads((p/'tracks.json').read_text());tl=json.loads((p/'timeline.json').read_text())
def intervals(samples,predicate):
    groups=[]
    for s in samples:
        if predicate(s):
            if not groups or s['t']-groups[-1][-1]['t']>.075:groups.append([])
            groups[-1].append(s)
    return [{'first_positive_s':g[0]['t'],'last_positive_s':g[-1]['t'],'samples':len(g),'sample_spacing_s':.05,'boundary_note':'Threshold-positive samples only, not guaranteed event onset/offset. Rejected or occluded samples may precede/follow these.'} for g in groups]
summary={'source_sha256':raw['source_sha256'],'decoded_frames':raw['decoded_frames'],'analyzed_samples':len(raw['samples']),'first_pts_s':raw['samples'][0]['pts_s'],'last_pts_s':raw['samples'][-1]['pts_s'],'component_fits':{k:{'available':sum(bool(s['components'][k]) for s in raw['samples']),'median_p95_residual_px':statistics.median(s['components'][k]['residual_p95_px'] for s in raw['samples'] if s['components'][k])} for k in raw['samples'][0]['components']},'pointer_positive_samples':sum(s['pointer']['accepted'] for s in raw['samples']),'linked_glow_tracks':tl['flightTrackCount'],'glow_identity':'geometric only; tracks split across >110ms gaps; not item IDs or backend events','recording_window_zoom':intervals(tl['samples'],lambda s:s['camera'][0]>1.02),'content_reflow':intervals(tl['samples'],lambda s:s['t']>10 and s['parts']['ring'][0]<.95),'tooltip_template_positives':intervals(tl['samples'],lambda s:bool(s.get('tooltip'))),'tooltip_boundary':'Positive detections only; false negatives between these samples mean no complete appearance/hover duration is established.','measurement_grid_spacing_s':.05,'grid_is_not_event_timing_accuracy':True,'ocr_time_spacing_s':.5,'observed_late_browser_chrome':[{'frame':630,'pts_s':10.5,'text':'50%','confidence':'human-readable native frame','causality':'Visible browser zoom indicator; exact keyboard/wheel/menu input unseen'},{'frame':660,'pts_s':11,'text':'67%','confidence':'human-readable native frame','causality':'Browser content reflows within same fixed shell, not recorder-only zoom'}],'unobservable':['True backend records, transport, store and event dispatch','Input commands, clicks or wheel ticks not visible','Full identity through occlusion/glow collisions','Source CSS easing, timers or animation library','Hidden lower-panel details before they enter viewport'],'not_fully_reconstructed':['Expanding transient event rings and all event-label lifetimes','All per-lane tool mix/status/timer transitions','All late sparkline data after browser zoom','Complete lower LIVE FEED text','Exact zoom popup lifetimes and browser UI controls'],'source_binding_status':'Issue #5 supplies future CompanyOS ownership contract; video supplies fixture pixels only.'}
assert summary['decoded_frames']==909 and summary['analyzed_samples']==304
(p/'events-and-confidence.json').write_text(json.dumps(summary,indent=2))
for file in ['motion_analysis.py','motion_publish.py','reference_motion.py','verify_motion_reference.py','measure_motion_fidelity.py']:
    src=Path(__file__).parent/file
    summary.setdefault('scripts',{})[file]=hashlib.sha256(src.read_bytes()).hexdigest()
(p/'analysis-summary.json').write_text(json.dumps(summary,indent=2))
print(json.dumps(summary,indent=2))
