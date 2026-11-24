"""Sky-filled acrylic object stage: separate material from real browser capture.

The uploaded Y2K cloud-glass image is a *material/shape reference* only.
No source artwork, fake window, cursor or UI is reproduced. This opt-in
preset retains all original Chromium pixels on a separate foreground plane.
"""
from __future__ import annotations

from functools import lru_cache
import cv2
import numpy as np


PRESET = "cloud_glass_v1"


def window_geometry(source_size, output_size):
    sw, sh = source_size
    ow, oh = output_size
    if sw <= 0 or sh <= 0 or ow <= 0 or oh <= 0:
        raise ValueError("Invalid original source or output dimensions")
    aspect = sw / sh
    # Real browser gets an inset display cavity, not 97% of the glass.
    # This deliberate composition leaves enough exposed sky material.
    width = min(ow * .68, oh * .74 * aspect)
    height = width / aspect
    x0 = round(ow * .11)
    y0 = round(oh * .13)
    x1 = round(x0 + width)
    y1 = round(y0 + height)
    if x1 > ow * .795 or y1 > oh * .90:
        raise ValueError("Browser would intrude into the glass-object cutout")
    radius = max(5, round(oh * .022))
    return x0, y0, x1, y1, radius


def _cubic(a, b, c, d, steps=28):
    out=[]
    for t in np.linspace(0.,1.,steps):
        p=(1-t)**3*np.array(a)+3*(1-t)**2*t*np.array(b)+3*(1-t)*t*t*np.array(c)+t**3*np.array(d)
        out.append(p)
    return out


@lru_cache(maxsize=5)
def object_mask(output_size):
    ow,oh=output_size
    points=[]
    def curve(a,b,c,d):
        points.extend(_cubic(a,b,c,d))
    p=lambda x,y:(x*ow,y*oh)
    # Reference silhouette: pillowy corners, large sky body and lower-right
    # recessed curl into a short broad tail. No regular rectangle+neon rim.
    curve(p(.075,.028),p(.35,.026),p(.72,.028),p(.935,.03))
    curve(p(.935,.03),p(.985,.03),p(.993,.083),p(.992,.15))
    curve(p(.992,.15),p(.995,.31),p(.992,.50),p(.986,.566))
    curve(p(.986,.566),p(.972,.685),p(.925,.706),p(.863,.714))
    curve(p(.863,.714),p(.815,.721),p(.795,.752),p(.794,.803))
    curve(p(.794,.803),p(.787,.86),p(.803,.94),p(.773,.965))
    curve(p(.773,.965),p(.752,.99),p(.72,.989),p(.66,.984))
    curve(p(.66,.984),p(.49,.982),p(.25,.986),p(.08,.985))
    curve(p(.08,.985),p(.016,.984),p(.012,.938),p(.014,.865))
    curve(p(.014,.865),p(.013,.68),p(.014,.36),p(.016,.135))
    curve(p(.016,.135),p(.018,.069),p(.034,.031),p(.075,.028))
    mask=np.zeros((oh,ow),np.uint8)
    cv2.fillPoly(mask,[np.round(points).astype(np.int32)],255,cv2.LINE_AA)
    # Subpixel antialias without flattening the silhouette.
    return cv2.GaussianBlur(mask,(0,0),.75)


@lru_cache(maxsize=5)
def card_mask(source_size,output_size):
    ow,oh=output_size
    x0,y0,x1,y1,r=window_geometry(source_size,output_size)
    m=np.zeros((oh,ow),np.uint8)
    cv2.rectangle(m,(x0+r,y0),(x1-r,y1),255,-1)
    cv2.rectangle(m,(x0,y0+r),(x1,y1-r),255,-1)
    for cx,cy in ((x0+r,y0+r),(x1-r,y0+r),(x0+r,y1-r),(x1-r,y1-r)):
        cv2.circle(m,(cx,cy),r,255,-1,cv2.LINE_AA)
    return m


