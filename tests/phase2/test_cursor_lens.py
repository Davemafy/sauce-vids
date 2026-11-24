from pathlib import Path
import sys
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'scripts'))
from cursor_lens import local_inverse,local_forward,spring_step,REST_STRENGTH,MOVING_STRENGTH,BASE_SAG
from motion_glass import forward,inverse_map
from cloud_window_clearface_stage import window_geometry

def test_local_lens_is_bounded_invertible_and_continuous():
    c=np.array([480.,310.]);r=210.
    for s in (REST_STRENGTH,MOVING_STRENGTH):
        rr=np.linspace(0,r,501)
        x,y=local_inverse(c[0]+rr,c[1],c,r,s)
        assert np.all(np.diff(x)>0)
        assert abs(x[-1]-(c[0]+r))<1e-9
        assert abs((x[-1]-x[-2])/(rr[-1]-rr[-2])-1)<.001
        for p in ([480,310],[530,320],[660,340],[700,310]):
            q=local_forward(p,c,r,s)
            np.testing.assert_allclose(local_inverse(*q,c,r,s),p,atol=1e-6)

def test_combined_mapping_matches_source():
    src=(2880,1800);out=(1920,1080);g=window_geometry(src,out)
    mx,my,*_=inverse_map(src,out,BASE_SAG)
    c=np.array([960.,300.]);r=200.;s=.25
    for x,y in [(960,300),(990,325),(1080,360),(450,550)]:
        original=local_inverse(mx[y,x],my[y,x],c,r,s)
        mapped=forward(local_forward(original,c,r,s),g,BASE_SAG)
        np.testing.assert_allclose(mapped,[x,y],atol=.002)

def test_critical_spring_has_no_overshoot():
    pos=np.zeros(2);vel=np.zeros(2);target=np.array([300.,100.])
    for _ in range(90):
        new,vel=spring_step(pos,vel,target,1/60)
        assert np.all(new>=pos-1e-9) and np.all(new<=target+1e-9)
        pos=new
    np.testing.assert_allclose(pos,target,atol=.001)
