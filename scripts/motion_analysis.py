#!/usr/bin/env python3
"""Bounded offline video measurements; no inferred inputs or backend authority."""
import argparse, hashlib, json, subprocess, sys
from pathlib import Path
import cv2
import numpy as np
from scipy.optimize import least_squares
from scipy.signal import find_peaks

# Source-native frame-zero coordinates; not output viewport coordinates.
REGIONS={'ring':[195,120,676,602], 'outcome':[785,135,1200,372],
         'metrics':[785,382,1396,603], 'lanes':[102,637,1394,1007],
         'header':[102,69,1396,108]}
RING_CENTER=np.array([435.25,360.13])
RADII=np.array([80.317,97.038,113.86,130.601,147.415,164.167,180.992,197.726,214.531,231.3])
IDENTITY=np.array([[1.,0,0],[0,1.,0]])

def digest(data): return hashlib.sha256(data).hexdigest()
def save(path, obj): path.write_text(json.dumps(obj,indent=2,allow_nan=False))
def within(points, box):
    x,y,X,Y=box
    return (points[:,0]>=x)&(points[:,0]<X)&(points[:,1]>=y)&(points[:,1]<Y)
def corners(box):
    x,y,X,Y=box
    return np.array([[x,y],[X,y],[X,Y],[x,Y]],float)
def mapped(points,M): return np.asarray(points)@np.asarray(M)[:,:2].T+np.asarray(M)[:,2]

def stabilize(image,M,box):
    x,y,X,Y=box
    # Destination crop coordinates -> original native source coordinates.
    local=np.asarray(M).copy();local[:,2]+=local[:,:2]@np.array([x,y])
    patch=cv2.warpAffine(image,local,(X-x,Y-y),flags=cv2.INTER_LINEAR|cv2.WARP_INVERSE_MAP)
    valid=cv2.warpAffine(np.ones(image.shape[:2],np.uint8),local,(X-x,Y-y),flags=cv2.INTER_NEAREST|cv2.WARP_INVERSE_MAP)
    return patch,valid

def delta(previous,current,valid):
    a=cv2.cvtColor(previous,cv2.COLOR_BGR2GRAY);b=cv2.cvtColor(current,cv2.COLOR_BGR2GRAY)
    change=(cv2.absdiff(a,b)>14).astype(np.uint8)*valid
    change=cv2.morphologyEx(change,cv2.MORPH_OPEN,np.ones((2,2),np.uint8))
    n,_,stats,_=cv2.connectedComponentsWithStats(change)
    boxes=[s[:4].tolist()+[int(s[4])] for s in stats[1:] if s[4]>=6]
    a=cv2.resize(a,None,fx=.5,fy=.5);b=cv2.resize(b,None,fx=.5,fy=.5)
    flow=cv2.calcOpticalFlowFarneback(a,b,None,.5,3,15,3,5,1.2,0)*2
    mag=np.linalg.norm(flow,axis=2)
    active=cv2.resize(valid,(a.shape[1],a.shape[0]),interpolation=cv2.INTER_NEAREST)>0
    return {'changed_fraction':float(change.sum()/max(1,valid.sum())),
            'flow_p90_native_px_per_sample':float(np.percentile(mag[active],90)) if active.any() else None,
            'segmented_changes_xywh_area_crop':sorted(boxes,key=lambda b:b[4],reverse=True)[:24]}

