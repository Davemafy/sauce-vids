import sys
from pathlib import Path
import numpy as np
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'scripts'))
from evidence_edl_renderer import Shot, camera, summary_safe_camera

def manifest():
    return {'events':[{'kind':'state_change','evidence':'real recorded numbers',
        'summaryRects':[{'x':563.,'y':263.,'width':572.656,'height':80.},
                        {'x':1265.656,'y':263.,'width':572.672,'height':80.},
                        {'x':1968.328,'y':263.,'width':572.672,'height':80.}]}]}

def test_protected_card_group_is_fully_visible_at_all_keyframes():
    m=manifest();shot=Shot('actual metrics',0,240,
        [{'f':0,'zoom':1.22,'anchor':'wide'},
         {'f':55,'zoom':2.55,'anchor':'summary:0'},
         {'f':239,'zoom':2.55,'anchor':'summary:0'}])
    for f in (0,12,28,55,120,239):
        original=camera(m,shot,f,(2640,1440),(1920,1080))
        safe=summary_safe_camera(m,shot,original,(2640,1440),(1920,1080))
        assert safe[0,0]<=original[0,0]
        for rect in m['events'][0]['summaryRects']:
            for x in (rect['x'],rect['x']+rect['width']):
                for y in (rect['y'],rect['y']+rect['height']):
                    p=safe @ np.array([x,y,1.])
                    assert 115 <= p[0] <= 1805
                    assert 64 <= p[1] <= 1016

def test_default_and_other_shots_unchanged():
    m=manifest();shot=Shot('ordinary',0,120,[{'f':0,'zoom':2.,'anchor':'wide'}])
    old=camera(m,shot,0,(2640,1440),(1920,1080))
    np.testing.assert_array_equal(summary_safe_camera(m,shot,old,(2640,1440),(1920,1080)),old)

def test_invalid_summary_geometry_fails_closed():
    m=manifest()
    m['events'][0]['summaryRects'][2]['x']=2630.
    shot=Shot('bad',0,120,[{'f':0,'zoom':2.,'anchor':'summary:0'}])
    with pytest.raises(ValueError,match='outside actual source'):
        summary_safe_camera(m,shot,np.eye(2,3),(2640,1440),(1920,1080))
