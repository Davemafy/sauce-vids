from pathlib import Path
from types import SimpleNamespace
import sys
import cv2
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'scripts'))
from safe_cursor_lens import SafeCursorLens,warp,coefficients

def test_focus_context_monotonic_and_boundary_fixed():
    u=np.linspace(0,1,4097)
    for k in (0,.41,.82):
        for b in (-.18,0,.18):
            v=warp(u,k,b)
            assert v[0]==0 and v[-1]==1
            assert np.diff(v).min()/(u[1]-u[0])>=.40

def test_safe_edges_and_cursor_in_actual_render():
    class Pointer:
        times=np.array([0.,1.])
        def at(self,t):return (1440+150*t,350)
    stage=SimpleNamespace(source_size=(2880,1800),output_size=(1920,1080),
                         immersive=False,mouse_follow=None,camera=[],duration=1.)
    stage.quad=lambda t:np.float32([[180-250*t,45-100*t],[1740+200*t,45-100*t],[1740+200*t,1035+130*t],[180-250*t,1035+130*t]])
    lens=SafeCursorLens(stage,{'events':[]},Pointer(),60)
    assert lens.min_boundary_alpha>=.995
    assert np.linalg.norm(lens.focus_point([1250,400],0)-lens.focus_point([1250,400],1))>3
    src=np.full((1800,2880,3),18,np.uint8)
    markers=[(25,900),(2850,900),(1440,25),(1440,1770),(1490,350)]
    for x,y in markers:cv2.circle(src,(x,y),12,(0,255,0),-1)
    for t in (0,.75):
        out=lens.render(src,t)
        q=lens.camera_quad(t)
        h=cv2.getPerspectiveTransform(np.float32([[0,0],[2879,0],[2879,1799],[0,1799]]),q)
        for x,y in markers:
            flat=cv2.perspectiveTransform(np.float32([[[x,y]]]),h)[0,0]
            px,py=np.rint(lens.project(flat,t)).astype(int)
            assert lens.alpha[py,px]>.995
            patch=out[py-13:py+14,px-13:px+14].astype(float)
            yy,xx=np.where((patch[:,:,1]>150)&(patch[:,:,1]>patch[:,:,0]+70)&(patch[:,:,1]>patch[:,:,2]+70))
            assert len(xx)>0
            assert np.hypot(xx.mean()-13,yy.mean()-13)<3
