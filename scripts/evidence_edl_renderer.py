#!/usr/bin/env python3
"""Sauce opt-in evidence-backed editorial shot rendering over actual browser media.

A shot is a contiguous range of decoded source frames with a smooth, anchored
camera path. Editorial cuts skip unstable recorded source frames without
inventing interface pixels. Source events and resultRect/detailRect authorize
each camera target. Refs.video technique study, NOT branded reference footage.
"""
from __future__ import annotations
import argparse,json,hashlib,math,subprocess,sys,time
from dataclasses import dataclass
from pathlib import Path
import cv2,numpy as np
from recorded_pointer import pointer_track,project_pointer

def quintic(x):
    u=max(0.,min(1.,float(x)))
    return u*u*u*(u*(u*6-15)+10)

def pose(manifest,selector,source_size):
    w,h=source_size
    if selector=='wide':
        return .432*w,.5*h
    kind,index=selector.split(':')
    events=[e for e in manifest['events'] if e.get('kind')=='state_change']
    if not 0<=int(index)<len(events) or kind not in ('result','detail','summary','overview','result-upper'):
        raise ValueError('Unsupported or unobserved camera anchor')
    state=events[int(index)]
    if not isinstance(state.get('evidence'),str) or not state['evidence'].strip():
        raise ValueError('Missing state-change proof')
    if kind=='overview':
        # A real multi-card outcome can only be presented as a complete
        # information group when *each* card was DOM-measured in the capture.
        boxes=state.get('summaryRects')
        if not isinstance(boxes,list) or len(boxes)<2:
            raise ValueError('No verified multi-element result for overview')
        visible=[]
        for box in boxes:
            if not isinstance(box,dict):raise ValueError('Bad summary group rectangle')
            try:
                rx,ry,rw,rh=[float(box[k]) for k in ('x','y','width','height')]
            except (KeyError,ValueError,TypeError) as exc:
                raise ValueError('Bad summary geometry') from exc
            if not all(map(math.isfinite,(rx,ry,rw,rh))) or rw<=0 or rh<=0:
                raise ValueError('Bad summary dimensions')
            x0,y0=max(0.,rx),max(0.,ry)
            x1,y1=min(float(w),rx+rw),min(float(h),ry+rh)
            if x1<=x0 or y1<=y0 or (x1-x0)*(y1-y0)<.80*rw*rh:
                raise ValueError('Multi-card summary mostly outside captured viewport')
            visible.append((x0,y0,x1,y1))
        return (min(q[0] for q in visible)+max(q[2] for q in visible))/2,(
            min(q[1] for q in visible)+max(q[3] for q in visible))/2
    key={'result':'resultRect','detail':'detailRect','summary':'summaryRects',
         'result-upper':'resultRect'}[kind]
    b=state.get(key)
    if isinstance(b,list):b=b[0] if b else None
    if not isinstance(b,dict):raise ValueError('No verified anchor rectangle')
    x,y,bw,bh=[float(b[k]) for k in ('x','y','width','height')]
    if not all(map(math.isfinite,(x,y,bw,bh))) or bw<=0 or bh<=0:
        raise ValueError('Invalid source geometry')
    # Some real DOM rectangles extend a few pixels below the browser capture.
    # Intersect them with the *measured source viewport*: never extrapolate UI.
    left,top=max(0.,x),max(0.,y)
    right,bottom=min(float(w),x+bw),min(float(h),y+bh)
    visible=max(0.,right-left)*max(0.,bottom-top)/(bw*bh)
    if visible<.80 or right<=left or bottom<=top:
        raise ValueError('Verified result is mostly outside recorded source')
    return (left+right)/2,(top+(bottom-top)*.34 if kind=='result-upper'
                            else (top+bottom)/2)

@dataclass
class Shot:
    label:str
    start:int
    end:int
    keys:list
    out_start:int=0
    def length(self):return self.end-self.start

