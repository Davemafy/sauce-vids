"""A single deep rounded cloud-glass enclosure, with an opaque source display."""
from functools import lru_cache
import cv2
import numpy as np
from cloud_window_sky_stage import sky_background, _rounded_mask

PRESET="cloud_window_volume_v1"

def window_geometry(source_size,output_size):
    sw,sh=source_size;ow,oh=output_size
    if min(sw,sh,ow,oh)<=0:raise ValueError("Invalid glass geometry")
    height=min(.85*oh,.84*ow*sh/sw)
    width=height*sw/sh
    x0=round((ow-width)/2);y0=round((oh-height)/2)
    return x0,y0,round(x0+width),round(y0+height),max(4,round(.020*oh))

@lru_cache(maxsize=5)
def card_mask(source_size,output_size):
    x0,y0,x1,y1,r=window_geometry(source_size,output_size)
    return _rounded_mask(output_size,(x0,y0,x1,y1),r)

@lru_cache(maxsize=5)
def object_mask(source_size,output_size):
    x0,y0,x1,y1,r=window_geometry(source_size,output_size)
    p=max(4,round(output_size[1]*.048))
    outer=(x0-p,y0-p,x1+p,y1+p)
    if min(outer[0],outer[1])<2 or outer[2]>output_size[0]-2 or outer[3]>output_size[1]-2:
        raise ValueError("Glass enclosure would clip")
    return cv2.GaussianBlur(_rounded_mask(output_size,outer,r+p),(0,0),.65)

@lru_cache(maxsize=4)
def physical_plate(source_size,output_size):
    """Cloud-filled solid glass backing, curved walls and recessed display seat."""
    ow,oh=output_size
    original=sky_background(output_size).astype(np.float32)
    sky=original.copy()
    shell=object_mask(source_size,output_size)
    aperture=card_mask(source_size,output_size)
    surf=shell.astype(np.float32)/255.
    x0,y0,x1,y1,r=window_geometry(source_size,output_size)
    pad=round(oh*.048)
    rows,cols=np.indices((oh,ow),dtype=np.float32)
    u=(cols-x0+pad)/(x1-x0+2*pad)
    v=(rows-y0+pad)/(y1-y0+2*pad)
    # Soft elevation and dense short contact shadow on the existing sky.
    reduced=cv2.resize(shell,(ow//4,oh//4),interpolation=cv2.INTER_AREA)
    for blur,offset,strength in ((16,5,.26),(5,3,.20)):
        a=cv2.GaussianBlur(reduced,(0,0),blur)
        shifted=np.zeros_like(a);shifted[offset:]=a[:-offset]
        sky*=1-strength*cv2.resize(shifted,(ow,oh))[:,:,None].astype(np.float32)/255.
    # Separate cloud body with convex refraction and depth-dependent blue.
    dist=cv2.distanceTransform((shell>225).astype(np.uint8),cv2.DIST_L2,5)
    gy,gx=np.gradient(dist);norm=np.hypot(gx,gy)+1e-5
    curvature=np.exp(-dist/max(1.,pad*.70))*surf
    mx=(.08+.84*u)*ow+gx/norm*curvature*oh*.028
    my=(.07+.86*v)*oh+gy/norm*curvature*oh*.040
    glass=cv2.remap(original,mx,my,cv2.INTER_LINEAR,borderMode=cv2.BORDER_REFLECT_101)
    glass=cv2.GaussianBlur(glass,(0,0),max(.7,oh*.0015))
    tint=np.empty_like(glass);tint[:]=[202,119,45]
    a=(.08+.20*np.clip(v,0,1))[:,:,None]
    glass=glass*(1-a)+tint*a
    # Broad, pillow-like curved wall; stronger upper left studio reflection.
    bevel=np.clip(1-dist/max(1.,pad),0,1)*surf
    directional=np.clip(.85-.52*v+.12*(1-u),.25,1.)
    shine=(bevel**1.65*.58*directional)[:,:,None]
    glass=glass*(1-shine)+np.float32([255,255,255])*shine
    top=np.exp(-((v-.023)/.010)**2-((u-.33)/.28)**6)*.72
    left=np.exp(-((u-.013)/.008)**2-((v-.36)/.30)**4)*.44
    right=np.exp(-((u-.984)/.008)**2-((v-.33)/.27)**4)*.38
    spec=np.clip(top+left+right,0,.75)*surf
    glass=glass*(1-spec[:,:,None])+255.*spec[:,:,None]
    # Refraction darkens the lower curved wall, rather than drawing a white ring.
    bottom=bevel*np.clip((v-.58)/.42,0,1)*.27
    glass*=1-bottom[:,:,None]
    # Small inset contact shadow where the opaque display meets the glass.
    seat=cv2.GaussianBlur(aperture,(0,0),max(1.,oh*.006)).astype(np.float32)/255.
    seat*=1-aperture.astype(np.float32)/255.
    glass*=1-.36*seat[:,:,None]
    # Aperture is filled later with untouched source pixels, not this glass.
    return np.rint(np.clip(sky*(1-surf[:,:,None])+glass*surf[:,:,None],0,255)).astype(np.uint8)
