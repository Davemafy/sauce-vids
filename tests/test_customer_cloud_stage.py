"""Customer full-glass stage: source-only proof, exact page pixels, safe motion."""
from __future__ import annotations
import unittest
import numpy as np
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from scripts.customer_cloud_window import (verified_cloud_moment,render_customer_cloud,
                                             verified_detail_matrix,verified_detail_source)


def sample_events():
    return [
        {"kind":"click","t":.63,"semanticGoal":"Inspect real public modal",
         "label":"Open modal"},
        {"kind":"state_change","t":1.47,
         "evidence":"Observed public modal opened in real Chromium",
         "resultRect":{"x":710.,"y":80.,"width":350.,"height":260.}},
        {"kind":"interaction_complete","t":3.7},
    ]


class CustomerCloudMomentTests(unittest.TestCase):
    def test_real_clicked_outcome_drives_only_post_result_camera(self):
        moment=verified_cloud_moment(sample_events(),5.0,(1920,1080))
        self.assertEqual(moment.click,.63)
        self.assertEqual(moment.result,1.47)
        self.assertEqual(moment.amplitude(.63),0)
        self.assertEqual(moment.amplitude(1.50),0)
        self.assertGreater(moment.amplitude(2.5),.9)
        self.assertLess(moment.amplitude(4.65),.001)

    def test_source_detail_occurs_only_after_proof_and_cannot_invent_margins(self):
        m=verified_cloud_moment(sample_events(),5.0,(1920,1080))
        pre=verified_detail_matrix(m,1.1,(1920,1080))
        self.assertTrue(np.array_equal(pre,np.float32([[1,0,0],[0,1,0]])))
        mid=verified_detail_matrix(m,2.5,(1920,1080))
        self.assertGreater(mid[0,0],1.5)
        self.assertLessEqual(mid[0,2],0)
        self.assertGreaterEqual(mid[0,2],1920*(1-mid[0,0]))
        self.assertLessEqual(mid[1,2],0)
        self.assertGreaterEqual(mid[1,2],1080*(1-mid[1,1]))
        r=m.bounds
        self.assertGreaterEqual(r["x"]*mid[0,0]+mid[0,2],0)
        self.assertLessEqual((r["x"]+r["width"])*mid[0,0]+mid[0,2],1920)
        self.assertLessEqual((r["y"]+r["height"])*mid[1,1]+mid[1,2],1080)

    def test_unverified_or_incomplete_outcome_never_generates_stage(self):
        for events in ([],sample_events()[:1],sample_events()[:2],
                       [sample_events()[0],{**sample_events()[1],"evidence":""},
                        sample_events()[2]],
                       [sample_events()[0],{**sample_events()[1],"t":3.0},
                        sample_events()[2]],
                       [sample_events()[0],{**sample_events()[1],"resultRect":
                        {"x":1900,"y":50,"width":300,"height":200}},sample_events()[2]]):
            with self.subTest(events=events):
                with self.assertRaises(ValueError):
                    verified_cloud_moment(events,5.0,(1920,1080))

    def test_actual_cobalt_stage_is_source_derived_without_fake_ui(self):
        import cv2
        from scripts.cloud_window_sky_stage import window_geometry,sky_background
        # Synthetic image only for *unit test*, never a customer demo.
        frame=np.full((1080,1920,3),(19,28,31),np.uint8)
        cv2.rectangle(frame,(620,200),(1300,480),(203,235,248),-1)
        cv2.putText(frame,"SOURCE 29",(720,330),cv2.FONT_HERSHEY_SIMPLEX,
                    2.0,(10,18,25),5,cv2.LINE_AA)
        moment=verified_cloud_moment(sample_events(),5.0,(1920,1080))
        at0=render_customer_cloud(frame,1.2,moment)
        at1=render_customer_cloud(frame,2.5,moment)
        self.assertEqual(at0.shape,(1080,1920,3))
        self.assertEqual(at1.shape,(1080,1920,3))
        # The outer corners remain the original cobalt print during motion.
        sky=sky_background((1920,1080))
        for y,x in ((0,0),(1079,1919)):
            self.assertTrue(np.array_equal(at0[y,x],at1[y,x]))
        x0,y0,x1,y1,_=window_geometry((1920,1080),(1920,1080))
        # The blue cloud print must NEVER bleed across the real source.
        # Verify a representative *dim* original UI plate as well as white.
        from scripts.cloud_shadow_stage import render_cloud_overview
        # The center of the window must be exactly a source resample, even
        # during a modal (large dim background) — no decorative overlays.
        clean=cv2.resize(frame,(x1-x0,y1-y0),interpolation=cv2.INTER_AREA)
        center=at0[y0+80:y1-80,x0+80:x1-80]
        want=clean[80:-80,80:-80]
        self.assertLess(np.abs(center.astype(np.int16)-want.astype(np.int16)).mean(),.02)
        # Under real modal dimming, the sky must not appear over the
        # opaque browser when the floating window advances. This catches
        # the previous (source-oldSky)+newSky subtraction bug.
        scale=1.+.043*moment.amplitude(2.5)
        M=np.float32([[scale,0,(1-scale)*960],[0,scale,(1-scale)*540]])
        # Expected image consists ONLY of the source-verified post-result
        # crop, then the whole-browser physical push. No old/new sky delta.
        focused=verified_detail_source(frame,2.5,moment)
        foreground=render_cloud_overview(focused,(1920,1080),
                         stage_preset="cloud_window_fullglass_v1",coat_source=False)
        expected=cv2.warpAffine(foreground,M,(1920,1080),
                flags=cv2.INTER_LINEAR,borderMode=cv2.BORDER_CONSTANT)
        inner=(slice(290,730),slice(360,1560))
        self.assertLess(np.abs(at1[inner].astype(np.int16)-
                         expected[inner].astype(np.int16)).mean(),1.5)
        coating=render_cloud_overview(frame,(1920,1080),
                    stage_preset="cloud_window_fullglass_v1",coat_source=True)
        self.assertGreater(np.abs(coating[y0+80:y1-80,x0+80:x1-80].astype(np.int16)-
                         want.astype(np.int16)).mean(),.2)
        # At least part of the native source content is still visible in
        # the full large window. No fake borders/address bars are authored.
        middle=at0[y0+100:y1-100,x0+100:x1-100]
        self.assertGreater(middle.shape[0],100)
        self.assertGreater(middle.shape[1],100)
        self.assertGreater(np.abs(at1.astype(np.int16)-at0.astype(np.int16)).mean(),.01)


