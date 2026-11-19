"""Source-true, site-independent creative JSON for the existing Sauce compositor.

The plan controls framing and optional recorded cursor/audio only. It cannot
execute a browser action, invent product state, or replace real source pixels.
All semantic anchors resolve against the separate verified capture manifest.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import math
from pathlib import Path

import numpy as np

SCHEMA = "sauce-film-plan-v1"
MAX_KEYFRAMES = 32


def _obj(v, keys, where):
    if not isinstance(v, dict) or set(v) - set(keys):
        raise ValueError(f"Bad {where}: unexpected keys or non-object")
    return v


def _float(v, where, low=None, high=None):
    if type(v) not in (int, float) or not math.isfinite(v):
        raise ValueError(f"{where} must be finite")
    value = float(v)
    if low is not None and value < low or high is not None and value > high:
        raise ValueError(f"{where} is out of bounds")
    return value


def _rectangle(event, key, width, height):
    box = event.get(key)
    if not isinstance(box, dict):
        raise ValueError(f"Missing verified {key}")
    try:
        x,y,w,h=(_float(box[k],f"{key}.{k}") for k in ("x","y","width","height"))
    except KeyError as exc:
        raise ValueError(f"Incomplete verified {key}") from exc
    if x < 0 or y < 0 or w<=0 or h<=0 or x+w>width or y+h>height:
        raise ValueError(f"{key} outside genuine source viewport")
    return x,y,w,h


def _anchor(anchor, time, manifest, width, height):
    if anchor == "wide":
        return width/2, height/2, None
    if not isinstance(anchor,str):
        raise ValueError("Anchor must be a string")
    parts=anchor.split(":")
    if len(parts)!=3 or parts[0]!="event" or not parts[1].isdigit() or parts[2] not in ("target","result","group","component"):
        raise ValueError("Only wide or event:<index>:<target|result|group|component> are supported")
    index=int(parts[1])
    events=manifest.get("events")
    if not isinstance(events,list) or index>=len(events):
        raise ValueError("Missing genuine recorded action")
    event=events[index]
    if not isinstance(event,dict) or not isinstance(event.get("evidence"),str) or not event["evidence"].strip():
        raise ValueError("Event anchor must carry verified outcome evidence")
    result_time=_float(event.get("t"),"observed result time",0)
    if result_time > manifest.get("_source_duration",float("inf")):
        raise ValueError("Event is outside source video duration")
    if parts[2] in ("result","group","component") and time < result_time:
        raise ValueError("Camera cannot anticipate a not-yet-observed result")
    target=_rectangle(event,"targetRect",width,height)
    if parts[2]=="target":
        boxes=[target]
    else:
        result=_rectangle(event,"componentRect" if parts[2]=="component" else "resultRect",width,height)
        boxes=[result] if parts[2] in ("result","component") else [target,result]
    x0=min(r[0] for r in boxes);y0=min(r[1] for r in boxes)
    x1=max(r[0]+r[2] for r in boxes);y1=max(r[1]+r[3] for r in boxes)
    return (x0+x1)/2,(y0+y1)/2,(x0,y0,x1,y1)


def _ease(t,kind):
    t=max(0.,min(1.,t))
    if kind=="hold":return 0.
    if kind=="linear":return t
    return t*t*t*(t*(6*t-15)+10)


@dataclass(frozen=True)
class CameraKey:
    at: float
    start_at: float
    center_x: float
    center_y: float
    zoom: float
    easing: str
    anchor: str
    bounds: tuple[float,float,float,float]|None


@dataclass(frozen=True)
class FilmPlan:
    source_sha256: str
    manifest_sha256: str
    duration: float
    presentation: str
    cursor: str
    audio_file: Path|None
    camera_keys: tuple[CameraKey,...]
    source_size: tuple[int,int]

    def at(self,t,output_size,*,stretch=False):
        """Affine matrix in *source-pixel* coordinates; output 16:9."""
        keys=self.camera_keys
        previous=keys[0];next_key=previous;alpha=0.
        for k in keys[1:]:
            if t < k.at:
                next_key=k
                alpha=(_ease((t-k.start_at)/(k.at-k.start_at),k.easing)
                       if t>=k.start_at and k.at>k.start_at else 0.0)
                break
            previous=k
        else:
            next_key=previous
        focus_x=previous.center_x+(next_key.center_x-previous.center_x)*alpha
        focus_y=previous.center_y+(next_key.center_y-previous.center_y)*alpha
        zoom=previous.zoom+(next_key.zoom-previous.zoom)*alpha
        sw,sh=self.source_size; ow,oh=output_size
        base=max(ow/sw,oh/sh)
        sx,sy=((ow/sw*zoom,oh/sh*zoom) if stretch else (base*zoom,base*zoom))
        cw=ow/sx/2;ch=oh/sy/2
        focus_x=min(sw-cw,max(cw,focus_x))
        focus_y=min(sh-ch,max(ch,focus_y))
        return np.array([[sx,0,ow/2-focus_x*sx],
                         [0,sy,oh/2-focus_y*sy]],dtype=np.float64)



def load_window(data, plan_path):
    _obj(data, ("scale", "backdrop", "backdropSha256"), "window")
    scale = _float(data.get("scale", 1), "window.scale", .65, 1)
    relative = data.get("backdrop")
    digest = data.get("backdropSha256")
    if relative is None and digest is None:
        return scale, None
    if not isinstance(relative, str) or not relative or Path(relative).is_absolute() or ".." in Path(relative).parts:
        raise ValueError("Backdrop must be local to the plan")
    home = Path(plan_path).resolve().parent
    backdrop = (home / relative).resolve()
    if not backdrop.is_relative_to(home) or backdrop.suffix.lower() not in (".jpg", ".jpeg", ".png") or not backdrop.is_file():
        raise ValueError("Backdrop missing or outside the plan directory")
    if backdrop.stat().st_size > 20*1024*1024 or hashlib.sha256(backdrop.read_bytes()).hexdigest() != digest:
        raise ValueError("Backdrop is too large or does not match the plan SHA256")
    return scale, backdrop


def load_film_plan(data,manifest,source_path,manifest_path,source_size,source_duration,plan_path):
    _obj(data,("schema","sourceSha256","manifestSha256","durationSeconds","presentation","cursor","camera","audio","composition","window","glassLoupe"),"film plan")
    if data.get("schema")!=SCHEMA:
        raise ValueError("Unsupported Sauce film-plan schema")
    expected=data.get("sourceSha256")
    if not isinstance(expected,str) or len(expected)!=64 or any(c not in "0123456789abcdef" for c in expected):
        raise ValueError("A 64-character lowercase source SHA256 is required")
    source_file=Path(source_path)
    actual=hashlib.sha256(source_file.read_bytes()).hexdigest()
    if actual != expected:
        raise ValueError("Source SHA256 mismatch: cannot render a different recording")
    declared_manifest_hash=data.get("manifestSha256")
    if (not isinstance(declared_manifest_hash,str) or len(declared_manifest_hash)!=64 or
            any(c not in "0123456789abcdef" for c in declared_manifest_hash)):
        raise ValueError("A 64-character lowercase capture manifest SHA256 is required")
    actual_manifest_hash=hashlib.sha256(Path(manifest_path).read_bytes()).hexdigest()
    if actual_manifest_hash!=declared_manifest_hash:
        raise ValueError("Capture manifest SHA256 mismatch: event evidence cannot be swapped")
    if manifest.get("cursorless") is not True:
        raise ValueError("Capture must declare if it has a source cursor; double cursors forbidden")
    sw,sh=source_size
    captured=manifest.get("capture_rect")
    if not isinstance(captured,dict) or tuple(captured.get(k) for k in ("width","height"))!=(sw,sh):
        raise ValueError("Verified manifest source size mismatch")
    duration=_float(data.get("durationSeconds"),"durationSeconds",.5,source_duration)
    if data.get("presentation") not in ("fullscreen","window"):
        raise ValueError("Unsupported presentation")
    if data.get("cursor") not in ("recorded","none"):
        raise ValueError("Cursor mode must be recorded or none")
    if ("window" in data or "glassLoupe" in data) and data["presentation"] != "window":
        raise ValueError("Window and glass loupe controls require window presentation")
    if "glassLoupe" in data and data["cursor"] != "recorded":
        raise ValueError("Glass loupe requires the recorded cursor")
    if data["cursor"]=="recorded" and "glassLoupe" not in data:
        from recorded_pointer import pointer_track
        if pointer_track(manifest,sw,sh) is None:
            raise ValueError("Recorded cursor requires a valid, source-timed track")
    audio=data.get("audio",{"mode":"clean"})
    _obj(audio,("mode","file"),"audio")
    if audio.get("mode") not in ("clean","file"):
        raise ValueError("Unsupported audio mode")
    audio_file=None
    if audio["mode"]=="file":
        relative=audio.get("file")
        if not isinstance(relative,str) or not relative or Path(relative).is_absolute() or ".." in Path(relative).parts:
            raise ValueError("Audio file must be local to the plan")
        home=Path(plan_path).resolve().parent
        audio_file=(home/relative).resolve()
        if not audio_file.is_relative_to(home) or not audio_file.is_file() or audio_file.suffix.lower() not in (".wav",".m4a",".mp3"):
            raise ValueError("Audio media missing or outside the plan directory")
    elif "file" in audio:
        raise ValueError("Clean audio mode cannot reference media")
    timeline=data.get("camera")
    if not isinstance(timeline,list) or not 2<=len(timeline)<=MAX_KEYFRAMES:
        raise ValueError("Camera must contain 2..32 keyframes")
    keys=[]
    m=dict(manifest,_source_duration=source_duration)
    for item in timeline:
        _obj(item,("at","startAt","anchor","zoom","easing"),"camera keyframe")
        t=_float(item.get("at"),"camera.at",0,duration)
        if keys and t<=keys[-1].at:
            raise ValueError("Camera timeline must be strictly increasing")
        start_at=_float(item.get("startAt",keys[-1].at if keys else 0.),"camera.startAt",0,t)
        if keys and start_at < keys[-1].at:
            raise ValueError("Camera transition cannot begin before preceding keyframe")
        zoom=_float(item.get("zoom"),"camera.zoom",1,2.5)
        ease=item.get("easing","quintic")
        if ease not in ("quintic","linear"):
            raise ValueError("Unsupported camera easing")
        anchor=item.get("anchor")
        cx,cy,bounds=_anchor(anchor,t,m,sw,sh)
        # Even a keyframe that *arrives* after a result could otherwise pan
        # toward that future result during the preceding action.
        if isinstance(anchor,str) and anchor.startswith("event:"):
            parts=anchor.split(":")
            if len(parts)==3 and parts[2] in ("result","group","component"):
                observed_at=_float(m["events"][int(parts[1])].get("t"),"observed result time",0)
                if start_at < observed_at:
                    raise ValueError("Camera would anticipate unobserved result during easing")
        keys.append(CameraKey(t,start_at,cx,cy,zoom,ease,anchor,bounds))
    if keys[0].at!=0 or keys[-1].at>duration:
        raise ValueError("Camera must establish the first frame and fit duration")
    # Source rectangle safety for every result/group endpoint: no clipped proof.
    result=FilmPlan(actual,actual_manifest_hash,duration,data["presentation"],data["cursor"],audio_file,tuple(keys),(sw,sh))
    for k in keys:
        if k.bounds is None:continue
        for out_size in ((1920,1080),(1280,720)):
            mat=result.at(k.at,out_size)
            x0,y0,x1,y1=k.bounds
            points=[mat @ (x,y,1) for x,y in ((x0,y0),(x1,y1))]
            margin=4
            if not (margin<=points[0][0]<points[1][0]<=out_size[0]-margin and
                    margin<=points[0][1]<points[1][1]<=out_size[1]-margin):
                raise ValueError(f"Keyframe {k.at}: verified {k.anchor} would be clipped")
    return result
