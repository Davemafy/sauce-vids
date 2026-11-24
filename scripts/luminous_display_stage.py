"""Reference-inspired optical cover: one opaque source display under a lens.

Approximate dielectric light transport in linear light, not ray tracing.
All UI emission comes from the native capture. Curvature, Fresnel, edge
dispersion and light scattering share a single stationary cover geometry.
"""
from functools import lru_cache
import cv2
import numpy as np
from cloud_window_clearface_stage import card_mask, window_geometry
from cloud_window_sky_stage import sky_background

PRESET = "cloud_luminous_display_v1"
KX, KY = .052, .039
LINEAR = np.where(np.arange(256,dtype=np.float32)/255<=.04045,
                  np.arange(256,dtype=np.float32)/3294.6,
                  ((np.arange(256,dtype=np.float32)/255+.055)/1.055)**2.4)
SRGB = np.rint(255*np.where(np.linspace(0,1,16384)<=.0031308,
                 12.92*np.linspace(0,1,16384),
                 1.055*np.linspace(0,1,16384)**(1/2.4)-.055)).astype(np.uint8)

def to_srgb(a):
    return SRGB[np.rint(np.clip(a,0,1)*16383).astype(np.int32)]

def geom(source_size,output_size):
    x0,y0,x1,y1,_=window_geometry(source_size,output_size)
    return (x0+x1)*.5,(y0+y1)*.5,(x1-x0)*.5,(y1-y0)*.5

def forward(points,source_size,output_size):
    cx,cy,hx,hy=geom(source_size,output_size)
    p=np.asarray(points,np.float32)
    u=(p[...,0]-cx)/hx;v=(p[...,1]-cy)/hy
    return np.stack((cx+hx*u*(1+KX*(1-v*v)),
                     cy+hy*v*(1+KY*(1-u*u))),axis=-1).astype(np.float32)

