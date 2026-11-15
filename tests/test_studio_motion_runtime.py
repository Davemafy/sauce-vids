"""Trace-driven engine tests, without importing optional scientific libraries in CI."""
from __future__ import annotations
from pathlib import Path
import hashlib,json,shutil,sys,unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from studio_motion_bridge import plan_studio_motion,BUNDLE


class StudioMotionPlanTests(unittest.TestCase):
    @unittest.skipUnless(BUNDLE.is_file() and shutil.which('node'),"Requires compiled TypeScript motion planner")
    def test_realistic_trace_lock_and_reproducible_frame_plan(self):
        trace=json.loads((ROOT/'tests/fixtures/studio-motion-trace.json').read_text())
        cfg={"enableTimeWarp":True,"maxWarpSpeed":4,
             "enableStudioFloor":True,"floorReflectionIntensity":.25,
             "enableCallouts":True,"calloutCooldownMs":2500,
             "maxCalloutLifetimeMs":1800}
        a=plan_studio_motion(trace,9.,60,cfg)
        b=plan_studio_motion(trace,9.,60,cfg)
        self.assertEqual(json.dumps(a,sort_keys=True),json.dumps(b,sort_keys=True))
        self.assertEqual(a['stage']['window']['width'],1480)
        self.assertLess(a['outputDurationMs'],9000)
        self.assertGreater(max(f['speed'] for f in a['frameMap']),3.9)
        self.assertGreaterEqual(len(a['deadZones']),2)
        self.assertEqual([c['text'] for c in a['callouts']],['Connect Agent'])
        # The later submit is correctly suppressed when the 4x warp
        # compresses its output-time gap below the 2500ms cooldown.
        self.assertTrue(all(b['sourceMs']>a['frameMap'][i-1]['sourceMs']
                            for i,b in enumerate(a['frameMap']) if i))

    @unittest.skipUnless(BUNDLE.is_file() and shutil.which('node'),"Requires compiled TypeScript motion planner")
    def test_real_capture_fallback_uses_verified_selector(self):
        s=json.loads((ROOT/'studio/.tmp/brimble-reference-v16-ink/session.json').read_text()) if (
            ROOT/'studio/.tmp/brimble-reference-v16-ink/session.json').is_file() else None
        if s is None:self.skipTest('Vultr private real capture not available')
        plan=plan_studio_motion(s,4.2,60,{'enableTimeWarp':True,'maxWarpSpeed':4,
             'enableCallouts':True,'enableStudioFloor':True,'floorReflectionIntensity':.25})
        self.assertEqual([c['text'] for c in plan['callouts']],['Connect Agent'])
        self.assertEqual(len(plan['actionWindows']),2)
        self.assertEqual(len(plan['frameMap']),181)
        self.assertEqual(round(plan['outputDurationMs']),3005)

    def test_stage_is_separate_from_optional_audio(self):
        producer=(ROOT/'scripts/produce_cinematic_demo.py').read_text()
        replay=(ROOT/'scripts/session_replay.py').read_text()
        self.assertIn('studio_motion_plan=studio_plan',producer)
        self.assertIn('StudioMotion test excludes all audio tracks',producer)
        self.assertIn('studio_motion_plan:dict|None=None',replay)
        self.assertIn('source_index=min(source_total-1',replay)
        self.assertIn('callout_renderer.draw(final,index',replay)
        self.assertIn('source=directional_blur(source,vx,vy,speed)',replay)

    def test_capture_contains_safe_semantic_metadata(self):
        src=(ROOT/'scripts/session_capture.py').read_text()
        for token in ("eventType:type","tag:el?.tagName","ariaLabel:semantic?",
                      "innerText:semantic?","sensitive.test(value)"):
            self.assertIn(token,src)

class StudioPixelTests(unittest.TestCase):
    def setUp(self):
        try:
            import cv2,numpy
            from cinematic_stage import CinematicStage
            from studio_motion_blur import directional_blur
            from studio_motion_callouts import KineticCalloutRenderer
        except ImportError:self.skipTest('Native rendering dependencies not installed')
        self.np=numpy
        self.Stage=CinematicStage
        self.blur=directional_blur
        self.Callouts=KineticCalloutRenderer

    def test_perspective_floor_changes_only_composition_and_is_deterministic(self):
        np=self.np
        src=np.zeros((832,1480,3),np.uint8)
        src[:]=[217,219,222]
        src[-110:,220:550,:]=[90,135,200]
        plain=self.Stage().render(src,tilt=(1.,-1.))
        film=self.Stage(enable_studio_floor=True).render(src,tilt=(1.,-1.))
        duplicate=self.Stage(enable_studio_floor=True).render(src,tilt=(1.,-1.))
        self.assertTrue(np.array_equal(film,duplicate))
        self.assertFalse(np.array_equal(plain,film))
        self.assertTrue(np.all(src[-110:,220:550]==[90,135,200]))
        self.assertGreater(np.abs(film[995:,:,:].astype('int16')-
                                  plain[995:,:,:].astype('int16')).sum(),10000)

    def test_directional_blur_only_for_actual_movement_and_fast_playback(self):
        np=self.np
        frame=np.zeros((32,70,3),np.uint8);frame[:,30:,:]=255
        self.assertTrue(np.array_equal(self.blur(frame,12,1,1.2),frame))
        self.assertTrue(np.array_equal(self.blur(frame,0,0,4),frame))
        changed=self.blur(frame,12,1,4)
        self.assertFalse(np.array_equal(changed,frame))

    def test_blur_shutter_growth_follows_warp_speed(self):
        np=self.np
        frame=np.zeros((48,96,3),np.uint8)
        frame[:,44:50,:]=255
        slow=self.blur(frame,10,0,1.6)
        quick=self.blur(frame,10,0,4.0)
        self.assertGreater(int(np.abs(quick.astype('int16')-
                             frame.astype('int16')).sum()),
                           int(np.abs(slow.astype('int16')-
                             frame.astype('int16')).sum()))

    def test_callout_is_visible_and_deterministic_at_matching_frame(self):
        np=self.np
        cue={'text':'Connect Agent','outputStartMs':700,'outputEndMs':2400,
             'box':{'x':210,'y':290,'width':230,'height':40}}
        frame=np.full((1080,1920,3),23,np.uint8)
        forrun=[]
        for _ in range(2):
            image=frame.copy()
            renderer=self.Callouts([cue],fps=60)
            for k in range(42,62):
                renderer.draw(image,k,1480/1280.,0,0,(1.4,-.8),(220,124,1480,832))
            forrun.append(hashlib.sha256(image.tobytes()).digest())
        self.assertEqual(*forrun)
        self.assertGreater(int(np.abs(image.astype('int16')-frame.astype('int16')).sum()),10000)

if __name__=='__main__':unittest.main()
