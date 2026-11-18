"""Source-pixel-preserving spatial handoff primitives for Sauce.

Only operates on recorded source frames and explicitly supplied verified
geometry. It has no UI synthesis, text inference, browser calls or network.
The full source plane and a geometry-derived original crop share one
continuous output-frame clock. This module is opt-in laboratory code.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

import cv2
import numpy as np

VEC2 = tuple[float, float]
MASTER = (1920, 1080)


def eased(t: float) -> float:
    if not math.isfinite(t):
        raise ValueError("Nonfinite animation time")
    u = min(1.0, max(0.0, t))
    return u * u * u * (u * (u * 6.0 - 15.0) + 10.0)


@dataclass(frozen=True)
class VerifiedPatch:
    """Recorded source rect plus post-action proof; never a synthesized state."""

    source_width: int
    source_height: int
    x: int
    y: int
    width: int
    height: int

    def __post_init__(self) -> None:
        if (self.source_width < 320 or self.source_height < 240
            or self.width < 40 or self.height < 24
            or self.x < 0 or self.y < 0
            or self.x + self.width > self.source_width
            or self.y + self.height > self.source_height):
            raise ValueError("Patch outside genuine source pixels")

    def extract(self, frame: np.ndarray) -> np.ndarray:
        if (frame.shape != (self.source_height, self.source_width, 3)
            or frame.dtype != np.uint8):
            raise ValueError("Source frame dimensions or format are unverified")
        return frame[self.y:self.y+self.height,
                     self.x:self.x+self.width].copy()

    def corners(self) -> np.ndarray:
        x,y,w,h = self.x,self.y,self.width,self.height
        return np.float32([[x,y],[x+w,y],[x+w,y+h],[x,y+h]])


def homography_quad(points: np.ndarray) -> np.ndarray:
    arr=np.asarray(points,dtype=np.float32)
    if arr.shape!=(4,2) or not np.isfinite(arr).all():
        raise ValueError("Invalid plane quad")
    area=cv2.contourArea(arr)
    if area < 50:
        raise ValueError("Degenerate plane quad")
    return arr


def interpolate_quad(start: np.ndarray, end: np.ndarray, t: float) -> np.ndarray:
    a,b=homography_quad(start),homography_quad(end)
    p=eased(t)
    return np.float32(a+(b-a)*p)


def crop_quad_from_homography(patch: VerifiedPatch, full_quad: np.ndarray) -> np.ndarray:
    source=np.float32([[0,0],[patch.source_width,0],
                       [patch.source_width,patch.source_height],[0,patch.source_height]])
    h=cv2.getPerspectiveTransform(source,homography_quad(full_quad))
    return cv2.perspectiveTransform(patch.corners().reshape(1,4,2),h)[0]


def projected(frame: np.ndarray, quad: np.ndarray,
              canvas: tuple[int,int]=MASTER,
              interpolation: int=cv2.INTER_CUBIC) -> tuple[np.ndarray,np.ndarray]:
    """Return warped authentic RGB/BGR pixels with an exact planar alpha mask."""
    if frame.dtype != np.uint8 or frame.ndim != 3 or frame.shape[2] != 3:
        raise ValueError("Expected recorded uint8 BGR pixels")
    dest=homography_quad(quad)
    w,h=canvas
    fh,fw=frame.shape[:2]
    src=np.float32([[0,0],[fw,0],[fw,fh],[0,fh]])
    matrix=cv2.getPerspectiveTransform(src,dest)
    transformed=cv2.warpPerspective(frame,matrix,(w,h),flags=interpolation,
                                     borderMode=cv2.BORDER_CONSTANT)
    # Same projected geometry as the source, never an independent guessed shape.
    solid=np.full((fh,fw),255,np.uint8)
    alpha=cv2.warpPerspective(solid,matrix,(w,h),
                  flags=cv2.INTER_LINEAR,borderMode=cv2.BORDER_CONSTANT)
    return transformed,alpha


def overlay(background: np.ndarray, source: np.ndarray,
            mask: np.ndarray) -> np.ndarray:
    if (background.shape != source.shape
        or mask.shape != background.shape[:2]
        or background.dtype != np.uint8 or source.dtype != np.uint8
        or mask.dtype != np.uint8):
        raise ValueError("Invalid compositing planes")
    opacity=(mask.astype(np.float32)/255)[:,:,None]
    return np.uint8(np.rint(background.astype(np.float32)*(1-opacity)+
                            source.astype(np.float32)*opacity))


def source_difference(a: np.ndarray,b: np.ndarray,
                      patch: VerifiedPatch) -> float:
    x=patch.extract(a).astype(np.int16)
    y=patch.extract(b).astype(np.int16)
    return float(np.abs(x-y).mean())


def locate_sustained_change(frames: list[np.ndarray], start_index: int,
                            patch: VerifiedPatch,
                            threshold: float=2.0,
                            persistence: int=4) -> int:
    """Detect the decoded visual change, independent of drifting event time."""
    if (len(frames)<persistence+2 or persistence<2 or
        not 0.1<=threshold<=100 or start_index<0):
        raise ValueError("Insufficient proof frames")
    reference=frames[0]
    for i in range(1,len(frames)-persistence):
        if (source_difference(frames[i-1],frames[i],patch)>=threshold
            and source_difference(reference,frames[i],patch)>=threshold
            and all(source_difference(reference,frames[j],patch)>=threshold
                    for j in range(i,i+persistence))):
            return start_index+i
    raise ValueError("No source-verified sustained change")


def audio_clock(frame_index: int, fps: int=60, sample_rate: int=48000) -> int:
    if frame_index < 0 or fps != 60 or sample_rate != 48000:
        raise ValueError("Sauce video/audio clock requires nonnegative 60fps frame")
    return frame_index*800
