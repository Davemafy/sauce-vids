"""Opaque real display beneath a continuous polished, gently convex cover glass.

The glass has no sky texture, separate inset screen or thick decorative bezel.
Its reflection is neutral studio light, not an image of the environment.
The source is projected first; the cover's optical transmission/reflection is
applied last, in the same physical window coordinates.
"""
from functools import lru_cache
import cv2
import numpy as np
from cloud_window_sky_stage import sky_background, window_geometry as sky_geometry, _rounded_mask

PRESET = "cloud_window_clearface_v1"
CALIBRATION = None  # explicit, process-local opt-in for renderer studies

def window_geometry(source_size,output_size):
    x0,y0,x1,y1,_=sky_geometry(source_size,output_size)
    return x0,y0,x1,y1,max(6,round(output_size[1]*.038))

@lru_cache(maxsize=5)
def card_mask(source_size,output_size):
    x0,y0,x1,y1,r=window_geometry(source_size,output_size)
    return _rounded_mask(output_size,(x0,y0,x1,y1),r)


@lru_cache(maxsize=4)
def shadow_transmission(source_size, output_size):
    """Neutral multiplicative contact shadow, independent of backdrop pixels."""
    ow,oh=output_size
    mask=card_mask(source_size,output_size)
    low=cv2.resize(mask,(max(2,ow//4),max(2,oh//4)),interpolation=cv2.INTER_AREA)
    trans=np.ones((oh,ow),dtype=np.float32)
    for sigma,offset,strength in ((16.,5,.25),(4.,2,.19)):
        a=cv2.GaussianBlur(low,(0,0),sigma)
        shifted=np.zeros_like(a);shifted[offset:]=a[:-offset]
        trans*=1.-strength*cv2.resize(shifted,(ow,oh)).astype(np.float32)/255.
    return trans

@lru_cache(maxsize=4)
def physical_plate(source_size,output_size):
    """Original cloud treatment, retaining the physical contact shadow."""
    sky=sky_background(output_size).astype(np.float32)
    return np.rint(sky*shadow_transmission(source_size,output_size)[:,:,None]).astype(np.uint8)

@lru_cache(maxsize=4)
def optical_field(source_size, output_size):
    """Cover-glass transmission and neutral premultiplied reflected light.

    A rounded shoulder uses a smooth curvature profile, with a broad grazing
    reflection, a narrow elongated softbox catch and subdued lower-edge
    absorption. No texture sampling or luma-based transparency of the UI.
    """
    ow, oh = output_size
    x0,y0,x1,y1,_ = window_geometry(source_size,output_size)
    rows,cols = np.indices((oh,ow),dtype=np.float32)
    u=(cols-x0)/max(1,x1-x0); v=(rows-y0)/max(1,y1-y0)
    mask=card_mask(source_size,output_size)
    d=cv2.distanceTransform((mask>127).astype(np.uint8),cv2.DIST_L2,5)
    ny,nx=np.gradient(d)
    length=np.hypot(nx,ny)+1e-5
    nx/=length;ny/=length
    # A ~1.8%-height rolloff into the flat optical face, not a separate frame.
    shoulder=np.clip(1-d/max(2.,oh*.026),0,1)**1.6
    # Fresnel-like directionality: highlights bend round the actual corners.
    incidence=np.clip(.48+.32*ny+.18*nx,.12,.95)
    edge=shoulder*incidence*.48
    # Thin perimeter catch wraps the corners, rather than an independent ring.
    glint=np.exp(-((d-oh*.0025)/max(.7,oh*.0018))**2)*incidence*.46
    # A real studio softbox reflection across the front face: long, slightly
    # oblique and softly feathered. No clouds are reflected onto source pixels.
    softbox=np.exp(-((u-.27)/.25)**6-((v-.048-.014*u)/.014)**4)*.34
    broad=np.exp(-((u-.19)/.48)**2-((v-.10-.035*u)/.17)**2)*.075
    right=np.exp(-((u-.991)/.0065)**2-((v-.39)/.31)**4)*.36
    # Broad dark reflection at lower grazing angle; retain readable contrast.
    lower=shoulder*np.clip((v-.64)/.36,0,1)*.10
    alpha=np.clip(edge+glint+softbox+broad+right,0,np.where(d<oh*.005,.70,.42))
    transmission=(1-alpha)*(1-lower)
    # Cache in fixed window space. Masking occurs once in the final compositor.
    return np.dstack((transmission,alpha*250.)).astype(np.float32)

def coat_glass_face(projected,source_size,output_size,view=None):
    """Apply one optical cover after projection; the opaque display stays opaque."""
    if projected.shape!=(output_size[1],output_size[0],3):
        raise ValueError("Glass needs genuine projected display dimensions")
    if CALIBRATION is not None:
        return CALIBRATION.apply(projected,source_size,output_size,view)
    field=optical_field(source_size,output_size)
    if view is not None:
        field=cv2.warpAffine(field,view,output_size,flags=cv2.INTER_LINEAR,
                              borderMode=cv2.BORDER_CONSTANT,borderValue=(1.,0.))
    return np.rint(np.clip(projected.astype(np.float32)*field[:,:,0:1]+
                            field[:,:,1:2],0,255)).astype(np.uint8)
