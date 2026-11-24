"""Exercise the actual WebGL texture lookup, not just duplicated CPU math."""
from pathlib import Path
import base64
import cv2
import numpy as np
import pytest
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[2]
CHROME=Path('/opt/devmcp-browsers/chromium_headless_shell-1255/chrome-headless-shell-linux64/chrome-headless-shell')

@pytest.mark.skipif(not CHROME.is_file(),reason='Existing Sauce SwiftShader worker required')
@pytest.mark.parametrize("polished,sag",[(False,.26),(True,.26),(2,.096),(3,.096)])
def test_bulged_display_and_pointer_match_real_shader(polished,sag):
    # Diagnostic texture only; never used in a product film or owner preview.
    w,h=640,400
    src=np.zeros((h,w,3),np.uint8)
    targets=[(320,200),(205,100),(450,285)]+ ([(15,200),(625,200),(320,15),(320,385)] if polished>=2 else [])
    for x,y in targets:cv2.circle(src,(x,y),3,(0,255,0),-1)
    uri=lambda a:'data:image/png;base64,'+base64.b64encode(cv2.imencode('.png',a)[1]).decode()
    with sync_playwright() as p:
        b=p.chromium.launch(headless=True,executable_path=str(CHROME),args=['--no-sandbox','--enable-unsafe-swiftshader','--use-gl=angle','--use-angle=swiftshader'])
        page=b.new_page()
        page.set_content((ROOT/'assets/shaders/optical-cover-study.html').read_text())
        result=page.evaluate('async d=>window.study(...d)',[uri(src),uri(np.zeros((32,32,3),np.uint8)),True,sag,polished])
        frame=cv2.imdecode(np.frombuffer(base64.b64decode(result.split(',',1)[1]),np.uint8),cv2.IMREAD_COLOR)
        for x,y in targets:
            hit=page.evaluate('d=>window.projectSource(...d)',[[x,y],w,h,sag,polished])
            assert hit['visible'] and hit['residual']<1e-6
            if polished==3:
                previous=page.evaluate('d=>window.projectSource(...d)',[[x,y],w,h,sag,2])
                assert previous==hit  # material change must not move the source or cursor
            px,py=map(lambda v:int(round(v)),hit['pixel'])
            patch=frame[py-14:py+15,px-14:px+15].astype(float)
            mask=(patch[:,:,1]>180)&(patch[:,:,1]>patch[:,:,0]+60)&(patch[:,:,1]>patch[:,:,2]+60)
            yy,xx=np.where(mask)
            assert len(xx)>0
            assert np.hypot(xx.mean()-14,yy.mean()-14)<3
        b.close()