@lru_cache(maxsize=3)
def fields(source_size,output_size):
    ow,oh=output_size;cx,cy,hx,hy=geom(source_size,output_size)
    y,x=np.indices((oh,ow),dtype=np.float32)
    a=(x-cx)/hx;b=(y-cy)/hy
    u=a.copy();v=b.copy()
    for _ in range(8):
        u=a/(1+KX*(1-v*v));v=b/(1+KY*(1-u*u))
    mx=(cx+hx*u).astype(np.float32);my=(cy+hy*v).astype(np.float32)
    alpha=cv2.remap(card_mask(source_size,output_size),mx,my,cv2.INTER_LINEAR).astype(np.float32)/255
    binary=(alpha>.5).astype(np.uint8)
    di=cv2.distanceTransform(binary,cv2.DIST_L2,5)
    do=cv2.distanceTransform(1-binary,cv2.DIST_L2,5)
    d=(di-do)/max(.3,oh/1080)
    gy,gx=np.gradient(d);n=np.maximum(np.hypot(gx,gy),1e-5)
    nx=gx/n;ny=gy/n
    # Polished dielectric shoulder: the changing surface normal increases
    # grazing reflection, while the center transmits almost all display light.
    shoulder=np.exp(-np.maximum(d,0)/18)
    cos_theta=np.clip(1-.90*shoulder-.08*np.minimum(u*u+v*v,1),.04,1)
    fresnel=.04+.96*(1-cos_theta)**5
    orientation=np.clip(.65+.24*ny+.13*nx,.25,1)
    spec=np.maximum(fresnel-.04,0)*orientation
    # Chromatic caustic: separate RGB focal paths across the narrow meniscus.
    # The paths follow the actual curved boundary, not an independent stroke.
    dispersion=np.clip(nx*.8+ny*.36,-1,1)
    ridge=lambda shift: np.exp(-((d-2.8-shift)/1.8)**2)
    spectral=np.stack((ridge(-1.9*dispersion),ridge(.25),ridge(1.9*dispersion)),axis=-1)
    spectral*=np.clip(.45+.22*ny+.12*nx,.22,.85)[:,:,None]
    # Simulated multiple internal reflections in the thick cover glass.
    # Cool glass material is localized near the shoulder, never a UI recolor.
    lower=np.clip((v+.25)/1.25,0,1)
    guide=np.exp(-np.maximum(d,0)/32)*(.09+.28*lower)
    scatter=guide[:,:,None]*np.float32([.63,.24,.36])
    softbox=np.exp(-((u+.38)/.8)**4-((v+.94+.028*u)/.055)**2)*.024
    core=np.exp(-((d-2.0)/1.25)**2)*(.32+.16*orientation)
    reflection=spec[:,:,None]*np.float32([.26,.28,.32])+spectral*.44+scatter+core[:,:,None]*np.float32([.94,.97,1])
    reflection+=softbox[:,:,None]*np.float32([.8,.9,1])
    reflection*=alpha[:,:,None]
    # Lens is opaque in the sense that only the captured display is visible
    # behind it. No sky is transmitted through UI.
    sky=LINEAR[sky_background(output_size)]
    shadow=cv2.GaussianBlur(cv2.resize(alpha,(max(2,ow//4),max(2,oh//4))), (0,0),10)
    shadow=cv2.resize(shadow,output_size)
    board=sky*(1-.28*shadow[:,:,None])
    return mx,my,alpha,d,fresnel,reflection,board

def project_point(stage,t,x,y):
    sw,sh=stage.source_size
    h=cv2.getPerspectiveTransform(np.float32([[0,0],[sw-1,0],[sw-1,sh-1],[0,sh-1]]),stage.quad(t))
    p=cv2.perspectiveTransform(np.float32([[[x,y]]]),h)[0,0]
    return forward(p,stage.source_size,stage.output_size)

def render(stage,source,t):
    sw,sh=stage.source_size;ow,oh=stage.output_size
    if source.shape!=(sh,sw,3):raise ValueError("Wrong native source geometry")
    mx,my,alpha,d,fresnel,reflection,board=fields(stage.source_size,stage.output_size)
    q=stage.quad(t)
    scale=min(1.,max(np.linalg.norm(q[1]-q[0])/sw,np.linalg.norm(q[3]-q[0])/sh)*1.12)
    if scale<.85:
        source=cv2.resize(source,(max(2,round(sw*scale)),max(2,round(sh*scale))),interpolation=cv2.INTER_AREA)
    h,w=source.shape[:2]
    inv=cv2.getPerspectiveTransform(q,np.float32([[0,0],[w-1,0],[w-1,h-1],[0,h-1]]))
    z=inv[2,0]*mx+inv[2,1]*my+inv[2,2]
    sx=((inv[0,0]*mx+inv[0,1]*my+inv[0,2])/z).astype(np.float32)
    sy=((inv[1,0]*mx+inv[1,1]*my+inv[1,2])/z).astype(np.float32)
    valid=alpha>.98
    if np.any((sx[valid]<-1.5)|(sy[valid]<-1.5)|(sx[valid]>w+.5)|(sy[valid]>h+.5)):
        raise ValueError("Optical source does not cover aperture")
    ui=LINEAR[cv2.remap(source,sx,sy,cv2.INTER_CUBIC,borderMode=cv2.BORDER_REPLICATE)]
    # Selective display emission diffusion. Only genuine bright pixels emit;
    # preserve the original sharp image rather than replacing it with blur.
    lum=ui@np.float32([.0722,.7152,.2126])
    emit=ui*np.clip((lum-.42)/.58,0,1)[:,:,None]*alpha[:,:,None]
    small=cv2.resize(emit,(max(2,ow//4),max(2,oh//4)),interpolation=cv2.INTER_AREA)
    bloom=cv2.resize(cv2.GaussianBlur(small,(0,0),1.15), (ow,oh))
    wide=cv2.resize(cv2.GaussianBlur(small,(0,0),5.0), (ow,oh))
    # Transmission, source-driven bloom and internal reflections add in
    # linear light. Limit absorption to the actual grazing shoulder.
    face=ui*(1-np.clip(fresnel-.04,0,.55)[:,:,None]*.48)
    face+=.055*bloom+.025*wide+reflection
    # Fine, restrained display microtexture, zero in bright typography.
    # Fixed optical coordinates, no frame-varying flicker or fake scanlines.
    texture=(.5+.5*np.cos(my*np.pi/2))*np.exp(-np.maximum(d,0)/70)
    face*=1-.012*texture[:,:,None]*(1-lum[:,:,None])
    return to_srgb(board*(1-alpha[:,:,None])+face*alpha[:,:,None])
