#!/usr/bin/env python3
"""Render a 20–40s storyboard from SHA-verified Sauce capture states.

Examples:
  python scripts/render_scripted_v2.py --script demos/brimble-v2.json --out studio/.tmp/script-v2
  python scripts/render_scripted_v2.py --script demos/brimble-v2.json --out studio/.tmp/script-v2-1440 --resolution 1440p --silent
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time

import cv2
import numpy as np
from PIL import Image, ImageDraw

from scripted_v2_schema import load_script,FPS
from scripted_v2_render import ScriptedV2Compositor,iter_story_frames
from scripted_v2_audio import make_soundtrack,mux_sound,measured_lufs


def _contact_sheet(samples,output:Path,size,step=24):
    width,height=size
    cols=5
    thumb_width=420
    thumb_height=int(thumb_width*height/width)
    rows=(len(samples)+cols-1)//cols
    result=Image.new('RGB',(cols*thumb_width,rows*(thumb_height+25)),(236,238,242))
    draw=ImageDraw.Draw(result)
    for i,(n,thumbnail) in enumerate(samples):
        x=(i%cols)*thumb_width
        y=(i//cols)*(thumb_height+25)
        result.paste(Image.fromarray(cv2.cvtColor(thumbnail,cv2.COLOR_BGR2RGB)),(x,y+25))
        draw.text((x+8,y+6),f'{n/FPS:.1f}s / frame {n}',fill=(30,35,43))
    result.save(output,quality=91)


def render(script:Path,out_dir:Path,resolution:str='1080p',
           voice:Path|None=None,music:Path|None=None,
           bed:bool=False,silent:bool=False):
    session_dir,session,shots,total=load_script(script)
    width,height={'1080p':(1920,1080),'1440p':(2560,1440)}[resolution]
    out_dir=out_dir.resolve()
    # Prevent untrusted raw captures from being copied into a public export.
    if session_dir==out_dir or session_dir.is_relative_to(out_dir) or out_dir.is_relative_to(session_dir):
        raise ValueError("Output and private screenshot capture must be separate")
    out_dir.mkdir(parents=True,exist_ok=True)
    compositor=ScriptedV2Compositor(session_dir,session,(width,height))
    raw_video=out_dir/'.video-only.tmp.mp4'
    master=out_dir/('master-1080p60.mp4' if resolution=='1080p' else 'master-1440p60.mp4')
    stderr_log=out_dir/'ffmpeg-encode.log'
    # Constant-frame-rate 60fps rawvideo pipe: machine speed never changes
    # the number or presentation time of a single output frame.
    command=['ffmpeg','-hide_banner','-loglevel','error','-y','-nostdin',
        '-f','rawvideo','-pix_fmt','bgr24','-s',f'{width}x{height}',
        '-framerate',str(FPS),'-i','pipe:0','-an',
        # True decoded-frame identity is more stringent than raw-frame hashes.
        # Lossless QP=0 avoids CRF's minute GOP-dependent pixel variations on
        # a 1.5s still hold; the separate mobile preview uses High-profile CRF.
        '-c:v','libx264','-preset','fast','-qp','0','-bf','0',
        '-g','300','-sc_threshold','0','-threads','6',
        '-pix_fmt','yuv420p','-r',str(FPS),
        '-color_primaries','bt709','-color_trc','bt709','-colorspace','bt709',
        '-movflags','+faststart',str(raw_video)]
    hashes=[]
    snapshots=[]
    start=time.monotonic()
    with stderr_log.open('wb') as err:
        process=subprocess.Popen(command,stdin=subprocess.PIPE,stderr=err)
        try:
            if process.stdin is None:raise RuntimeError("FFmpeg pipe unavailable")
            for n,frame in iter_story_frames(compositor,shots):
                if frame.shape!=(height,width,3):
                    raise RuntimeError(f"Unexpected frame dimensions at {n}")
                data=frame.tobytes(order='C')
                hashes.append(hashlib.sha256(data).hexdigest())
                process.stdin.write(data)
                if n%24==0:
                    thumb=cv2.resize(frame,(420,round(420*height/width)),
                                     interpolation=cv2.INTER_AREA)
                    snapshots.append((n,thumb))
                if n==0:
                    cv2.imwrite(str(out_dir/'first-frame-100pct.png'),frame)
                if n==total-1:
                    cv2.imwrite(str(out_dir/'final-frame-100pct.png'),frame)
                if n%240==0:
                    print(f"FRAME {n}/{total} wall={time.monotonic()-start:.1f}s",flush=True)
            process.stdin.close()
            code=process.wait(timeout=120)
            if code:raise RuntimeError(f"FFmpeg encode failed; see {stderr_log}")
        except Exception:
            if process.poll() is None:process.kill()
            raise
    if len(hashes)!=total:
        raise RuntimeError("Missing or duplicated scripted video frame")
    # Freeze the observed source pixels for at least the last 60 frames.
    end_hold=shots[-1].hold_frames
    if len(set(hashes[-end_hold:]))!=1:
        raise RuntimeError("Final result must be fully identical, not blurred or animated")
    _contact_sheet(snapshots,out_dir/'contact-every-0.4s.jpg',(width,height))
    (out_dir/'frame-sha256.json').write_text(json.dumps(hashes))
    sound_result={}
    with tempfile.TemporaryDirectory(prefix='.sauce-v2-audio-',dir=out_dir.parent) as tmp:
        wav=Path(tmp)/'audio.wav'
        sound_result=make_soundtrack(wav,total,voice,music,bed,silent)
        sound_result.update(mux_sound(raw_video,wav,master,total,sound_result['silent']))
    raw_video.unlink()
    ffprobe=json.loads(subprocess.check_output([
        'ffprobe','-v','error','-show_entries',
        'stream=codec_type,codec_name,width,height,r_frame_rate,nb_frames,sample_rate:format=duration',
        '-of','json',str(master)],text=True))
    video=next(v for v in ffprobe['streams'] if v.get('codec_type')=='video')
    audio=next(v for v in ffprobe['streams'] if v.get('codec_type')=='audio')
    if (video['width'],video['height'],video['r_frame_rate'],int(video['nb_frames']))!=(
        width,height,'60/1',total):
        raise RuntimeError("Final MP4 is not a complete 60fps master")
    if video['codec_name']!='h264' or audio['codec_name']!='aac' or audio['sample_rate']!='48000':
        raise RuntimeError("Master must contain H264 + AAC/48kHz")
    subprocess.run(['ffmpeg','-v','error','-xerror','-i',str(master),
        '-f','null','-'],check=True,timeout=180)
    # MP4 decoder acceptance: all last 1.0–1.5 seconds must be byte-identical
    # AFTER H.264 decode, not merely before encoder quantization.
    tail=subprocess.run(['ffmpeg','-v','error','-nostdin','-i',str(master),
       '-an','-vf',f'select=gte(n\\,{total-end_hold})',
       '-vsync','0','-f','framemd5','-'],capture_output=True,text=True,
       check=True,timeout=90)
    decoded=[row.rsplit(',',1)[-1].strip() for row in tail.stdout.splitlines()
             if row.startswith('0,')]
    if len(decoded)!=end_hold or len(set(decoded))!=1:
        raise RuntimeError(f'Decoded final-hold mismatch: '
                           f'{len(decoded)} frames, {len(set(decoded))} unique')
    lufs=measured_lufs(master)
    if not silent and (voice or music or bed) and (lufs is None or abs(lufs+16)>1):
        raise RuntimeError(f"EBU R128 loudness exceeds target tolerance: {lufs}")
    proof={
      'schema':'sauce-scripted-demo-v2-receipt',
      'scriptSHA256':hashlib.sha256(script.read_bytes()).hexdigest(),
      'sourceManifestSHA256':hashlib.sha256((session_dir/'session.json').read_bytes()).hexdigest(),
      'sourceDPR':session['page']['dpr'],'stateCount':len(session['states']),
      'resolution':[width,height],'fps':FPS,'frames':total,
      'durationSeconds':total/FPS,'master':master.name,
      'sha256':hashlib.sha256(master.read_bytes()).hexdigest(),
      'noTilt':True,'fixedStageWindow':True,'cameraEasing':'quintic zero-velocity endpoints',
      'finalHoldFrames':end_hold,'finalHoldIdentical':True,
      'decodedFinalHoldUniqueFrames':len(set(decoded)),
      'decodedFinalHoldFrameCount':len(decoded),
      'finalFrameSHA256':hashes[-1],
      'captionAndCalloutSource':'authored over actual verified UI states',
      'terminalConcealment':'presentation-only mask of captured terminal, no invented UI',
      'audio':dict(sound_result,measuredLUFS=lufs),
      'shots':[{'index':s.index,'state':s.state,'action':s.action,
                'moveFrames':s.transition_frames,'holdFrames':s.hold_frames,
                'zoom':s.zoom,'target':s.target,'terminalHidden':s.hide_terminal,
                'redactedRegions':len(s.blur_regions)} for s in shots]
    }
    (out_dir/'release.json').write_text(json.dumps(proof,indent=2))
    print(json.dumps({'master':str(master),'sha256':proof['sha256'],
          'frames':total,'duration':total/FPS,'LUFS':lufs,
          'finalHoldIdentical':True,'contact':str(out_dir/'contact-every-0.4s.jpg')},
          indent=2),flush=True)
    return proof


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--script',type=Path,required=True)
    parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--resolution',choices=('1080p','1440p'),default='1080p')
    parser.add_argument('--voice',type=Path,default=None,
                        help='Optional authorized local voiceover WAV/MP3/OGG')
    parser.add_argument('--music',type=Path,default=None,
                        help='Optional authorized local music bed')
    parser.add_argument('--original-bed',action='store_true',
                        help='Generate a subtle original three-tone ambient bed')
    parser.add_argument('--silent',action='store_true',
                        help='Output an actual silent 48kHz AAC stream')
    args=parser.parse_args()
    if args.original_bed and args.music:parser.error('Select one music bed')
    render(args.script,args.out,args.resolution,args.voice,args.music,
           args.original_bed,args.silent)


if __name__=='__main__':main()
