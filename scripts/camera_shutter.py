"""Opt-in simulated camera-shutter sampling for source-true UI films.

Blur only during genuine EDL camera movement. All shutter samples warp the
*same decoded real product frame*; we never cross a cut, synthesize browser
states or redraw text. Stable holds preserve the original sharp render.
"""
from __future__ import annotations

import cv2
import numpy as np


def shutter_camera_warp(source, shot, frame_index, manifest, source_size,
                        output_size, camera_fn, threshold_px=0.8):
    """Return BGR frame from a 3-sample 0.64-frame shutter exposure."""
    h,w=output_size[1],output_size[0]
    frame_index=max(0.,min(float(frame_index),shot.length()-1))
    mid=camera_fn(manifest,shot,frame_index,source_size,output_size)
    def warp(matrix):
        return cv2.warpAffine(source,matrix,(w,h),
                              flags=cv2.INTER_CUBIC,
                              borderMode=cv2.BORDER_REPLICATE)
    before=camera_fn(manifest,shot,max(0.,frame_index-.32),source_size,output_size)
    after=camera_fn(manifest,shot,min(shot.length()-1,frame_index+.32),
                    source_size,output_size)
    sw,sh=source_size
    corners=np.float64([[0,sw,0,sw],[0,0,sh,sh],[1,1,1,1]])
    motion=np.linalg.norm((after-before)@corners,axis=0)
    current=warp(mid)
    if float(motion.max()) < threshold_px:
        return current
    a=warp(before)
    b=warp(after)
    # Weighed mid exposure, 0.2/0.6/0.2. The cursor is composited later.
    return ((a.astype(np.uint16)+3*current.astype(np.uint16)
             +b.astype(np.uint16)+2)//5).astype(np.uint8)
