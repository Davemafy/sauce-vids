"""Professional film cursor following the *recorded* source pointer.

Preserves exact recorded click hotspots while smoothing high-frequency X11
sample jitter. The existing Brimble reference SVG is reused, never redrawn.
No extra pointer actions are invented or cursor positions relocated to a CTA.
"""
from __future__ import annotations
import numpy as np
from PIL import Image
from cinematic_presentation_v13 import _blend
from reference_cursor_v15 import load_cursor,press_scale


class CinematicRecordedPointer:
    def __init__(self, track:np.ndarray,click_times, *, style='ink',
                 film_scale=.55):
        if not .35<=film_scale<=1:raise ValueError("Unsafe cursor size")
        if style not in ('ink','outline'):raise ValueError("Unsupported cursor")
        self.track=track
        self.clicks=tuple(float(t) for t in click_times)
        self.style=style
        self.film_scale=film_scale
        self.t0=float(track[0,0]);self.t1=float(track[-1,0])
        self.times=np.arange(self.t0,self.t1+1/120.,1/120.)
        self.values=np.column_stack([
            np.interp(self.times,track[:,0],track[:,i]) for i in (1,2)])
        # Small symmetric low-pass, 25ms standard deviation; no lag.
        k=np.arange(-6,7).astype(np.float64)
        weights=np.exp(-.5*(k/2.7)**2);weights/=weights.sum()
        pad=len(k)//2
        smoothed=np.column_stack([
            np.convolve(np.pad(self.values[:,i],(pad,pad),mode='edge'),
                        weights,mode='valid') for i in range(2)])
        self.smoothed=smoothed
        # Source-true click correction: lens hotspot remains exactly at the
        # original recorded interpolation for a click, despite smoothing.
        self.click_corrections=[]
        for t in self.clicks:
            if not self.t0<=t<=self.t1:continue
            observed=np.array([np.interp(t,track[:,0],track[:,i])
                               for i in (1,2)],dtype=np.float64)
            filtered=np.array([np.interp(t,self.times,smoothed[:,i])
                               for i in range(2)],dtype=np.float64)
            self.click_corrections.append((t,observed-filtered))

    def at(self,t:float)->tuple[float,float]|None:
        if t<self.t0:
            return None
        if t>=self.t1:
            return (float(self.track[-1,1]),float(self.track[-1,2]))
        t=float(t)
        position=np.array([np.interp(t,self.times,self.smoothed[:,i])
                           for i in range(2)],np.float64)
        for click,residual in self.click_corrections:
            dt=abs(t-click)
            if dt<.13:position+=residual*np.exp(-.5*(dt/.040)**2)
        return (float(position[0]),float(position[1]))

    def click_center(self,t):
        # Never use the filtered position for an interaction hotspot.
        return (float(np.interp(t,self.track[:,0],self.track[:,1])),
                float(np.interp(t,self.track[:,0],self.track[:,2])))

    def paint(self,stage:np.ndarray,projected_position:tuple[float,float],
              t:float):
        sprite=load_cursor(self.style)
        age=min((t-c for c in self.clicks if 0<=t-c<.25),default=None)
        scale=self.film_scale*press_scale(age)*(stage.shape[0]/1080.)
        art=sprite.rgba
        if scale<.999:
            w=max(2,round(art.shape[1]*scale))
            h=max(2,round(art.shape[0]*scale))
            art=np.asarray(Image.fromarray(art,'RGBA').resize(
                (w,h),Image.Resampling.LANCZOS),dtype=np.uint8)
        x,y=projected_position
        hotx=round(x-sprite.hotspot[0]*scale)
        hoty=round(y-sprite.hotspot[1]*scale)
        _blend(stage,art,hotx,hoty)


def pointer_visibility_report(pointer,shots,manifest,source_size,output_size,
                              camera_fn,stage_scale=1.0):
    """Flag missing/offscreen *recorded* pointers before costly video encoding.

    The camera may choose another verified source target, but a synthetic
    pointer relocation is not an acceptable repair.
    """
    width,height=output_size
    lead=float(manifest['lead_s'])
    missing=0
    offscreen=[]
    for shot in shots:
        for j in range(shot.length()):
            source_t=(shot.start+j)/60-lead
            original=pointer.at(source_t)
            if original is None:
                missing+=1
                continue
            m=camera_fn(manifest,shot,j,source_size,output_size)
            if stage_scale!=1.:
                from floating_ui_stage import floating_matrix
                m=floating_matrix(m,output_size,stage_scale)
            px,py=m @ np.float64([original[0],original[1],1])
            if not (24<=px<=width-24 and 24<=py<=height-24):
                offscreen.append({
                    'sourceFrame':shot.start+j,'outputFrame':shot.out_start+j,
                    'position':[round(float(px),2),round(float(py),2)],
                    'shot':shot.label})
    return {'unrecordedOpeningFrames':missing,
            'offscreenFrames':len(offscreen),
            'firstOffscreenFrames':offscreen[:4],
            'recordedInputNeverRepositioned':True}
