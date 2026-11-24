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
    sw, sh = source_size
    ow, oh = output_size
    if min(sw, sh, ow, oh) <= 0:
        raise ValueError("Invalid screen or stage geometry")
    aspect = sw / sh
    # Floating body has spacious material exposure; original source is not
    # stretched or cropped to imitate a rounded screenshot.
    width = min(ow * .64, oh * .69 * aspect)
    height = width / aspect
    x0 = round(ow * .145)
    y0 = round(oh * .125)
    x1 = round(x0 + width)
    y1 = round(y0 + height)
    if x1 > ow * .79 or y1 > oh * .83:
        raise ValueError("Source aperture collides with the sculpted tail")
    return x0, y0, x1, y1, max(6, round(oh * .025))


def _curve(points, a, b, c, d):
    pa, pb, pc, pd = (np.array(v, dtype=np.float64) for v in (a, b, c, d))
    for t in np.linspace(0, 1, 25, endpoint=False):
        points.append(np.rint((1-t)**3*pa+3*(1-t)**2*t*pb+
                               3*(1-t)*t*t*pc+t**3*pd).astype(np.int32))


@lru_cache(maxsize=5)
def object_mask(output_size):
    ow, oh = output_size
    p=lambda x,y:(round(x*ow), round(y*oh))
    points=[]
    # Smooth pneumatic silhouette. Lower-right interior recess echoes the
    # last image, but never clips the independently captured browser.
    curves=[
      ((.16,.060),(.40,.048),(.75,.073),(.865,.09)),
      ((.865,.09),(.928,.108),(.931,.145),(.931,.215)),
      ((.931,.215),(.934,.40),(.932,.60),(.925,.675)),
      ((.925,.675),(.919,.748),(.877,.756),(.843,.760)),
      ((.843,.760),(.794,.76),(.787,.803),(.773,.822)),
      ((.773,.822),(.748,.867),(.735,.914),(.684,.918)),
      ((.684,.918),(.48,.92),(.30,.922),(.163,.916)),
      ((.163,.916),(.102,.915),(.092,.875),(.092,.812)),
      ((.092,.812),(.086,.60),(.088,.34),(.090,.177)),
      ((.090,.177),(.09,.104),(.109,.071),(.16,.060)),
    ]
    for a,b,c,d in curves:
        _curve(points,p(*a),p(*b),p(*c),p(*d))
    mask=np.zeros((oh,ow),np.uint8)
    cv2.fillPoly(mask,[np.asarray(points,np.int32)],255,cv2.LINE_AA)
    return cv2.GaussianBlur(mask,(0,0),.60)


@lru_cache(maxsize=5)
def card_mask(source_size, output_size):
    # Reuse the proven exact source mask algorithm but use the new, smaller
    # viewport geometry. Never apply a soft focus or colour wash to source.
    ow,oh=output_size
    x0,y0,x1,y1,r=window_geometry(source_size,output_size)
    r=min(r,(x1-x0)//4,(y1-y0)//4)
    mask=np.zeros((oh,ow),np.uint8)
    cv2.rectangle(mask,(x0+r,y0),(x1-r,y1),255,-1)
    cv2.rectangle(mask,(x0,y0+r),(x1,y1-r),255,-1)
    for x,y in ((x0+r,y0+r),(x1-r,y0+r),(x0+r,y1-r),(x1-r,y1-r)):
        cv2.circle(mask,(x,y),r,255,-1,cv2.LINE_AA)
    return mask


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
    shell=object_mask(output_size)
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
    # Top softbox glints / wing reflections from generated visual reference.
    box1=np.exp(-((x-.29)/.28)**4-((y-.096)/.033)**2)*.48
    box2=np.exp(-((x-.63)/.125)**4-((y-.106)/.023)**2)*.34
    left=np.exp(-((x-.115)/.024)**2-((y-.36)/.40)**4)*.21
    right=np.exp(-((x-.909)/.018)**2-((y-.32)/.30)**4)*.25
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