if __name__=="__main__":
    unittest.main()


def test_wide_real_result_caps_detail_zoom_and_stays_visible():
    events=sample_events()
    r={'x':576.7,'y':182.,'width':1343.3,'height':882.}
    events[1]['resultRect']=r
    m=verified_cloud_moment(events,5.,(1920,1080))
    a=verified_detail_matrix(m,2.8,(1920,1080))
    z=float(a[0,0])
    assert 1.<z<=1080/882+.0001
    assert z*r['x']+a[0,2]>=-.01
    assert z*(r['x']+r['width'])+a[0,2]<=1920+.01
    assert z*r['y']+a[1,2]>=-.01
    assert z*(r['y']+r['height'])+a[1,2]<=1080+.01


def test_alternate_stage_grades_quiet_background_without_touching_product():
    from types import SimpleNamespace
    import cv2
    from scripts.cloud_shadow_stage import render_cloud_stage
    from cloud_window_clearface_stage import window_geometry
    from cloud_window_sky_stage import sky_background
    size=(640,360)
    x0,y0,x1,y1,_=window_geometry(size,size)
    q=np.float32([[x0,y0],[x1,y0],[x1,y1],[x0,y1]])
    M=np.float32([[1,0,0],[0,1,0]])
    yy,xx=np.indices((360,640))
    source=np.stack([(xx%256),(yy%256),((xx+yy)%256)],axis=-1).astype(np.uint8)
    def render(tone,strength=0.):
        stage=SimpleNamespace(source_size=size,output_size=size,
            stage_preset="cloud_window_clearface_v1",immersive=True,
            view_transform=lambda t:M,quad=lambda t:q,
            shutter_times=lambda t:None,hero_backdrop_strength=lambda t:strength,
            backdrop_tone=tone)
        return render_cloud_stage(stage,source,0.)
    cobalt=render("cobalt")
    muted=render("muted")
    graphite=render("graphite")
    # At fully opaque aperture pixels the grade has no influence on the UI.
    inside=(slice(y0+30,y1-30),slice(x0+30,x1-30))
    for image in (muted,graphite,render("graphite",.9)):
        np.testing.assert_array_equal(image[inside],cobalt[inside])
    # Check the exact cobalt corners where the contact shadow is absent.
    sky=sky_background(size)
    np.testing.assert_array_equal(cobalt[0,0],sky[0,0])
    # Outer strips are outside the opaque product; compare luma contrast.
    strip=lambda im:cv2.cvtColor(im,cv2.COLOR_BGR2GRAY)[:10].std()
    assert strip(graphite)<strip(muted)<strip(cobalt)
