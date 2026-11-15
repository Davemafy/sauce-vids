"""Real frame callouts anchored to real UI boxes, AFTER 3D homography.

Pills use a blurred real-frame backdrop, softened specular border and
leader line. A critically damped mass=.8 stiffness=220 damping=20 spring
keeps callouts attached during moving camera and window parallax.
"""
from __future__ import annotations
from dataclasses import dataclass,field
from functools import lru_cache
from math import exp
import cv2,numpy as np
from PIL import Image,ImageDraw,ImageFont
from spatial_parallax import window_homography,map_pointer


@lru_cache(maxsize=1)
def _font():
    for path in ('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
                 '/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf'):
        try:return ImageFont.truetype(path,24)
        except OSError:pass
    return ImageFont.load_default()


@dataclass
class _Spring:
    x:float=0.
    y:float=0.
    vx:float=0.
    vy:float=0.
    ready:bool=False

    def step(self,tx:float,ty:float,dt:float):
        if not self.ready:
            self.x,self.y=tx,ty;self.ready=True
        mass,stiffness,damping=.8,220.,20.
        ax=(stiffness*(tx-self.x)-damping*self.vx)/mass
        ay=(stiffness*(ty-self.y)-damping*self.vy)/mass
        self.vx+=ax*dt;self.vy+=ay*dt
        self.x+=self.vx*dt;self.y+=self.vy*dt
        return self.x,self.y


@dataclass
class KineticCalloutRenderer:
    callouts:list[dict]
    fps:int=60
    _springs:dict[int,_Spring]=field(default_factory=dict)

    def draw(self,frame:np.ndarray,frame_idx:int,
             source_factor:float,dx:float,dy:float,
             tilt:tuple[float,float],window:tuple[int,int,int,int],
             focal:float=1820.)->None:
        now_ms=frame_idx*1000./self.fps
        x,y,w,h=window
        H=window_homography(x,y,w,h,*tilt,focal=focal)
        for i,cue in enumerate(self.callouts):
            start=float(cue['outputStartMs']);end=float(cue['outputEndMs'])
            if not start<=now_ms<end:continue
            text=str(cue['text'])
            if not text or len(text)>58:continue
            box=cue['box']
            anchor_x=x+dx+(box['x']+box['width']/2)*source_factor
            anchor_y=y+dy+box['y']*source_factor
            ax,ay=map_pointer(H,anchor_x,anchor_y)
            font=_font()
            text_w=int(ImageDraw.Draw(Image.new('RGB',(1,1))).textlength(text,font=font))
            pill_w=max(170,text_w+54)
            pill_h=53
            target_x=max(30,min(frame.shape[1]-pill_w-30,ax-pill_w/2))
            target_y=max(30,min(frame.shape[0]-pill_h-35,ay-90))
            state=self._springs.setdefault(i,_Spring())
            px,py=state.step(target_x,target_y,1/self.fps)
            px,py=round(px),round(py)
            # Modulate visibility at ingress/egress; fixed 1800ms max lifetime.
            fade=min(1,(now_ms-start)/180,(end-now_ms)/220)
            alpha=max(0.,min(1.,fade))
            if alpha<=0:continue
            x0=max(0,px);y0=max(0,py);x1=min(frame.shape[1],px+pill_w);y1=min(frame.shape[0],py+pill_h)
            if x0>=x1 or y0>=y1:continue
            roi=frame[y0:y1,x0:x1]
            softened=cv2.GaussianBlur(roi,(0,0),16)
            frame[y0:y1,x0:x1]=np.uint8(
                roi.astype(np.float32)*(1-alpha*.72)+softened.astype(np.float32)*(alpha*.72))
            # Exact visible film surface is BGR; PIL works in RGB.
            image=Image.fromarray(cv2.cvtColor(frame[y0:y1,x0:x1],cv2.COLOR_BGR2RGB))
            shade=Image.new('RGBA',(x1-x0,y1-y0),(0,0,0,0))
            d=ImageDraw.Draw(shade)
            dw,dh=x1-x0,y1-y0
            d.rounded_rectangle((0,0,dw-1,dh-1),radius=19,
                fill=(11,15,24,round(200*alpha)),
                outline=(216,230,244,round(80*alpha)),width=1)
            d.line((17,2,dw-17,2),fill=(255,255,255,round(65*alpha)),width=1)
            d.text((27,12),text,font=font,fill=(247,248,249,round(255*alpha)))
            image=Image.alpha_composite(image.convert('RGBA'),shade).convert('RGB')
            frame[y0:y1,x0:x1]=cv2.cvtColor(np.array(image),cv2.COLOR_RGB2BGR)
            # Thin physical connection to projected UI anchor.
            line_from=(round(px+pill_w*.5),round(py+pill_h))
            line_to=(round(ax),round(ay-4))
            overlay=frame.copy()
            cv2.line(overlay,line_from,line_to,(193,204,218),1,cv2.LINE_AA)
            cv2.circle(overlay,line_to,3,(221,226,237),-1,cv2.LINE_AA)
            cv2.addWeighted(overlay,alpha*.55,frame,1-alpha*.55,0,dst=frame)
