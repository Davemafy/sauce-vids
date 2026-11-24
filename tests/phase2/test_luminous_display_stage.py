from pathlib import Path
import sys
import cv2
import numpy as np
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'scripts'))
from luminous_display_stage import fields,forward,project_point,render,to_srgb,LINEAR
from cloud_window_clearface_stage import window_geometry
from cloud_window_sky_stage import sky_background

class Stage:
    source_size=(320,180)
    output_size=(640,360)
    def quad(self,t):
        x0,y0,x1,y1,_=window_geometry(self.source_size,self.output_size)
        return np.float32([[x0,y0],[x1,y0],[x1,y1],[x0,y1]])

def test_inverse_and_spectral_material():
    s=Stage()
    mx,my,a,d,f,refl,board=fields(s.source_size,s.output_size)
    y=np.array([30,90,180,270,330]);x=np.array([40,160,320,480,600])
    np.testing.assert_allclose(forward(np.stack([mx[y,x],my[y,x]],-1),s.source_size,s.output_size),np.stack([x,y],-1),atol=.025)
    assert a[0].max()==a[-1].max()==a[:,0].max()==a[:,-1].max()==0
    assert refl[d>100].max()<.01
    assert refl[d>150].max()<.002
    assert refl[d>250].max()<.0001
    assert f[(d>0)&(d<5)].mean()>f[d>100].mean()
    assert np.max(np.ptp(refl[(d>0)&(d<7)],axis=1))>.1
    sky=sky_background(s.output_size).astype(int)
    outside=a==0
    # The fixed original sky receives only an elevation shadow, not glass tint.
    np.testing.assert_array_less(to_srgb(board)[outside].astype(int),sky[outside]+2)
    base=LINEAR[sky]
    lit=outside & (base.min(axis=2)>.01)
    ratio=board[lit]/base[lit]
    assert ratio.min()>=.72-1e-5 and ratio.max()<=1+1e-5
    assert np.max(np.ptp(ratio,axis=1))<1e-5

def test_actual_display_emission_not_replacement():
    s=Stage()
    src=np.full((180,320,3),24,np.uint8)
    cv2.circle(src,(220,88),8,(240,240,240),-1)
    original=src.copy()
    out=render(s,src,0)
    px,py=np.rint(project_point(s,0,220,88)).astype(int)
    assert out[py,px].min()>230
    assert out[180,320].max()<28
    np.testing.assert_array_equal(src,original)
    np.testing.assert_array_equal(out,render(s,src,0))

def test_invalid_coverage_fails():
    s=Stage()
    s.quad=lambda t:np.float32([[100,100],[300,100],[300,250],[100,250]])
    with pytest.raises(ValueError,match='does not cover'):
        render(s,np.zeros((180,320,3),np.uint8),0)
