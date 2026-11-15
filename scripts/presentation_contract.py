"""Presentation motion rules. Dependency-free so they run in GitHub CI.

These functions control film presentation, not Chromium's raw input events.
"""
from __future__ import annotations
import math


def presentation_css_cursor(css:str|None,
                            pointer:tuple[float,float]|None,
                            actions:list[dict])->str:
    """A presentation pointer must not disappear on CSS cursor:none."""
    if css in ('text','vertical-text'):return 'text'
    if css in ('pointer','grab','grabbing'):return 'pointer'
    if css=='none' and pointer:
        x,y=pointer
        for box in actions:
            if (box['x']-2<=x<=box['x']+box['width']+2 and
                box['y']-2<=y<=box['y']+box['height']+2):
                return 'pointer'
    return 'default'


def press_scale(events:list[dict],t:float,start_ms:float)->float:
    """A short, deterministic visual press followed by damped release."""
    ages=[t-(e['t']-start_ms)/1000. for e in events
          if e['type']=='pointerdown' and e.get('x') is not None]
    ages=[a for a in ages if 0<=a<=.22]
    if not ages:return 1.
    age=min(ages)
    if age<=.065:
        phase=age/.065
        return 1.0-.11*(phase*phase*(3-2*phase))
    phase=min(1.,(age-.065)/.155)
    omega=7.2
    response=(1+omega*phase)*math.exp(-omega*phase)
    return 1-.11*response


def modal_spring_scale(age_seconds:float)->float:
    """Real modal receives a tiny critically damped 0.95->1.0 emphasis."""
    if age_seconds<0:return 1.
    omega=23.
    return min(1.,1-.05*(1+omega*age_seconds)*math.exp(-omega*age_seconds))
