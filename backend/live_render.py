"""Postproduce continuous public-browser footage without inventing a replay.

Camera motion is the actual Chromium browser motion. This intentionally does
not masquerade as the deterministic replay compositor: source, duration,
motion and SHA are recorded in the release ledger.
"""
from __future__ import annotations
import hashlib,json,subprocess,sys,math
from pathlib import Path
from scripts.session_contract import safe_url

sys.path.insert(0,str(Path(__file__).parents[1]/'scripts'))
from produce_cinematic_demo import verify_mp4,build_web_player

def file_digest(path):
 h=hashlib.sha256()
 with Path(path).open('rb') as inp:
  for chunk in iter(lambda:inp.read(2**20),b''):h.update(chunk)
 return h.hexdigest()

def probe(src):
 return json.loads(subprocess.check_output(['ffprobe','-v','error',
   '-show_entries','stream=codec_type,codec_name,width,height,r_frame_rate:format=duration',
   '-of','json',str(src)],text=True,timeout=20))

def render(source_dir:Path,out:Path,title:str,story:str,mode:str):
 source_dir=Path(source_dir);out=Path(out)
 receipt=json.loads((source_dir/'continuous-capture.json').read_text())
 src=source_dir/'continuous-source.webm'
 if not src.is_file() or file_digest(src)!=receipt['sha256']:
  raise RuntimeError('Continuous browser evidence missing or modified')
 evidence=probe(src)
 stream=next((s for s in evidence['streams'] if s.get('codec_type')=='video'),None)
 if not stream or stream['width']!=1280 or stream['height']!=720:
  raise RuntimeError('Invalid browser footage dimensions')
 full_duration=float(evidence['format']['duration'])
 if full_duration<1.7 or full_duration>75:raise RuntimeError('Invalid live source duration')
 # Playwright starts the recorder before the initial page is ready. Remove
 # that dead-air loading time, retaining a short establishing lead-in.
 trim=max(0,min(full_duration-2.0,float(receipt.get('lead_in_seconds',0))-0.40))
 duration=full_duration-trim
 out.mkdir(parents=True,exist_ok=True)
 master=out/'master-1080p60.mp4'
 # Frame-rate conversion keeps the original browser timing; no freeze-frame
 # montages, transition slides or synthesized screenshots.
 command=['ffmpeg','-hide_banner','-loglevel','error','-y','-nostdin',
  '-ss',str(round(trim,3)),'-i',str(src),'-map','0:v:0',
  '-vf','scale=1920:1080:flags=lanczos,setsar=1,fps=60,format=yuv420p',
  '-an','-c:v','libx264','-preset','medium','-crf','17',
  '-movflags','+faststart','-progress','pipe:1',str(master)]
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
    print(f'REPLAY {min(count,total)} of {total}',flush=True)
 errors=worker.stderr.read() if worker.stderr else ''
 if worker.wait(timeout=190)!=0:raise RuntimeError('Continuous video encoding failed: '+errors[-300:])
 verify_mp4(master,1920,1080,60)
 preview=out/'preview.mp4'
 subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y','-nostdin',
  '-i',str(master),'-map','0:v:0',
  '-vf','scale=1280:720:flags=lanczos,fps=30',
  '-an','-c:v','libx264','-preset','medium','-crf','18',
  '-pix_fmt','yuv420p','-movflags','+faststart',str(preview)],
  check=True,timeout=110)
 verify_mp4(preview,1280,720,30)
 poster=out/'poster.jpg'
 subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y','-nostdin',
  '-ss',str(min(2.2,max(.25,duration*.3))),'-i',str(master),
  '-frames:v','1','-vf','scale=1280:720:flags=lanczos',
  '-q:v','3',str(poster)],check=True,timeout=30)
 if not poster.is_file():raise RuntimeError('Poster export missing')
 build_web_player(Path(__file__).parents[1]/'docs/sauce-premium-player-template.html',
                   out,title,story,duration)
 result={
  'render_mode':'continuous-browser-capture','source_url':safe_url(receipt['source_url']),
  'title':title,'description':story,'film_mode':mode,'duration_seconds':round(duration,2),
  'discarded_initial_loading_seconds':round(trim,2),
  'source_sha256':receipt['sha256'],
  'source_pixel_stream_recorded':True,
  'continuous_motion':True,'source_verified':True,'replay_verified':False,
  'observed_actions':receipt['actions'],
  'master_dimensions':[1920,1080],'master_fps':60,'preview_dimensions':[1280,720],
  'preview_fps':30,'limitations':[
   'A continuous Chromium recording is actual UI motion, not a deterministic DOM replay.',
   'Master 60fps resamples the browser recorder frame rate; it does not create new UI frames.',
   'Controls behind authentication and sensitive form submission are not explored.']}
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
 a=p.parse_args()
 print(json.dumps(render(a.source,a.out,a.title,a.story,a.mode)),flush=True)
