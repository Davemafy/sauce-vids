"""Genuine WebGL2 post-processing pass over final 1080p composited frames.

Uses Chromium SwiftShader on GPU-less VPS, never substitutes CPU pixel
filters. Shader is always the final pass after the source site, 3D tilt,
cursor, and overlays are composed. Grains are deterministic by frame index.
"""
from __future__ import annotations
import base64
from pathlib import Path
import cv2
import numpy as np

SHADER_HTML=(Path(__file__).resolve().parents[1]/"assets/shaders/optics-webgl2.html")

class WebGLOptics:
    def __init__(self,context):
        self.page=context.new_page()
        self.page.set_content(SHADER_HTML.read_text(),wait_until="load")
        self.renderer=self.page.evaluate("()=>window.opticsRenderer||null")
        error=self.page.evaluate("()=>window.shaderError||null")
        if self.renderer!="WebGL2" or error:
            raise RuntimeError("Real WebGL2 optics initialization failed: "+str(error))
        self.frames=0

    def apply(self,frame_bgr:np.ndarray,index:int)->np.ndarray:
        if frame_bgr.shape!=(1080,1920,3):
            raise ValueError("Shader requires a full-resolution 1080p frame")
        ok,encoded=cv2.imencode(".png",frame_bgr,[cv2.IMWRITE_PNG_COMPRESSION,1])
        if not ok:raise RuntimeError("WebGL source PNG encode failed")
        b64=base64.b64encode(encoded.tobytes()).decode("ascii")
        result=self.page.evaluate("async (d)=>window.sauceOptics(d.png,d.index)",
                                  {"png":b64,"index":int(index)})
        data=np.frombuffer(base64.b64decode(result),dtype=np.uint8)
        output=cv2.imdecode(data,cv2.IMREAD_COLOR)
        if output is None or output.shape!=frame_bgr.shape:
            raise RuntimeError("WebGL readback not 1080p")
        self.frames+=1
        return output

    def close(self):
        self.page.close()
