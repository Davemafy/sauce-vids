"""Postproduce continuous public-browser footage without inventing a replay.

Source is continuous Chromium footage. The presentation compositor wraps it
in a window and may add camera motion after a verified browser event.
"""
from __future__ import annotations
import hashlib,json,os,subprocess,sys,math,shutil
from pathlib import Path
from tempfile import TemporaryDirectory
from scripts.live_edit_plan import parse_live_edit
from scripts.slider_framing import slider_framing
from scripts.session_contract import safe_url
from backend.price_narration import render_narration
from backend.native60_capture import source_video_filename
from backend.licensed_music_bed import licensed_music_from_env,add_music_to_master

sys.path.insert(0,str(Path(__file__).parents[1]/'scripts'))
from produce_cinematic_demo import verify_mp4,build_web_player

def file_digest(path):
 h=hashlib.sha256()
 with Path(path).open('rb') as inp:
  for chunk in iter(lambda:inp.read(2**20),b''):h.update(chunk)
 return h.hexdigest()

def evaluate_encoded_customer_film(master:Path,source_dir:Path,receipt:dict,duration:float,out:Path,
                                   *,source_trim_seconds:float=0.):
 """Evaluate EVERY real customer master, not only passive cloud overviews.

 A film's source must still be a verified Chromium recording. This only
 supplies a technical reject/review receipt, never creative approval.
 """
 from scripts.quality_preview_supervisor import analyze
 if (receipt.get("continuous_recording") is not True or
     not isinstance(receipt.get("sha256"),str) or
     receipt["sha256"]!=file_digest(Path(source_dir)/source_video_filename(receipt))):
  raise ValueError("Unverified original continuous source")
 record=Path(source_dir)/"continuous-capture.json"
 if not record.is_file():
  raise ValueError("Missing real capture receipt")
 quality=analyze(Path(master),evidence={
   "source_path":str(Path(source_dir)/source_video_filename(receipt)),
   "source_sha256":receipt["sha256"],
   "event_manifest_path":str(record),
   "event_manifest_sha256":file_digest(record),
   "source_trim_seconds":source_trim_seconds},seconds=duration)
 if quality.get("verdict") not in ("REJECT","HUMAN_REVIEW_REQUIRED"):
  raise ValueError("Encoded quality gate returned an untrusted verdict")
 if not isinstance(quality.get("findings"),list):
  raise ValueError("Encoded quality findings missing")
 out=Path(out)
 (out/"encoded-quality.json").write_text(json.dumps(quality,indent=2)+"\n")
 return {"encoded_quality_verdict":quality["verdict"],
         "encoded_quality_findings":[x["code"] for x in quality["findings"]],
         "creative_approved":False}

def probe(src):
 return json.loads(subprocess.check_output(['ffprobe','-v','error',
   '-show_entries','stream=codec_type,codec_name,width,height,r_frame_rate,nb_frames:format=duration',
   '-of','json',str(src)],text=True,timeout=20))

def source_video_profile(stream:dict,receipt:dict):
 """Validate real recorded dimensions, then select native-source encoding.

 No input is silently upscaled and mislabeled as a high-resolution capture.
 The legacy 720p pilot remains supported without changing its receipts.
 """
 size=[stream.get('width'),stream.get('height')]
 if size not in ([1280,720],[1920,1080]):
  raise RuntimeError('Invalid browser footage dimensions')
 expected=receipt.get('requested_video_size')
 if expected and size != [expected.get('width'),expected.get('height')]:
  raise RuntimeError('Recorded footage differs from verified capture size')
 quality=receipt.get('capture_quality','standard')
 dpr=receipt.get('source_dpr',1)
 native_proof=receipt.get('native_source_capture')
 if native_proof is not None:
  if (not isinstance(native_proof,dict) or
      native_proof.get('source_capture_method')!='x11grab60-original-browser' or
      native_proof.get('source_fps')!='60/1' or
      receipt.get('video')!='continuous-source.mp4' or
      stream.get('r_frame_rate')!='60/1' or
      not isinstance(native_proof.get('viewport_match_error'),(int,float)) or
      not 0<=native_proof['viewport_match_error']<=11):
   raise RuntimeError('Native60 browser recording provenance mismatch')
 if quality=='high' and (size!=[1920,1080] or dpr!=2):
  raise RuntimeError('High-density source proof mismatch')
 # Playwright pads a 1920x1080 record_video frame if the captured CSS
 # viewport is only 1280x720. Validate the *actual CSS capture viewport*
 # before accepting the high-density label; container dimensions alone
 # cannot establish sharp, full-frame source footage.
 viewport=receipt.get('viewport_css_size')
 if quality=='high' and (
     not isinstance(viewport,dict)
     or viewport.get('width') != 1920
     or viewport.get('height') != 1080):
  raise RuntimeError('High-density CSS viewport does not fill recorded frame')
 native=size==[1920,1080]
 filter_graph=('setsar=1,fps=60,format=yuv420p' if native
               else 'scale=1920:1080:flags=lanczos,setsar=1,fps=60,format=yuv420p')
 return {'dimensions':size,'native_1080p':native,'source_dpr':dpr,
         'source_fps':stream.get('r_frame_rate'),'filter':filter_graph}


