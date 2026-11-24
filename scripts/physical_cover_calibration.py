"""Baked ray-traced optical transfer, with no source-coordinate distortion.

Two synthetic calibration renders (opaque black and opaque white behind the
same Cycles mesh) isolate reflection and transmission. Playback retains
the exact verified source projection, camera, pointer and clock. This is
not per-frame ray tracing: optical geometry and lights are fixed in the
window's local coordinate system.
"""
from pathlib import Path
from functools import lru_cache
import hashlib
import cv2
import numpy as np

def linear(x):
    return np.where(x<=.04045,x/12.92,((x+.055)/1.055)**2.4)

def bake(black,white,output):
    def read(p):
        a=cv2.imread(str(p),cv2.IMREAD_UNCHANGED)
        if a is None or a.dtype!=np.uint16 or a.shape!=(540,960,4):
            raise ValueError("Expected 960x540 16-bit Cycles calibration PNG")
        return linear(a[:,:,:3].astype(np.float32)/65535)
    b,w=read(black),read(white)
    # Suppress Monte Carlo sampling noise, not any real product pixels.
    r=cv2.GaussianBlur(b,(5,5),.8)
    t=cv2.GaussianBlur(w-b,(5,5),.8)
    # Bound clipped light estimates and preserve underlying readability.
    r=np.clip(r,0,.48);t=np.clip(t,.72,1.)
    np.savez_compressed(output,reflectance=r.astype(np.float16),transmission=t.astype(np.float16))

class CoverCalibration:
    def __init__(self,path,expected):
        path=Path(path)
        if not path.is_file() or path.stat().st_size>8_000_000:
            raise ValueError("Missing or oversized optical calibration")
        self.sha256=hashlib.sha256(path.read_bytes()).hexdigest()
        if self.sha256!=expected:raise ValueError("Optical calibration hash mismatch")
        with np.load(path,allow_pickle=False) as data:
            self.r=data["reflectance"].astype(np.float32)
            self.t=data["transmission"].astype(np.float32)
        for a,lo,hi in ((self.r,0,.481),(self.t,.719,1.001)):
            if a.shape!=(540,960,3) or not np.isfinite(a).all() or a.min()<lo or a.max()>hi:
                raise ValueError("Invalid optical transfer")
    @lru_cache(maxsize=2)
    def field(self,size):
        return (cv2.resize(self.r,size,interpolation=cv2.INTER_LINEAR),
                cv2.resize(self.t,size,interpolation=cv2.INTER_LINEAR))
    def apply(self,image,source_size,output_size,view=None):
        if abs(source_size[0]/source_size[1]-1.6)>.002 or output_size!=(1920,1080):
            raise ValueError("Calibration supports the measured 1.6:1 display on 1080p only")
        r,t=self.field(output_size)
        if view is not None:
            r=cv2.warpAffine(r,view,output_size,borderMode=cv2.BORDER_CONSTANT,borderValue=(0,0,0))
            t=cv2.warpAffine(t,view,output_size,borderMode=cv2.BORDER_CONSTANT,borderValue=(1,1,1))
        rgb=linear_lut[image]
        result=np.clip(rgb*t+r,0,1)
        return encode_lut[np.rint(result*65535).astype(np.uint16)]

linear_lut=linear(np.arange(256,dtype=np.float32)/255)
x=np.arange(65536,dtype=np.float32)/65535
encode_lut=np.rint(np.where(x<=.0031308,x*12.92,1.055*x**(1/2.4)-.055)*255).astype(np.uint8)
