"""Source-faithful semantic plane verification at the MP4 compositor boundary."""
import sys
from pathlib import Path
import unittest
import numpy as np
import cv2

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
from semantic_spatial_handoff import (
    VerifiedPatch,eased,source_difference,locate_sustained_change,
    crop_quad_from_homography,projected,interpolate_quad,overlay,audio_clock
)


class SemanticHandoffTest(unittest.TestCase):
    def setUp(self):
        self.w,self.h=640,360
        self.before=np.full((self.h,self.w,3),190,dtype=np.uint8)
        self.after=self.before.copy()
        self.patch=VerifiedPatch(self.w,self.h,100,80,120,70)
        self.after[85:135,110:200]=(15,60,240)

    def test_persistent_source_change(self):
        frames=[self.before.copy() for _ in range(4)]
        frames += [self.after.copy() for _ in range(6)]
        self.assertEqual(locate_sustained_change(frames,200,self.patch),204)
        self.assertGreater(source_difference(frames[3],frames[4],self.patch),5)

    def test_no_fabricated_result(self):
        with self.assertRaisesRegex(ValueError,"sustained"):
            locate_sustained_change([self.before.copy() for _ in range(7)],
                                    100,self.patch)

    def test_invalid_bounds_rejected(self):
        for args in [(640,360,-2,80,120,70),(640,360,570,80,120,70),
                     (640,360,100,80,2,70)]:
            with self.assertRaises(ValueError):VerifiedPatch(*args)

    def test_pixel_identity_at_handoff(self):
        quad=np.float32([[0,0],[640,0],[640,360],[0,360]])
        full,mask=projected(self.after,quad,(640,360),interpolation=cv2.INTER_NEAREST)
        self.assertTrue(np.array_equal(full,self.after))
        crop=self.patch.extract(self.after)
        dest=crop_quad_from_homography(self.patch,quad)
        patch,alpha=projected(crop,dest,(640,360),interpolation=cv2.INTER_NEAREST)
        out=overlay(full,patch,alpha)
        inside=out[90:120,120:170]
        self.assertTrue(np.array_equal(inside,self.after[90:120,120:170]))
        self.assertTrue(np.array_equal(out[:70],self.after[:70]))

    def test_source_quad_tracks_projective_plane(self):
        start=np.float32([[0,0],[640,0],[640,360],[0,360]])
        end=np.float32([[15,35],[415,20],[445,320],[30,339]])
        self.assertTrue(np.allclose(interpolate_quad(start,end,0),start))
        self.assertTrue(np.allclose(interpolate_quad(start,end,1),end))
        original=crop_quad_from_homography(self.patch,start)
        self.assertLess(np.max(np.abs(original-self.patch.corners())),.01)

    def test_smooth_finite_ease(self):
        self.assertEqual(eased(-1),0)
        self.assertEqual(eased(2),1)
        self.assertAlmostEqual(eased(.5),.5)
        with self.assertRaises(ValueError):eased(float("nan"))

    def test_transient_flash_is_not_a_real_result(self):
        frames=[self.before.copy() for _ in range(3)]
        frames.append(self.after.copy())
        frames.extend(self.before.copy() for _ in range(5))
        with self.assertRaisesRegex(ValueError, "sustained"):
            locate_sustained_change(frames, 20, self.patch, persistence=3)

    def test_two_source_patches_share_same_projected_clock(self):
        left=VerifiedPatch(self.w,self.h,100,80,120,70)
        right=VerifiedPatch(self.w,self.h,260,120,100,60)
        self.after[120:180,260:360]=(85,120,240)
        initial=np.float32([[0,0],[640,0],[640,360],[0,360]])
        final=np.float32([[25,20],[480,26],[468,310],[30,318]])
        for t in (0,.25,.5,.75,1):
            full_quad=interpolate_quad(initial,final,t)
            for patch in (left,right):
                roi=patch.extract(self.after)
                owned=crop_quad_from_homography(patch,full_quad)
                self.assertGreater(cv2.contourArea(owned),40)
                self.assertEqual(roi.shape[:2],(patch.height,patch.width))

    def test_invalid_recording_format_fails_closed(self):
        with self.assertRaisesRegex(ValueError,"unverified"):
            self.patch.extract(self.after.astype(np.float32))

    def test_audio_frame_clock(self):
        self.assertEqual(audio_clock(300),240000)
        with self.assertRaises(ValueError):audio_clock(-1)


if __name__=="__main__": unittest.main()
