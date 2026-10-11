#!/usr/bin/env python3
"""Derive reviewable trajectories from image-space candidates; gaps stay gaps."""
from pathlib import Path
import json
import numpy as np
from scipy.optimize import linear_sum_assignment

def link_highlights(rows,min_samples=5):
    tracks=[]
    for row in rows:
        t=row['pts_s'];points=row['ring_highlights']
        active=[i for i,x in enumerate(tracks) if 0<t-x['samples'][-1]['t']<=.11]
        if active and points:
            costs=np.full((len(active),len(points)),1e6)
            for ii,i in enumerate(active):
                tr=tracks[i];last=tr['samples'][-1];speed=0
                if len(tr['samples'])>1:
                    a,b=tr['samples'][-2:];speed=np.clip((b['angle']-a['angle'])/(b['t']-a['t']),-120,120)
                pred=last['angle']+speed*(t-last['t'])
                for j,p in enumerate(points):
                    d=(p['angle_deg']-pred+180)%360-180
                    if p['ring']==tr['ring'] and abs(d)<7:costs[ii,j]=abs(d)
            a,b=linear_sum_assignment(costs)
            paired={j:active[i] for i,j in zip(a,b) if costs[i,j]<7}
        else:paired={}
        for j,pt in enumerate(points):
            if j not in paired:
                tracks.append({'ring':pt['ring'],'samples':[]});i=len(tracks)-1
            else:i=paired[j]
            tr=tracks[i];angle=pt['angle_deg']
            if tr['samples']:
                prev=tr['samples'][-1]['angle'];angle=prev+(angle-prev+180)%360-180
            tr['samples'].append({'t':t,'angle':angle,'source_xy':pt['source_xy']})
    result=[]
    for tr in tracks:
        if len(tr['samples'])<min_samples:continue
        t=np.array([s['t'] for s in tr['samples']]);v=np.array([s['angle'] for s in tr['samples']])
        slope,offset=np.polyfit(t-t[0],v,1);residual=v-(offset+slope*(t-t[0]))
        if abs(slope)<3 or np.ptp(v)<2:continue
        tr.update({'id':f'flight-{len(result):03d}','start_s':float(t[0]),'end_s':float(t[-1]),'confidence':'medium','identity_boundary':'Geometric association only; no identity across >110ms gaps or collision proof.', 'linear_fit':{'deg_per_s':float(slope),'rmse_deg':float(np.sqrt(np.mean(residual**2))),'max_abs_deg':float(np.max(np.abs(residual)))}})
        result.append(tr)
    return result


def parse_tsv(txt):
    import csv,io
    words=[]
    for item in csv.DictReader(io.StringIO(txt),delimiter='\t',quoting=csv.QUOTE_NONE):
        if item.get('text','').strip():words.append({'text':item['text'],'confidence':float(item['conf']),'source_xywh':[int(item[x])/2 for x in ['left','top','width','height']],'block':int(item['block_num']),'line':int(item['line_num'])})
    return words

def select_camera(row):
    from motion_analysis import IDENTITY
    # A fixed wallpaper can win a whole-image RANSAC while the recorded content
    # window zooms. Prefer cross-component agreement over that false consensus.
    if row['pts_s']>=10:return IDENTITY.copy()
    parts=[x for k,x in row['components'].items() if k!='header' and x and x['inliers']>=10 and x['residual_p95_px']<2.5]
    zoom=[x for x in parts if x['scale']>1.012]
    if len(zoom)>=2:
        center=np.median([x['scale'] for x in zoom])
        agreeing=[x for x in zoom if abs(x['scale']-center)<.025]
        if len(agreeing)>=2:return np.array(max(agreeing,key=lambda x:x['inliers'])['matrix'])
    common=row['common_transform']
    return np.array(common['matrix']) if common and common['scale']>1.006 else IDENTITY.copy()

