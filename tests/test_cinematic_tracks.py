"""Cinematic camera acceptance: action-led, stable, no context-free zoom."""
from __future__ import annotations
import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from cinematic_tracks import cinematic_camera
from spring_motion import cursor_track


def synthetic():
    base=1000.0
    rows=[{'t':base+i*40,'type':'pointermove','x':900-(i/30)**2*600,
           'y':510-(i/30)**2*150,'cursor':'default'}
           for i in range(31)]
    rows.extend([
     {'t':2220,'type':'pointerdown','x':300,'y':360,'box':{'x':215,'y':344,'width':170,'height':32}},
     {'t':2300,'type':'dialog-visible','box':{'x':440,'y':180,'width':400,'height':360}},
    ])
    for i in range(31):
        rows.append({'t':2450+i*32,'type':'pointermove',
                'x':300+(i/30)**2*310,'y':360+(i/30)**2*100,'cursor':'pointer'})
    rows.append({'t':3500,'type':'pointerdown','x':610,'y':460,
                 'box':{'x':480,'y':448,'width':260,'height':24}})
    return sorted(rows,key=lambda a:a['t'])


class CinematicCameraTests(unittest.TestCase):
    def setUp(self):
        self.events=synthetic()

    def test_no_click_means_no_camera_movement(self):
        e=[v for v in self.events if v['type']!='pointerdown']
        track,meta=cinematic_camera(e,1000,4,60)
        self.assertEqual(meta['policy'],'no-click-no-zoom')
        self.assertEqual(set(track),{(1.,640.,360.)})

    def test_no_movement_before_cursor_approach(self):
        track,meta=cinematic_camera(self.events,1000,4.5,60)
        first=meta['first_zoom_frame']
        self.assertIsNotNone(first)
        self.assertGreaterEqual(first,1)
        pre_motion_frames=int((meta['first_pointer_motion_ms']-1000)/1000*60)
        for state in track[:pre_motion_frames]:
            self.assertEqual(state,(1.,640.,360.))
        self.assertGreater(track[first][0],1.0001)

    def test_zoom_during_real_cursor_approach(self):
        track,_=cinematic_camera(self.events,1000,4.5,60)
        self.assertGreater(track[60][0],1.015)
        self.assertLess(track[60][0],1.17)

    def test_real_dialog_changes_camera_focus(self):
        track,_=cinematic_camera(self.events,1000,4.5,60)
        pre=track[round(1.18*60)]
        modal=track[round(1.9*60)]
        self.assertLess(pre[1],550)
        self.assertGreater(modal[1],630)
        self.assertGreater(modal[0],pre[0])

    def test_dialog_stays_inside_safe_zoom(self):
        track,meta=cinematic_camera(self.events,1000,4.5,60)
        self.assertLessEqual(meta['max_zoom'],1.44)
        self.assertGreater(meta['max_zoom'],1.33)
        self.assertAlmostEqual(meta['dialog_css_center'][0],640.)

    def test_no_random_camera_change(self):
        a,meta=cinematic_camera(self.events,1000,4.5,60)
        b,meta2=cinematic_camera(self.events,1000,4.5,60)
        self.assertEqual(a,b)
        self.assertEqual(meta,meta2)
        self.assertEqual(len(a),270)

    def test_sparse_legacy_capture_stays_wide_instead_of_inventing_motion(self):
        events=[v for v in self.events if v['type']!='pointermove']
        events.extend([
            {'type':'pointermove','t':1050.,'x':900.,'y':500.},
            {'type':'pointermove','t':2200.,'x':300.,'y':360.},
        ])
        events.sort(key=lambda a:a['t'])
        frames,meta=cinematic_camera(events,1000.,3.5,60)
        self.assertEqual(meta['policy'],'legacy-sparse-cursor-no-automatic-zoom')
        self.assertEqual(set(frames),{(1.,640.,360.)})

    def test_missing_pointer_sample_rejected(self):
        events=[v for v in self.events if v['type']!='pointermove']
        with self.assertRaisesRegex(ValueError,'No pointer trajectory'):
            cinematic_camera(events,1000,4.5,60)

    def test_eased_clicks_remain_accurate(self):
        positions=[]
        for row in self.events:
            if row['type']=='pointermove':
                pos=(max(0.,(row['t']-1000)/1000),row['x'],row['y'])
                positions.append(pos)
        path=cursor_track(samples=positions,fps=60,duration=4.5,
                         stiffness=900,damping=60)
        # A stationary target has time to settle before the click.
        self.assertEqual(len(path),270)

if __name__=='__main__':unittest.main()