def verified_action_intro_trim(editorial_events, original_trim, *, pre_click_seconds=.55):
    """Keep real recorded approach footage without a largely static opener.

    Read-only postproduction helper: only trim if a verified source click has
    a separately recorded visible DOM result within 1.8 seconds. This never
    inserts action frames, invents an outcome, or retimes the original event.
    """
    if (type(original_trim) not in (int,float) or
        not math.isfinite(original_trim) or original_trim<0):
        raise ValueError("Invalid real source trim")
    clicks=[e for e in editorial_events if
            isinstance(e,dict) and e.get('kind')=='click'
            and isinstance(e.get('semanticGoal'),str) and e['semanticGoal'].strip()
            and type(e.get('t')) in (float,int) and math.isfinite(e['t'])]
    for click in clicks:
        t=click['t']
        outcome=next((e for e in editorial_events if
                      isinstance(e,dict) and e.get('kind')=='state_change'
                      and isinstance(e.get('evidence'),str) and e['evidence'].strip()
                      and isinstance(e.get('resultRect'),dict)
                      and type(e.get('t')) in (float,int) and
                      math.isfinite(e['t']) and t<=e['t']<=t+1.8),None)
        if outcome is not None and t>0 and t>=original_trim:
            return round(max(original_trim,t-pre_click_seconds),3)
    return original_trim


def render(source_dir:Path,out:Path,title:str,story:str,mode:str, *, brief="", audio="auto", edit_plan=None, cursor_pack="founder-reference"):
 source_dir=Path(source_dir);out=Path(out)
 if edit_plan is None:
  return _render(source_dir,out,title,story,mode,brief,audio,source_dir,None,cursor_pack)
 out.mkdir(parents=True,exist_ok=True)
 with TemporaryDirectory(prefix='.sauce-edit-',dir=out) as work:
  return _render(source_dir,out,title,story,mode,brief,audio,Path(work),edit_plan,cursor_pack)


