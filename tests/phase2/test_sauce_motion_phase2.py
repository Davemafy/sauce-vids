"""Sauce Motion Engine Phase 2: privacy, 3D projection and 48kHz Foley."""
from __future__ import annotations
import json,os,subprocess,sys,tempfile,wave
from pathlib import Path

import numpy as np
import pytest

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'scripts'))
from session_capture import CAPTURE_JS
from cinematic_stage import apply_spotlight_focus
from spatial_parallax import projected_target_quad,window_homography,map_pointer
from foley_mixer import render_foley_plan,RATE
from studio_motion_bridge import plan_studio_motion


def _plan(*,muted=False):
    return {
        'schema':'sauce-foley-plan-v1','sampleRate':RATE,'durationMs':1000,
        'muted':muted,'masterGain':.5,'musicGain':.55,
        'cues':[
            {'sound':'click_crisp','outputSample':4800,'outputMs':100.,'gain':.8},
            {'sound':'pop_glass','outputSample':12000,'outputMs':250.,'gain':.7},
            {'sound':'whoosh_soft','outputSample':24000,'outputMs':500.,'gain':.4}
        ],
        'duckIntervals':[{
            'startSample':6000,'endSample':19000,
            'attenuationDb':-10,'attackMs':40,'releaseMs':90
        }]
    }


def _read_pcm(path):
    with wave.open(str(path),'rb') as data:
        assert data.getframerate()==RATE
        assert data.getnchannels()==2 and data.getsampwidth()==2
        n=data.getnframes()
        pcm=np.frombuffer(data.readframes(n),dtype='<i2').reshape(-1,2).copy()
    return pcm


def test_procedural_audio_deterministic_and_sample_accurate(tmp_path):
    a,b=tmp_path/'a.wav',tmp_path/'b.wav'
    report=render_foley_plan(_plan(),a,target_duration_ms=1016.667)
    render_foley_plan(_plan(),b,target_duration_ms=1016.667)
    assert a.read_bytes()==b.read_bytes()
    assert report['cue_count']==3
    assert all(v=='procedural' for v in report['asset_sources'].values())
    assert report['sample_rate']==48000
    pcm=_read_pcm(a)
    assert len(pcm)==round(1016.667*48) or len(pcm)==int(np.ceil(1016.667*48))
    assert np.all(pcm[:4800]==0)
    assert np.any(pcm[4810:5000]!=0)
    assert np.max(np.abs(pcm.astype('int32')))<=int(.951*32767)


def test_48khz_aac_mux_retains_event_sample_alignment(tmp_path):
    """Actual encode/decode regression, not merely FoleyPlan arithmetic."""
    from scipy.signal import correlate, correlation_lags

    wav=tmp_path/'foley.wav'
    render_foley_plan(_plan(),wav,target_duration_ms=1000.)
    master=tmp_path/'test-60fps.mp4'
    subprocess.run([
        'ffmpeg','-hide_banner','-v','error','-nostdin','-y',
        '-f','lavfi','-i','color=c=black:s=320x180:r=60:d=1',
        '-i',str(wav),'-map','0:v:0','-map','1:a:0',
        '-c:v','libx264','-pix_fmt','yuv420p',
        '-c:a','aac','-ar','48000','-b:a','192k','-t','1',
        str(master)],check=True,timeout=50)
    audio=subprocess.run([
        'ffmpeg','-v','error','-nostdin','-i',str(master),
        '-map','0:a:0','-f','f32le','-ac','2','-ar','48000','-'
    ],capture_output=True,check=True,timeout=30)
    decoded=np.frombuffer(audio.stdout,dtype='<f4').reshape(-1,2)
    expected=_read_pcm(wav).astype(np.float32)/32768.
    assert len(decoded)>=RATE-2048
    # Correlate the first 700ms, including the scheduled click and pop,
    # after AAC decode; true A/V alignment must be better than 1 frame.
    reference=expected[:int(.70*RATE),0]
    observed=decoded[:int(.75*RATE),0]
    score=correlate(observed,reference,mode='full',method='fft')
    shifts=correlation_lags(len(observed),len(reference),mode='full')
    bounded=(shifts>=-1000)&(shifts<=1000)
    lag=int(shifts[bounded][np.argmax(score[bounded])])
    assert abs(lag)<=RATE//60, f'AAC audio shifted by {lag/RATE*1000:.2f}ms'
    assert np.max(np.abs(decoded))>0


