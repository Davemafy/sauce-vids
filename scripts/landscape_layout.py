"""Landscape film framing contract at native 1920×1080 master resolution.

Keep product UI, caption baseline and pointer metrics independent. These
constants are shared by the renderer, acceptance tests and quality gate.
"""
from dataclasses import dataclass

MASTER_W,MASTER_H=1920,1080
BROWSER_X,BROWSER_Y=160,25
BROWSER_W,BROWSER_H=1600,900
CAPTION_Y1,CAPTION_Y2=991,1054
CURSOR_W,CURSOR_H=27,37

def validate_layout() -> None:
    assert BROWSER_W/BROWSER_H==16/9
    assert BROWSER_X==(MASTER_W-BROWSER_W)//2
    assert 0<=BROWSER_Y and BROWSER_Y+BROWSER_H<MASTER_H
    assert CAPTION_Y1-(BROWSER_Y+BROWSER_H)>=55
    assert MASTER_H-CAPTION_Y2>=20
    assert 0<CURSOR_W<=30 and 0<CURSOR_H<=40

validate_layout()
