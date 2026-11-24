"""Persistent convex cover + bounded cursor-led local lens (research only).

The lens is evaluated on the source clock and never uses model target guesses.
The inverse radial field has compact C2 support and a positive Jacobian.
"""
import math
import cv2
import numpy as np
from motion_glass import MotionGlass, forward, inverse_map

BASE_SAG=.17
REST_STRENGTH=.19
MOVING_STRENGTH=.28
OMEGA=19.
RADIUS=245.

def local_inverse(x,y,center,radius,strength):
    dx=x-center[0];dy=y-center[1]
    r2=(dx*dx+dy*dy)/(radius*radius)
    weight=np.maximum(1-r2,0.)**3
    factor=1-strength*weight
    return center[0]+dx*factor,center[1]+dy*factor

def local_forward(point,center,radius,strength):
    delta=np.asarray(point,dtype=float)-center
    d=float(np.linalg.norm(delta))
    if d==0 or d>=radius:return np.asarray(point,dtype=float)
    lo,hi=d,radius
    for _ in range(32):
        mid=(lo+hi)/2
        mapped=mid*(1-strength*(1-(mid/radius)**2)**3)
        if mapped<d:lo=mid
        else:hi=mid
    return center+delta*((lo+hi)/2/d)

def spring_step(position,velocity,target,dt):
    # Exact critically damped solution for a piecewise constant observed target.
    error=position-target
    impulse=velocity+OMEGA*error
    decay=math.exp(-OMEGA*dt)
    return target+(error+impulse*dt)*decay,(velocity-OMEGA*impulse*dt)*decay

class CursorLens(MotionGlass):
    def __init__(self,stage,manifest,pointer,fps):
        super().__init__(stage,manifest)
        if fps!=60:raise ValueError('Cursor lens requires native60 source')
        self.fps=fps
        self.first=float(pointer.times[0])
        self.states=[]
        self.positions=[]
        self.base_maps=inverse_map(stage.source_size,stage.output_size,BASE_SAG)
        self.prepare_material()
        x0,y0,x1,y1,r=self.geometry
        # Keep entire local support inside the rounded aperture, including corners.
        margin=max(16.,r*.6)
        lo=np.array([x0+margin,y0+margin],dtype=float)
        hi=np.array([x1-margin,y1-margin],dtype=float)
        pos=vel=None
        for i in range(math.ceil(stage.duration*fps)+1):
            t=i/fps
            sw,sh=stage.source_size
            h=cv2.getPerspectiveTransform(np.float32([[0,0],[sw-1,0],[sw-1,sh-1],[0,sh-1]]),stage.quad(t))
            xy=pointer.at(t)
            target=cv2.perspectiveTransform(np.float32([[xy]]),h)[0,0].astype(float)
            # Minimum 85px support even near an edge; move center inward,
            # then limit radius by remaining room rather than pinching text.
            target=np.clip(target,lo+85,hi-85)
            if pos is None:pos=target.copy();vel=np.zeros(2)
            else:pos,vel=spring_step(pos,vel,target,1/fps)
            pos=np.clip(pos,lo+85,hi-85)
            radius=min(RADIUS,float(np.min(np.r_[pos-lo,hi-pos])))
            speed=float(np.linalg.norm(vel))
            strength=REST_STRENGTH+(MOVING_STRENGTH-REST_STRENGTH)*min(speed/600.,1.)
            # Fade in only after actual capture evidence. Remains active
            # thereafter, including stationary holds.
            u=np.clip((t-self.first)/.22,0.,1.)
            strength*=float(u*u*(3-2*u))*(.65+.35*radius/RADIUS)
            self.states.append((pos.copy(),radius,strength))
            self.positions.append(target)
    def state(self,t):
        i=min(max(t*self.fps,0.),len(self.states)-1)
        a=int(i);b=min(a+1,len(self.states)-1);u=i-a
        return tuple((1-u)*x+u*y for x,y in zip(self.states[a],self.states[b]))
    def energy(self,t):
        return .4
    def maps(self,t):
        mx,my,qx,qy=self.base_maps
        c,r,s=self.state(t)
        # Local inverse composed after global inverse: native source lookup
        # once, with no separate magnifier overlay or hard boundary.
        x,y=local_inverse(mx,my,c,r,s)
        return x.astype(np.float32),y.astype(np.float32),qx,qy
    def prepare_material(self):
        from luminous_display_stage import LINEAR
        mx,my,qx,qy=self.base_maps
        self.alpha=cv2.remap(self.mask,mx,my,cv2.INTER_LINEAR).astype(np.float32)/255
        if any(np.any(edge>0) for edge in (self.alpha[0],self.alpha[-1],self.alpha[:,0],self.alpha[:,-1])):
            raise ValueError('Persistent cover would clip the output')
        d=cv2.distanceTransform((self.alpha>.5).astype(np.uint8),cv2.DIST_L2,5)
        gy,gx=np.gradient(d);norm=np.maximum(np.hypot(gx,gy),1e-5)
        nx=gx/norm;ny=gy/norm
        direction=np.clip(.65+.22*ny+.10*nx,.35,.95)
        split=nx*1.6+ny*.6
        def ridge(shift):return np.exp(-((d-2.7-shift)/1.65)**2)
        spectrum=np.stack((ridge(-split),ridge(0),ridge(split)),axis=-1)
        core=np.exp(-((d-2.)/1.3)**2)*direction
        guide=np.exp(-d/28)*(.04+.13*np.clip((qy+.25)/1.25,0,1))
        self.light=(spectrum*.24+core[:,:,None]*.42+
                    guide[:,:,None]*np.float32([.65,.24,.42]))*self.alpha[:,:,None]
        self.light=self.light.astype(np.float32)
        self.transmission=(1-.12*np.exp(-d/12)).astype(np.float32)
        shadow=cv2.remap(self.shadow,mx,my,cv2.INTER_LINEAR,borderMode=cv2.BORDER_CONSTANT)
        self.board=LINEAR[np.clip(self.sky.astype(np.int16)+shadow,0,255).astype(np.uint8)]
    def finish(self,screen,mx,my,qx,qy,energy):
        from luminous_display_stage import LINEAR,to_srgb
        ui=LINEAR[screen]
        face=ui*self.transmission[:,:,None]+self.light
        # Preserve source pixels in the center. The optical shoulder stays
        # fixed; the local lens has no painted ring or separate housing.
        return to_srgb(self.board*(1-self.alpha[:,:,None])+face*self.alpha[:,:,None])
    def project(self,point,t):
        c,r,s=self.state(t)
        return forward(local_forward(point,c,r,s),self.geometry,BASE_SAG)
    def receipt(self):
        centers=np.array([x[0] for x in self.states])
        return {'profile':'persistent-cursor-lens-v1','baseSag':BASE_SAG,
                'restStrength':REST_STRENGTH,'maxStrength':MOVING_STRENGTH,
                'radiusRangePx':[float(min(x[1] for x in self.states)),float(max(x[1] for x in self.states))],
                'centerTravelPx':float(np.linalg.norm(np.diff(centers,axis=0),axis=1).sum()),
                'maxCenterStepPx':float(np.linalg.norm(np.diff(centers,axis=0),axis=1).max()),
                'recordedPointerOnly':True,'sourceClockPreserved':True,
                'cameraExposureDisabledForStudy':True,'creativeApproval':False}
