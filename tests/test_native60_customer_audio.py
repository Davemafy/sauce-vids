"""Independent opt-in source/native60 and genuinely licensed audio gates."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

import cv2
import numpy as np

from backend.native60_capture import calibrate_screen_origin,source_video_filename,capture_mode
from backend.licensed_music_bed import licensed_music_from_env,add_music_to_master,LicensedMusic
from backend.live_render import source_video_profile


def png(image):
    ok,data=cv2.imencode(".png",image)
    assert ok
    return data.tobytes()


def sha(blob):
    return hashlib.sha256(blob).hexdigest()


class Native60SourceTests(unittest.TestCase):
    def test_exact_browser_viewport_only_no_own_chrome_toolbar(self):
        # A genuine 1080p sample drawn as a diverse, deterministic target.
        r=np.random.default_rng(48)
        page=r.integers(0,255,(1080,1920,3),dtype=np.uint8)
        screen=np.full((1200,1920,3),29,dtype=np.uint8)
        screen[87:1167]=page.copy()
        result=calibrate_screen_origin(png(page),png(screen))
        self.assertEqual(result['y'],87)
        self.assertEqual(result['width'],1920)
        self.assertLess(result['mean_absolute_error'],.001)
        screen[87:1167]=47
        with self.assertRaises(RuntimeError):
            calibrate_screen_origin(png(page),png(screen))
        with self.assertRaises(ValueError):
            calibrate_screen_origin(png(page[:720]),png(screen))

    def test_safe_original_source_filename_and_mode(self):
        self.assertEqual(source_video_filename({}),'continuous-source.webm')
        self.assertEqual(source_video_filename({'video':'continuous-source.mp4'}),
                         'continuous-source.mp4')
        for filename in ('../secret','file:///etc/passwd','capture.avi','continuous-source.mkv'):
            with self.assertRaises(ValueError):
                source_video_filename({'video':filename})
        with patch.dict(os.environ,{'SAUCE_CAPTURE_MODE':'x11grab60'}):
            self.assertEqual(capture_mode(),'x11grab60')
        with patch.dict(os.environ,{'SAUCE_CAPTURE_MODE':'unsafemode'}):
            with self.assertRaises(ValueError):
                capture_mode()

    def test_60fps_source_receipt_is_independently_verified(self):
        stream={'width':1920,'height':1080,'r_frame_rate':'60/1'}
        proof={'source_capture_method':'x11grab60-original-browser',
               'source_fps':'60/1','viewport_match_error':.465}
        receipt={'capture_quality':'high','source_dpr':2,
                 'video':'continuous-source.mp4',
                 'viewport_css_size':{'width':1920,'height':1080},
                 'native_source_capture':proof}
        p=source_video_profile(stream,receipt)
        self.assertEqual(p['source_fps'],'60/1')
        for mutation in ({'source_fps':'25/1'},
                         {'viewport_match_error':13.0},
                         {'source_capture_method':'pretend-native'}):
            with self.subTest(mutation=mutation):
                with self.assertRaises(RuntimeError):
                    source_video_profile(stream,{**receipt,
                                                'native_source_capture':{**proof,**mutation}})
        with self.assertRaises(RuntimeError):
            source_video_profile({**stream,'r_frame_rate':'25/1'},receipt)


class LicenseAndMusicTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        root=Path(self.tmp.name)
        self.catalog=root/'taste'/'tweakcn'/'catalog.json'
        self.catalog.parent.mkdir(parents=True)
        self.audio=root/'tracks'/'tent.mp3'
        self.audio.parent.mkdir(parents=True)
        self.audio.write_bytes(b'fake-input-for-hash-only')
        self.proof=root/'fma'/'tent.html'
        self.proof.parent.mkdir()
        self.proof.write_text('''<title>Play House - Tent - Free Music Archive</title>
            Tent is licensed under a <a rel="license" href="https://creativecommons.org/publicdomain/zero/1.0/">CC0 1.0 Universal License</a>''')
        self.catalog.write_text(json.dumps({'tracks':[{
          'id':'tent','title':'Tent','artist':'Play House','license':'CC0-1.0',
          'license_url':'https://creativecommons.org/publicdomain/zero/1.0/',
          'file':'tracks/tent.mp3',
          'sha256':sha(self.audio.read_bytes()),
          'source':'https://freemusicarchive.org/music/play-house/songs-1/tent-1/'
        }]}))
        self.env={'SAUCE_CC0_TRACK_ID':'tent',
                  'SAUCE_CC0_CATALOG_PATH':str(self.catalog),
                  'SAUCE_CC0_PROOF_PATH':str(self.proof),
                  'SAUCE_CC0_PROOF_SHA256':sha(self.proof.read_bytes())}

    def tearDown(self):
        self.tmp.cleanup()

    def test_fma_license_must_be_hash_pinned_not_merely_named_cc0(self):
        with patch.dict(os.environ,self.env):
            track=licensed_music_from_env()
            self.assertEqual(track.id,'tent')
            self.assertEqual(track.audio_sha256,sha(self.audio.read_bytes()))
            self.assertFalse(track.public_receipt()['creative_approved'])
            self.proof.write_text('fake changed evidence')
            with self.assertRaises(ValueError):
                licensed_music_from_env()

    def test_reject_unlicensed_or_tampered_track(self):
        with patch.dict(os.environ,self.env):
            self.audio.write_bytes(b'replaced audio')
            with self.assertRaises(ValueError):
                licensed_music_from_env()
        self.audio.write_bytes(b'fake-input-for-hash-only')
        c=json.loads(self.catalog.read_text())
        c['tracks'][0]['license']='CC-BY-NC'
        self.catalog.write_text(json.dumps(c))
        with patch.dict(os.environ,self.env):
            with self.assertRaises(ValueError):
                licensed_music_from_env()

    def test_music_is_opt_in(self):
        with patch.dict(os.environ,{'SAUCE_CC0_TRACK_ID':''}):
            self.assertIsNone(licensed_music_from_env())

    def test_real_video_picture_survives_aac_music_mux(self):
        import shutil
        path=Path(self.tmp.name)
        master=path/'real-original-test.mp4'
        self.audio.write_bytes(b'')  # replace with genuine generated test tone only
        subprocess.run([
          'ffmpeg','-v','error','-y','-f','lavfi','-i',
          'color=c=blue:s=320x180:r=60:d=2.4','-t','2.4','-c:v','libx264',
          '-pix_fmt','yuv420p',str(master)],check=True,timeout=25)
        subprocess.run([
          'ffmpeg','-v','error','-y','-f','lavfi','-i',
          'sine=f=330:r=48000:d=4','-ac','2','-c:a','libmp3lame',
          str(self.audio)],check=True,timeout=25)
        before=subprocess.check_output(['ffmpeg','-v','error','-i',str(master),
          '-map','0:v','-c','copy','-f','md5','-'],timeout=20)
        track=LicensedMusic(self.audio,'tent','Tent','Play House',
            'https://freemusicarchive.org/music/play-house/songs-1/tent-1/',
            'CC0-1.0',sha(self.audio.read_bytes()),sha(self.proof.read_bytes()),
            'https://freemusicarchive.org/music/play-house/songs-1/tent-1/')
        add_music_to_master(master,track,2.4)
        after=subprocess.check_output(['ffmpeg','-v','error','-i',str(master),
          '-map','0:v','-c','copy','-f','md5','-'],timeout=20)
        self.assertEqual(before,after)
        res=json.loads(subprocess.check_output(['ffprobe','-v','error',
           '-show_streams','-of','json',str(master)],text=True))
        self.assertEqual(len(res['streams']),2)
        self.assertEqual(res['streams'][1]['codec_name'],'aac')
        self.assertEqual(res['streams'][1]['sample_rate'],'48000')

    def test_pinned_music_can_preserve_existing_foley(self):
        master=Path(self.tmp.name)/'source-with-foley.mp4'
        subprocess.run(['ffmpeg','-v','error','-y','-f','lavfi','-i',
          'color=c=blue:s=320x180:r=60:d=3','-f','lavfi','-i',
          'sine=f=1100:r=48000:d=3','-t','3','-c:v','libx264','-c:a','aac',
          '-pix_fmt','yuv420p',str(master)],check=True,timeout=25)
        subprocess.run(['ffmpeg','-v','error','-y','-f','lavfi','-i',
          'sine=f=330:r=48000:d=4','-ac','2','-c:a','libmp3lame',
          str(self.audio)],check=True,timeout=25)
        track=LicensedMusic(self.audio,'tent','Tent','Play House',
            'https://freemusicarchive.org/music/play-house/songs-1/tent-1/',
            'CC0-1.0',sha(self.audio.read_bytes()),sha(self.proof.read_bytes()),
            'https://freemusicarchive.org/music/play-house/songs-1/tent-1/')
        def picture():
            return subprocess.check_output(['ffmpeg','-v','error','-i',str(master),
              '-map','0:v','-c','copy','-f','md5','-'],timeout=20)
        before=picture()
        add_music_to_master(master,track,3,preserve_foley=True)
        self.assertEqual(before,picture())
        pcm=np.frombuffer(subprocess.check_output(['ffmpeg','-v','error','-ss','1',
          '-i',str(master),'-t','1','-vn','-ac','1','-ar','48000','-f','f32le','-'],
          timeout=20),dtype='<f4')[:48000]
        spec=np.abs(np.fft.rfft(pcm))
        self.assertGreater(spec[1100],500)  # original 1100Hz event-audio stand-in
        self.assertGreater(spec[330],100)   # independently licensed music stand-in


if __name__=='__main__':
    unittest.main()