def fit_easing(rows, key):
    valid=[(r['pts_s'],r[key]['scale']) for r in rows if r.get(key)]
    if len(valid)<5:return []
    t,y=np.array(valid).T
    moving=np.abs(np.diff(y))>.0015
    ids=np.where(moving)[0];groups=[]
    for i in ids:
        if not groups or i>groups[-1][-1]+3:groups.append([i])
        else:groups[-1].append(i)
    results=[]
    for g in groups:
        lo,hi=g[0],min(g[-1]+1,len(t)-1)
        if hi-lo<4 or abs(y[hi]-y[lo])<.03:continue
        x=(t[lo:hi+1]-t[lo])/(t[hi]-t[lo]);v=(y[lo:hi+1]-y[lo])/(y[hi]-y[lo])
        fits=[]
        for name,func in [('power-in',lambda x,p:x**p),('power-out',lambda x,p:1-(1-x)**p),('smoothstep',lambda x,p:x*x*(3-2*x)),('linear',lambda x,p:x)]:
            opt=least_squares(lambda p:func(x,p[0])-v,[2.],bounds=([.2],[8.]),loss='soft_l1',f_scale=.05)
            residual=(func(x,opt.x[0])-v)*(y[hi]-y[lo])
            fits.append({'model':name,'power':float(opt.x[0]) if name.startswith('power') else None,'rmse_scale':float(np.sqrt(np.mean(residual**2))),'max_error_scale':float(np.max(np.abs(residual)))})
        results.append({'start_s':float(t[lo]),'end_s':float(t[hi]),'sample_count':int(hi-lo+1),'start_scale':float(y[lo]),'end_scale':float(y[hi]),'candidates':sorted(fits,key=lambda f:f['rmse_scale']),'interpretation':'Approximate image-space fit; not identification of source CSS easing or input.'})
    return results

