"""Focus/context optics: retain camera energy without throwing away the viewport.

All source coordinates inside the captured viewport map to the opaque safe
interior. The outer feather is reserved for a narrow optical shoulder.
This is bounded nonlinear reframing, not a physically accurate camera dolly.
"""
import cv2
import numpy as np
from feathered_cursor_lens import FeatheredCursorLens
from cursor_lens import local_forward, BASE_SAG
from motion_glass import forward

def warp(u,k,b):
    return u+u*(1-u)*(k*(u-.5)+b)

def coefficients(quad,lo,hi):
    extent=hi-lo
    center=(np.min(quad,axis=0)+np.max(quad,axis=0))*.5
    size=np.ptp(quad,axis=0)
    # Smoothly bounded magnification and pan; derivative >= .40.
    zoom=np.mean(size/extent)-1
    k=.82*np.tanh(max(zoom,0)*3.2)
    b=.18*np.tanh(4*(center-(lo+hi)*.5)/extent)
    return float(k),b

class SafeCursorLens(FeatheredCursorLens):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.min_boundary_alpha=self.verify_boundary()
        if self.min_boundary_alpha<.995:raise ValueError('Source boundary enters feather')

    def safe_bounds(self):
        x0,y0,x1,y1,_=self.geometry
        # Reserve an aspect-preserving margin within the original cover.
        margin=(y1-y0)*.038
        inset=np.array([margin*(x1-x0)/(y1-y0),margin])
        return np.array([x0,y0])+inset,np.array([x1,y1])-inset

    def camera_quad(self,t):
        a,b=self.safe_bounds()
        return np.float32([a,[b[0],a[1]],b,[a[0],b[1]]])

    def params(self,t):
        lo,hi=self.safe_bounds()
        # Measure existing camera, including zoom and pan, on every source frame.
        return coefficients(self.stage.quad(t),lo,hi)

    def focus_point(self,point,t):
        lo,hi=self.safe_bounds();k,b=self.params(t)
        u=(np.asarray(point)-lo)/(hi-lo)
        return lo+(hi-lo)*warp(u,k,b)

    def project(self,point,t):
        return super().project(self.focus_point(point,t),t)

    def maps(self,t):
        x,y,qx,qy=super().maps(t)
        lo,hi=self.safe_bounds();k,b=self.params(t)
        axis=np.linspace(0,1,4097)
        self.margin=np.maximum(np.maximum(lo[0]-x,x-hi[0]),np.maximum(lo[1]-y,y-hi[1]))
        # Outside the source domain, hold boundary colors only for the glass
        # shoulder; no extra duplicated UI text is sampled into the interior.
        a=np.interp((x-lo[0])/(hi[0]-lo[0]),warp(axis,k,b[0]),axis)
        c=np.interp((y-lo[1])/(hi[1]-lo[1]),warp(axis,k,b[1]),axis)
        return (lo[0]+(hi[0]-lo[0])*a).astype(np.float32),(lo[1]+(hi[1]-lo[1])*c).astype(np.float32),qx,qy

    def finish(self,screen,mx,my,qx,qy,energy,t):
        # Only the reserved margin is softened; source content stays opaque.
        u=np.clip(self.margin/12,0,1).astype(np.float32)
        a=(u*u*(3-2*u))[:,:,None]
        low=cv2.resize(screen,(120,68),interpolation=cv2.INTER_AREA)
        edge=cv2.resize(cv2.GaussianBlur(low,(0,0),1.6),self.stage.output_size)
        screen=np.rint(screen*(1-a)+edge*.58*a).astype(np.uint8)
        return super().finish(screen,mx,my,qx,qy,energy,t)

    def verify_boundary(self):
        lo,hi=self.safe_bounds()
        u=np.linspace(0,1,65)
        points=np.concatenate([np.column_stack((u,np.zeros_like(u))),np.column_stack((u,np.ones_like(u))),
                               np.column_stack((np.zeros_like(u),u)),np.column_stack((np.ones_like(u),u))])
        points=lo+points*(hi-lo)
        minimum=1.
        for i in range(len(self.states)):
            t=i/self.fps
            c,r,s=self.state(t)
            warped=self.focus_point(points,t)
            mapped=np.array([forward(local_forward(p,c,r,s),self.geometry,BASE_SAG) for p in warped])
            sample=cv2.remap(self.alpha,mapped[:,0].astype(np.float32).reshape(1,-1),mapped[:,1].astype(np.float32).reshape(1,-1),cv2.INTER_LINEAR)
            minimum=min(minimum,float(sample.min()))
        return minimum

    def receipt(self):
        return {**super().receipt(),'profile':'safe-focus-context-lens-v1',
                'cameraUnchanged':False,'sourceProjectionUnchanged':False,
                'fullViewportInOpaqueInterior':True,'minimumSampledBoundaryAlpha':self.min_boundary_alpha,
                'nonlinearPeripheralCompression':True,'cameraPlanUsedAsFocusContextDriver':True,
                'stageCameraMetricsDescribeInputPlanNotRenderedCamera':True}
