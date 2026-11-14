#!/usr/bin/env python3
"""Estimate visible pan/zoom from real MP4 frames for comparison studies.

Uses SIFT correspondences and RANSAC, not manually authored camera keyframes.
UI animation and scene cuts can bias these estimates; results are advisory.
Requires opencv-python-headless and numpy.
"""
from __future__ import annotations
import argparse, json, math
from pathlib import Path
import cv2
import numpy as np

def measure(path: Path, step_s: float = 0.12) -> dict:
    cap = cv2.VideoCapture(str(path))
    fps = float(cap.get(cv2.CAP_PROP_FPS))
    frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    if not cap.isOpened() or fps <= 0 or frames <= 0:
        raise ValueError("Video could not be decoded")
    duration = frames / fps
    sift = cv2.SIFT_create(nfeatures=1100)
    matcher = cv2.BFMatcher(cv2.NORM_L2)
    prev = None
    samples = []
    for t in np.arange(0.0, duration, step_s):
        cap.set(cv2.CAP_PROP_POS_MSEC, float(t)*1000)
        ok, frame = cap.read()
        if not ok:
            break
        image = cv2.GaussianBlur(
            cv2.cvtColor(cv2.resize(frame, (480, 270)), cv2.COLOR_BGR2GRAY),
            (3,3), 0
        )
        key, desc = sift.detectAndCompute(image, None)
        if prev and desc is not None and prev[1] is not None:
            matches = matcher.knnMatch(prev[1], desc, k=2)
            good = [m for m,n in matches if m.distance < .75*n.distance]
            if len(good) >= 10:
                old_xy = np.float32([prev[0][m.queryIdx].pt for m in good])
                new_xy = np.float32([key[m.trainIdx].pt for m in good])
                matrix, inliers = cv2.estimateAffinePartial2D(
                    old_xy, new_xy, method=cv2.RANSAC,
                    ransacReprojThreshold=2.8, maxIters=2000
                )
                if matrix is not None and inliers is not None:
                    scale = float(np.hypot(matrix[0,0], matrix[0,1]))
                    offset = float(np.hypot(matrix[0,2],matrix[1,2]))
                    samples.append({
                        "t":round(float(t),3),
                        "zoom_pct":round((scale-1)*100,3),
                        "pan_px_at_480":round(offset,3),
                        "matches":len(good),
                        "confidence":round(float(inliers.mean()),3),
                    })
        prev = (key,desc)
    cap.release()
    reliable = [x for x in samples
                if x["matches"] >= 25 and x["confidence"] >= .68]
    moving = [x for x in reliable if abs(x["zoom_pct"])>.23
              or x["pan_px_at_480"]>2.5]
    groups = []
    for x in moving:
        direction = "push" if x["zoom_pct"]>0 else "release"
        if groups and x["t"]-groups[-1][-1]["t"] <= step_s*2.2                 and direction == ("push" if groups[-1][0]["zoom_pct"]>0 else "release"):
            groups[-1].append(x)
        else:
            groups.append([x])
    phases = []
    for g in groups:
        if len(g) < 3:continue
        phases.append({
            "kind":"push" if g[0]["zoom_pct"]>0 else "release",
            "from_s":g[0]["t"],
            "to_s":g[-1]["t"],
            "estimated_relative_scale":round(math.prod(1+x["zoom_pct"]/100 for x in g),3),
            "sample_count":len(g)
        })
    return {"source":str(path),"duration":round(duration,4),
            "source_fps":round(fps,3),"step_s":step_s,
            "reliable_samples":len(reliable),
            "samples":samples,"phases":phases}

if __name__ == "__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("video",type=Path)
    parser.add_argument("--out",type=Path)
    parser.add_argument("--step",type=float,default=.12)
    args=parser.parse_args()
    result=measure(args.video,args.step)
    report=json.dumps(result,indent=2)
    if args.out:
        args.out.parent.mkdir(parents=True,exist_ok=True)
        args.out.write_text(report)
    print(json.dumps({k:result[k] for k in ("duration","source_fps","reliable_samples","phases")},indent=2))
