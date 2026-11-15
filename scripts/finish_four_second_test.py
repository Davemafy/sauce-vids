#!/usr/bin/env python3
"""Finish a real four-second, narrated product shot with restrained captions.

Consumes Sauce's verified 60fps replay, preserves recorded VO and clicks,
then adds only typographic captions in the dark gutter below the window.
The third-party benchmark clip remains private and is NEVER republished.
"""
from __future__ import annotations
import argparse,json,subprocess,os
from pathlib import Path


def timestamp(sec:float)->str:
    if sec<0:raise ValueError('Subtitle time cannot be negative')
    centiseconds=round(sec*100)
    whole,cs=divmod(centiseconds,100)
    return f"{whole//3600}:{whole//60%60:02d}:{whole%60:02d}.{cs:02d}"


def ass_document(cues:list[dict])->str:
    lines=[
        '[Script Info]','Title: Sauce — narrated 4-second product film',
        'ScriptType: v4.00+','PlayResX: 1920','PlayResY: 1080',
        'WrapStyle: 2','ScaledBorderAndShadow: yes','','[V4+ Styles]',
        'Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding',
        'Style: Caption,Inter,37,&H00F5F2ED,&H00F5F2ED,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,0,0,2,60,60,46,1',
        '','[Events]',
        'Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text'
    ]
    for cue in cues:
        text=cue['text'].replace('\\','').replace('{','').replace('}','').replace('\n',' ')
        lines.append(f"Dialogue: 0,{timestamp(float(cue['start']))},{timestamp(float(cue['end']))},Caption,,0,0,0,,{{\\fad(170,170)}}{text}")
    return '\n'.join(lines)+'\n'


def probe(path:Path)->dict:
    return json.loads(subprocess.check_output([
        'ffprobe','-v','error',
        '-show_entries','stream=codec_type,width,height,r_frame_rate,nb_frames,sample_rate:format=duration',
        '-of','json',str(path)],text=True))


def finish(directory:Path,cues_json:Path)->dict:
    before=directory/'master-1080p60.mp4'
    meta=json.loads(cues_json.read_text())
    cues=meta['lines']
    if [i['id'] for i in cues]!=['connect','copy']:
        raise ValueError('This film must contain exactly two verified narration beats')
    if any(not 0<=x['start']<x['end']<=4 for x in cues):
        raise ValueError('Caption timing outside four-second film')
    (directory/'captions.ass').write_text(ass_document(cues))
    output=directory/'captioned-master.mp4'
    subprocess.run([
        'ffmpeg','-hide_banner','-loglevel','error','-y',
        '-i',str(before),'-vf',f'ass={directory/"captions.ass"}',
        '-c:v','libx264','-preset','medium','-crf','13',
        '-pix_fmt','yuv420p','-c:a','copy','-movflags','+faststart',
        str(output)],check=True,timeout=150)
    out=probe(output)
    v=next(s for s in out['streams'] if s['codec_type']=='video')
    a=next((s for s in out['streams'] if s['codec_type']=='audio'),None)
    if a is None:raise RuntimeError('Narration was dropped from four-second film')
    if (v['width'],v['height'],v['r_frame_rate'],int(v['nb_frames']))!=(1920,1080,'60/1',240):
        raise RuntimeError('Video shape or frame count changed')
    if abs(float(out['format']['duration'])-4)>0.025:
        raise RuntimeError('Unexpected film duration')
    os.replace(output,before)
    preview=directory/'preview.mp4'
    subprocess.run([
        'ffmpeg','-hide_banner','-loglevel','error','-y',
        '-i',str(before),'-vf','fps=30,scale=1280:720:flags=lanczos',
        '-c:v','libx264','-preset','slow','-crf','18',
        '-c:a','aac','-b:a','160k','-pix_fmt','yuv420p',
        '-movflags','+faststart',str(preview)],check=True,timeout=125)
    subprocess.run([
        'ffmpeg','-hide_banner','-loglevel','error','-y',
        '-ss','2.50','-i',str(before),'-frames:v','1',
        '-vf','scale=1280:720:flags=lanczos','-q:v','3',
        str(directory/'poster.jpg')],check=True,timeout=35)
    subprocess.run(['ffmpeg','-v','error','-xerror','-i',str(before),
                    '-f','null','-'],check=True,timeout=90)
    report_path=directory/'release.json'
    receipt=json.loads(report_path.read_text())
    receipt.update({'test':'four-second-narrated-story',
       'caption_style':'Inter 37px, no pill, 46px bottom margin',
       'narration':cues,
       'evidence':'recorded Connect and Codex clicks, expanded modal rechecked via DOM',
       'duration':4.0,'frames':240,'has_audio':True})
    report_path.write_text(json.dumps(receipt,indent=2))
    return receipt


if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--dir',type=Path,required=True)
    p.add_argument('--audio-meta',type=Path,required=True)
    args=p.parse_args()
    print(json.dumps(finish(args.dir,args.audio_meta),indent=2))
