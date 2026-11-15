"""Production specifications shared by Sauce's cinematic renderer and export.

This is the film preset, not a replacement for the captured website.
"""
from __future__ import annotations

DPR_CHOICES=(2,3)
DEFAULT_DPR=2
MASTER_SIZE=(1920,1080)
PREVIEW_SIZE=(1280,720)
FPS=60

CURSOR_FILM_SCALE=.56
CURSOR_PRESS_PEAK=.88
CURSOR_FILL='#111113'
CURSOR_OUTLINE='#FFFFFF'
CURSOR_OUTLINE_WIDTH=2.2
CURSOR_SHADOW=(0,12,24,.35)

AMBIENT_BLUR=120
# CSS target: 0 25px 50px -12px rgba(0,0,0,.5), etc.
SHADOW_LAYERS=((50,100,-20,.30),(25,50,-12,.50),(8,17,0,.28))
WINDOW_RIM_ALPHA=.08

CSS_STAGE_SHADOW=(
    "0 0 0 1px rgba(255,255,255,0.08), "
    "0 25px 50px -12px rgba(0,0,0,0.5), "
    "0 50px 100px -20px rgba(0,0,0,0.3)"
)

def enforce_hidpi(dpr:int)->int:
    if dpr not in DPR_CHOICES:
        raise ValueError("Production capture requires DPR 2 or 3")
    return dpr

def ffmpeg_lanczos_preview(master_width:int=1920,master_height:int=1080,
                           preview_width:int=1280,preview_height:int=720)->str:
    if master_width*preview_height!=master_height*preview_width:
        raise ValueError('Preview and master must have matching aspect ratio')
    if preview_width>master_width or preview_height>master_height:
        raise ValueError('Preview is not a downscale')
    return f"fps=30,scale={preview_width}:{preview_height}:flags=lanczos"
