"""A source-true, frame-accurate editorial reveal cut for an observed modal.

Opt-in finishing step for a verified film, not a generic native DOM animator.
Removes only already-recorded frames during a known low-contrast transition:
no inpainting, fabricated UI, duplicated click or invented dialog state.

Input must include the corresponding real Sauce session; output metadata is
private and intentionally does not include raw source events, URLs or HAR.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import hashlib
import math

FPS=60
AUDIO_RATE=48000
SAMPLES_PER_FRAME=AUDIO_RATE//FPS
MAX_TRANSITION_FRAMES=12


def validated_cut(session:dict,start_frame:int,settled_frame:int)->dict:
    if (type(start_frame) is not int or type(settled_frame) is not int or
        start_frame<2 or not 1 <= settled_frame-start_frame <= MAX_TRANSITION_FRAMES):
        raise ValueError("Only short <=12-frame, non-initial reveal cuts are allowed")
    states=session.get('states')
    events=session.get('events')
    if not isinstance(states,list) or not states or not isinstance(events,list):
        raise ValueError("Verified Sauce session required")
    start_ms=states[0].get('at_ms')
    if type(start_ms) not in (float,int):
        raise ValueError("Missing actual source clock")
    real_clicks=[e for e in events if e.get('type')=='pointerdown'
                 and type(e.get('t')) in (float,int)]
    if not any(abs(round((e['t']-start_ms)*FPS/1000)-start_frame)<=1
               for e in real_clicks):
        raise ValueError("Reveal cut must begin at observed pointerdown event")
    # Cut the translucent source frames [start,settled), keeping only
    # authentic, already-encoded source footage. Preserve the first click
    # and its audible ~80 ms decay: a 1-frame J-cut truncates the sound and
    # materially weakens it. Later cues resume at the same source clock as
    # the video, after an exactly equal-sized 800-sample/frame audio cut.
    removed=settled_frame-start_frame
    audio_carry=min(5,removed)
    return {'firstRemoved':start_frame,'firstRetainedAfter':settled_frame,
            'removedFrames':removed,'audioCarryFrames':audio_carry,
            'audioHeadSamples':(start_frame+audio_carry)*SAMPLES_PER_FRAME,
            'audioTailSamples':(settled_frame+audio_carry)*SAMPLES_PER_FRAME}


def ffprobe(path:Path)->dict:
    return json.loads(subprocess.check_output(
        ['ffprobe','-v','error','-show_entries',
         'stream=codec_type,codec_name,width,height,r_frame_rate,nb_frames,sample_rate:format=duration',
         '-of','json',str(path)],text=True,timeout=25))


def sha256(path:Path):
    h=hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda:stream.read(2**20),b''):
            h.update(chunk)
    return h.hexdigest()


def splice(source:Path,session_file:Path,output:Path,start:int,settled:int):
    source=Path(source);session_file=Path(session_file);output=Path(output)
    if source.resolve()==output.resolve():
        raise ValueError("Never overwrite the verified source master")
    if output.exists():raise ValueError("Output already exists; preserve earlier proof")
    source_info=ffprobe(source)
    vid=next((x for x in source_info['streams'] if x['codec_type']=='video'),None)
    aud=next((x for x in source_info['streams'] if x['codec_type']=='audio'),None)
    if (not vid or vid.get('width')!=1920 or vid.get('height')!=1080
        or vid.get('r_frame_rate')!='60/1' or not aud
        or aud.get('sample_rate')!='48000'):
        raise ValueError("Source must be exact 1080p60 film with 48kHz Foley")
    count=int(vid['nb_frames'])
    if count>3600 or count<120:raise ValueError("Film outside bounded scope")
    cut=validated_cut(json.loads(session_file.read_text()),start,settled)
    if settled>=count-30:raise ValueError("Do not trim the recorded payoff")
    output.parent.mkdir(parents=True,exist_ok=True)
    temporary=output.with_name('.'+output.stem+'.partial.mp4')
    if temporary.exists():raise ValueError("An incomplete export already exists")
    length=cut['removedFrames']
    # Video: remove ONLY the observed native transition. Audio: preserve
    # the actual click and decay, then remove an equal-duration later window
    # so post-cut event samples realign to the corresponding video frames.
    graph=(
        f"[0:v:0]select='not(between(n,{start},{settled-1}))',"
        f"setpts=N/({FPS}*TB)[v];"
        "[0:a:0]aresample=48000,asplit=2[a0][a1];"
        f"[a0]atrim=end_sample={cut['audioHeadSamples']},"
        "asetpts=PTS-STARTPTS[head];"
        f"[a1]atrim=start_sample={cut['audioTailSamples']},"
        "asetpts=PTS-STARTPTS[tail];"
        "[head][tail]concat=n=2:v=0:a=1[a]"
    )
    expected=count-length
    command=['ffmpeg','-hide_banner','-loglevel','error','-nostdin','-y',
             '-i',str(source),'-filter_complex',graph,
             '-map','[v]','-map','[a]',
             '-frames:v',str(expected),'-r','60','-fps_mode','cfr',
             '-c:v','libx264','-preset','medium','-crf','16',
             '-pix_fmt','yuv420p',
             '-c:a','aac','-ar','48000','-b:a','192k',
             '-movflags','+faststart',str(temporary)]
    try:
        subprocess.run(command,check=True,timeout=180)
        outinfo=ffprobe(temporary)
        video=next((v for v in outinfo['streams'] if v['codec_type']=='video'),None)
        audio=next((v for v in outinfo['streams'] if v['codec_type']=='audio'),None)
        if (not video or int(video['nb_frames'])!=expected or
                video['width']!=1920 or video['height']!=1080 or
                video['r_frame_rate']!='60/1' or not audio or
                audio.get('sample_rate')!='48000'):
            raise RuntimeError("Editorial splice output failed stream checks")
        subprocess.run(['ffmpeg','-hide_banner','-v','error','-xerror',
                        '-i',str(temporary),'-f','null','-'],
                       check=True,timeout=90)
        temporary.replace(output)
    finally:
        temporary.unlink(missing_ok=True)
    receipt={'schema':'sauce-source-edit-v1',
             'mode':'source-true-reveal-cut',
             'sourceMasterSha256':sha256(source),
             'outputSha256':sha256(output),
             'sourceFrames':count,'outputFrames':expected,
             'removedSourceFrames':[start,settled-1],
             'firstRetainedSettledFrame':settled,
             'sourceVerifiedPointerdownFrame':start,
             'audioJcutFrameOffset':cut['audioCarryFrames'],
             'audioSamplesPerFrame':SAMPLES_PER_FRAME,
             'outputDurationSeconds':expected/FPS,
             'preservesRealCapturedPixels':True,
             'notes':'Re-encodes observed source UI frames; no invented UI or source event.'}
    receipt_file=output.with_suffix('.edit.json')
    receipt_file.write_text(json.dumps(receipt,indent=2)+"\n")
    return receipt


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source',type=Path,required=True)
    parser.add_argument('--session',type=Path,required=True)
    parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--click-frame',type=int,required=True)
    parser.add_argument('--settled-frame',type=int,required=True)
    args=parser.parse_args()
    print(json.dumps(splice(args.source,args.session,args.out,
                            args.click_frame,args.settled_frame),indent=2))


if __name__=='__main__':
    main()
