from pathlib import Path
import hashlib,sys
import numpy as np
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'scripts'))
from physical_cover_calibration import CoverCalibration

def test_hash_bound_calibration_preserves_coordinates(tmp_path):
    path=tmp_path/'cover.npz'
    r=np.zeros((540,960,3),np.float16)
    t=np.ones_like(r)
    np.savez_compressed(path,reflectance=r,transmission=t)
    h=hashlib.sha256(path.read_bytes()).hexdigest()
    with pytest.raises(ValueError,match='hash mismatch'):
        CoverCalibration(path,'0'*64)
    c=CoverCalibration(path,h)
    f=np.random.default_rng(42).integers(0,256,(1080,1920,3),dtype=np.uint8)
    np.testing.assert_array_equal(c.apply(f,(2880,1800),(1920,1080)),f)
    with pytest.raises(ValueError,match='measured'):
        c.apply(f,(1920,1080),(1920,1080))

def test_invalid_transfer_fails_closed(tmp_path):
    p=tmp_path/'bad.npz'
    np.savez_compressed(p,reflectance=np.zeros((2,2)),transmission=np.ones((2,2)))
    with pytest.raises(ValueError,match='Invalid optical transfer'):
        CoverCalibration(p,hashlib.sha256(p.read_bytes()).hexdigest())
