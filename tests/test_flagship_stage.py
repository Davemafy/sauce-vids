"""Flagship optical restraint and single-pointer production contracts."""
import sys,unittest,json,math,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
try:
 import numpy as np
 from flagship_stage import FlagshipStage,WINDOW
 from cinematic_stage import CinematicCursor
 from spring_motion import cursor_track
except ImportError:
 np=FlagshipStage=CinematicCursor=cursor_track=None

@unittest.skipUnless(FlagshipStage is not None,'Requires render extras')
class FlagshipStageTests(unittest.TestCase):
 def test_matte_never_modifies_verified_source_and_has_no_purple_bloom(self):
  stage=FlagshipStage()
  self.assertEqual(stage.window,(138,78,1644,924))
  self.assertEqual(stage.enable_studio_floor,False)
  source=np.full((924,1644,3),210,np.uint8)
  out=stage.render(source)
  self.assertEqual(out.shape,(1080,1920,3))
  self.assertTrue(np.array_equal(out[300:600,340:1500],source[222:522,202:1362]))
  self.assertLess(int(out[15,15].max())-int(out[15,15].min()),9)
  self.assertTrue(np.array_equal(out,stage.render(source)))
 def test_source_cursor_and_connected_oval_are_disabled_for_flagship(self):
  source=(ROOT/'scripts/session_replay.py').read_text()
  self.assertIn('if studio_motion_plan and not flagship_mode else None',source)
  self.assertIn('show_ripple=not bool(flagship_mode)',source)
  cursor=CinematicCursor(FlagshipStage(),[],0.,show_ripple=False)
  self.assertFalse(cursor.show_ripple)
 def test_spring_is_deterministic_and_contact_lock_compatible(self):
  samples=[(0.,700.,400.),(.15,600.,390.),(.5,300.,360.),(.85,300.,360.),
           (1.,300.,360.),(1.5,300.,360.)]
  a=cursor_track(samples=samples,fps=60,duration=1.5,stiffness=120,damping=18)
  b=cursor_track(samples=samples,fps=60,duration=1.5,stiffness=120,damping=18)
  self.assertEqual(a,b)
  self.assertLess(math.dist(a[60],(300,360)),3)

if __name__=='__main__':unittest.main()

class FlagshipMotionTests(unittest.TestCase):
 def test_badge_has_independent_lag_and_seek_stability(self):
  if cursor_track is None:self.skipTest('Requires render extras')
  from flagship_motion import badge_spring_track,shutter_velocity
  cursor=[(200.+min(i,14)*18.,340.) for i in range(25)]
  badge=badge_spring_track(cursor)
  self.assertEqual(badge,badge_spring_track(cursor))
  self.assertGreater(cursor[10][0]+38.-badge[10][0],0.)
  self.assertEqual(len(badge),len(cursor))
  shutter=shutter_velocity(cursor)
  self.assertEqual(shutter[0],(0.,0.))
  self.assertAlmostEqual(shutter[4][0],9.)
 def test_click_contact_remains_exact_in_precomputed_source_clock(self):
  if cursor_track is None:self.skipTest('Requires render extras')
  from session_replay import align_click_positions,cursor_motion
  import json
  fixture=ROOT/'studio/.tmp/flagship/capture-v2/session.json'
  if not fixture.exists():self.skipTest('Real capture only available on Vultr')
  session=json.loads(fixture.read_text())
  start=session['states'][0]['at_ms'];length=(session['states'][-1]['at_ms']-start)/1000.+.35
  _,samples=cursor_motion(session['events'],start,length,60)
  cursor=cursor_track(samples=samples,fps=60,duration=length,
                      stiffness=120.,damping=18.)
  cursor=align_click_positions(cursor,session['events'],start,60)
  for e in session['events']:
   if e['type']=='pointerdown' and e.get('x') is not None:
    idx=round((e['t']-start)*.06)
    self.assertLessEqual(math.dist(cursor[idx],(e['x'],e['y'])),3.)

class FlagshipEditTests(unittest.TestCase):
 def test_original_sound_bed_is_48k_deterministic_bounded_and_fades(self):
  if np is None:self.skipTest('Requires numpy')
  from flagship_edit import original_ambient_bed,RATE
  a=original_ambient_bed(2*RATE)
  self.assertEqual(a.shape,(96000,2))
  self.assertTrue(np.array_equal(a,original_ambient_bed(2*RATE)))
  self.assertEqual(float(a[0,0]),0.)
  self.assertLess(float(np.max(np.abs(a))),.2)
  self.assertGreater(float(np.sqrt(np.mean(a[25000:68000]**2))),.02)

class FlagshipCursorShutterTests(unittest.TestCase):
 def test_fast_cursor_blur_is_small_symmetric_and_never_shadows_contact(self):
  if np is None:self.skipTest('Requires numpy/opencv')
  from flagship_motion import cursor_shutter_art
  art=np.zeros((64,64,4),np.uint8)
  art[12:39,19:38,:3]=10
  art[12:39,19:38,3]=255
  blurred=cursor_shutter_art(art,(6.,0.))
  self.assertEqual(blurred.shape,art.shape)
  self.assertFalse(np.array_equal(blurred,art))
  self.assertLess(abs(int(blurred[:,:,3].sum())-int(art[:,:,3].sum())),170)
  self.assertTrue(np.array_equal(cursor_shutter_art(art,(6.,0.),contact_locked=True),art))
  self.assertTrue(np.array_equal(blurred,cursor_shutter_art(art,(6.,0.))))
  self.assertTrue(np.array_equal(cursor_shutter_art(art,(0.,0.)),art))
  with self.assertRaises(ValueError):cursor_shutter_art(art,(float('nan'),1.))
 def test_source_capture_has_no_competing_animated_bee_while_product_hero_keeps_it(self):
  if np is None:self.skipTest('Requires numpy/opencv')
  import cv2
  folder=ROOT/'studio/.tmp/flagship/capture-v2'
  img=folder/'states/001-approach.png'
  if not img.exists():self.skipTest('Vultr capture fixture not packaged')
  screenshot=cv2.imread(str(img),cv2.IMREAD_GRAYSCALE)
  # These pixels are the *recorded click target*, not a cosmetically
  # painted/blurred patch in the final export.
  forbidden=screenshot[610:795,590:730]
  self.assertLess(float(np.mean(forbidden<70)),.007)
  trace=json.loads((folder/'session.json').read_text())
  self.assertEqual(trace['presentation_hide_selector'],'img[src*="bee-cutout-"]')
  proof=ROOT/'studio/.tmp/flagship/hero-v1/manifest.json'
  if proof.exists():
   from flagship_story_v3 import verify_hero
   source,receipt=verify_hero(proof)
   # Separate genuine brand shot retains the real bee; no global deletion.
   self.assertEqual(source.shape,(1440,2560,3))
   self.assertEqual(receipt['heading'],'The cloud for AI agents')
