from pathlib import Path
import sys
import numpy as np
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'scripts'))
from editorial_cursor_lens import protected_quad, EditorialCursorLens
from types import SimpleNamespace
import cv2

def test_selective_bounds_preserve_zoom_and_source_coverage():
    g=(293,57,1626,1024,41)
    r=dict(x=36,y=254,width=2417,height=1359.7656)
    q=np.float32([[180,-80],[1840,-80],[1840,1120],[180,1120]])
    actual=protected_quad(q,g,(3200,2320),r)
    assert np.ptp(actual[:,0])>1.15*(g[2]-g[0])
    assert actual[0,0]<=g[0] and actual[2,0]>=g[2]
    h=cv2.getPerspectiveTransform(np.float32([[0,0],[3199,0],[3199,2319],[0,2319]]),actual)
    pts=cv2.perspectiveTransform(np.float32([[[36,254],[2453,1613.7656]]]),h)[0]
    assert pts[0,0]>=g[0]+13-.01
    assert pts[0,1]>=g[1]+54-.01
    assert pts[1,0]<=g[2]-13+.8
    assert pts[1,1]<=g[3]-54+.8
    with pytest.raises(ValueError):
        protected_quad(q,g,(3200,2320),dict(x=0,y=0,width=3200,height=2320))

def test_projected_drawing_boundary_and_moving_pointer():
    class Pointer:
        times=np.array([0.,1.])
        def at(self,t):return (1400+100*t,800)
    stage=SimpleNamespace(source_size=(3200,2320),output_size=(1920,1080),
        immersive=False,mouse_follow=None,camera=[],duration=1.)
    stage.quad=lambda t:np.float32([[293-140*t,57-90*t],[1626+160*t,57-90*t],[1626+160*t,1024+90*t],[293-140*t,1024+90*t]])
    r=dict(x=36,y=254,width=2417,height=1359.7656)
    lens=EditorialCursorLens(stage,{'events':[dict(targetRect=r,resultRect=r,evidence='fixture',t=.8,start=.2,end=.7)]},Pointer(),60)
    assert lens.min_alpha>=.98
    assert max(lens.zoom)>1.1
    src=np.full((2320,3200,3),20,np.uint8)
    point=(1450,800)
    cv2.circle(src,point,12,(0,255,0),-1)
    t=.5
    q=lens.camera_quad(t)
    h=cv2.getPerspectiveTransform(np.float32([[0,0],[3199,0],[3199,2319],[0,2319]]),q)
    flat=cv2.perspectiveTransform(np.float32([[point]]),h)[0,0]
    x,y=np.rint(lens.project(flat,t)).astype(int)
    out=lens.render(src,t)
    patch=out[y-14:y+15,x-14:x+15].astype(float)
    yy,xx=np.where((patch[:,:,1]>150)&(patch[:,:,1]>patch[:,:,0]+70)&(patch[:,:,1]>patch[:,:,2]+70))
    assert len(xx)>0 and np.hypot(xx.mean()-14,yy.mean()-14)<3
