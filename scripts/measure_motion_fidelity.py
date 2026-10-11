#!/usr/bin/env python3
"""Native, unregistered RGB comparison; screenshot evidence is not pixel perfection."""
from pathlib import Path
import argparse,json,re,hashlib
import cv2,numpy as np
from PIL import Image,ImageDraw
from skimage.metrics import structural_similarity

def main(out):
    p=out/'browser';raw=json.loads((out/'tracks.json').read_text());cap=cv2.VideoCapture(raw['source'])
    baseline=np.array(Image.open('/workspace/zer0/data/operations/company-os-recovery/video-replica/browser-native.png').convert('RGB'))
    regions={'full_frame':[0,0,1496,1080],'dashboard':[56,41,1440,1040],'ring_initial_coordinates':[195,120,675,602],'metrics_initial_coordinates':[785,137,1396,601],'lanes_initial_coordinates':[102,638,1394,1005]}
    records=[];thumbs=[]
    for path in sorted(p.glob('browser-*.png')):
        match=re.fullmatch(r'browser-(\d+\.\d+)\.png',path.name)
        if not match:continue
        t=float(match[1]);index=min(908,round(t*60));cap.set(cv2.CAP_PROP_POS_FRAMES,index);ok,bgr=cap.read();assert ok
        source=cv2.cvtColor(bgr,cv2.COLOR_BGR2RGB);candidate=np.array(Image.open(path).convert('RGB'));assert candidate.shape==source.shape==baseline.shape
        record={'time_s':t,'frame':index,'candidate':str(path),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'regions':{}}
        for name,(x,y,X,Y) in regions.items():
            a=source[y:Y,x:X];b=candidate[y:Y,x:X];c=baseline[y:Y,x:X]
            record['regions'][name]={'candidate_ssim':float(structural_similarity(a,b,channel_axis=2,data_range=255)),'candidate_mae':float(np.abs(a.astype(float)-b).mean()),'static_initial_baseline_ssim':float(structural_similarity(a,c,channel_axis=2,data_range=255)),'static_initial_baseline_mae':float(np.abs(a.astype(float)-c).mean())}
        records.append(record)
        overlay=Image.blend(Image.fromarray(source),Image.fromarray(candidate),.5);overlay.save(p/f'overlay-{t:07.3f}.png')
        a=Image.fromarray(source).resize((499,360));b=Image.fromarray(candidate).resize((499,360));sheet=Image.new('RGB',(998,384),(20,24,24));sheet.paste(a,(0,24));sheet.paste(b,(499,24));ImageDraw.Draw(sheet).text((8,5),f'{t:.3f}s / frame {index}     SOURCE (left) | COMPONENT REPLAY (right)',fill='white');sheet.save(p/f'compare-{t:07.3f}.jpg');thumbs.append(sheet.resize((750,289)))
    assert len(records)==14,len(records)
    contact=Image.new('RGB',(1500,289*7),(20,24,24))
    for i,img in enumerate(thumbs):contact.paste(img,((i%2)*750,(i//2)*289))
    contact.save(p/'full-sequence-comparison.jpg')
    result={'method':'Native RGB 1496x1080 DPR1, no alignment/resampling. Every source decoded at exact index. Fixed region boxes (not tracking crops). Static baseline is preserved original browser-native.png at t=0, not its old 1.5s loop. Flat dark areas inflate SSIM.','captures':records}
    (out/'fidelity.json').write_text(json.dumps(result,indent=2))
    print(json.dumps([{'t':r['time_s'],**r['regions']['dashboard']} for r in records],indent=2))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);main(p.parse_args().out)
