from pathlib import Path
from types import SimpleNamespace
import sys
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'scripts'))
from cursor_lens import CursorLens
from feathered_cursor_lens import FeatheredCursorLens,feather_mask,FEATHER_PX

def test_feather_has_compact_support_and_no_outward_spill():
    a=np.zeros((100,100),np.float32);a[10:90,10:90]=1
    f=feather_mask(a,20)
    assert np.all(f[a==0]==0)
    assert np.all(f[30:70,30:70]==1)
    assert 0<f[50,10]<f[50,20]<f[50,29]+1e-6
    assert np.all(np.diff(f[50,10:31])>=0)

def test_previous_lens_geometry_and_central_pixels_are_unchanged():
    class Pointer:
        times=np.array([0.,1.])
        def at(self,t):return (1440+100*t,350)
    stage=SimpleNamespace(source_size=(2880,1800),output_size=(1920,1080),
        immersive=False,mouse_follow=None,camera=[],duration=1.)
    stage.quad=lambda t:np.float32([[50,20],[1870,20],[1870,1060],[50,1060]])
    a=CursorLens(stage,{'events':[]},Pointer(),60)
    b=FeatheredCursorLens(stage,{'events':[]},Pointer(),60)
    np.testing.assert_array_equal(a.camera_quad(.5),b.camera_quad(.5))
    for x,y in zip(a.maps(.5),b.maps(.5)):np.testing.assert_array_equal(x,y)
    np.testing.assert_array_equal(a.project([960,350],.5),b.project([960,350],.5))
    src=np.full((1800,2880,3),38,np.uint8)
    old=a.render(src,.5);new=b.render(src,.5)
    same=a.alpha==b.alpha
    np.testing.assert_array_equal(old[same],new[same])
    assert np.any(old!=new)
