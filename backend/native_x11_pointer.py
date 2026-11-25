"""Actual pointer input on a dedicated native capture display (never host desktop)."""
import ctypes as C
import re
from contextlib import contextmanager

@contextmanager
def native_pointer(display,width,height):
    if not re.fullmatch(r":[0-9]+",display):
        raise ValueError("Expected isolated Xvfb display")
    x=C.CDLL("libX11.so.6")
    t=C.CDLL("libXtst.so.6")
    ptr=C.c_void_p;win=C.c_ulong;integer=C.c_int;uint=C.c_uint
    def bind(lib,name,args,restype):
        f=getattr(lib,name);f.argtypes=args;f.restype=restype;return f
    open_=bind(x,"XOpenDisplay",[C.c_char_p],ptr)
    close=bind(x,"XCloseDisplay",[ptr],integer)
    sync=bind(x,"XSync",[ptr,integer],integer)
    root=bind(x,"XDefaultRootWindow",[ptr],win)
    sw=bind(x,"XDisplayWidth",[ptr,integer],integer)
    sh=bind(x,"XDisplayHeight",[ptr,integer],integer)
    query=bind(x,"XQueryPointer",[ptr,win,C.POINTER(win),C.POINTER(win),C.POINTER(integer),C.POINTER(integer),C.POINTER(integer),C.POINTER(integer),C.POINTER(uint)],integer)
    motion=bind(t,"XTestFakeMotionEvent",[ptr,integer,integer,integer,C.c_ulong],integer)
    button=bind(t,"XTestFakeButtonEvent",[ptr,uint,integer,C.c_ulong],integer)
    d=open_(display.encode())
    if not d:raise RuntimeError("Cannot open capture pointer display")
    held=False
    def position():
        a,b=win(),win();rx,ry,cx,cy=integer(),integer(),integer(),integer();mask=uint()
        if not query(d,root(d),C.byref(a),C.byref(b),C.byref(rx),C.byref(ry),C.byref(cx),C.byref(cy),C.byref(mask)):
            raise RuntimeError("Cannot observe native pointer")
        return rx.value,ry.value
    def move(px,py):
        px,py=round(px),round(py)
        if not (0<=px<width and 0<=py<height):raise ValueError("Native pointer outside capture")
        if not motion(d,0,px,py,0):raise RuntimeError("Native pointer move failed")
        sync(d,0)
        observed=position()
        if observed!=(px,py):raise RuntimeError("Native pointer position mismatch")
        return observed
    def press(down):
        nonlocal held
        if not button(d,1,int(down),0):raise RuntimeError("Native pointer button failed")
        held=down;sync(d,0)
    try:
        if (sw(d,0),sh(d,0))!=(width,height):raise ValueError("Native pointer display geometry mismatch")
        yield move,press,position
    finally:
        if held:button(d,1,0,0);sync(d,0)
        close(d)
