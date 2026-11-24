from pathlib import Path
from types import SimpleNamespace
import sys
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'scripts'))
from motion_glass import forward,inverse_map,travel_windows,energy_at,PEAK_SAG
from cloud_window_clearface_stage import window_geometry

def test_protected_holds_and_smooth_motion():
    def k(start,at,scale):return SimpleNamespace(start_at=start,at=at,scale=scale,center_x=.5,center_y=.5,cut=False)
    windows=travel_windows([k(0,0,1),k(.1,1.1,1.2),k(2,3,1)], [{'start':.8,'t':1.3}],4)
    assert windows==((.1,.7100000000000001),(2,3)) or np.allclose(windows,[(.1,.71),(2,3)])
    assert energy_at(windows,.8)==energy_at(windows,1.4)==energy_at(windows,4)==0
    assert energy_at(windows,2.5)==1
    assert energy_at(windows,2)==energy_at(windows,3)==0

def test_inverse_map_matches_cursor_projection():
    src=(2880,1800);out=(1920,1080);g=window_geometry(src,out)
    for sag in (0,.02,PEAK_SAG):
        mx,my,*_=inverse_map(src,out,sag)
        for x,y in [(960,540),(250,200),(1660,870),(960,80)]:
            p=forward((mx[y,x],my[y,x]),g,sag)
            np.testing.assert_allclose(p,[x,y],atol=.001)