def test_mute_generates_real_zero_pcm_track(tmp_path):
    file=tmp_path/'mute.wav'
    receipt=render_foley_plan(_plan(muted=True),file)
    assert receipt['muted'] is True and receipt['cue_count']==0
    assert not np.any(_read_pcm(file))


def test_local_wav_or_ogg_sample_overrides_procedural(tmp_path):
    assets=tmp_path/'assets';assets.mkdir()
    sound=assets/'click_crisp.wav'
    sample=(np.sin(np.arange(960)*2*np.pi*900/RATE)*3500).astype('<i2')
    with wave.open(str(sound),'wb') as f:
        f.setnchannels(1);f.setsampwidth(2);f.setframerate(RATE)
        f.writeframes(sample.tobytes())
    plan=_plan();plan['cues']=plan['cues'][:1];plan['duckIntervals']=[]
    wav=tmp_path/'sourced.wav'
    result=render_foley_plan(plan,wav,asset_dir=assets)
    assert result['asset_sources']['click_crisp']=='local'
    assert np.any(_read_pcm(wav)[4800:5100])
    # ffmpeg's native Vorbis encoder is an optional supported OGG path.
    ogg=assets/'click_crisp.ogg'
    subprocess.run(['ffmpeg','-v','error','-y','-i',str(sound),str(ogg)],
                   check=True,timeout=30)
    sound.unlink()
    again=render_foley_plan(plan,tmp_path/'ogg.wav',asset_dir=assets)
    assert again['asset_sources']['click_crisp']=='local'


def test_music_ducking_reduces_background_beneath_cues(tmp_path):
    music=tmp_path/'background.wav'
    sine=(np.sin(np.arange(RATE*2)*2*np.pi*340/RATE)*12000).astype('<i2')
    with wave.open(str(music),'wb') as f:
        f.setnchannels(1);f.setsampwidth(2);f.setframerate(RATE)
        f.writeframes(sine.tobytes())
    plan=_plan();plan['cues']=[]
    render_foley_plan(plan,tmp_path/'duck.wav',music=music)
    audio=_read_pcm(tmp_path/'duck.wav').astype('float32')
    mid=np.sqrt(np.mean(audio[9000:11000]**2))
    edge=np.sqrt(np.mean(audio[2500:4000]**2))
    assert mid<edge*.65,(mid,edge)


def test_spotlight_projection_matches_exact_camera_homography():
    window=(220,124,1480,832)
    box={'x':420.,'y':220.,'width':310.,'height':180.}
    factor=1480/1280*1.22
    dx=-100.;dy=-35.
    tilt=(1.25,2.1)
    quad=projected_target_quad(box,window,factor,dx,dy,*tilt,perspective_px=1200)
    H=window_homography(*window,*tilt,focal=1200)
    px=window[0]+dx+(box['x']+box['width']/2)*factor
    py=window[1]+dy+box['y']*factor
    tip=map_pointer(H,px,py)
    assert np.allclose(quad[0],map_pointer(H,
        window[0]+dx+box['x']*factor,
        window[1]+dy+box['y']*factor),atol=.015)
    # Projective transforms do not preserve midpoints.
    # A 1-2px midpoint difference is expected from exact shared homography.
    assert np.linalg.norm(np.asarray(tip)-np.mean(quad[:2],axis=0))<3.
    assert not np.allclose(quad[0],[window[0]+dx+box['x']*factor,
                                     window[1]+dy+box['y']*factor])


def test_spotlight_retains_sharp_region_and_draws_projected_rim():
    img=np.full((1080,1920,3),188,dtype=np.uint8)
    window=(220,124,1480,832)
    box={'x':460.,'y':210.,'width':220.,'height':160.}
    f=1480/1280;tilt=(1.,1.5)
    out=apply_spotlight_focus(img,box,window,f,0.,0.,tilt,1200.,6.,.25)
    assert not np.shares_memory(out,img)
    assert np.all(img==188)
    assert np.array_equal(out[25,25],img[25,25])
    quad=projected_target_quad(box,window,f,0.,0.,*tilt,perspective_px=1200)
    x,y=np.rint(quad.mean(axis=0)).astype(int)
    assert np.linalg.norm(out[y,x].astype(float)-img[y,x].astype(float))<8
    assert np.mean(out[350,400])<np.mean(img[350,400])*.86
    corner=np.rint(quad[0]).astype(int)
    patch=out[corner[1]-3:corner[1]+4,corner[0]-3:corner[0]+4]
    assert np.max(patch)>220  # 1px luminous specular rim, antialiased
    assert out.shape==img.shape


