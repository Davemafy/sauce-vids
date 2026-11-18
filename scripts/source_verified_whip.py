"""Opt-in one-frame-at-a-time cut whip between *separate* real UI states.

No inter-state transparency or synthesized UI. Each side is always entirely
one actual decoded source frame. For 4-5 frames a measured camera accelerates
out and decelerates into the next source-backed state. A brief one-axis
motion exposure obscures the unavoidable source remount discontinuity.
"""
from __future__ import annotations

import cv2
import numpy as np


CUT_WHIP_FRAMES = 5
MAX_SHIFT_PX_1080 = 60.0
MAX_BLUR_WIDTH_1080 = 27


def whip_phase(local_frame: float, duration: int, *, incoming: bool,
               outgoing: bool, frames: int = CUT_WHIP_FRAMES) -> float:
    if type(frames) is not int or not 3 <= frames <= 7:
        raise ValueError("Cut whip supports only 3–7 actual frames per side")
    if not 0 <= local_frame < duration or duration < frames * 2:
        return 0.0
    if incoming and local_frame < frames:
        u=(frames-1-local_frame)/(frames-1)
        return -max(0.0,u) ** 2
    if outgoing and local_frame >= duration-frames:
        u=(local_frame-(duration-frames))/(frames-1)
        return min(1.0,u) ** 2
    return 0.0


def camera_whip_dx(phase:float, output_width:int)->float:
    if not isinstance(phase,(float,int)) or not -1 <= phase <= 1:
        raise ValueError("Invalid bounded cut motion")
    return float(phase)*MAX_SHIFT_PX_1080*(output_width/1920.0)


def film_shutter_whip(frame:np.ndarray, phase:float)->np.ndarray:
    if not isinstance(phase,(float,int)) or not -1<=phase<=1:
        raise ValueError("Invalid bounded cut motion")
    if frame.dtype != np.uint8 or frame.ndim != 3 or frame.shape[2] != 3:
        raise ValueError("Expected final BGR film source layer")
    k=round((MAX_BLUR_WIDTH_1080 * frame.shape[1]/1920.0)
            * abs(phase)**1.35)
    k=max(1,k|1)  # odd width, no disturbance at zero phase
    if k<3:return frame
    return cv2.GaussianBlur(frame,(k,1),sigmaX=0,
                            borderType=cv2.BORDER_REPLICATE)
