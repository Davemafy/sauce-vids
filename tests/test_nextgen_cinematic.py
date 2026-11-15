"""Next-generation film systems: bounded, data-driven regression contracts."""
from __future__ import annotations
import ast
import hashlib
import math
import shutil
import tempfile
import unittest
import wave
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
try:
    import cv2
    import numpy as np
    from audio_reactive import audio_envelope
    from spatial_parallax import inertial_tilt_track, window_homography, map_pointer
    from code_semantics import (resolve_code_focus,plan_focus_cues,
                                semantic_camera_track,active_code_focus,
                                highlight_code_region)
    from cinematic_stage import CinematicStage
    AVAILABLE=True
except ImportError:
    AVAILABLE=False


class IntegrationSourceContracts(unittest.TestCase):
    def test_shader_is_real_webgl2_not_an_encoded_css_filter(self):
        text=(ROOT/'assets/shaders/optics-webgl2.html').read_text()
        for needle in ('getContext("webgl2"','gl.createShader','gl.texImage2D',
                       'gl.drawArrays','gl.finish()','vec3 clr=vec3',
                       'mono*.020','smoothstep(.56,.77','vignette'):
            self.assertIn(needle,text)
        script=(ROOT/'scripts/postprocess_webgl_video.py').read_text()
        self.assertIn('shader.apply(frame,frames)',script)
        self.assertIn('if frames!=min(frame_count',script)

    def test_default_production_pipeline_requires_real_shader(self):
        src=(ROOT/'scripts/produce_cinematic_demo.py').read_text()
        self.assertIn('webgl_optics:bool=True',src)
        self.assertIn('spatial_parallax:bool=True',src)
        self.assertIn('apply_video(master,webgl_master)',src)
        self.assertIn("os.replace(webgl_master,master)",src)
        self.assertIn('audio_envelope(',src)
        self.assertIn('code_root=code_root',src)

    def test_code_capture_emits_grounded_file_and_line(self):
        src=(ROOT/'scripts/session_capture.py').read_text()
        self.assertIn("closest('[data-sauce-code-file],[data-code-file]')",src)
        self.assertIn("push('code-focus',e",src)
        self.assertIn("push('terminal-focus',e",src)
        self.assertIn('Number.isInteger(line)',src)

    def test_ast_parser_is_not_eval_and_has_pinned_dependency(self):
        js=(ROOT/'scripts/code_focus_ast.cjs').read_text()
        self.assertIn('parser.parse(source',js)
        self.assertNotIn('eval(',js)
        self.assertIn('"typescript"',js)
        manifest=(ROOT/'scripts/package.json').read_text()
        self.assertIn('"@babel/parser":"7.26.9"',manifest)


@unittest.skipUnless(AVAILABLE,'local scientific/video render dependencies not installed')
class NextGenNativeTests(unittest.TestCase):
    def test_tilt_uses_real_velocity_and_respects_2_5_degree_limit(self):
        path=[(120.,160.)]*10+[(120+i*13.,160+i*7.) for i in range(20)]+[(380.,300.)]*40
        track=inertial_tilt_track(path,60)
        self.assertEqual(track[0],(0.,0.))
        self.assertTrue(all(x==0 and y==0 for x,y in track[:10]))
        self.assertGreater(max(abs(y) for _,y in track),.2)
        self.assertLessEqual(max(max(abs(x),abs(y)) for x,y in track),2.5)

    def test_pointer_uses_exact_same_projective_mapping_as_window(self):
        h=window_homography(220,124,1480,832,1.7,-1.2)
        point=map_pointer(h,470,382)
        self.assertTrue(0<point[0]<1920 and 0<point[1]<1080)
        a=np.float32([[[470,382]]])
        b=cv2.perspectiveTransform(a,h)[0,0]
        self.assertAlmostEqual(point[0],float(b[0]),places=4)
        self.assertAlmostEqual(point[1],float(b[1]),places=4)

    def test_ast_python_symbol_and_path_sandbox(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)
            (p/'svc.py').write_text('class Worker:\n    def execute(self):\n        return True\n')
            event={'type':'code-focus','file':'svc.py','line':3,'t':800,
                   'box':{'x':240,'y':80,'width':800,'height':500},
                   'line_height':21,'first_visible_line':1}
            f=resolve_code_focus(event,p)
            self.assertEqual((f.name,f.kind),('execute','FunctionDef'))
            self.assertEqual(f.target_rect()['y'],101.)
            bad=dict(event,file='../nope.py')
            with self.assertRaises((ValueError,FileNotFoundError)):
                resolve_code_focus(bad,p)

    def test_typescript_ast_method_and_timestamp_gate(self):
        if not shutil.which('node'):self.skipTest('Node unavailable')
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);(p/'ui.ts').write_text(
                'export class Card {\n  render(text: string) {\n    return text.trim();\n  }\n}\n')
            ev={'type':'code-focus','file':'ui.ts','line':3,'t':600,
                'box':{'x':220,'y':100,'width':750,'height':440}}
            try:focus=resolve_code_focus(ev,p)
            except __import__('subprocess').CalledProcessError:
                self.skipTest('Babel parser not installed in test environment')
            self.assertEqual(focus.name,'render')
            baseline=[(1.,640.,360.)]*120
            camera=semantic_camera_track(baseline,[focus],0,60,(1280,720))
            self.assertEqual(camera[0],baseline[0])
            self.assertEqual(camera[10],baseline[10])
            self.assertGreater(camera[80][0],1.05)
            self.assertIsNone(active_code_focus([focus],100))
            self.assertIsNotNone(active_code_focus([focus],850))

    def test_terminal_focus_has_no_synthetic_ast(self):
        ev={'type':'terminal-focus','t':410,'box':{'x':400,'y':260,'width':520,'height':240}}
        cue=plan_focus_cues([ev],None)
        self.assertEqual(len(cue),1)
        self.assertEqual(cue[0].kind,'terminal')
        self.assertEqual(cue[0].target_rect()['width'],520.)

    def test_audio_rms_peaks_and_remains_quiet_during_silence(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'pulse.wav'
            sr=48000;n=2*sr
            samples=np.zeros(n,dtype=np.int16)
            for start in (int(.25*sr),int(1.20*sr)):
                length=int(.16*sr)
                t=np.arange(length)/sr
                wave_values=np.sin(2*math.pi*150*t)*np.hanning(length)
                samples[start:start+length]=np.int16(wave_values*25000)
            with wave.open(str(p),'wb') as sound:
                sound.setnchannels(1);sound.setsampwidth(2);sound.setframerate(sr)
                sound.writeframes(samples.tobytes())
            levels=audio_envelope(p,60,120)
            self.assertEqual(len(levels),120)
            self.assertLess(levels[2],.001)
            self.assertGreater(levels[20],.05)
            self.assertGreater(levels[75],.05)
            self.assertTrue(all(0<=x<=1 for x in levels))

    def test_glow_pulses_only_behind_window(self):
        stage=CinematicStage()
        site=np.full((832,1480,3),220,dtype=np.uint8)
        before=stage.render(site,glow=0)
        after=stage.render(site,glow=.9)
        self.assertGreater(float(np.abs(before[460,80].astype('int16')-
                                       after[460,80].astype('int16')).sum()),0)
        self.assertTrue(np.array_equal(before[450,900],after[450,900]))


if __name__=='__main__':unittest.main()
