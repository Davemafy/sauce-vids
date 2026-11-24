from pathlib import Path
from types import SimpleNamespace
import sys
import cv2
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'scripts'))
from framed_cursor_lens import FramedCursorLens

def test_full_source_fit_and_actual_rendered_marker_alignment():
    class Pointer:
        times=np.array([0.,1.])
        def at(self,t):return (1440+100*t,350)
    stage=SimpleNamespace(source_size=(2880,1800),output_size=(1920,1080),
                         immersive=False,mouse_follow=None,camera=[],duration=1.)
    stage.quad=lambda t:np.float32([[-400,-200],[2000,-200],[2000,1200],[-400,1200]])
    lens=FramedCursorLens(stage,{'events':[]},Pointer(),60)
    x0,y0,x1,y1,_=lens.geometry
    q=lens.camera_quad(.5)
    np.testing.assert_array_equal(q,[[x0,y0],[x1,y0],[x1,y1],[x0,y1]])
    h=cv2.getPerspectiveTransform(np.float32([[0,0],[2879,0],[2879,1799],[0,1799]]),q)
    src=np.full((1800,2880,3),18,np.uint8)
    markers=[(25,900),(2850,900),(1440,25),(1440,1770),(1490,350)]
    for x,y in markers:cv2.circle(src,(x,y),10,(0,255,0),-1)
    out=lens.render(src,.5)
    for x,y in markers:
        flat=cv2.perspectiveTransform(np.float32([[[x,y]]]),h)[0,0]
        px,py=np.rint(lens.project(flat,.5)).astype(int)
        assert lens.alpha[py,px]>.98
        patch=out[py-12:py+13,px-12:px+13].astype(float)
        yy,xx=np.where((patch[:,:,1]>150)&(patch[:,:,1]>patch[:,:,0]+70)&(patch[:,:,1]>patch[:,:,2]+70))
        assert len(xx)>0
        assert np.hypot(xx.mean()-12,yy.mean()-12)<3
    assert lens.receipt()['fullSourceFit']
    # Central reading surface must not become a milky grey overlay.
    assert out[540,960].max()<25
