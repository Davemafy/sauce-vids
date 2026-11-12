"""Sauce Vids directing primitives: inspect, edit decision record, and quality review.

Hermes chooses the shots; this module provides verifiable browser observations and
reproducible local media transforms. No synthetic UI, decorative stock, or cloud keys.
"""
import json
import math
import os
from pathlib import Path
import re
import shutil
import subprocess
import time
import uuid
from urllib.parse import urljoin, urlsplit

from . import tools


def _json(**value):
    return json.dumps(value, ensure_ascii=False)


def _ffmpeg():
    executable = shutil.which("ffmpeg")
    if not executable:
        try:
            import imageio_ffmpeg
            executable = imageio_ffmpeg.get_ffmpeg_exe()
        except ImportError:
            pass
    if not executable:
        raise ValueError("FFmpeg is required")
    return executable


def _ffprobe():
    return shutil.which("ffprobe")


def _duration(path):
    ffprobe = _ffprobe()
    if not ffprobe:
        raise ValueError("ffprobe is required for planning")
    result = subprocess.run(
        [ffprobe, "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
        capture_output=True, text=True, timeout=15, check=True,
    )
    return float(result.stdout.strip())


# Selectors come from the observed DOM, not guessed by Hermes. Only links or tabs
# are returned as actionable: no submit buttons, forms, or billing operations.
SCOUT_JS = r"""() => {
  function selector(el) {
    if (el.id && /^[a-zA-Z][a-zA-Z0-9_-]*$/.test(el.id)) return '#' + CSS.escape(el.id);
    const testId=el.getAttribute('data-testid');
    if (testId && /^[a-zA-Z0-9_-]{1,60}$/.test(testId))
      return '[data-testid="' + testId + '"]';
    const path=[];
    for(let node=el;node && node.nodeType===1 && path.length<7;node=node.parentElement){
      const name=node.tagName.toLowerCase();
      if(name==='html'){path.unshift('html');break;}
      let n=1;
      for(let prev=node.previousElementSibling;prev;prev=prev.previousElementSibling)
        if(prev.tagName===node.tagName)n++;
      path.unshift(name+':nth-of-type('+n+')');
    }
    const result=path.join(' > ');
    return result.length<=150 ? result : null;
  }
  const headings=[...document.querySelectorAll('h1,h2,h3,[role="heading"]')]
    .filter(el=>{const b=el.getBoundingClientRect();return b.width>0 && b.height>0;})
    .slice(0,60).map(el=>{
      const b=el.getBoundingClientRect();
      const region=el.closest('section');
      const regionHeading=region && region.querySelector('h1,h2');
      const row=el.parentElement && el.parentElement.parentElement;
      const mediaNode=row && row.children.length===2 &&
        [...row.children].find(c=>c!==el.parentElement);
      const mediaBox=mediaNode && mediaNode.getBoundingClientRect();
      const mediaCenterX=(mediaBox && mediaBox.width>=250 && mediaBox.height>=85)
        ? Math.round(mediaBox.x+mediaBox.width/2) : null;
      return {text:(el.innerText||el.textContent||'').trim().slice(0,110),
              media_center_x:mediaCenterX,
              section_title:regionHeading ? (regionHeading.innerText||'').trim().slice(0,100) : '',
              tag:el.tagName,selector:selector(el),
              document_y:Math.round(b.top+window.scrollY),
              center_x:Math.round(b.left+b.width/2),
              screen_y:Math.round(b.top+b.height/2)};
    });
  const controls=[...document.querySelectorAll('a[href],[role="tab"]')]
    .filter(el=>{const b=el.getBoundingClientRect();return b.width>0 && b.height>0;})
    .slice(0,90).map(el=>{
      const box=el.getBoundingClientRect();
      return {type:el.getAttribute('role')==='tab'?'click_tab':'click_link',
        label:(el.innerText||el.getAttribute('aria-label')||'').trim().slice(0,80),
        selector:selector(el),href:el.getAttribute('href'),
        position:{x:Math.round(box.x+box.width/2),y:Math.round(box.y+box.height/2)}};
    }).filter(c=>c.selector && c.label);
  return {title:document.title,headings,controls,
          document_height:document.documentElement.scrollHeight,
          viewport:{width:innerWidth,height:innerHeight}};
}"""


def scout(args, **kwargs):
    """Observe the real page, screenshot three positions, list non-destructive controls."""
    try:
        project = tools._id(args.get("project"))
        url = args.get("url")
        host = tools._url(url)
        from playwright.sync_api import sync_playwright
        scout_id = project + "-scout-" + uuid.uuid4().hex[:8]
        folder = tools._dir(scout_id)
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True, args=["--no-sandbox"])
            try:
                ctx = browser.new_context(viewport={"width": 1440, "height": 900},
                                          device_scale_factor=1)
                page = ctx.new_page()
                page.goto(url, wait_until="domcontentloaded", timeout=30000)
                tools._url(page.url, host)
                page.wait_for_timeout(1200)
                scan = page.evaluate(SCOUT_JS)
                controls = []
                for c in scan["controls"]:
                    if c["type"] == "click_link":
                        target = urljoin(page.url, c.get("href") or "")
                        try:
                            tools._url(target, host)
                        except ValueError:
                            continue
                    controls.append(c)
                screenshots = []
                for idx, offset in enumerate((0, 700, 1400)):
                    page.evaluate("(offset)=>window.scrollTo(0,offset)", offset)
                    page.wait_for_timeout(350)
                    path = folder / f"scout-{idx}.png"
                    page.screenshot(path=str(path), animations="disabled")
                    screenshots.append(str(path))
                observed = {"scout_id":scout_id,"url":page.url,
                            "title":scan["title"],"headings":scan["headings"],
                            "controls":controls[:50],"document_height":scan["document_height"],
                            "viewport":scan["viewport"],"screenshots":screenshots}
                (folder/"scout.json").write_text(json.dumps(observed,indent=2))
                return _json(ok=True,**observed)
            finally:
                browser.close()
    except Exception as exc:
        return _json(ok=False,error=str(exc))


