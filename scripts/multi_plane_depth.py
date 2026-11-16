"""True two-plane Z-parallax using only live, source-verified browser pixels."""
from __future__ import annotations

import cv2
import numpy as np

from spatial_parallax import window_homography,projected_target_quad

DEPTH_PX=60.
MAX_BACKGROUND_BLUR=6.
RIM_COLOR=(249,236,216)

def _mask_bounds(shape,quad):
    mask=np.zeros(shape.shape[:2],dtype=np.uint8)
    cv2.fillConvexPoly(mask,np.rint(quad).astype(np.int32),255,lineType=cv2.LINE_AA)
    return mask

def _depth_quad(box,window,factor,dx,dy,tilt,focal,z):
    return projected_target_quad(box,window,factor,dx,dy,*tilt,
                                 perspective_px=focal,z=z)

def focus_background_plane(frame,stage_window,tilt,focal,
                           blur_px=6.,dim_opacity=.25):
    """Blur/dim the entire projected UI plane, not an imaginary sharp modal."""
    if frame.ndim!=3 or frame.shape[2]!=3:
        raise ValueError("Expected BGR film frame")
    if not 0<=blur_px<=MAX_BACKGROUND_BLUR or not 0<=dim_opacity<=.7:
        raise ValueError("Invalid background focus")
    x,y,w,h=stage_window
    H0=window_homography(x,y,w,h,*tilt,focal=focal,z=0.)
    quad=cv2.perspectiveTransform(
        np.float32([[[x,y],[x+w,y],[x+w,y+h],[x,y+h]]]),H0)[0]
    mask=_mask_bounds(frame,quad).astype(np.float32)[:,:,None]/255.
    softened=cv2.GaussianBlur(frame,(0,0),max(.01,blur_px)) if blur_px>0 else frame
    subdued=softened.astype(np.float32)*(1-dim_opacity)
    return np.uint8(np.clip(frame.astype(np.float32)*(1-mask)+subdued*mask,0,255))

