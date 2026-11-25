import unittest
import numpy as np
from scripts.customer_craft_contract import verify_plan,split_findings

class Stage:
    source_size=(3840,2160)
    output_size=(1920,1080)
    stage_preset="cloud_window_clearface_v1"
    immersive=True
    motion_style="cinematic"
    shutter=0
    payoff_mode="overview"
    def __init__(self,defect=None):self.defect=defect
    def source_aligned_cuts(self,fps):return (60,) if self.defect=="cut" else ()
    def quad(self,t):
        q=np.float32([[96,54],[1824,54],[1824,1026],[96,1026]])
        if self.defect=="jump" and abs(t-10)<.00001:q+=np.float32([30,0])
        if self.defect=="clip" and abs(t-10)<.00001:q[:,1]-=45
        return q
    def region_visibility(self,t,box):
        return .8 if self.defect=="result" and 3.5<=t<=4.0 else 1.
    def point_visible(self,t,x,y):return not(self.defect=="pointer" and 2.<=t<2.2)

class CraftTests(unittest.TestCase):
    def setUp(self):
        self.manifest={"duration":30.,"cursorless":True,"events":[
            {"start":t,"end":t+.1,"t":t+1.5,"targetRect":{"x":1000,"y":500,"width":200,"height":100},"resultRect":{"x":800,"y":400,"width":2800,"height":1500}}
            for t in (2.,9.,17.,24.)]}
        self.plan={"schema":"sauce-film-plan-v1","durationSeconds":30.,"presentation":"fullscreen","cursor":"recorded","audio":{"mode":"eventFoley","eventIndices":[0,1,2,3],"clickGain":.44,"motionGain":.22,"masterGain":.78},"studioStage":{}}
        self.pointer=np.asarray([[i/10,1100,550] for i in range(300)],dtype=float)
    def verify(self,defect=None):
        return verify_plan(self.plan,self.manifest,Stage(defect),self.pointer,60,1800)
    def test_good_plan_checks_every_frame_and_action(self):
        v=self.verify();self.assertEqual(v["checkedFrames"],1800);self.assertEqual(v["checkedActions"],4)
        self.assertEqual(v["minimumTargetVisible"],1.)
        self.assertFalse(v["creativeApproved"])
    def test_interstitial_camera_and_earlier_action_defects_fail(self):
        for defect in ("jump","clip","cut","result","pointer"):
            with self.subTest(defect=defect),self.assertRaises(ValueError):self.verify(defect)
    def test_weak_audio_and_hidden_cursor_rejected(self):
        self.plan["audio"]["clickGain"]=0
        with self.assertRaises(ValueError):self.verify()
        self.plan["audio"]["clickGain"]=.44
        self.plan["cursor"]="none"
        with self.assertRaises(ValueError):self.verify()
    def test_cursor_must_hit_actual_target_not_just_be_visible(self):
        self.pointer[:,1]=1600
        with self.assertRaisesRegex(ValueError,"misses genuine action target"):self.verify()
    def test_no_unreviewed_optical_effects(self):
        self.plan["glassLoupe"]={}
        with self.assertRaises(ValueError):self.verify()
    def test_findings_split_never_approves(self):
        q=split_findings({"findings":[{"code":"STATIC_OPENING_2S"},{"code":"TRANSIENT_FRAME_REVERSION"},{"code":"UNKNOWN"}]})
        self.assertEqual(q["editorial"],["STATIC_OPENING_2S"])
        self.assertEqual(q["technical"],["TRANSIENT_FRAME_REVERSION","UNKNOWN"])
        self.assertFalse(q["creativeApproved"])

if __name__=="__main__":unittest.main()
