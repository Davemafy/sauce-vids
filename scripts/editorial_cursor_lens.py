"""Selective optical focus with genuine action/result bounds, opt-in research."""
import cv2
import numpy as np
from cursor_lens import CursorLens
from feathered_cursor_lens import feather_mask

FEATHER=7.
SAFE_INSET=13.

def protected_quad(q,geometry,source_size,rect):
    """Preserve source coverage and protected rect; retain as much zoom as fits."""
    x0,y0,x1,y1,_=geometry
    lo=np.array([x0,y0],float);hi=np.array([x1,y1],float)
    base=hi-lo
    sw,sh=source_size
    start=np.array([rect['x']/sw,rect['y']/sh])
    end=start+np.array([rect['width']/sw,rect['height']/sh])
    if np.any(start<0) or np.any(end>1.00001) or np.any(end<=start):
        raise ValueError('Invalid protected source geometry')
    inset=np.array([SAFE_INSET,geometry[4]+SAFE_INSET])
    safe_lo=lo+inset;safe_hi=hi-inset
    wanted=np.ptp(q,axis=0)
    z=max(1.,float(np.min(wanted/base)))
    # Coverage and protected bounds give linear inequalities on translation.
    def limits(z):
        size=base*z
        return np.maximum(hi-size,safe_lo-start*size),np.minimum(lo,safe_hi-end*size)
    a,b=limits(1.)
    if np.any(a>b):raise ValueError('Protected region cannot fit inside the optical aperture')
    if np.any(limits(z)[0]>limits(z)[1]):
        left,right=1.,z
        for _ in range(24):
            mid=(left+right)/2
            a,b=limits(mid)
            if np.all(a<=b):left=mid
            else:right=mid
        z=left
    a,b=limits(z)
    p=np.clip(np.min(q,axis=0),a,b)
    e=p+base*z
    return np.float32([p,[e[0],p[1]],e,[p[0],e[1]]])

class EditorialCursorLens(CursorLens):
    def __init__(self,stage,manifest,pointer,fps):
        events=manifest.get('events',[])
        if len(events)!=1 or not events[0].get('evidence'):
            raise ValueError('Single verified action required for selective framing study')
        e=events[0]
        a,b=e['targetRect'],e['resultRect']
        x=min(a['x'],b['x']);y=min(a['y'],b['y'])
        self.protected={'x':x,'y':y,'width':max(a['x']+a['width'],b['x']+b['width'])-x,
                        'height':max(a['y']+a['height'],b['y']+b['height'])-y}
        super().__init__(stage,manifest,pointer,fps)
        self.verify_protected()
    def camera_quad(self,t):
        return protected_quad(self.stage.quad(t),self.geometry,self.stage.source_size,self.protected)
    def prepare_material(self):
        super().prepare_material()
        d=cv2.distanceTransform((self.alpha>.5).astype(np.uint8),cv2.DIST_L2,5)
        self.alpha=feather_mask(self.alpha,FEATHER*self.stage.output_size[1]/1080).astype(np.float32)
        _,_,qx,qy=self.base_maps
        # Restrained, directional neutral light, not a thick neon rim.
        glint=np.exp(-((d-8)/1.65)**2)*np.clip(-qy,0,1)**5*np.exp(-((qx+.25)/.78)**6)
        self.light+=glint[:,:,None]*np.float32([.09,.10,.11])
        self.light=np.minimum(self.light,.45)
    def verify_protected(self):
        r=self.protected
        sw,sh=self.stage.source_size
        u=np.linspace(0,1,17)
        x=r['x']+u*r['width'];y=r['y']+u*r['height']
        p=np.concatenate([np.column_stack((x,np.full_like(x,y[0]))),np.column_stack((x,np.full_like(x,y[-1]))),
          np.column_stack((np.full_like(y,x[0]),y)),np.column_stack((np.full_like(y,x[-1]),y))]).astype(np.float32)
        self.min_alpha=1.;self.zoom=[]
        for i in range(len(self.states)):
            t=i/self.fps;q=self.camera_quad(t)
            h=cv2.getPerspectiveTransform(np.float32([[0,0],[sw-1,0],[sw-1,sh-1],[0,sh-1]]),q)
            flat=cv2.perspectiveTransform(p[None,:,:],h)[0]
            mapped=np.array([self.project(x,t) for x in flat])
            a=cv2.remap(self.alpha,mapped[:,0].astype(np.float32)[None,:],mapped[:,1].astype(np.float32)[None,:],cv2.INTER_LINEAR)
            if float(a.min())<self.min_alpha:
                self.min_alpha=float(a.min());self.worst=(t,mapped[int(a.argmin())].tolist(),flat[int(a.argmin())].tolist(),q.tolist())
            self.zoom.append(float(np.ptp(q,axis=0)[0]/(self.geometry[2]-self.geometry[0])))
        if self.min_alpha<.98:raise ValueError(f'Protected alpha {self.min_alpha}: {self.worst}, {self.geometry}')
    def receipt(self):
        return {**super().receipt(),'profile':'editorial-cursor-lens-v1',
                'protectedRect':self.protected,'minimumSampledProtectedAlpha':self.min_alpha,
                'cameraZoomRange':[min(self.zoom),max(self.zoom)],'inwardFeatherPxAt1080':FEATHER,
                'stageCameraMetricsDescribeInputPlanNotRenderedCamera':True}