@lru_cache(maxsize=5)
def stage_plate(source_size,output_size):
    from cloud_shadow_stage import backdrop
    ow,oh=output_size
    white=np.full((oh,ow,3),[250,251,253],dtype=np.float32)
    object_m=object_mask(output_size)
    inner=card_mask(source_size,output_size)
    # A real large volumetric object casts a soft broad-area shadow on the
    # pale gallery background, not a cobalt halftone wallpaper.
    for sigma,offset,opacity in ((25.,22,.20),(9.,8,.17)):
        reduced=cv2.resize(object_m,(max(2,ow//4),max(2,oh//4)),interpolation=cv2.INTER_AREA)
        blurred=cv2.GaussianBlur(reduced,(0,0),sigma)
        shifted=np.zeros_like(blurred)
        dy=max(0,round(offset/4))
        shifted[dy:,:]=blurred[:-dy,:] if dy else blurred
        shadow=cv2.resize(shifted,(ow,oh),interpolation=cv2.INTER_LINEAR).astype(np.float32)/255.
        white*=1-opacity*shadow[:,:,None]

    # The only cloud imagery is the user's existing legitimate artwork.
    # Low-pass the halftone ink INSIDE the acrylic to approximate softly
    # embedded clouds while the outside remains a clean white photo studio.
    sky=cv2.GaussianBlur(backdrop(ow,oh),(0,0),2.6).astype(np.float32)
    ys,xs=np.indices((oh,ow),dtype=np.float32)
    y=ys/max(1,oh-1);x=xs/max(1,ow-1)
    # Volume-specific colour: pale cyan upper glass, cobalt blue at base.
    blue=np.zeros_like(sky)
    blue[:,:,0]=235.-32.*y
    blue[:,:,1]=195.-91.*y
    blue[:,:,2]=141.-106.*y
    pigment=(.14+.18*y)[:,:,None]
    glass=sky*(1-pigment)+blue*pigment
    upper=np.exp(-((x-.14)/.62)**2-((y-.09)/.38)**2)
    milk=(.055+.20*upper)[:,:,None]
    glass=glass*(1-milk)+np.array([253.,254.,255.],np.float32)*milk

    # The thick 3D meniscus bends clouds only within the object (never UI).
    dist=cv2.distanceTransform((object_m>220).astype(np.uint8),cv2.DIST_L2,5)
    grad_y,grad_x=np.gradient(dist)
    norm=np.sqrt(grad_x*grad_x+grad_y*grad_y)+1e-4
    refr=np.exp(-dist/max(3.,oh*.030))*(object_m.astype(np.float32)/255.)
    dx=(grad_x/norm)*refr*(ow*.006)
    dy=(grad_y/norm)*refr*(oh*.010)
    glass=cv2.remap(glass,xs+dx,ys+dy,cv2.INTER_LINEAR,borderMode=cv2.BORDER_REFLECT_101)

    # Wide refractive light at every curved boundary, with upper-left specular
    # concentration. A broad luminous meniscus is not a 2px outline.
    rim=np.clip((oh*.052-dist)/max(1.,oh*.052),0.,1.)
    rim*=object_m.astype(np.float32)/255.
    bias=np.clip(.88-.48*y+.18*(1-x),.34,1.05)
    rim_alpha=np.clip(rim*bias*.62,0.,.70)
    glass=glass*(1-rim_alpha[:,:,None])+np.array([253.,254.,255.],np.float32)*rim_alpha[:,:,None]

    # Concentric, curved translucent edge bands give the surface *thickness*.
    # The bands move with the original non-rectangular outline and still
    # never cross onto the genuine product image.
    outside=object_m.astype(np.float32)/255.
    inner_ridge=np.exp(-((dist-oh*.013)/max(1.,oh*.009))**2)*outside
    glint=np.exp(-((dist-oh*.003)/max(1.,oh*.004))**2)*outside
    directional=(.45+.5*np.clip(1.-y/.75,0.,1.)+.11*np.clip(1.-x/.25,0.,1.))
    glass=glass*(1-(inner_ridge*.16)[:,:,None])+np.float32([249,253,255])*(inner_ridge*.16)[:,:,None]
    shine_edge=np.clip(glint*.37*directional,0.,.46)
    glass=glass*(1-shine_edge[:,:,None])+255.*shine_edge[:,:,None]

    # Atmospheric top-left reflection and two elongated curved softboxes.
    # This broad low-frequency source is what a neon-outline approximation
    # misses; it is optical white reflection, not an overlaid UI element.
    softbox=np.exp(-((x-.22)/.40)**4-((y-.071)/.066)**2)*.32
    left_refl=np.exp(-((x-.039)/.022)**2-((y-.30)/.37)**4)*.26
    right_refl=np.exp(-((x-.973)/.022)**2-((y-.30)/.30)**4)*.21
    large_shine=np.clip(softbox+left_refl+right_refl,0.,.46)
    glass=glass*(1-large_shine[:,:,None])+np.float32([253,254,255])*large_shine[:,:,None]

    # Long softbox reflection across the upper blue glass, 3D streak shaped
    # like the material reference; kept outside the real browser aperture.
    x0,y0,x1,y1,_=window_geometry(source_size,output_size)
    highlight=np.zeros((oh,ow),np.float32)
    cv2.line(highlight,(round(ow*.10),round(oh*.071)),
             (round(ow*.55),round(oh*.077)),1.,max(3,round(oh*.022)),cv2.LINE_AA)
    tight=cv2.GaussianBlur(highlight,(0,0),oh*.009)
    wide=cv2.GaussianBlur(highlight,(0,0),oh*.027)
    highlight=np.clip(tight*.88+wide*.50,0,.74)
    glass=glass*(1-highlight[:,:,None])+255.*highlight[:,:,None]
    # Lower light bounce across the curve, weaker than the reference top catch.
    bounce=np.exp(-((x-.30)/.44)**2-((y-.96)/.09)**2)*.11
    glass=glass*(1-bounce[:,:,None])+255.*bounce[:,:,None]

    alpha=(object_m.astype(np.float32)/255.)[:,:,None]
    white=white*(1-alpha)+glass*alpha
    # A softly bevelled inset aperture belongs to the material only.
    lip=cv2.dilate(inner,np.ones((7,7),np.uint8))
    edge=np.maximum(0,lip.astype(np.float32)-inner.astype(np.float32))/255.
    lip_a=edge*.28
    white=white*(1-lip_a[:,:,None])+np.float32([243.,250.,255.])*lip_a[:,:,None]
    return np.clip(white,0,255).astype(np.uint8)
