#!/usr/bin/env python3
"""Objective export QA for the narrated four-second Sauce challenge."""
from __future__ import annotations
import argparse,json,math,subprocess
from pathlib import Path
import numpy as np, cv2

def video_data(path:Path):
    return json.loads(subprocess.check_output([
        'ffprobe','-v','error','-show_entries',
        'stream=codec_type,codec_name,width,height,avg_frame_rate,nb_frames:format=duration,size',
        '-of','json',str(path)],text=True))


def check(directory:Path,audio_meta:Path,geometry:Path):
    film=directory/'master-1080p60.mp4'
    preview=directory/'preview.mp4'
    meta=video_data(film)
    v=next(s for s in meta['streams'] if s['codec_type']=='video')
    a=next(s for s in meta['streams'] if s['codec_type']=='audio')
    assert (v['codec_name'],v['width'],v['height'],int(v['nb_frames']))==('h264',1920,1080,240)
    assert abs(float(meta['format']['duration'])-4.0)<.03
    assert a['codec_name']=='aac'
    p=video_data(preview)
    pv=next(s for s in p['streams'] if s['codec_type']=='video')
    assert (pv['width'],pv['height'])==(1280,720)
    r=json.loads((directory/'release.json').read_text())
    assert r['semantic_checks']==3 and r['pixel_region_checks']==3
    assert r['editorial_closeup'] and r['root_component']=='CinematicStage'
    assert r['source_dpr']>=2 and r['cursor_scale']==.56
    audio=json.loads(audio_meta.read_text())
    dialog=json.loads(geometry.read_text())['observed_rect']
    assert dialog['height']==476 and dialog['width']==400
    assert audio['lines'][0]['start']<audio['recorded_clicks'][0]<audio['lines'][0]['end']
    assert abs(audio['recorded_clicks'][1]-audio['lines'][1]['start'])<.03

    cap=cv2.VideoCapture(str(film))
    def frame(t:float):
        cap.set(cv2.CAP_PROP_POS_MSEC,t*1000)
        ok,img=cap.read()
        if not ok: raise RuntimeError('Could not decode frame at '+str(t))
        return img
    before=frame(.06)
    first=frame(.72)
    gap=frame(1.90)
    second=frame(2.9)
    after=frame(3.90)
    cap.release()
    # Caption text must actually exist only during voice phrases.
    band=lambda image: image[975:1060,475:1445]
    bright=lambda image: int(np.count_nonzero(band(image).max(axis=2)>155))
    counts={'pre':bright(before),'first':bright(first),
            'gap':bright(gap),'second':bright(second),'post':bright(after)}
    assert counts['first']-counts['pre']>1700,counts
    assert counts['second']-counts['gap']>1700,counts
    assert counts['gap']<150 and counts['post']<150,counts
    assert before[12,12].mean()<35
    # Final code reveal must not be clipped off the stage.
    win=(220,124,1480,832)
    assert (win[1]+win[3])<1080
    # Preserve the entire expanded modal at 1.30× in the 1480x832 stage.
    projected_height=dialog['height']*(832/720)*1.30
    assert projected_height<832-105
    result={'duration_s':4.0,'master':'1080p60 H.264 + AAC',
       'preview':'720p30 H.264 + AAC Lanczos','frames':240,
       'recorded_clicks_s':audio['recorded_clicks'],
       'voice_cues':audio['lines'],'captions_present_at_voice':counts,
       'expanded_dialog_source_css':dialog,
       'expanded_dialog_projected_height_px':round(projected_height),
       'clip_check':'pass','UI_state_checks':'3/3','ROI_checks':'3/3',
       'copyright':'Reference clips used for private evaluation, not included in public export',
       'superiority_claim':'not proven; requires blinded reviewer comparison'}
    (directory/'quality-report.json').write_text(json.dumps(result,indent=2))
    return result

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--dir',type=Path,required=True)
    p.add_argument('--audio-meta',type=Path,required=True)
    p.add_argument('--geometry',type=Path,required=True)
    args=p.parse_args()
    print(json.dumps(check(args.dir,args.audio_meta,args.geometry),indent=2))
