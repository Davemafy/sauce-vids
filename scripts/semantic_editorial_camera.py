"""Source-true single-plane editorial camera for a verified UI result.

The camera always transforms ONE genuine captured frame at a time, with no
synthetic UI, duplicated foreground, rebuilt panel, or inferred text.
Developed to provide a coherent fall-back when a multi-plane "lift" fails
visual review or no verified modal-free background can be captured.
"""
from __future__ import annotations
import math
from dataclasses import dataclass
import numpy as np
import cv2


def ease5(t: float) -> float:
    if not math.isfinite(t):
        raise ValueError("Nonfinite camera time")
    s=max(0.0,min(1.0,float(t)))
    return s*s*s*(s*(s*6-15)+10)


@dataclass(frozen=True)
class EditorialFocus:
    source_width: int
    source_height: int
    x: float
    y: float
    width: float
    height: float
    start_frame: int
    result_frame: int
    end_scale: float = 2.45
    output_width: int = 1920
    output_height: int = 1080

    def __post_init__(self):
        vals=(self.x,self.y,self.width,self.height,self.end_scale)
        if (not all(math.isfinite(float(v)) for v in vals)
            or self.source_width<320 or self.source_height<240
            or self.width<=10 or self.height<=10
            or self.x<0 or self.y<0
            or self.x+self.width>self.source_width
            or self.y+self.height>self.source_height
            or self.start_frame<self.result_frame
            or not (1.05<=self.end_scale<=4)
            or self.output_width<640 or self.output_height<360):
            raise ValueError("Invalid or prematurely started editorial focus")
        # Perspective-free final crop must contain the complete verified
        # result box with a context cushion. Reject clipped results.
        window_w=self.source_width/self.end_scale
        window_h=self.source_height/self.end_scale
        safe_w=window_w*.93
        safe_h=window_h*.87
        if self.width>safe_w or self.height>safe_h:
            raise ValueError("Result would clip in end-frame reading shot")

    @property
    def source_center(self):
        return (self.source_width/2.0,self.source_height/2.0)

    @property
    def result_center(self):
        return (self.x+self.width/2.0,self.y+self.height/2.0)

    def params(self,progress: float):
        p=ease5(progress)
        # Move from the exact full-frame center to an observed result.
        srcx,srcy=self.source_center
        dstx,dsty=self.result_center
        zoom=1+(self.end_scale-1)*p
        # Camera pan and push use identical output-time p: no focus seam.
        focus_x=srcx+(dstx-srcx)*p
        focus_y=srcy+(dsty-srcy)*p
        return zoom,focus_x,focus_y

    def matrix(self,progress:float):
        scale,cx,cy=self.params(progress)
        sx=self.output_width/self.source_width*scale
        sy=self.output_height/self.source_height*scale
        # No skew, anamorphic scaling, or perspective-corner holes. Source
        # aspect and output must agree to retain unmodified source geometry.
        if abs(sx-sy)>1e-5:
            raise ValueError("Incompatible source and film aspect ratio")
        return np.float64([[sx,0.,self.output_width/2-cx*sx],
                           [0.,sy,self.output_height/2-cy*sy]])

    def render(self,frame:np.ndarray,progress:float):
        if (frame.dtype != np.uint8
            or frame.shape != (self.source_height,self.source_width,3)):
            raise ValueError("Expected actual uint8 BGR source frame")
        return cv2.warpAffine(frame,self.matrix(progress),
             (self.output_width,self.output_height),flags=cv2.INTER_LANCZOS4,
             borderMode=cv2.BORDER_REPLICATE)

    def source_bbox_at_output(self,progress:float):
        matrix=self.matrix(progress)
        pts=np.float64([[self.x,self.y,1],
                        [self.x+self.width,self.y+self.height,1]])
        result=pts@matrix.T
        return (float(result[0,0]),float(result[0,1]),
                float(result[1,0]),float(result[1,1]))
