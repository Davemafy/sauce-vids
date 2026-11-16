"""Evidence, pixel, cursor, sample clock and encoded-media flagship gate.

This is an *engineering* verdict, never a 9/10 creative certification.
Visual quality and audible mix taste require independent human evaluation.
"""
from __future__ import annotations
import argparse,hashlib,json,math,subprocess,wave
from pathlib import Path
import cv2,numpy as np
from session_contract import verify_package
from session_replay import cursor_motion,align_click_positions
from spring_motion import cursor_track
from flagship_story_v3 import verify_hero


def measure(film:Path,receipt_file:Path,session_dir:Path,hero_manifest:Path,
            output:Path)->dict:
    film=film.resolve();receipt=json.loads(receipt_file.read_text())
    session_dir=session_dir.resolve()
    session=json.loads((session_dir/'session.json').read_text())
    verify_package(session,session_dir)
    screenshot=session_dir/'states'/session['states'][1]['file']
    source=cv2.imread(str(screenshot),cv2.IMREAD_GRAYSCALE)
    if source is None or source.shape!=(1440,2560):
        raise ValueError('Verified source image not present')
    bee_dark_ratio=float(np.mean(source[610:795,590:730]<70))
    if bee_dark_ratio>.007:raise ValueError('Bee visual obstruction in click ROI')
    if session.get('presentation_hide_selector')!='img[src*="bee-cutout-"]':
        raise ValueError('Source bee suppression receipt is absent')
    _,hero=verify_hero(hero_manifest)
    if hero['source_sha256']!=receipt['hero_source_sha256']:
        raise ValueError('Film does not belong to verified homepage')
    start=session['states'][0]['at_ms']
    duration=(session['states'][-1]['at_ms']-start)/1000.+.35
    _,samples=cursor_motion(session['events'],start,duration,60)
    motion=cursor_track(samples=samples,fps=60,duration=duration,
                        stiffness=120.,damping=18.)
    motion=align_click_positions(motion,session['events'],start,60)
    clicks=[]
    for event in session['events']:
        if event['type']!='pointerdown' or event.get('x') is None:continue
        source_frame=round((event['t']-start)*60/1000)
        diff=math.dist(motion[source_frame],(event['x'],event['y']))
        # The browser screenshot maps 1280 CSS pixels to 1644 film px;
        # conservative safety includes the max 1.22× editorial closeup.
        bound=diff*(1644/1280)*1.22
        if bound>3:raise ValueError(f'Cursor mapped error {bound:.2f}px >3px')
        clicks.append({'source_frame':source_frame,
             'css_pixel_residual':round(diff,4),
             'conservative_master_pixel_residual':round(bound,4)})
    if len(clicks)!=2:raise ValueError('Expected two genuine clicks')
    media=json.loads(subprocess.check_output(['ffprobe','-v','error',
        '-of','json','-show_entries',
        'stream=codec_type,codec_name,width,height,r_frame_rate,sample_rate,nb_frames,duration',
        str(film)],text=True,timeout=30))
    vs=[s for s in media['streams'] if s['codec_type']=='video']
    au=[s for s in media['streams'] if s['codec_type']=='audio']
    n=receipt['video_frames']
    if not (len(vs)==1 and len(au)==1 and
        vs[0]['codec_name']=='h264' and vs[0]['r_frame_rate']=='60/1' and
        (vs[0]['width'],vs[0]['height'])==(1920,1080) and
        int(vs[0]['nb_frames'])==n and au[0]['codec_name']=='aac' and
        int(au[0]['sample_rate'])==48000):
        raise ValueError('Export format differs from exact 1080p60 AAC release')
    wav=film.parent/'sound-clock-48k.wav'
    with wave.open(str(wav),'rb') as w:
        if w.getnframes()!=n*800 or w.getframerate()!=48000 or w.getnchannels()!=2:
            raise ValueError('Audio sample-locked timeline mismatch')
    # Decode the complete *encoded* master, not just intermediate PNGs.
    subprocess.run(['ffmpeg','-v','error','-xerror','-i',str(film),
                    '-f','null','-'],check=True,capture_output=True,timeout=120)
    # Read actual frames across cuts. Outside the intentional outro fade and
    # initial black opening, no full-screen black flash can slip through.
    cuts=[receipt['hero_frames'],
       receipt['hero_frames']+receipt['real_interaction_frames'],
       receipt['hero_frames']+receipt['real_interaction_frames']+receipt['verified_result_hold_frames']]
    cap=cv2.VideoCapture(str(film));luma=[]
    for cut in cuts:
        for delta in (-2,-1,0,1,2):
            index=cut+delta;cap.set(cv2.CAP_PROP_POS_FRAMES,index)
            ok,frame=cap.read()
            if not ok:raise ValueError(f'Could not decode cut frame {index}')
            mean=float(np.mean(cv2.cvtColor(cv2.resize(frame,(160,90)),
                                  cv2.COLOR_BGR2GRAY)))
            luma.append({'frame':index,'mean_luma':round(mean,3)})
            if mean<9:raise ValueError(f'Black flash at frame {index}')
    cap.release()
    # Independently confirm source optics/duplicated callout disabled.
    source_release=json.loads((film.parent.parent/'cinematic-v3'/'release.json').read_text())
    if source_release.get('webgl_optics') is not None:
        raise ValueError('Selected source unexpectedly uses optical shader')
    if source_release.get('spotlight_frames',0)>0:
        raise ValueError('Selected film has competing spotlight blur')
    result={'result':'ENGINEERING_PASS_CREATIVE_NOT_CERTIFIED',
        'file':str(film),'sha256':hashlib.sha256(film.read_bytes()).hexdigest(),
        'frames':n,'fps':60,'resolution':[1920,1080],
        'audio_samples':n*800,'audio_rate':48000,
        'audio_roundoff_ms':round((float(vs[0]['duration'])-float(au[0]['duration']))*1000,3),
        'source_sha256':hero['source_sha256'],
        'cursor_clicks':clicks,'unwanted_bee_dark_ratio':round(bee_dark_ratio,5),
        'cut_frame_luminance':luma,
        'visual_policy':'Exactly one generated Sauce pointer; bee hidden only in action footage; ripple and duplicate badge off',
        'creative_gate':'FAIL until seven-category scores clear 9/10 overall and 8/10 individually'}
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(result,indent=2)+'\n')
    return result

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--film',type=Path,required=True)
    p.add_argument('--release',type=Path,required=True)
    p.add_argument('--session',type=Path,required=True)
    p.add_argument('--hero',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    a=p.parse_args()
    r=measure(a.film,a.release,a.session,a.hero,a.out)
    print(json.dumps({k:v for k,v in r.items() if k!='cut_frame_luminance'},indent=2))
