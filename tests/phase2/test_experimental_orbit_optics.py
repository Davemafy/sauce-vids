"""Isolated optics, exact camera response and encoded-video safety gates."""
from __future__ import annotations
import hashlib
import sys
from pathlib import Path
import cv2
import numpy as np
import pytest

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"scripts"))
from cinematic_stage import CinematicStage
from stage_optics import apply_stage_optics

def ssim(a:np.ndarray,b:np.ndarray)->float:
    """Canonical 11px Gaussian SSIM with 8-bit C1/C2, no extra package."""
    a=a.astype(np.float32);b=b.astype(np.float32)
    m1=cv2.GaussianBlur(a,(11,11),1.5)
    m2=cv2.GaussianBlur(b,(11,11),1.5)
    s1=cv2.GaussianBlur(a*a,(11,11),1.5)-m1*m1
    s2=cv2.GaussianBlur(b*b,(11,11),1.5)-m2*m2
    s12=cv2.GaussianBlur(a*b,(11,11),1.5)-m1*m2
    c1=(.01*255)**2;c2=(.03*255)**2
    value=((2*m1*m2+c1)*(2*s12+c2)/
           ((m1*m1+m2*m2+c1)*(s1+s2+c2)))
    return float(np.mean(value))

def make_source()->np.ndarray:
    # Structured image with high-frequency detail exercises text integrity.
    yy,xx=np.mgrid[0:832,0:1480]
    signal=np.empty((832,1480,3),dtype=np.uint8)
    signal[:,:,0]=(24+xx//14%7*20).astype(np.uint8)
    signal[:,:,1]=(110+yy//9%8*13).astype(np.uint8)
    signal[:,:,2]=(196+((xx//7+yy//5)%2)*35).astype(np.uint8)
    return signal

def test_stage_optics_pixel_isolation_with_real_h0_h60_projection():
    source=make_source()
    kwargs=dict(tilt=(.30,-.40),perspective_px=1200.,
      spotlight={'active':True,'box':{'x':440.,'y':182.6,
                         'width':400.,'height':450.},
        'factor':1480/1280,'dx':0.,'dy':0.,'blurPx':6.,'dimOpacity':.25},
      foreground={'source':source,'box':{'x':440.,'y':182.6,
                          'width':400.,'height':450.},'radiusCss':12.})
    off=CinematicStage(backdrop_style='fluted-glass')
    on=CinematicStage(backdrop_style='fluted-glass',enable_stage_optics=True)
    flat=off.render(source,**kwargs)
    fx=on.render(source,frame_index=98,**kwargs)
    roi=(slice(124,956),slice(220,1700))
    score=ssim(flat[roi],fx[roi])
    print(f'ACTIVE_MODAL_FULL_WINDOW_SSIM={score:.8f}')
    assert score>=.999,(score,np.abs(flat[roi].astype(int)-fx[roi].astype(int)).max())
    assert np.any(flat[:114,:]!=fx[:114,:]),"Stage must visibly change"
    # Original 832x1480 source was neither overwritten nor recolored.
    assert np.array_equal(source,make_source())
    # Fixed seed+frame+pose yields bytewise identical projected film image.
    again=on.render(source,frame_index=98,**kwargs)
    assert hashlib.sha256(fx.tobytes()).digest()==hashlib.sha256(again.tobytes()).digest()
    next_frame=on.render(source,frame_index=99,**kwargs)
    assert not np.array_equal(fx[:114,:],next_frame[:114,:])

def test_optic_separation_is_clamped_and_seed_controls_grain():
    source=np.full((260,460,3),24,dtype=np.uint8)
    quad=np.float32([[90,40],[365,40],[365,218],[90,218]])
    with pytest.raises(ValueError):
        apply_stage_optics(source,quad,0,dispersion_px=1.6)
    a=apply_stage_optics(source,quad,19,seed=2110)
    b=apply_stage_optics(source,quad,19,seed=2110)
    c=apply_stage_optics(source,quad,19,seed=2111)
    assert np.array_equal(a,b)
    assert not np.array_equal(a,c)
    assert np.array_equal(a[60:190,110:345],source[60:190,110:345])


def test_canonical_final_frame_lock_is_seed_plan_and_source_bound(tmp_path):
    from canonical_frame_cache import (CanonicalComposition,
                                       identity_for_composition)
    codefile=ROOT/"scripts/stage_optics.py"
    frameplan={'frames':[{'sourceMs':0},{'sourceMs':1000/60}]}
    root_identity='a'*64
    one=identity_for_composition(root_identity,frameplan,100,[codefile])
    assert one!=identity_for_composition(root_identity,frameplan,101,[codefile])
    assert one!=identity_for_composition('b'*64,frameplan,100,[codefile])
    assert one!=identity_for_composition(root_identity,
        {'frames':[{'sourceMs':10}]},100,[codefile])
    frame0=np.full((32,48,3),70,np.uint8)
    frame1=np.full((32,48,3),90,np.uint8)
    writer=CanonicalComposition(tmp_path,one,2)
    assert not writer.reused
    assert np.array_equal(writer.use(0,frame0),frame0)
    assert np.array_equal(writer.use(1,frame1),frame1)
    writer.finish()
    reader=CanonicalComposition(tmp_path,one,2)
    assert reader.reused
    # Browser-driven overlay changed, but export remains source-locked.
    unstable=np.full((32,48,3),99,np.uint8)
    assert np.array_equal(reader.use(0,unstable),frame0)
    assert np.array_equal(reader.use(1,unstable),frame1)
    assert reader.live_diff_frames==2
    # Corrupt private cache must fail instead of hiding source divergence.
    file=reader.directory/"00001.png"
    file.write_bytes(file.read_bytes()+b'corrupt')
    with pytest.raises(RuntimeError,match="hash mismatch"):
        reader.use(1,unstable)