def analyze(source,out,stride=3,max_frames=1000):
    cv2.setNumThreads(2);cv2.setRNGSeed(7)
    out.mkdir(parents=True,exist_ok=True);(out/'frames').mkdir(exist_ok=True)
    probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-select_streams','v:0','-show_streams','-show_frames','-show_entries','frame=best_effort_timestamp_time,pkt_duration_time:stream=width,height,avg_frame_rate,nb_frames,duration','-of','json',str(source)]))
    save(out/'ffprobe.json',probe)
    total=len(probe['frames'])
    if total>max_frames:raise ValueError('Source exceeds explicit max-frames bound')
    indices=set(range(0,total,stride))|{total-1}
    cap=cv2.VideoCapture(str(source));sift=cv2.SIFT_create(nfeatures=6000,contrastThreshold=.012)
    rows=[];manifest=[];previous={};profiles=[];ring_valid=[];template=None;prev_gray=None
    for index in range(total):
        ok,image=cap.read()
        if not ok: raise RuntimeError(f'Decode failed at {index}')
        manifest.append({'frame':index,'pts_s':float(probe['frames'][index]['best_effort_timestamp_time']),'pixel_sha256_bgr':digest(image.tobytes())})
        if index not in indices:continue
        gray=cv2.cvtColor(image,cv2.COLOR_BGR2GRAY)
        kp,desc=sift.detectAndCompute(gray,None)
        if index==0:
            base_points=np.float32([k.pt for k in kp]);base_desc=desc
            template=gray[560:604,856:885].copy()
        matches=[a for a,b in cv2.BFMatcher().knnMatch(base_desc,desc,k=2) if a.distance<.7*b.distance]
        src=np.float32([base_points[m.queryIdx] for m in matches]);dst=np.float32([kp[m.trainIdx].pt for m in matches])
        global_fit=fit_transform(src,dst)
        fixed=(src[:,0]<53)|(src[:,0]>1445)|(src[:,1]<37)|(src[:,1]>1045)|within(src,REGIONS['header'])
        camera=fit_transform(src[fixed],dst[fixed])
        provenance='fixed wallpaper/header anchors'
        if camera is None:
            camera=global_fit;provenance='common content transform; fixed anchors cropped: camera/UI separation uncertain'
        components={}
        for name,box in REGIONS.items():
            pick=within(src,box);fit=fit_transform(src[pick],dst[pick])
            if fit:
                M=np.array(fit['matrix']);poly=mapped(corners(box),M)
                crop,valid=stabilize(image,M,box)
                fit.update({'original_frame0_crop':box,'source_polygon_xy':poly.tolist(),'visible_fraction':float(valid.mean())})
                if camera:
                    C=np.vstack([camera['matrix'],[0,0,1]]);U=np.linalg.inv(C)@np.vstack([M,[0,0,1]])
                    fit['camera_removed_matrix']=U[:2].tolist()
                if name in previous and previous[name][0]==index-stride:
                    fit['residual_motion']=delta(previous[name][1],crop,valid*previous[name][2])
                previous[name]=(index,crop,valid)
            components[name]=fit
        row={'frame':index,'pts_s':manifest[-1]['pts_s'],'source_pixel_sha256':manifest[-1]['pixel_sha256_bgr'], 'camera':camera,'camera_basis':provenance,'common_transform':global_fit,'components':components}
        # An unconstrained homography is a diagnostic, not automatically the chosen model.
        if len(src)>=8:
            H,inl=cv2.findHomography(src,dst,cv2.RANSAC,2.5)
            if H is not None:row['homography_diagnostic']={'matrix':H.tolist(),'inliers':int(inl.sum()),'chosen':False}
        if prev_gray is not None:
            pts=cv2.goodFeaturesToTrack(prev_gray,250,.015,10)
            q,st,err=cv2.calcOpticalFlowPyrLK(prev_gray,gray,pts,None,winSize=(21,21),maxLevel=3)
            back,st2,_=cv2.calcOpticalFlowPyrLK(gray,prev_gray,q,None,winSize=(21,21),maxLevel=3)
            fb=np.linalg.norm(back-pts,axis=2).ravel();good=(st.ravel()>0)&(st2.ravel()>0)&(fb<1)
            row['lucas_kanade']={'candidates':len(pts),'forward_backward_inliers':int(good.sum()),'fb_median_px':float(np.median(fb[good])) if good.any() else None,'frame_delta':index-rows[-1]['frame']}
        prev_gray=gray
        # Pointer matching uses recording scale, not CSS/component scale.
        scale=camera['scale'] if camera else 1
        templ=cv2.resize(template,None,fx=scale,fy=scale)
        score_map=cv2.matchTemplate(gray,templ,cv2.TM_CCOEFF_NORMED)
        _,score,_,loc=cv2.minMaxLoc(score_map)
        row['pointer']={'source_xy':list(loc),'source_wh':[templ.shape[1],templ.shape[0]],'correlation':float(score),'accepted':score>=.66,'confidence':'medium' if score>=.66 else 'unresolved','note':'Template identity; cursor image does not prove click/hover causality.'}
        fit=components['ring']
        if fit and fit['visible_fraction']>.6:
            angles=np.arange(720)*np.pi/360

            values=[];vis=[]
            for r in RADII:
                xy=np.stack([RING_CENTER[0]+(r+np.arange(-4,5)[:,None])*np.sin(angles),RING_CENTER[1]-(r+np.arange(-4,5)[:,None])*np.cos(angles)],axis=-1)
                p=mapped(xy.reshape(-1,2),fit['matrix']).reshape(9,720,2)
                v=cv2.remap(gray,p[:,:,0].astype(np.float32),p[:,:,1].astype(np.float32),cv2.INTER_LINEAR)
                values.append(v.max(axis=0));vis.append(((p[:,:,0]>=0)&(p[:,:,0]<gray.shape[1])&(p[:,:,1]>=0)&(p[:,:,1]<gray.shape[0])).all(axis=0))
            profiles.append(values);ring_valid.append(vis)
        else:profiles.append(np.zeros((10,720),np.uint8));ring_valid.append(np.zeros((10,720),bool))
        frame_path=out/'frames'/f'{index:04d}.jpg';cv2.imwrite(str(frame_path),image,[cv2.IMWRITE_JPEG_QUALITY,94])
        row['review_frame']={'path':str(frame_path.relative_to(out)),'sha256':digest(frame_path.read_bytes()),'format':'JPEG94 for review only; measurements use native decoded BGR'}
        rows.append(row)
        if len(rows)%30==0:
            save(out/'partial-tracks.json',rows)
            save(out/'progress.json',{'sampled':len(rows),'last_frame':index});print(f'analyzed {index}/{total}',flush=True)
    cap.release()
    assert len(manifest)==total and len(rows)==len(indices)
    profiles=np.array(profiles);visible=np.array(ring_valid)
    np.savez_compressed(out/'ring-intensity.npz',gray_peak=profiles,visible=visible,radii=RADII,center=RING_CENTER,angles_deg=np.arange(720)*.5)
    # Robust temporal baseline isolates moving brightness from fixed completion arcs.
    baseline=np.nanpercentile(np.where(visible,profiles,np.nan),35,axis=0)
    for i,row in enumerate(rows):
        row['ring_highlights']=[]
        for ring,r in enumerate(RADII):
            signal=np.where(visible[i,ring],np.nan_to_num(profiles[i,ring]-baseline[ring]),0)
            peaks,props=find_peaks(np.r_[signal[-20:],signal,signal[:20]],height=30,prominence=18,distance=9)
            for j,p in enumerate(peaks):
                angle=(p-20)*.5
                if not 0<=angle<360:continue
                # Exclude fixed arc endpoints; identities near collisions stay unresolved.
                xy=RING_CENTER+r*np.array([np.sin(np.deg2rad(angle)),-np.cos(np.deg2rad(angle))])
                fit=row['components']['ring']
                row['ring_highlights'].append({'ring':ring,'angle_deg':angle,'baseline_excess_gray':float(props['peak_heights'][j]),'frame0_xy':xy.tolist(),'source_xy':mapped([xy],fit['matrix'])[0].tolist(),'confidence':'medium','identity':'unassigned; may include expanding events or occlusion edges'})
    result={'schema':'companyos.motion.measurements.v1','source':str(source.resolve()),'source_sha256':digest(source.read_bytes()),'analyzer_sha256':digest(Path(__file__).read_bytes()),'native_size':[1496,1080],'decoded_frames':len(manifest),'sample_stride':stride,'timing_uncertainty_s':stride/60,'samples':rows,'easing_camera':fit_easing(rows,'camera'),'easing_common':fit_easing(rows,'common_transform'),'versions':{'python':sys.version,'opencv':cv2.__version__,'numpy':np.__version__},'truth_boundary':'Image-space evidence only. Unknown input, source CSS, hidden content and backend/event causality are not recovered.'}
    save(out/'decoded-frame-manifest.json',manifest);save(out/'tracks.json',result)
    return result

