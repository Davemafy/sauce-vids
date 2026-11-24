"""Clouds BEHIND a genuinely captured, glossy floating browser window.

Owner-directed 2026-11-24 composition: floating translucent acrylic replaces
the opaque cloud-filled glass body. Sky/clouds belong to the environment.
There are deliberately no fake window dots, address bars, text, or buttons;
the original browser image is projected last and remains fully source-true.
"""
from __future__ import annotations

from functools import lru_cache
import cv2
import numpy as np

PRESET = "cloud_window_sky_v1"


def window_geometry(source_size, output_size):
    """Large centered source aperture. Clouds are OUTSIDE the screen."""
    sw, sh = source_size
    ow, oh = output_size
    if min(sw, sh, ow, oh) <= 0:
        raise ValueError("Invalid source or output geometry")
    aspect = sw / sh
    # Fill the available height while preserving the source aspect ratio.
    # No separate tiny webpage surrounded by an ornamental silhouette.
    height = min(oh * .895, ow * .90 / aspect)
    width = height * aspect
    x0 = round((ow - width) / 2)
    y0 = round((oh - height) / 2)
    x1, y1 = round(x0 + width), round(y0 + height)
    radius = max(6, round(oh * .024))
    return x0, y0, x1, y1, radius


def _rounded_mask(dimensions, bounds, radius):
    ow, oh = dimensions
    x0, y0, x1, y1 = bounds
    r = min(radius, (x1-x0)//3, (y1-y0)//3)
    m = np.zeros((oh, ow), np.uint8)
    cv2.rectangle(m, (x0+r,y0), (x1-r,y1), 255,-1)
    cv2.rectangle(m, (x0,y0+r), (x1,y1-r), 255,-1)
    for cx,cy in ((x0+r,y0+r),(x1-r,y0+r),
                  (x0+r,y1-r),(x1-r,y1-r)):
        cv2.circle(m,(cx,cy),r,255,-1,cv2.LINE_AA)
    return m


@lru_cache(maxsize=8)
def object_mask(output_size, source_size=(2880, 1800)):
    """One conventional rounded glass browser, without organic tails."""
    ow,oh=output_size
    x0,y0,x1,y1,r=window_geometry(source_size,output_size)
    pad=max(4,round(oh*.017))
    outer=(x0-pad,y0-pad,x1+pad,y1+pad)
    if min(outer[0],outer[1])<2 or outer[2]>ow-2 or outer[3]>oh-2:
        raise ValueError("Glass browser edge would be cut off")
    return cv2.GaussianBlur(_rounded_mask(output_size,outer,r+pad),
                             (0,0),.6)


@lru_cache(maxsize=5)
def card_mask(source_size,output_size):
    x0,y0,x1,y1,r=window_geometry(source_size,output_size)
    return _rounded_mask(output_size,(x0,y0,x1,y1),r)


@lru_cache(maxsize=4)
def sky_background(output_size):
    """The existing source-proven cobalt cloud asset becomes the BACKGROUND.

    Gentle atmospheric smoothing removes most print micro-dots and places
    the cloud formations in an airy blue environment. The scene never
    contains model-invented source application imagery.
    """
    from cloud_shadow_stage import backdrop
    ow,oh=output_size
    original=backdrop(ow,oh)
    sky=cv2.GaussianBlur(original,(0,0),2.35).astype(np.float32)
    y=np.linspace(0,1,oh,dtype=np.float32)[:,None,None]
    tint=np.zeros((1,ow,3),np.float32)
    tint[:]=np.array([252.,220.,160.],np.float32)  # BGR soft daylight sky
    # Preserve actual cloud shapes while lifting the deep cobalt shadows.
    strength=.43+.08*y
    sky=sky*(1-strength)+tint*strength
    # Upper-left daylight spills into sky naturally, no radial color blobs.
    illum=np.exp(-((np.arange(ow,dtype=np.float32)[None,:]/ow-.03)/.55)**2)
    illum=illum*np.exp(-((np.arange(oh,dtype=np.float32)[:,None]/oh-.02)/.6)**2)
    white=(.11*illum)[:,:,None]
    sky=sky*(1-white)+np.float32([255,255,255])*white
    return np.clip(sky,0,255).astype(np.uint8)


@lru_cache(maxsize=4)
def physical_plate(source_size,output_size):
    """Actual transparent shell, shadows and bright edge glints over the sky."""
    ow,oh=output_size
    sky=sky_background(output_size).astype(np.float32)
    shell=object_mask(output_size,source_size)
    card=card_mask(source_size,output_size)
    surf=shell.astype(np.float32)/255.
    rows,cols=np.indices((oh,ow),dtype=np.float32)
    x=cols/ow; y=rows/oh

    # Shadow is composited onto the CLOUDS (not a white/gradient wallpaper).
    low=cv2.resize(shell,(max(2,ow//4),max(2,oh//4)),interpolation=cv2.INTER_AREA)
    for blur,off,opacity in ((20.,22,.27),(7.,8,.22)):
        a=cv2.GaussianBlur(low,(0,0),blur)
        dy=max(1,round(off/4))
        shifted=np.zeros_like(a)
        shifted[dy:,:]=a[:-dy,:]
        shade=cv2.resize(shifted,(ow,oh),interpolation=cv2.INTER_LINEAR)
        sky*=1.-opacity*shade[:,:,None].astype(np.float32)/255.

    # Light transmission: glass is CLEAR. It slightly refracts the sky
    # underneath, instead of filling itself with its own cloud illustration.
    dist=cv2.distanceTransform((shell>225).astype(np.uint8),cv2.DIST_L2,5)
    gy,gx=np.gradient(dist)
    normal=np.sqrt(gx*gx+gy*gy)+1e-4
    edge=np.exp(-dist/max(3.,oh*.035))*surf
    shiftx=(gx/normal)*edge*(ow*.0055)
    shifty=(gy/normal)*edge*(oh*.0085)
    refr=cv2.remap(sky,cols+shiftx,rows+shifty,cv2.INTER_LINEAR,
                   borderMode=cv2.BORDER_REFLECT_101)

    # Subtle blue optical tint and broad translucent centre, not opaque paint.
    blue=np.zeros_like(refr)
    blue[:,:,0]=242.-10.*y
    blue[:,:,1]=183.-45.*y
    blue[:,:,2]=105.-36.*y
    tint=.19+.11*y
    refr=refr*(1.-tint[:,:,None])+blue*tint[:,:,None]
    milky=np.exp(-((x-.19)/.52)**2-((y-.15)/.34)**2)*.14
    refr=refr*(1.-milky[:,:,None])+np.float32([255,255,255])*milky[:,:,None]

    # Physical rounded meniscus with multiple specular tracks, not a neon
    # outline or a blurred product screenshot. Everything stays outside UI.
    rim=np.clip((oh*.055-dist)/(oh*.055),0,1)*surf
    upper=np.clip(1.-y/.85,.05,1.)
    fresnel=np.clip(rim*(.28+.36*upper),0,.66)
    refr=refr*(1-fresnel[:,:,None])+np.float32([255,255,255])*fresnel[:,:,None]
    ridge=np.exp(-((dist-oh*.012)/(oh*.006))**2)*surf
    glint=np.exp(-((dist-oh*.004)/(oh*.003))**2)*surf
    spec=np.clip(ridge*.31+glint*(.36+.28*upper),0,.78)
    refr=refr*(1-spec[:,:,None])+np.float32([254,254,255])*spec[:,:,None]
    # Specular bands follow the browser shell, never a separate shape.
    x0,y0,x1,y1,_=window_geometry(source_size,output_size)
    top=(y0-max(4,round(oh*.017))*.52)/oh
    left_x=(x0-max(4,round(oh*.017))*.52)/ow
    right_x=(x1+max(4,round(oh*.017))*.52)/ow
    box1=np.exp(-((x-.35)/.24)**4-((y-top)/.013)**2)*.36
    box2=np.exp(-((x-.63)/.10)**4-((y-top)/.010)**2)*.22
    left=np.exp(-((x-left_x)/.009)**2-((y-.35)/.34)**4)*.16
    right=np.exp(-((x-right_x)/.009)**2-((y-.35)/.34)**4)*.19
    shine=np.clip(box1+box2+left+right,0,.55)*surf
    refr=refr*(1-shine[:,:,None])+255.*shine[:,:,None]

    # Opaque original browser pixels replace all material in the aperture.
    # A narrow glass lip belongs to the exterior, not to any source pixel.
    dilated=cv2.dilate(card,np.ones((9,9),np.uint8))
    lip=np.clip((dilated.astype(np.float32)-card.astype(np.float32))/255.,0,1)*.20
    a=surf[:,:,None]*.69
    plate=sky*(1.-a)+refr*a
    plate=plate*(1-lip[:,:,None])+np.float32([249,253,255])*lip[:,:,None]
    return np.clip(plate,0,255).astype(np.uint8)