def test_bridge_uses_one_versioned_frame_and_foley_clock():
    path=ROOT/'studio/.tmp/brimble-reference-v16-ink/session.json'
    if not path.exists():pytest.skip('Private verified Brimble fixture is worker-only')
    session=json.loads(path.read_text())
    p=plan_studio_motion(session,4.2,60,{},preset='3d-launch')
    motion=p['motionEngine'];frames=motion['framePlan']['frames']
    foley=motion['foleyPlan']
    assert motion['schema']=='sauce-motion-plan-v1'
    assert len(frames)==len(p['frameMap'])==197
    assert foley['sampleRate']==48000
    assert all(abs(c['outputSample']/48-c['outputMs'])<.05 for c in foley['cues'])
    assert any(frame['camera']['spotlightActive'] for frame in frames)


@pytest.mark.skipif(os.getenv('SAUCE_BROWSER_TEST')!='1',
                    reason='Set SAUCE_BROWSER_TEST=1 on a worker with Chromium')
def test_browser_capture_copy_paste_submit_redacts_values():
    from playwright.sync_api import sync_playwright
    with sync_playwright() as playwright:
        configured=Path(os.environ.get('SAUCE_CHROME_BIN',
            '/opt/devmcp-browsers/chromium_headless_shell-1254/chrome-headless-shell-linux64/chrome-headless-shell'))
        opts={'executable_path':str(configured)} if configured.is_file() else {}
        browser=playwright.chromium.launch(
            headless=True,args=['--no-sandbox','--disable-dev-shm-usage'],**opts)
        try:
            page=browser.new_page(viewport={'width':1280,'height':720})
            page.set_content("""
              <form id="form"><input id="secret_password" type="password">
              <input id="normal" name="search">
              <button id="publish" type="submit">Publish</button></form>
            """)
            page.evaluate(CAPTURE_JS)
            page.evaluate("""() => document.querySelector('form')
                .addEventListener('submit',e=>e.preventDefault())""")
            page.locator('#secret_password').fill('TOP_SECRET_INPUT_4812')
            page.locator('#normal').fill('CLIPBOARD_SECRET_9481')
            page.locator('#normal').evaluate("""el=>{
                el.dispatchEvent(new Event('copy',{bubbles:true}));
                el.dispatchEvent(new Event('paste',{bubbles:true}));
            }""")
            page.locator('#publish').click()
            rows=page.evaluate('window.__sauceCapture.flush()')
            filtered=[r for r in rows if r['type'] in ('copy','paste','submit')]
            assert [r['type'] for r in filtered]==['copy','paste','submit']
            assert all(r['redacted'] and r['length'] is None for r in filtered)
            assert all(r['box']['width']>1 and r['box']['height']>1 for r in filtered)
            assert all(r['t']>=0 for r in filtered)
            raw=json.dumps(rows)
            assert 'TOP_SECRET_INPUT_4812' not in raw
            assert 'CLIPBOARD_SECRET_9481' not in raw
            assert 'secret_password' not in raw
        finally:
            browser.close()


def test_3d_launch_mp4_audio_stream_and_frame_count():
    release=ROOT/'studio/.tmp/sauce-motion-phase2-3d-launch'
    if not (release/'master-1080p60.mp4').exists():
        pytest.skip('Encoded Brimble integration film only exists on Vultr worker')
    manifest=json.loads((release/'release.json').read_text())
    assert manifest['preset']=='3d-launch'
    assert manifest['preset_camera_frames']==197
    assert manifest['spotlight_frames']>80
    assert manifest['foley_audio']['cue_count']==7
    streams=json.loads(subprocess.check_output([
        'ffprobe','-v','error','-show_streams','-of','json',
        str(release/'master-1080p60.mp4')],text=True))['streams']
    assert len(streams)==2
    video=next(s for s in streams if s['codec_type']=='video')
    audio=next(s for s in streams if s['codec_type']=='audio')
    assert (video['width'],video['height'],video['r_frame_rate'],int(video['nb_frames']))==(
        1920,1080,'60/1',197)
    assert audio['sample_rate']=='48000' and audio['codec_name']=='aac'