def fit_transform(src, dst):
    if len(src)<6: return None
    M, mask=cv2.estimateAffinePartial2D(np.float32(src),np.float32(dst),method=cv2.RANSAC,ransacReprojThreshold=2.5,maxIters=3000,confidence=.995)
    if M is None: return None
    good=mask.ravel().astype(bool)
    if good.sum()<6: return None
    residual=np.linalg.norm(np.asarray(src)@M[:,:2].T+M[:,2]-dst,axis=1)[good]
    scale=float(np.hypot(M[0,0],M[1,0]))
    if not .35<scale<2.6: return None
    return {'matrix':M.tolist(),'scale':scale,'matches':len(src),'inliers':int(good.sum()),'inlier_fraction':float(good.mean()),'residual_median_px':float(np.median(residual)),'residual_p95_px':float(np.percentile(residual,95)),'confidence':'high' if good.sum()>=16 and np.percentile(residual,95)<1.8 else 'medium'}

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--stride',type=int,default=3);p.add_argument('--max-frames',type=int,default=1000)
    args=p.parse_args()
    if args.stride<1:p.error('stride must be positive')
    r=analyze(args.source,args.out,args.stride,args.max_frames)
    print(json.dumps({'decoded_frames':r['decoded_frames'],'analyzed_samples':len(r['samples']),'source_sha256':r['source_sha256']}))