def plan(args, **kwargs):
    """Persist an explicit EDL (edit decision list) after capture. No model inference."""
    try:
        run_id = tools._id(args.get("run_id"))
        folder = tools._dir(run_id)
        source = folder/"recording.webm"
        if not source.is_file():
            raise ValueError("Capture a recording before planning shots")
        source_duration = _duration(source)
        shots = args.get("shots")
        if not isinstance(shots, list) or not 1 <= len(shots) <= 12:
            raise ValueError("Provide 1–12 shots")
        normalized = []
        previous_end = 0.0
        for i, shot in enumerate(shots):
            if not isinstance(shot, dict):
                raise ValueError("Each shot must be an object")
            start, end = float(shot["start_s"]), float(shot["end_s"])
            zoom = float(shot.get("zoom",1))
            fx,fy = float(shot.get("focus_x",0.5)),float(shot.get("focus_y",0.5))
            label = shot.get("label","")
            if not all(math.isfinite(v) for v in (start,end,zoom,fx,fy)):
                raise ValueError("Scene values must be finite")
            if not 0 <= start < end <= source_duration + 0.05:
                raise ValueError("Shot outside recorded duration")
            if i and start < previous_end - 0.01:
                raise ValueError("Shots must be chronological and non-overlapping")
            if not 1.0 <= zoom <= 1.45 or not 0 <= fx <= 1 or not 0 <= fy <= 1:
                raise ValueError("Zoom/focus outside allowed range")
            if not isinstance(label,str) or len(label)>120:
                raise ValueError("Shot label too long")
            normalized.append({"start_s":start,"end_s":end,"zoom":zoom,
                               "focus_x":fx,"focus_y":fy,"label":label})
            previous_end = end
        edl = {"schema_version":1,"run_id":run_id,"source_duration_s":source_duration,
               "output_duration_s":round(sum(s["end_s"]-s["start_s"] for s in normalized),2),
               "shots":normalized}
        (folder/"edit-plan.json").write_text(json.dumps(edl,indent=2))
        return _json(ok=True,edit_plan=str(folder/"edit-plan.json"),**edl)
    except Exception as exc:
        return _json(ok=False,error=str(exc))


def _asset(value, allowed_extensions):
    """Resolve a licensed asset by filename only, under explicitly configured root."""
    if not isinstance(value,str) or not re.fullmatch(r"[a-zA-Z0-9_.-]{1,90}",value):
        raise ValueError("Invalid licensed asset filename")
    root = os.environ.get("SAUCE_ASSET_DIR")
    if not root:
        raise ValueError("Configure SAUCE_ASSET_DIR for licensed assets")
    root = Path(root).expanduser().resolve()
    path = (root/value).resolve()
    if path.parent != root or path.suffix.lower() not in allowed_extensions or not path.is_file():
        raise ValueError("Licensed asset not found or unsupported format")
    return path


