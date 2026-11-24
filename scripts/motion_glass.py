"""Opt-in optical motion on the verified clearface stage.

Use the existing source camera and timestamps. A convex inverse map and
its analytic forward counterpart share one deformation for UI and cursor.
Only the window and its shadow deform; the environment never does.
"""
from functools import lru_cache
import math
import cv2
import numpy as np
from cloud_window_clearface_stage import window_geometry, card_mask, physical_plate
from cloud_window_sky_stage import sky_background

PEAK_SAG=.055
MIN_TRAVEL=.30

def travel_windows(camera, events, duration):
    """Only genuine camera travel, outside observed interaction/result holds."""
    protected=[]
    for event in events:
        start=float(event.get('start',event['t']))
        end=max(float(event['t']),float(event.get('end',event['t'])))
        protected.append((max(0.,start-.09), min(duration,end+.30)))
    windows=[]
    for old,new in zip(camera,camera[1:]):
        if new.cut or new.at-new.start_at<MIN_TRAVEL:
            continue
        if abs(new.scale-old.scale)<.015 and abs(new.center_x-old.center_x)+abs(new.center_y-old.center_y)<.015:
            continue
        pieces=[(new.start_at,new.at)]
        for left,right in protected:
            result=[]
            for a,b in pieces:
                if b<=left or a>=right:result.append((a,b))
                else:
                    if a<left:result.append((a,left))
                    if b>right:result.append((right,b))
            pieces=result
        windows.extend((a,b) for a,b in pieces if b-a>=MIN_TRAVEL)
    return tuple(windows)

def energy_at(windows,t):
    return max((math.sin(math.pi*(t-a)/(b-a))**2 for a,b in windows if a<t<b),default=0.)

def forward(point,geometry,sag):
    x0,y0,x1,y1,_=geometry
    center=np.array([(x0+x1)/2.,(y0+y1)/2.])
    half=np.array([(x1-x0)/2.,(y1-y0)/2.])
    q=(np.asarray(point)-center)/half
    denom=1-sag+sag*np.dot(q,q)/2
    return center+half*q/denom

@lru_cache(maxsize=4)
def grid(source_size,output_size):
    x0,y0,x1,y1,_=window_geometry(source_size,output_size)
    ow,oh=output_size
    # Full canvas mapping is bounded; outside the silhouette only the
    # existing soft shadow is affected.
    y,x=np.indices((oh,ow),dtype=np.float32)
    cx,cy=(x0+x1)/2.,(y0+y1)/2.
    hx,hy=(x1-x0)/2.,(y1-y0)/2.
    return (x-cx)/hx,(y-cy)/hy,cx,cy,hx,hy

def inverse_map(source_size,output_size,sag):
    u,v,cx,cy,hx,hy=grid(source_size,output_size)
    a=.5*sag*(u*u+v*v)
    k=2*(1-sag)/(1+np.sqrt(np.maximum(1-4*a*(1-sag),.01)))
    qx,qy=u*k,v*k
    return (qx*hx+cx).astype(np.float32),(qy*hy+cy).astype(np.float32),qx,qy

def reflect_face(image,qx,qy,energy):
    # Deliberate specular sweep along upper-left and right shoulders.
    # At rest it is very faint, and never replaces the source.
    top=np.exp(-((qx+.32-.22*energy)/.50)**6-((qy+.965-.065*energy)/.020)**4)
    side=np.exp(-((qx-.976+.018*energy)/.013)**2-((qy+.13)/.60)**6)
    light=np.clip((.075+.26*energy)*top+(.05+.16*energy)*side,0,.36)
    return np.rint(image*(1-light[:,:,None])+250*light[:,:,None]).astype(np.uint8)

class MotionGlass:
    def __init__(self,stage,manifest):
        if stage.immersive or stage.mouse_follow is not None or any(k.cut or k.yaw or k.pitch for k in stage.camera):
            raise ValueError('Motion glass study requires continuous axis-aligned single-plane camera')
        self.stage=stage
        self.windows=travel_windows(stage.camera,manifest['events'],stage.duration)
        self.geometry=window_geometry(stage.source_size,stage.output_size)
        self.mask=card_mask(stage.source_size,stage.output_size)
        self.sky=sky_background(stage.output_size)
        self.shadow=physical_plate(stage.source_size,stage.output_size).astype(np.int16)-self.sky.astype(np.int16)
    def energy(self,t):
        return energy_at(self.windows,t)
    def project(self,point,t):
        return forward(point,self.geometry,PEAK_SAG*self.energy(t))
    def maps(self,t):
        return inverse_map(self.stage.source_size,self.stage.output_size,PEAK_SAG*self.energy(t))
    def render(self,source,t):
        stage=self.stage; sw,sh=stage.source_size; ow,oh=stage.output_size
        quad=stage.quad(t)
        # Reuse the source-true camera; antialias before projection.
        scale=min(1.,max(np.linalg.norm(quad[1]-quad[0])/sw,
                         np.linalg.norm(quad[3]-quad[0])/sh)*1.10)
        if scale<.85:source=cv2.resize(source,(round(sw*scale),round(sh*scale)),interpolation=cv2.INTER_AREA)
        h,w=source.shape[:2]
        H=cv2.getPerspectiveTransform(np.float32([[0,0],[w-1,0],[w-1,h-1],[0,h-1]]),quad)
        energy=self.energy(t)
        mx,my,qx,qy=self.maps(t)
        # Direct inverse source lookup: one resampling pass, no double blur.
        I=np.linalg.inv(H)
        den=I[2,0]*mx+I[2,1]*my+I[2,2]
        sx=((I[0,0]*mx+I[0,1]*my+I[0,2])/den).astype(np.float32)
        sy=((I[1,0]*mx+I[1,1]*my+I[1,2])/den).astype(np.float32)
        screen=cv2.remap(source,sx,sy,cv2.INTER_CUBIC,borderMode=cv2.BORDER_REPLICATE)
        return self.finish(screen,mx,my,qx,qy,energy)
    def finish(self,screen,mx,my,qx,qy,energy):
        screen=reflect_face(screen,qx,qy,energy)
        mask=cv2.remap(self.mask,mx,my,cv2.INTER_LINEAR,borderMode=cv2.BORDER_CONSTANT)
        shadow=cv2.remap(self.shadow,mx,my,cv2.INTER_LINEAR,borderMode=cv2.BORDER_CONSTANT)
        board=np.clip(self.sky.astype(np.int16)+shadow,0,255).astype(np.uint8)
        alpha=mask.astype(np.uint16)[:,:,None]
        return ((board.astype(np.uint16)*(255-alpha)+screen.astype(np.uint16)*alpha+127)//255).astype(np.uint8)
    def receipt(self):
        return {'profile':'camera-travel-optical-v1','peakSag':PEAK_SAG,'windows':self.windows,
                'sourceClockPreserved':True,'cameraExposureDisabledForStudy':True,'creativeApproval':False}
