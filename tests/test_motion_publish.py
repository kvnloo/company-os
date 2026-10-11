import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import motion_publish as p

def test_linking_never_bridges_an_occlusion():
    rows=[{'pts_s':t,'ring_highlights':[{'ring':0,'angle_deg':a,'source_xy':[a,0]}]} for t,a in [(0,10),(.05,12),(.1,14),(.8,18),(.85,20),(.9,22)]]
    tracks=p.link_highlights(rows,min_samples=3)
    assert len(tracks)==2
    assert all(x['end_s']-x['start_s']<.2 for x in tracks)
    assert all(abs(x['linear_fit']['deg_per_s']-40)<.01 for x in tracks)


def test_tsv_quotes_are_literal_ocr_text():
    tsv='level\tleft\ttop\twidth\theight\tconf\tblock_num\tline_num\ttext\n5\t2\t4\t6\t8\t91\t1\t1\t"\n5\t4\t6\t8\t10\t92\t1\t1\t19\n'
    words=p.parse_tsv(tsv)
    assert [w['text'] for w in words]==['"','19']
    assert words[1]['source_xywh']==[2,3,4,5]


def test_content_zoom_not_swallowed_by_static_wallpaper():
    import numpy as np
    row={'pts_s':2,'common_transform':{'scale':1,'matrix':[[1,0,0],[0,1,0]]},'components':{'outcome':{'scale':1.5,'inliers':25,'residual_p95_px':1,'matrix':[[1.5,0,-200],[0,1.5,-100]]},'metrics':{'scale':1.502,'inliers':18,'residual_p95_px':1,'matrix':[[1.502,0,-201],[0,1.502,-101]]}}}
    assert np.isclose(p.select_camera(row)[0,0],1.5)


def test_publish_full_clip(tmp_path):
    import os, json, pytest
    path=os.environ.get('MOTION_TRACKS')
    if not path:pytest.skip('Set MOTION_TRACKS for actual-clip publication')
    result=p.publish(Path(path),tmp_path)
    assert len(result['samples'])==304
    assert result['duration']==15.133333
    assert result['sourceSha256']=='84a29e4fafea04c7a4b945f7db4f6c5b09877ba8996572d244662996093063b5'
    assert all('camera' in r and 'parts' in r for r in result['samples'])
    assert (tmp_path/'timeline.json').exists()
    for raw,row in zip(json.loads(Path(path).read_text())['samples'],result['samples']):
        for name,status in row['partConfidence'].items():
            if status=='observed':assert raw['components'][name]['inliers']>=8
