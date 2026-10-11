"""Review-only contact sheet of measured lane summary crops, no inferred text."""
from pathlib import Path
import json,cv2
from PIL import Image,ImageDraw
from motion_analysis import stabilize
p=Path('/workspace/zer0/data/operations/company-os-recovery/motion-analysis')
r=json.loads((p/'tracks.json').read_text());cap=cv2.VideoCapture(r['source'])
rows=[x for x in r['samples'] if x['frame']%30==0 or x['frame']==908]
sheet=Image.new('RGB',(1460,len(rows)*60),(20,24,24));d=ImageDraw.Draw(sheet)
for i,row in enumerate(rows):
 cap.set(cv2.CAP_PROP_POS_FRAMES,row['frame']);ok,im=cap.read();assert ok
 fit=row['components']['lanes'];d.text((5,i*60+20),f"{row['pts_s']:.2f}s",fill='white')
 if fit:
  crop,valid=stabilize(im,fit['matrix'],[110,648,790,673]);rgb=cv2.cvtColor(crop,cv2.COLOR_BGR2RGB)
  sheet.paste(Image.fromarray(rgb).resize((1360,50)),(80,i*60+5))
sheet.save(p/'lane-summary-sheet.png')