def publish(track_path,out):
    import cv2, csv, io, re, subprocess
    from motion_analysis import IDENTITY, stabilize, mapped, save, digest, fit_easing
    out.mkdir(parents=True,exist_ok=True)
    raw=json.loads(track_path.read_text());rows=raw['samples'];flights=link_highlights(rows)
    cached={x['frame']:x['source_pixel_sha256'] for x in json.loads((out/'ocr-candidates.json').read_text())} if (out/'ocr-candidates.json').exists() else {}
    save(out/'flight-tracks.json',flights)
    accepted={(round(p['t'],6),tr['ring'],round(p['angle']%360,2)) for tr in flights for p in tr['samples']}
    cap=cv2.VideoCapture(raw['source']); cap.set(cv2.CAP_PROP_POS_FRAMES,300);ok,tipframe=cap.read();assert ok
    gray=cv2.cvtColor(tipframe,cv2.COLOR_BGR2GRAY);tip_template=gray[284:339,296:456];cross_template=gray[336:365,272:300]
    cap.set(cv2.CAP_PROP_POS_FRAMES,0)
    lookup={r['frame']:r for r in rows};samples=[];ocr=[];tip_events=[]
    matrix6=lambda M:[round(float(v),6) for v in [M[0,0],M[1,0],M[0,1],M[1,1],M[0,2],M[1,2]]]
    known_ui={k:IDENTITY.copy() for k in ['ring','outcome','metrics','lanes','header']}
    for index in range(raw['decoded_frames']):
        ok,image=cap.read()
        if not ok:raise RuntimeError('Decode failure in publication')
        if index not in lookup:continue
        row=lookup[index];t=row['pts_s'];common=row['common_transform']
        # Frame-wide content zoom is visually coherent during the two editorial
        # zoom intervals. Wallpaper can remain fixed, so this is a content-window
        # transform, not a physical camera claim. Crop-induced separation is unknown.
        C=select_camera(row)
        CI=np.linalg.inv(np.vstack([C,[0,0,1]]));parts={};confidence={}
        for name,fit in row['components'].items():
            if fit and fit['inliers']<8:fit=None
            if fit and fit['inliers']>=8:
                U=(CI@np.vstack([fit['matrix'],[0,0,1]]))[:2]
                # Metrics grid resizes/reflows after browser zoom; a single affine
                # gives false matches. Publish null, never a plausible false fit.
                if name=='metrics' and t>=10.15:fit=None
                else:known_ui[name]=U
            parts[name]=matrix6(known_ui[name])
            confidence[name]='observed' if fit else 'held-last-visible; unmeasured/occluded'
        current={'t':t,'frame':index,'camera':matrix6(C),'cameraBasis':'common-window scale/pan; scroll vs recorder pan not identifiable when fixed anchors leave crop' if not np.array_equal(C,IDENTITY) else 'fixed shell/wallpaper', 'parts':parts,'partConfidence':confidence,'pointer':row['pointer'] if row['pointer']['accepted'] else None,'flights':[]}
        for p in row['ring_highlights']:
            if (round(t,6),p['ring'],round(p['angle_deg'],2)) in accepted:
                current['flights'].append([p['ring'],p['angle_deg'],round(min(1,p['baseline_excess_gray']/100),2)])
        gray=cv2.cvtColor(image,cv2.COLOR_BGR2GRAY);sc=float(np.hypot(C[0,0],C[1,0]))
        for key,template,threshold in [('tooltip',tip_template,.73),('crossPointer',cross_template,.76)]:
            temp=cv2.resize(template,None,fx=sc,fy=sc)
            _,score,_,loc=cv2.minMaxLoc(cv2.matchTemplate(gray,temp,cv2.TM_CCOEFF_NORMED))
            if score>threshold:
                current[key]={'xy':list(loc),'wh':[temp.shape[1],temp.shape[0]],'score':float(score)}
                if key=='tooltip':tip_events.append({'frame':index,'t':t,'source_xywh':list(loc)+[temp.shape[1],temp.shape[0]],'template_correlation':float(score),'text':'P4 · Breadth census | 68.6% done · 648 done · 296 open | 12 in flight · 14 blocked','confidence':'medium; same-title template matching'})
        # Measured centerlines from three colored chart ROIs in component space.
        current['charts']={}
        if t<10.15:
            for name,part,box,color in [('completed','metrics',[1004,465,1181,496],'green'),('merged','metrics',[1209,465,1385,496],'purple'),('lanes','lanes',[1210,647,1385,676],'green')]:
                fit=row['components'].get(part)
                if not fit:continue
                patch,valid=stabilize(image,fit['matrix'],box)
                if valid.mean()<.9:continue
                b,g,r=cv2.split(patch)
                mask=((g.astype(float)>r.astype(float)*1.15)&(g>48)) if color=='green' else ((b.astype(float)>g.astype(float)*1.12)&(b>65))
                points=[]
                for x in range(patch.shape[1]):
                    yy=np.where(mask[:,x])[0]
                    if len(yy):points.append([x,float(np.median(yy))])
                if len(points)>patch.shape[1]*.7:current['charts'][name]={'box':box,'points':points,'native_matrix':fit['matrix'],'method':'color-segmented median centerline, 1px columns; compression-sensitive'}
        if index%30==0 or index==raw['decoded_frames']-1:
            # OCR remains candidates with native bounding boxes, not asserted truth.
            enlarged=cv2.resize(255-gray,None,fx=2,fy=2,interpolation=cv2.INTER_CUBIC)
            encoded=cv2.imencode('.png',enlarged)[1].tobytes()
            cache=out/f'ocr-{index:04d}.tsv'
            txt=cache.read_text() if cache.exists() and cached.get(index)==row['source_pixel_sha256'] else subprocess.run(['tesseract','stdin','stdout','--psm','11','tsv'],input=encoded,capture_output=True,check=True).stdout.decode()
            (out/f'ocr-{index:04d}.tsv').write_text(txt)
            words=parse_tsv(txt)
            ocr.append({'frame':index,'pts_s':t,'source_pixel_sha256':row['source_pixel_sha256'],'method':'Tesseract psm11; grayscale inverted + 2x cubic; every 0.5s; OCR candidates not verified text','words':words})
        samples.append(current)
    cap.release()
    result={'schema':'companyos.reference.timeline.v1','sourceSha256':raw['source_sha256'],'tracksSha256':digest(track_path.read_bytes()),'publisherSha256':digest(Path(__file__).read_bytes()),'duration':rows[-1]['pts_s'],'samples':samples,'flightTrackCount':len(flights),'sampleUncertaintySeconds':raw['timing_uncertainty_s'],'mode':'reference-fixture-only','liveConnected':False}
    save(out/'timeline.json',result);save(out/'ocr-candidates.json',ocr);save(out/'tooltip-track.json',tip_events)
    save(out/'selected-window-easing.json',fit_easing([{'pts_s':s['t'],'camera':{'scale':float(np.hypot(s['camera'][0],s['camera'][1]))}} for s in samples],'camera'))
    return result

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--tracks',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--module',type=Path)
    args=p.parse_args();result=publish(args.tracks,args.out)
    if args.module:args.module.write_text('export default '+json.dumps(result,separators=(',',':'))+';\n')
    print(json.dumps({'samples':len(result['samples']),'flights':result['flightTrackCount'],'duration':result['duration']}))