def build(manifest,edit,source_size,source_frames):
    if (manifest.get('cursorless') is not True or
        not isinstance(manifest.get('source_kind'),str) or
        not manifest['source_kind'].strip()):
        # A cursorless capture with a declared, identifiable real source is
        # required. No brand-specific screenshot, mockup or recreated pointer.
        raise ValueError('Need a verified real product recording and real pointer samples')
    stream=edit.get('shots')
    if not isinstance(stream,list) or not 3<=len(stream)<=12:
        raise ValueError('Invalid shot count')
    if len([e for e in manifest['events'] if e.get('kind')=='state_change' and e.get('evidence')])<3:
        raise ValueError('Missing multiple verified product outcomes')
    out=0;shots=[]
    for it in stream:
        a,b=it['startFrame'],it['endFrame']
        if type(a)!=int or type(b)!=int or a<0 or b>source_frames or b<=a+12:raise ValueError('Nonexistent source frames')
        keys=it.get('camera')
        if not isinstance(keys,list) or len(keys)<1:raise ValueError('Shot has no camera')
        last=-1
        for k in keys:
            if type(k.get('f'))!=int or not last<k['f']<b-a:raise ValueError('Bad keyframe order')
            last=k['f']
            z=k.get('zoom')
            if type(z) not in (float,int) or not math.isfinite(z) or not 1<=z<=3:
                raise ValueError('Unsafe camera scale')
            pose(manifest,k['anchor'],source_size)
        if keys[0]['f']!=0:raise ValueError('Camera must define initial frame')
        for bad in edit.get('unstableRanges',[]):
            x,y=bad
            if max(a,x)<=min(b-1,y):raise ValueError('EDL contains known corrupt raw browser frames')
        shots.append(Shot(str(it['label']),a,b,keys,out));out+=b-a
    if out>30*60 or out<7*60:raise ValueError('Unexpected film duration')
    return shots,out

def camera(manifest,shot,f,source_size,out_size):
    keys=shot.keys
    prev=keys[0]
    cur=prev
    u=0
    for k in keys[1:]:
        if f<k['f']:
            cur=k
            u=quintic((f-prev['f'])/(k['f']-prev['f']))
            break
        prev=k
    else:
        cur=prev
    c0=pose(manifest,prev['anchor'],source_size)
    c1=pose(manifest,cur['anchor'],source_size)
    x=c0[0]+(c1[0]-c0[0])*u
    y=c0[1]+(c1[1]-c0[1])*u
    z=prev['zoom']+(cur['zoom']-prev['zoom'])*u
    sw,sh=source_size;ow,oh=out_size
    scale=max(ow/sw,oh/sh)*z
    halfw=ow/(2*scale);halfh=oh/(2*scale)
    cx=min(sw-halfw,max(halfw,x))
    cy=min(sh-halfh,max(halfh,y))
    return np.array([[scale,0,ow/2-cx*scale],[0,scale,oh/2-cy*scale]],np.float64)

def compile_timeline(shots):
    return [{'label':s.label,'outputFrames':[s.out_start,s.out_start+s.length()],
             'sourceFrames':[s.start,s.end],
             'camera':s.keys} for s in shots]
