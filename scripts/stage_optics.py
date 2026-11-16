"""Opt-in deterministic optical stage pass, isolated from source UI pixels.

H0 and H60 polygons are protected while the surrounding stage and floor
receive shallow fluted refraction, channel-shifted shadow glints and grain.
No external textures, shaders, network, clocks or random global state.
"""
from __future__ import annotations
import cv2
import numpy as np

def _polygon(shape:tuple[int,int],quad:np.ndarray)->np.ndarray:
    mask=np.zeros(shape,np.uint8)
    cv2.fillConvexPoly(mask,np.rint(quad).astype(np.int32),255,lineType=cv2.LINE_AA)
    return mask


def apply_stage_optics(frame:np.ndarray,window_quad:np.ndarray,
                       frame_index:int,seed:int=20261116,
                       modal_quad:np.ndarray|None=None,
                       modal_coverage:np.ndarray|None=None,
                       fps:int=60,refraction_px:float=1.25,
                       dispersion_px:float=1.25,
                       spectral_weights:tuple[float,float]=(2.,2.))->np.ndarray:
    """Refract only outside H0; modal rim may glow outside H60 by <=1.5px.

    The protected window mask (4px guard) guarantees unchanged browser
    text/pixels even under a tilted H0 camera or elevated H60 modal.
    A frame index, not wall time, determines every refraction/grain sample.
    """
    if frame.ndim!=3 or frame.shape[2]!=3 or frame.dtype!=np.uint8:
        raise ValueError("Expected uint8 BGR frame")
    if fps<=0 or frame_index<0 or not isinstance(seed,int) or not 0<=seed<2**31:
        raise ValueError("Invalid deterministic stage time/seed")
    if not 0<=refraction_px<=1.5 or not 0<=dispersion_px<=1.5:
        raise ValueError("Refraction and spectral shift must be <=1.5px")
    if len(spectral_weights)!=2 or any(
            not isinstance(v,(float,int)) or not .5<=v<=2.
            for v in spectral_weights):
        raise ValueError("Spectral weights outside dim studio range")
    h,w=frame.shape[:2]
    window=_polygon((h,w),window_quad)
    protected=cv2.dilate(window,np.ones((7,7),np.uint8),iterations=1)
    modal=None
    if modal_coverage is not None:
        if modal_coverage.shape!=(h,w) or modal_coverage.dtype!=np.uint8:
            raise ValueError('Modal coverage must match frame dimensions')
        modal=modal_coverage
    elif modal_quad is not None:
        # Backward compatibility for callers without an H60 image mask.
        modal=_polygon((h,w),modal_quad)
    if modal is not None:
        protected=cv2.bitwise_or(protected,
                      cv2.dilate(modal,np.ones((7,7),np.uint8),iterations=1))
    outside=protected==0
    result=frame.copy()

    # Refraction is a real pixel sampling displacement across the *stage*
    # (including reflected floor pixels). 4.6s period is gentle enough not
    # to produce visible wobbles during a ~3.28s narrative.
    x=np.arange(w,dtype=np.float32)
    y=np.arange(h,dtype=np.float32)
    phi=2*np.pi*(x/45. + frame_index/(fps*4.6))
    offset=np.float32(refraction_px)*(np.sin(phi)*.76+
                                       np.sin(phi*2+.6)*.24)
    map_x=np.broadcast_to(x[None,:]+offset[None,:],(h,w)).copy()
    map_y=np.broadcast_to(y[:,None],(h,w)).copy()
    refracted=cv2.remap(frame,map_x,map_y,cv2.INTER_LINEAR,
                         borderMode=cv2.BORDER_REFLECT101)
    result[outside]=refracted[outside]

    # Seeded analog film grain: center-weighted (no exposure drift),
    # 2/255 max amplitude and no UI pixels touched. Frame-locked noise
    # deliberately differs by frame, but repeated renders are bit exact.
    rng=np.random.default_rng(seed+frame_index)
    noise=rng.integers(-2,3,size=(h,w),dtype=np.int8).astype(np.int16)
    grain=np.clip(result.astype(np.int16)+noise[:,:,None],0,255).astype(np.uint8)
    result[outside]=grain[outside]

    if dispersion_px:
        # The spectral glint lives on the outer 1.5px of the H0 shadow
        # contact region; fully guard the source content rectangle.
        edge=cv2.dilate(window,np.ones((9,9),np.uint8))
        rim=cv2.subtract(edge,window)
        shifted_r=cv2.warpAffine(rim,np.float32([[1,0,dispersion_px],[0,1,0]]),
                                (w,h),flags=cv2.INTER_LINEAR,
                                borderMode=cv2.BORDER_CONSTANT)
        shifted_b=cv2.warpAffine(rim,np.float32([[1,0,-dispersion_px],[0,1,0]]),
                                (w,h),flags=cv2.INTER_LINEAR,
                                borderMode=cv2.BORDER_CONSTANT)
        fringe=(cv2.subtract(shifted_r,shifted_b).astype(np.float32)/255.)
        # Color is restricted to pixels strictly outside the H0 polygon.
        shadow_outside=window==0
        r=result[:,:,2].astype(np.float32)
        b=result[:,:,0].astype(np.float32)
        r[shadow_outside]=np.clip(r[shadow_outside]+
                                  spectral_weights[0]*fringe[shadow_outside],0,255)
        b[shadow_outside]=np.clip(b[shadow_outside]-
                                  spectral_weights[1]*fringe[shadow_outside],0,255)
        result[:,:,2]=np.uint8(np.rint(r))
        result[:,:,0]=np.uint8(np.rint(b))

        if modal is not None:
            # Spectral fringe is derived from the projected rounded H60
            # mask, not the polygon bounding box with squared-off corners.
            m=modal
            r=cv2.warpAffine(m,np.float32([[1,0,dispersion_px],[0,1,0]]),
                             (w,h),flags=cv2.INTER_LINEAR)
            b=cv2.warpAffine(m,np.float32([[1,0,-dispersion_px],[0,1,0]]),
                             (w,h),flags=cv2.INTER_LINEAR)
            halo=(r.astype(np.float32)-b.astype(np.float32))/255.
            ring=(m==0)&(cv2.dilate(m,np.ones((5,5),np.uint8))>0)
            # 1–2 level color split makes the outer rim luminous without
            # drawing a new rim inside the protected H60 content.
            red=result[:,:,2].astype(np.float32)
            blue=result[:,:,0].astype(np.float32)
            red[ring]=np.clip(red[ring]+(.75*spectral_weights[0])*halo[ring],0,255)
            blue[ring]=np.clip(blue[ring]-(.75*spectral_weights[1])*halo[ring],0,255)
            result[:,:,2]=np.uint8(np.rint(red))
            result[:,:,0]=np.uint8(np.rint(blue))
    return result