def _render(source_dir,out,title,story,mode,brief,audio,work,edit_plan,cursor_pack="founder-reference"):
 receipt=json.loads((source_dir/'continuous-capture.json').read_text())
 src=source_dir/source_video_filename(receipt)
 if not src.is_file() or file_digest(src)!=receipt['sha256']:
  raise RuntimeError('Continuous browser evidence missing or modified')
 evidence=probe(src)
 stream=next((s for s in evidence['streams'] if s.get('codec_type')=='video'),None)
 if not stream:raise RuntimeError('No recorded browser video stream')
 profile=source_video_profile(stream,receipt)
 plan=parse_live_edit(edit_plan,receipt) if edit_plan is not None else None
 if plan:
  if mode!='interactive' or receipt.get('subject_shots'):
   raise ValueError('A live edit requires a single interactive capture')
  audio=plan.audio
 full_duration=float(evidence['format']['duration'])
 if full_duration<1.7 or full_duration>75:raise RuntimeError('Invalid live source duration')
 # Playwright starts the recorder before the initial page is ready. Remove
 # that dead-air loading time, retaining a short establishing lead-in.
 trim=max(0,min(full_duration-2.0,float(receipt.get('lead_in_seconds',0))-0.40))
 initial_trim=trim
 cursorless=receipt.get('cursorless') is True
 loupe=cursorless and not plan and os.getenv('SAUCE_SLIDER_LOUPE')=='1'
 if mode=='interactive' and not cursorless:
  trim=verified_action_intro_trim(receipt.get('editorial_events',[]),trim)
 if cursorless:
  slider=next(event for event in receipt['editorial_events']
              if event['kind']=='slider_change')
  # Keep enough pre-gesture context and finish on the verified price hold.
  trim=round(max(trim,slider['start']-(plan.lead if plan else .92 if loupe else 1.60)),3)
  end=slider['end']+(plan.hold if plan else 2.70 if loupe else 3.55)
  if plan and end>full_duration+1e-9:
   raise ValueError('Capture ends before the requested result hold')
  full_duration=min(full_duration,end)
 duration=full_duration-trim
 plan_camera={}
 if plan:
  event=next(e for e in receipt['editorial_events'] if e['kind']=='slider_change')
  _,fit,_,_=slider_framing(event,*profile['dimensions'])
  plan_camera={'keys':plan.camera_timeline(event['t']-trim,duration,fit),
               'cursor_scale':plan.cursor_scale}
 out.mkdir(parents=True,exist_ok=True)
 master=out/'master-1080p60.mp4'
 prepared=work/'presentation-source.mp4'
 # Frame-rate conversion keeps the original browser timing; no freeze-frame
 # montages, transition slides or synthesized screenshots.
 command=['ffmpeg','-hide_banner','-loglevel','error','-y','-nostdin',
  '-ss',str(round(trim,3)),'-i',str(src),'-t',str(round(duration,3)),'-map','0:v:0',
  '-vf',profile['filter'],
  '-an','-c:v','libx264','-preset','medium','-crf','17',
  '-movflags','+faststart','-progress','pipe:1',str(prepared)]
 subjects=receipt.get('subject_shots',[])
 if subjects:
  if mode!='showcase' or cursorless or receipt.get('editorial_events'):
   raise RuntimeError('Subject cuts must not edit interaction footage')
  filters=[]
  for i,shot in enumerate(subjects):
   start,frames,x,y,w,h=shot['start'],shot['frames'],*shot['crop']
   if start<0 or start+frames/60>full_duration or frames!=112:
    raise RuntimeError('Subject footage is outside the source timeline')
   phase='min(on/111,1)'
   zoom=f"1+{shot['zoom_delta']:.6f}*(.26+.74*(3*{phase}*{phase}-2*{phase}*{phase}*{phase}))"
   filters.append(
    f"[0:v]trim=start={start:.4f},setpts=PTS-STARTPTS,fps=60,trim=end_frame={frames},"
    f"crop={w}:{h}:{x}:{y},scale=2560:1440:flags=lanczos,"
    f"zoompan=z='{zoom}':x='iw/2-iw/zoom/2':y='ih/2-ih/zoom/2':"
    f"d=1:s=1920x1080:fps=60,setsar=1,format=yuv420p[s{i}]")
  filters.append(''.join(f'[s{i}]' for i in range(len(subjects)))+
                 f'concat=n={len(subjects)}:v=1:a=0[reel]')
  duration=sum(s['frames'] for s in subjects)/60
  command=['ffmpeg','-hide_banner','-loglevel','error','-y','-nostdin',
           '-filter_complex_threads','2','-i',str(src),'-filter_complex',';'.join(filters),
           '-map','[reel]','-an','-c:v','libx264','-preset','veryfast','-crf','17',
           '-movflags','+faststart','-progress','pipe:1',str(prepared)]
 total=max(1,int(round(duration*60)))
 worker=subprocess.Popen(command,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
 if not worker.stdout:raise RuntimeError('Video encoder did not open progress pipe')
 last=0
 for line in worker.stdout:
  if line.startswith('frame='):
   try:count=int(line.partition('=')[2])
   except ValueError:continue
   if count>last:
    last=count
    print(f'REPLAY {min(count,total)} of {2*total}',flush=True)
 errors=worker.stderr.read() if worker.stderr else ''
 if worker.wait(timeout=190)!=0:raise RuntimeError('Continuous video encoding failed: '+errors[-300:])
 composed=work/'composed-master.mp4'
 manifest=work/'presentation.json'
 events=[]
 w,h=profile['dimensions']
 sx,sy=1920/w,1080/h
 for raw in receipt.get('editorial_events',[]):
  event={**raw}
  for key in ('t','start','end'):
   if key in event:
    event[key]=max(0.,event[key]-trim)
  for key in ('resultRect','targetRect'):
   if key in event:
    event[key]={k:v*(sx if k in ('x','width') else sy)
                for k,v in event[key].items()}
  if 'pointer_samples' in event:
   event['pointer_samples']=[
    {'t':p['t']-trim,'x':p['x']*sx,'y':p['y']*sy}
    for p in event['pointer_samples']]
  events.append(event)
 manifest.write_text(json.dumps({'source':safe_url(receipt['source_url']),
  'cursorless':cursorless,'events':events,'edit_camera':plan_camera,'capture_rect':{'width':1920,'height':1080},
  'pointer_samples':next((e['pointer_samples'] for e in events if e['kind']=='slider_change'), [])}))
 from scripts.recorded_pointer import CURSOR_PACKS
 # Legacy jobs have a cursor already baked into the browser's source pixels.
 # The compositor does not understand their old 'circle'/'arrow' names, so
 # map only that inactive overlay setting to a reproducible legacy glyph.
 compositor_cursor=cursor_pack if cursor_pack in CURSOR_PACKS else 'tabler-legacy'
 command=[sys.executable,str(Path(__file__).resolve().parents[1]/'scripts/render_event_video.py'),
    '--video',str(prepared),'--manifest',str(manifest),'--output',str(composed),
    '--cursor-pack',compositor_cursor,
    '--camera-profile','action-first','--presentation','window']
 # Customer stage is an EXPLICIT opt-in, not a speculative visual switch.
 # Original source, capture clock, source cursor and verified result remain
 # intact; only the surrounding studio and whole-browser camera differ.
 stage=os.getenv('SAUCE_CUSTOMER_STAGE','')
 if stage not in ('','cloud_window_fullglass_v1'):
  raise ValueError('Unsupported opt-in Sauce customer stage')
 customer_cloud=(stage=='cloud_window_fullglass_v1')
 if customer_cloud:
  if mode!='interactive' or cursorless or subjects or plan:
   raise ValueError('Full-glass customer stage requires one verified click outcome')
  command.append('--customer-cloud-stage')
 cloud_overview=(mode=='showcase' and not events and not cursorless and not subjects)
 if cloud_overview:
  command+=['--cloud-overview']
 if loupe:
  command+=['--glass-loupe']
 elif cursorless:
  command[-1]='fullscreen'
  command+=['--slider-framing','--recorded-pointer']
 with (work/'presentation.log').open('w') as log:
  subprocess.run(command,check=True,stdout=log,stderr=subprocess.STDOUT,timeout=240)
 print(f'REPLAY {2*total} of {2*total}',flush=True)
 metrics=json.loads((work/'camera-metrics.json').read_text())
 if loupe and not metrics['glass_loupe_shots']:
  raise RuntimeError('Recorded slider evidence could not produce a glass shot')
 if (not cursorless or loupe) and not cloud_overview and not customer_cloud:
  shutil.copyfile(work/'SHOTCANDY-LICENSE.txt',out/'SHOTCANDY-LICENSE.txt')
 composed.replace(master)
 verify_mp4(master,1920,1080,60)
 # Opt-in, source/license-verified real music. Never synthesize empty audio,
 # change the source cursor, or mix over source-grounded speech.
 music=None
 if audio=='auto' and not any(
     e.get('kind')=='slider_change' and e.get('price_change') for e in events):
  music=licensed_music_from_env()
  if music:
   add_music_to_master(master,music,duration)
   verify_mp4(master,1920,1080,60)
 if subjects:
  stream=next(s for s in probe(master)['streams'] if s['codec_type']=='video')
  if int(stream.get('nb_frames',0))!=total:
   raise RuntimeError('Encoded subject reel does not match its planned frame count')
 preview=out/'preview.mp4'
 subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y','-nostdin',
  '-i',str(master),'-map','0:v:0','-map','0:a:0?',
  '-vf','scale=1280:720:flags=lanczos,fps=30',
  '-c:a','aac','-ar','48000','-b:a','128k',
  '-c:v','libx264','-preset','medium','-crf','18',
  '-pix_fmt','yuv420p','-movflags','+faststart',str(preview)],
  check=True,timeout=110)
 verify_mp4(preview,1280,720,30)
 narration=render_narration(work,events,float(probe(preview)['format']['duration']),brief,audio)
 if narration:
  clean=out/'preview-clean.mp4'
  preview.replace(clean)
  subprocess.run(['ffmpeg','-v','error','-xerror','-nostdin','-y','-i',str(clean),
    '-i',str(narration),'-map','0:v:0','-map','1:a:0','-c:v','copy','-c:a','aac',
    '-ar','48000','-b:a','96k','-af','apad','-shortest','-movflags','+faststart',str(preview)],
    check=True,timeout=35)
  verify_mp4(preview,1280,720,30)
  if not any(x.get('codec_type')=='audio' for x in probe(preview)['streams']):
   raise RuntimeError('Narrated export is missing audio')
 poster=out/'poster.jpg'
 subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y','-nostdin',
  '-ss',str(min(2.2,max(.25,duration*.3))),'-i',str(master),
  '-frames:v','1','-vf','scale=1280:720:flags=lanczos',
  '-q:v','3',str(poster)],check=True,timeout=30)
 if not poster.is_file():raise RuntimeError('Poster export missing')
 build_web_player(Path(__file__).parents[1]/'docs/sauce-premium-player-template.html',
                   out,title,story,duration)
 result={
  'render_mode':'continuous-browser-capture','presentation':('source-true-cobalt-glass'
       if customer_cloud else 'cloud-shadow-overview' if cloud_overview
       else 'slider-framing' if cursorless and not loupe else 'floating-browser'),
  'verified_camera_shots':metrics['zoom_shots'],
  'subject_shot_count':len(subjects),
  'verified_glass_shots':metrics['glass_loupe_shots'],'source_url':safe_url(receipt['source_url']),
  'licensed_music':music.public_receipt() if music else None,
  'music_only':bool(music),
  'title':title,'description':story,'film_mode':mode,'duration_seconds':round(duration,2),
  'discarded_initial_loading_seconds':round(initial_trim,2),
  'discarded_before_action_seconds':round(trim-initial_trim,2),
  'source_sha256':receipt['sha256'],
  'source_pixel_stream_recorded':True,
  'recorded_source_dimensions':profile['dimensions'],
  'recorded_source_fps':profile['source_fps'],
  'recorded_source_dpr':profile['source_dpr'],
  'native_1080p_source':profile['native_1080p'],
  'presentation_cursor':receipt.get('presentation_cursor','circle'),
  'cursor_pack':cursor_pack,
  'continuous_motion':True,'source_verified':True,'replay_verified':False,
  'native60_source_verified':bool(profile['source_fps']=='60/1' and
                                  receipt.get('native_source_capture')),
  'source_capture_method':('x11grab60-original-browser'
       if receipt.get('native_source_capture') else 'playwright-video-helper'),
  'observed_actions':receipt['actions'],
  'master_dimensions':[1920,1080],'master_fps':60,'preview_dimensions':[1280,720],
  'preview_fps':30,'narrated':narration is not None,'clean_preview':bool(narration),'limitations':[
   'A continuous Chromium recording is actual UI motion, not a deterministic DOM replay.',
   ('Native 60Hz X11 source captures original Chrome compositing frames; '
   'static source frames may remain unchanged and no animation is invented.'
   if receipt.get('native_source_capture')
   else 'Master 60fps resamples the browser recorder frame rate; it does not create new UI frames.'),
   'Controls behind authentication and sensitive form submission are not explored.']}
 if plan:
  result['edit_plan']={'schema':edit_plan['schema'],
                       'checksum':hashlib.sha256(json.dumps(edit_plan,sort_keys=True).encode()).hexdigest(),
                       'resolved_camera':plan_camera}
 result.update(evaluate_encoded_customer_film(
   master,source_dir,receipt,duration,out,source_trim_seconds=trim))
 (out/'release.json').write_text(json.dumps(result,indent=2))
 return result

if __name__=='__main__':
 import argparse
 p=argparse.ArgumentParser()
 p.add_argument('--source',type=Path,required=True)
 p.add_argument('--out',type=Path,required=True)
 p.add_argument('--title',default='Website demo')
 p.add_argument('--story',default='Recorded public website')
 p.add_argument('--mode',default='public_showcase')
 p.add_argument('--brief',default='')
 p.add_argument('--audio',choices=('auto','clean','narrated'),default='auto')
 from backend.cursor_capture_js import CURSOR_STYLES
 p.add_argument('--cursor-pack',choices=(*CURSOR_STYLES,'arrow','circle'),default='founder-reference')
 p.add_argument('--edit-plan',type=Path,help='Versioned JSON bound to the verified capture SHA-256')
 a=p.parse_args()
 try:
  print(json.dumps(render(a.source,a.out,a.title,a.story,a.mode,brief=a.brief,audio=a.audio,
                          edit_plan=json.loads(a.edit_plan.read_text()) if a.edit_plan else None,
                          cursor_pack=a.cursor_pack)),flush=True)
 except subprocess.TimeoutExpired as exc:
  print(f'Render stage exceeded {exc.timeout}s',file=sys.stderr)
  raise SystemExit(124) from exc
