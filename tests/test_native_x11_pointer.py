from pathlib import Path
import pytest
from backend.customer_story import native_display,W,H,D
from backend.native_x11_pointer import native_pointer

def test_pointer_uses_actual_isolated_display(tmp_path):
    with native_display(tmp_path) as display:
        with native_pointer(display,W*D,H*D) as (move,press,position):
            assert move(91,121)==(91,121)
            assert position()==(91,121)
            press(True);press(False)
            with pytest.raises(ValueError):move(-1,0)
        with pytest.raises(ValueError,match="geometry"):
            with native_pointer(display,1,1):pass

def test_remote_display_is_not_admitted():
    with pytest.raises(ValueError):
        with native_pointer("remote:0",1920,1080):pass