def render_edited(args):
    """Use recorded footage and a Hermes-authored EDL, with optional licensed music."""
    run_id = tools._id(args.get("run_id"))
    folder = tools._dir(run_id)
    source = folder/"recording.webm"
    if not source.is_file():
        raise ValueError("Recording not found")
    edl_path=folder/"edit-plan.json"
    if not edl_path.is_file():
        raise ValueError("Call sauce_plan first")
    edl=json.loads(edl_path.read_text())
    shots=edl["shots"]
    if not shots:
        raise ValueError("No shots in edit plan")
    music=args.get("music_asset")
    background=args.get("background_asset")
    music_path=_asset(music,{".mp3",".wav",".ogg",".m4a"}) if music else None
    bg_path=_asset(background,{".png",".jpg",".jpeg"}) if background else None
    cmd=[_ffmpeg(),"-hide_banner","-loglevel","error","-y","-i",str(source)]
    image_index=None
    music_index=None
    if bg_path:
        image_index=len([x for x in (source,) if x])  # 1
        cmd+=["-loop","1","-i",str(bg_path)]
    if music_path:
        music_index=1+(1 if bg_path else 0)
        cmd+=["-stream_loop","-1","-i",str(music_path)]
    parts=[]
    keys=[]
    for i,shot in enumerate(shots):
        zoom=shot["zoom"]
        # Progressive camera push over genuine footage. Work at 720p to
        # reduce filter memory consumption in the 1GiB worker.
        clip_seconds=max(0.25,shot["end_s"]-shot["start_s"])
        step=max(0,(zoom-1))/(clip_seconds*30)
        filt=(f"[0:v]trim=start={shot['start_s']}:end={shot['end_s']},"
              f"setpts=PTS-STARTPTS,fps=30,"
              f"scale=1280:720:force_original_aspect_ratio=increase:flags=bicubic,"
              f"crop=1280:720,setsar=1,zoompan=z='min({zoom:.4f},1+on*{step:.8f})':"
              f"x='max(0,min(iw-iw/zoom,iw*{shot['focus_x']:.4f}-iw/(2*zoom)))':"
              f"y='max(0,min(ih-ih/zoom,ih*{shot['focus_y']:.4f}-ih/(2*zoom)))':"
              f"d=1:s=1280x720:fps=30,"
              f"scale=1920:1080:flags=bicubic,format=yuv420p[v{i}]")
        parts.append(filt)
        keys.append(f"[v{i}]")
    parts.append("".join(keys)+f"concat=n={len(keys)}:v=1:a=0[cut]")
    duration=sum(shot["end_s"]-shot["start_s"] for shot in shots)
    final_video="[cut]"
    if bg_path:
        parts.append(f"[{image_index}:v]scale=1920:1080,format=yuv420p[bg]")
        parts.append("[cut]scale=1820:1024[content]")
        parts.append("[bg][content]overlay=50:28:shortest=1,format=yuv420p[v]")
        final_video="[v]"
    if music_path:
        fade_out=max(0,duration-0.7)
        parts.append(f"[{music_index}:a]atrim=0:{duration:.3f},asetpts=PTS-STARTPTS,"
                     f"volume=0.20,afade=t=in:st=0:d=0.3,"
                     f"afade=t=out:st={fade_out:.3f}:d={min(0.7,duration/2):.3f}[aud]")
    out=folder/"final.mp4"
    cmd+=["-filter_complex",";".join(parts),"-map",final_video]
    if music_path:
        cmd+=["-map","[aud]","-c:a","aac","-b:a","160k"]
    else:
        cmd+=["-an"]
    cmd+=["-c:v","libx264","-pix_fmt","yuv420p","-crf","20",
          "-preset","veryfast","-threads","1","-movflags","+faststart",
          "-t",f"{duration:.3f}",str(out)]
    result=subprocess.run(cmd,capture_output=True,text=True,timeout=300)
    if result.returncode:
        raise RuntimeError("FFmpeg edit failed: "+result.stderr[-1500:])
    receipt={"run_id":run_id,"video":str(out),"edit_plan":str(edl_path),
             "bytes":out.stat().st_size,"music_asset":music or None,
             "background_asset":background or None,
             "source":"recorded browser footage"}
    (folder/"render.json").write_text(json.dumps(receipt,indent=2))
    return receipt


def review(args, **kwargs):
    """Extract evidence frames and detect blank runs; Hermes judges visual quality."""
    try:
        run_id=tools._id(args.get("run_id"))
        folder=tools._dir(run_id)
        video=folder/"final.mp4"
        if not video.is_file():
            raise ValueError("Render first")
        duration=_duration(video)
        if duration<=0:
            raise ValueError("Invalid output duration")
        sample_times=sorted(set([max(0,duration*fr) for fr in (.08,.28,.50,.72,.92)]))
        samples=[]
        for idx,t in enumerate(sample_times):
            p=folder/f"review-{idx}.jpg"
            r=subprocess.run([_ffmpeg(),"-hide_banner","-loglevel","error",
               "-ss",f"{t:.3f}","-i",str(video),"-frames:v","1",
               "-q:v","2",str(p),"-y"],capture_output=True,text=True,timeout=30)
            if r.returncode:
                raise RuntimeError(r.stderr[-300:])
            samples.append({"time_s":round(t,2),"file":str(p)})
        detect=subprocess.run([_ffmpeg(),"-hide_banner","-i",str(video),
          "-vf","blackdetect=d=0.4:pix_th=0.10:pic_th=0.98","-an","-f","null","-"],
          capture_output=True,text=True,timeout=90)
        intervals=[]
        for start,end in re.findall(r"black_start:([0-9.]+)\s+black_end:([0-9.]+)",detect.stderr):
            intervals.append({"start_s":float(start),"end_s":float(end)})
        summary={"run_id":run_id,"duration_s":round(duration,2),
                 "frames":samples,"black_intervals":intervals,
                 "needs_visual_review":True,
                 "advice":"Inspect these actual frames; replace dead air/blank captures by revising sauce_plan."}
        (folder/"review.json").write_text(json.dumps(summary,indent=2))
        return _json(ok=True,**summary)
    except Exception as exc:
        return _json(ok=False,error=str(exc))
