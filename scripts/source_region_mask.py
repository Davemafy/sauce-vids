"""Shared source coverage for projected UI regions."""
import cv2
import numpy as np


def rounded_region_mask(shape,bounds,radius):
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

def composite_covered_pixels(output, foreground, coverage):
    """Composite source pixels using the same coverage as shadows and occlusion."""
    alpha = coverage.astype(np.float32)[:, :, None] / 255.
    output[:] = np.uint8(np.clip(
        output.astype(np.float32) * (1 - alpha) + foreground.astype(np.float32) * alpha,
        0, 255))


def dim_outside_region(frame, bounds, strength):
    """Keep a real result and its immediate context sharp and unchanged."""
    left, top, right, bottom = bounds
    feather = 48
    matte = rounded_region_mask(
        frame.shape, (left - feather, top - feather, right + feather, bottom + feather), 12)
    if not np.any(matte):
        return frame
    coverage = cv2.GaussianBlur(matte, (0, 0), feather / 3)
    # Gaussian tails have finite kernel support. Explicitly freeze the result
    # so the source glyphs remain identical even at the rounded corners.
    core = rounded_region_mask(frame.shape, bounds, 0)
    coverage[core == 255] = 255
    dimmed = cv2.convertScaleAbs(frame, alpha=1 - strength)
    composite_covered_pixels(dimmed, frame, coverage)
    return dimmed