def _rounded_region_mask(shape,bounds,radius):
    h,w=shape[:2]
    left,top,right,bottom=[int(round(v)) for v in bounds]
    left=max(0,left);top=max(0,top)
    right=min(w-1,right);bottom=min(h-1,bottom)
    mask=np.zeros((h,w),dtype=np.uint8)
    if right<=left or bottom<=top:return mask
    r=max(0,min(int(round(radius)),(right-left)//2,(bottom-top)//2))
    if not r:
        cv2.rectangle(mask,(left,top),(right,bottom),255,-1,cv2.LINE_AA)
    else:
        cv2.rectangle(mask,(left+r,top),(right-r,bottom),255,-1)
        cv2.rectangle(mask,(left,top+r),(right,bottom-r),255,-1)
        for cx,cy in ((left+r,top+r),(right-r,top+r),
                      (left+r,bottom-r),(right-r,bottom-r)):
            cv2.circle(mask,(cx,cy),r,255,-1,cv2.LINE_AA)
    return mask

def _shadow_from_mask(out,rounded_coverage,dx,dy,sigma,opacity):
    """Cast only the real rounded modal silhouette, never its bounding quad."""
    shift=np.float32([[1,0,dx],[0,1,dy]])
    moved=cv2.warpAffine(rounded_coverage,shift,
                         (out.shape[1],out.shape[0]),
                         flags=cv2.INTER_LINEAR,
                         borderMode=cv2.BORDER_CONSTANT)
    softened=cv2.GaussianBlur(moved,(0,0),sigma).astype(np.float32)
    coverage=(softened*(opacity/255.))[:,:,None]
    out[:]=np.uint8(np.clip(out.astype(np.float32)*(1-coverage),0,255))


def _rounded_outer_rim(out,coverage,rim_color=RIM_COLOR):
    """One gently feathered exterior pixel, with no rectangular corner joins.

    The coverage is the same projected, antialiased rounded modal mask used
    for the source photograph. Do not draw a rectangular cv2.polyline: that
    invents straight bright corners outside Brimble's actual border radius.
    """
    kernel=cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(3,3))
    raised=cv2.dilate(coverage,kernel)
    edge=cv2.subtract(raised,coverage)
    soft=cv2.GaussianBlur(edge,(0,0),.7)
    # A faint warm rim only outside source pixels; the user-facing text and
    # white dialog interior remain entirely untouched.
    strength=(soft.astype(np.float32)/255.)*.13*(
        1.-coverage.astype(np.float32)/255.)
    result=out.astype(np.float32)*(1.-strength[:,:,None])+(
        np.asarray(rim_color,dtype=np.float32)[None,None,:]*
        strength[:,:,None])
    out[:]=np.uint8(np.clip(np.rint(result),0,255))


def composite_elevated_modal(output,modal_source,box,stage_window,
                             factor,dx,dy,tilt,focal,radius_css=0.,
                             coverage_out=None,rim_color=RIM_COLOR):
    """Occlude real modal pixels over a separately captured modal-free plate.

    The overlay is ONLY enabled if the caller has separately verified that
    modal_source is an authentic Chromium frame and its background was hidden.
    """
    ox,oy,ww,wh=stage_window
    if modal_source.shape!=(wh,ww,3) or output.ndim!=3 or output.shape[2]!=3:
        raise ValueError("Mismatched foreground film frame")
    if not 0<=radius_css<=100 or factor<=0:
        raise ValueError("Invalid evidence-backed modal shape")
    front_quad=_depth_quad(box,stage_window,factor,dx,dy,tilt,focal,DEPTH_PX)
    if not np.isfinite(front_quad).all():
        raise ValueError("Invalid elevated projection")
    left=dx+float(box['x'])*factor
    top=dy+float(box['y'])*factor
    right=left+float(box['width'])*factor
    bottom=top+float(box['height'])*factor
    region=_rounded_region_mask(modal_source.shape,
                                (left,top,right,bottom),radius_css*factor)
    if np.count_nonzero(region)<20:
        raise ValueError("Modal outside the real browser viewport")
    # Stage coordinates -> local browser pixels, then z+60 homography.
    translate=np.float64([[1,0,ox],[0,1,oy],[0,0,1]])
    H60=window_homography(ox,oy,ww,wh,*tilt,focal=focal,z=DEPTH_PX)
    local_H=H60@translate
    canvas_size=(output.shape[1],output.shape[0])
    overlay=cv2.warpPerspective(modal_source,local_H,canvas_size,
                                flags=cv2.INTER_LINEAR)
    coverage=cv2.warpPerspective(region,local_H,canvas_size,
                                 flags=cv2.INTER_LINEAR)
    # Both shadow passes use the source-rounded mask. A rectangular quad
    # used here previously made right-angle dark outlines at curved corners.
    H0=window_homography(ox,oy,ww,wh,*tilt,focal=focal,z=0.)
    base_coverage=cv2.warpPerspective(region,H0@translate,canvas_size,
                                      flags=cv2.INTER_LINEAR)
    _shadow_from_mask(output,base_coverage,9,18,18,.22)
    _shadow_from_mask(output,coverage,4,9,12,.27)
    a=coverage.astype(np.float32)[:,:,None]/255.
    output[:]=np.uint8(np.clip(
        output.astype(np.float32)*(1-a)+overlay.astype(np.float32)*a,0,255))
    _rounded_outer_rim(output,coverage,rim_color=rim_color)
    # Allow experimental RGB dispersion to use this exact rounded mask,
    # instead of rebuilding a hard H60 bounding rectangle.
    if coverage_out is not None:
        if coverage_out.shape!=coverage.shape or coverage_out.dtype!=np.uint8:
            raise ValueError('Incorrect projected modal coverage buffer')
        coverage_out[:]=coverage
    return output
