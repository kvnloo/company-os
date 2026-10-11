"""Synthetic geometry fixtures are tests, never reference-video evidence."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
import numpy as np
import motion_analysis as m

def test_similarity_rejects_outliers_and_retains_original_coordinates():
    rng=np.random.default_rng(4)
    src=rng.uniform([0,0],[1496,1080],(80,2)).astype(np.float32)
    dst=src*1.7+[12,-91]
    dst[-12:]=rng.uniform(0,1000,(12,2))
    result=m.fit_transform(src,dst.astype(np.float32))
    assert result['inliers']==68
    assert np.allclose(result['matrix'],[[1.7,0,12],[0,1.7,-91]],atol=.001)
    assert result['residual_p95_px']<.001
    assert m.fit_transform(src[:2],dst[:2]) is None


def test_easing_serializes_without_numpy_scalars():
    import json
    rows=[{'pts_s':float(i)/20,'camera':{'scale':1+(i/20)**2}} for i in range(21)]
    assert len(json.dumps(m.fit_easing(rows,'camera')))>0


def test_clip_measurements_cover_first_and_last_frame(tmp_path):
    import os
    source=os.environ.get('MOTION_SOURCE')
    if not source:
        import pytest
        pytest.skip('Set MOTION_SOURCE for real-video integration')
    result=m.analyze(Path(source),tmp_path,stride=30,max_frames=1000)
    assert result['decoded_frames']==909
    assert len(result['samples'])==32
    assert result['samples'][0]['frame']==0
    assert result['samples'][-1]['frame']==908
    assert result['samples'][-1]['pts_s']>15
    assert all('components' in row and 'source_pixel_sha256' in row for row in result['samples'])
    assert (tmp_path/'tracks.json').is_file()