def render(movie:Path,manifest_path:Path,edit_path:Path,output:Path,
           size=(1920,1080),limit=None,quality_gate=False,bounded_repair=False,
           motion_shutter=False,floating_stage=False,premium_cursor=False,
           click_water_ripple=False,stage_scale=.79):
    manifest=json.loads(manifest_path.read_text())
    edit=json.loads(edit_path.read_text())
    probe=json.loads(subprocess.check_output([
      'ffprobe','-v','error','-select_streams','v:0',
      '-show_entries','stream=width,height,nb_frames,avg_frame_rate',
      '-of','json',str(movie)],text=True))
    vid=probe['streams'][0]
    sw,sh=int(vid['width']),int(vid['height'])
    fps=60
    if vid['avg_frame_rate']!='60/1' or tuple(manifest['capture_rect'][k] for k in ('width','height'))!=(sw,sh):
        raise ValueError('Source pixels/frame rate do not match real capture receipt')
    source_frames=int(vid['nb_frames'])
    if source_frames<2:raise ValueError('Empty source')
    sha=hashlib.sha256(movie.read_bytes()).hexdigest()
    if manifest.get('source_sha256')!=sha:raise ValueError('Raw source hash mismatch')
    repair_log=[]
    quality_findings=[]
    if quality_gate or bounded_repair:
        from editorial_quality_gate import bounded_repair as repair_edit, inspect_editorial
        if bounded_repair:
            edit,repair_log,quality_findings=repair_edit(manifest,edit)
        else:
            quality_findings=inspect_editorial(manifest,edit)
        blockers=[f for f in quality_findings if f['level']=='reject']
        if blockers:
            raise ValueError('EDL quality gate rejected unsafe edit: '+
                             json.dumps(blockers,sort_keys=True))
    shots,total=build(manifest,edit,(sw,sh),source_frames)
    track=pointer_track(manifest,sw,sh)
    if track is None:raise ValueError('Need authentic source-timed cursor track')
    if limit is not None:
        if type(limit)!=int or not 30<=limit<=total:raise ValueError('Invalid review length')
    max_frames=min(limit or total,total)
    cursor_visibility=None
    if premium_cursor:
        from cinematic_recorded_pointer import (
            CinematicRecordedPointer,pointer_visibility_report)
        verified_clicks=[float(e['t']) for e in manifest['events']
                         if e.get('kind')=='click']
        candidate=CinematicRecordedPointer(track,verified_clicks,
                                            style='ink',film_scale=.56)
        cursor_visibility=pointer_visibility_report(
            candidate,shots,manifest,(sw,sh),size,camera,
            stage_scale if floating_stage else 1.)
        if quality_gate and (
            cursor_visibility['offscreenFrames'] or
            cursor_visibility['unrecordedOpeningFrames']):
            raise ValueError('EDL cursor visibility rejection: '+
                             json.dumps(cursor_visibility,sort_keys=True))
    output.parent.mkdir(parents=True,exist_ok=True)
    ow,oh=size
    if ow*9!=oh*16 or ow<480 or oh<270:raise ValueError('Only landscape study output')
    args=['ffmpeg','-hide_banner','-loglevel','error','-y',
          '-f','rawvideo','-pix_fmt','bgr24','-video_size',f'{ow}x{oh}',
          '-framerate','60','-i','pipe:0','-frames:v',str(max_frames),
          '-an','-c:v','libx264','-preset','veryfast','-crf','17',
          '-pix_fmt','yuv420p','-profile:v','high','-g','120',
          '-threads','5','-movflags','+faststart',str(output)]
    encoder=subprocess.Popen(args,stdin=subprocess.PIPE,stderr=subprocess.PIPE)
    cap=cv2.VideoCapture(str(movie))
    if not cap.isOpened():raise RuntimeError('Source movie could not be decoded')
    rendered=0
    lead=float(manifest['lead_s'])
    clicks=[e for e in manifest['events'] if e.get('kind')=='click']
    clicked=[float(e['t']) for e in clicks]
    pointer=None
    if premium_cursor or click_water_ripple:
        from cinematic_recorded_pointer import CinematicRecordedPointer
        pointer=CinematicRecordedPointer(track,clicked,style='ink',film_scale=.56)
    if floating_stage:
        from floating_ui_stage import floating_matrix,composite_stage
        if not .62 <= stage_scale <= .96:
            raise ValueError('Stage scale must preserve positive UI coverage')
    if click_water_ripple:
        from click_water_ripple import apply_click_water_ripple,LIFETIME_S
    def compose_camera(m,shot,f,source_size,out_size):
        matrix=camera(m,shot,f,source_size,out_size)
        return floating_matrix(matrix,out_size,stage_scale) if floating_stage else matrix
    start=time.monotonic()
    try:
        for shot in shots:
            cap.set(cv2.CAP_PROP_POS_FRAMES,shot.start)
            for j in range(shot.length()):
                if rendered>=max_frames:break
                ok,frame=cap.read()
                if not ok or frame.shape[:2]!=(sh,sw):raise RuntimeError('Real source video ended early')
                mat=compose_camera(manifest,shot,j,(sw,sh),size)
                if motion_shutter:
                    from camera_shutter import shutter_camera_warp
                    image=shutter_camera_warp(
                        frame,shot,j,manifest,(sw,sh),size,compose_camera)
                else:
                    image=cv2.warpAffine(frame,mat,(ow,oh),flags=cv2.INTER_CUBIC,
                        borderMode=cv2.BORDER_REPLICATE)
                source_time=(shot.start+j)/fps
                trace_time=source_time-lead
                if click_water_ripple:
                    # Real click hotspots are projected through the SAME
                    # camera as their source pixels, before screen clipping.
                    for action in clicks:
                        age=trace_time-float(action['t'])
                        if not 0<=age<LIFETIME_S:continue
                        x,y=pointer.click_center(float(action['t']))
                        center=mat @ (x,y,1.)
                        apply_click_water_ripple(
                            image,(float(center[0]),float(center[1])),age,
                            intensity=.75,lifetime_s=.49)
                if floating_stage:
                    image=composite_stage(image,mat,(sw,sh))
                if premium_cursor:
                    position=pointer.at(trace_time)
                    if position is not None:
                        point=mat @ (position[0],position[1],1.)
                        pointer.paint(image,(float(point[0]),float(point[1])),
                                      trace_time)
                elif trace_time>=float(track[0,0]):
                    press=max((1-quintic((trace_time-t)/.17)
                              for t in clicked if 0<=trace_time-t<.17),default=0)
                    project_pointer(image,track,mat,trace_time,scale=1.0-.09*press)
                encoder.stdin.write(image.tobytes())
                rendered+=1
                if rendered%180==0:
                    print('RENDER',rendered,'/',max_frames,
                          round(time.monotonic()-start,2),'sec',flush=True)
            if rendered>=max_frames:break
        encoder.stdin.close()
        error=encoder.stderr.read().decode(errors='replace')
        code=encoder.wait(timeout=150)
        if code:raise RuntimeError(error[-1000:])
    finally:
        cap.release()
        if encoder.poll() is None:encoder.kill()
    receipt={
      'schema':'sauce-evidence-edl-proof-v1',
      'sourceSha256':sha,'sourceFrames':source_frames,
      'sourceDpr':manifest.get('dpr'),'sourceTruth':manifest['source_kind'],
      'frames':rendered,'fps':60,
      'size':[ow,oh],'durationSeconds':rendered/60,
      'cameraSources':'measured DOM result/detail rectangles only',
      'motionShutter':bool(motion_shutter),
      'floatingStage':bool(floating_stage),
      'stageScale':float(stage_scale) if floating_stage else None,
      'premiumCursor':bool(premium_cursor),
      'cursorVisibility':cursor_visibility,
      'clickWaterRipple':bool(click_water_ripple),
      'renderSeconds':round(time.monotonic()-start,2),
      'introIsActualRecordedOutcome':bool(
          shots[0].start > max((math.floor((float(e['t'])+float(manifest.get('lead_s',0)))*60)
                               for e in manifest['events'] if e.get('kind')=='state_change'),
                              default=0)),
      'editHasNonchronologicalProofTeaser':bool(
          shots[0].start>shots[1].start),
      'shotMap':compile_timeline(shots),
      'qualityGate':{'applied':bool(quality_gate or bounded_repair),
                     'objectiveFindings':quality_findings,
                     'boundedRepairs':repair_log,
                     'creativeApproval':False},
      'sourceUrl':manifest['source']}
    output.with_suffix('.receipt.json').write_text(json.dumps(receipt,indent=2))
    subprocess.run(['ffmpeg','-v','error','-xerror','-i',str(output),
                    '-f','null','-'],check=True,timeout=120)
    print('VERIFIED_RENDER',json.dumps({'output':str(output),'frames':rendered,
          'duration':rendered/60,'seconds':receipt['renderSeconds']}),flush=True)
    return receipt

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--video',type=Path,required=True)
    parser.add_argument('--manifest',type=Path,required=True)
    parser.add_argument('--edl',type=Path,required=True)
    parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--width',type=int,default=1920)
    parser.add_argument('--height',type=int,default=1080)
    parser.add_argument('--max-frames',type=int)
    parser.add_argument('--floating-stage',action='store_true',
                        help='Compose real UI as rounded floating screen on neutral matte')
    parser.add_argument('--premium-cursor',action='store_true',
                        help='Use the existing small rounded Brimble SVG pointer')
    parser.add_argument('--click-water-ripple',action='store_true',
                        help='Refract genuine click pixels with the tested water shader')
    parser.add_argument('--stage-scale',type=float,default=.79)
    parser.add_argument('--camera-shutter',action='store_true',
                        help='Opt-in 3-sample camera-motion exposure; holds stay sharp')
    parser.add_argument('--quality-gate',action='store_true',
                        help='Reject source-true but editorially misleading films')
    parser.add_argument('--bounded-repair',action='store_true',
                        help='Only remove a future-result teaser when safely supported')
    a=parser.parse_args()
    render(a.video,a.manifest,a.edl,a.out,(a.width,a.height),a.max_frames,
           quality_gate=a.quality_gate,bounded_repair=a.bounded_repair,
           motion_shutter=a.camera_shutter,
           floating_stage=a.floating_stage,premium_cursor=a.premium_cursor,
           click_water_ripple=a.click_water_ripple,stage_scale=a.stage_scale)

if __name__=='__main__':main()
