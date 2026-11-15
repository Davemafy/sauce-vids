"""Read installed X11 cursor glyphs as RGBA layers (no drawn approximation).

A bundled/recognized native X11 cursor theme gives arrow, hand and I-beam.
These OS glyphs aren't equivalent to copyrighted macOS pointer designs,
but preserve real hotspots and change state according to computed CSS cursor.
"""
from __future__ import annotations
import ctypes as C
from dataclasses import dataclass
from pathlib import Path
import subprocess,time
from PIL import Image


class _Image(C.Structure):
    _fields_=[
        ("x",C.c_short),("y",C.c_short),
        ("width",C.c_ushort),("height",C.c_ushort),
        ("xhot",C.c_ushort),("yhot",C.c_ushort),
        ("cursor_serial",C.c_ulong),("pixels",C.POINTER(C.c_ulong)),
        ("atom_name",C.c_ulong),
    ]


@dataclass
class CursorAsset:
    rgba: Image.Image
    hotspot_x: int
    hotspot_y: int

    def scaled(self, factor:int=2):
        return CursorAsset(
            self.rgba.resize((self.rgba.width*factor,self.rgba.height*factor),
                             Image.Resampling.LANCZOS),
            self.hotspot_x*factor,self.hotspot_y*factor)


def extract_native_cursors(display:str=':97',scale:int=2)->dict[str,CursorAsset]:
    if scale<1 or scale>4:raise ValueError("Unsupported cursor asset scale")
    x11=C.CDLL("libX11.so.6")
    xf=C.CDLL("libXfixes.so.3")
    x11.XOpenDisplay.argtypes=[C.c_char_p]
    x11.XOpenDisplay.restype=C.c_void_p
    x11.XDefaultRootWindow.argtypes=[C.c_void_p]
    x11.XDefaultRootWindow.restype=C.c_ulong
    x11.XCreateFontCursor.argtypes=[C.c_void_p,C.c_uint]
    x11.XCreateFontCursor.restype=C.c_ulong
    x11.XDefineCursor.argtypes=[C.c_void_p,C.c_ulong,C.c_ulong]
    x11.XSync.argtypes=[C.c_void_p,C.c_int]
    x11.XFree.argtypes=[C.c_void_p]
    xf.XFixesGetCursorImage.argtypes=[C.c_void_p]
    xf.XFixesGetCursorImage.restype=C.POINTER(_Image)
    for attempt in range(4):
        number=int(display.lstrip(':'))+attempt
        name=f':{number}'
        proc=subprocess.Popen(
            ['Xvfb',name,'-screen','0','640x480x24','-nolisten','tcp','-ac'],
            stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        time.sleep(.45)
        if proc.poll() is not None:continue
        conn=x11.XOpenDisplay(name.encode())
        if not conn:
            proc.terminate();continue
        try:
            root=x11.XDefaultRootWindow(conn)
            icons={}
            # X11 cursorfont: left_ptr=68, hand2=60, xterm=152.
            for css,glyph in [('default',68),('pointer',60),('text',152)]:
                font_cursor=x11.XCreateFontCursor(conn,glyph)
                x11.XDefineCursor(conn,root,font_cursor)
                x11.XSync(conn,False)
                time.sleep(.07)
                image=xf.XFixesGetCursorImage(conn)
                if not image:raise RuntimeError('XFixes could not resolve '+css)
                try:
                    data=image.contents
                    px=[int(data.pixels[j])&0xffffffff
                        for j in range(data.width*data.height)]
                    image_rgba=Image.new("RGBA",(data.width,data.height))
                    image_rgba.putdata([
                        ((v>>16)&255,(v>>8)&255,v&255,(v>>24)&255)
                        for v in px])
                    icons[css]=CursorAsset(image_rgba,int(data.xhot),int(data.yhot)).scaled(scale)
                finally:x11.XFree(C.cast(image,C.c_void_p))
            return icons
        finally:
            x11.XCloseDisplay(conn)
            proc.terminate()
            try:proc.wait(timeout=3)
            except subprocess.TimeoutExpired:proc.kill()
    raise RuntimeError('Could not create isolated X display for native cursors')


from session_contract import cursor_class
