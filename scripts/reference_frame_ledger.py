"""Extract exact decoded frame identity and measured motion diagnostics.

This is NOT a source layer reconstruction or a cinematic style certification.
No video frames, screenshots, speech or other copyrighted pixels are emitted.
Only a frame hash ledger and explicit measurements/candidate scene boundaries.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import subprocess
from fractions import Fraction
from pathlib import Path

import cv2
import numpy as np


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def video_properties(video: Path):
    cp = subprocess.run(
        ["ffprobe","-v","error","-select_streams","v:0",
         "-show_entries","stream=width,height,avg_frame_rate,r_frame_rate,nb_frames,pix_fmt",
         "-show_entries","format=duration",
         "-of","json",str(video)],
        check=True, capture_output=True, text=True)
    info = json.loads(cp.stdout)
    streams = info.get("streams", [])
    if len(streams) != 1: raise ValueError("Need exactly one video stream")
    s = streams[0]
    fps = Fraction(s["avg_frame_rate"])
    # Exact integer frame clock is a meaningful guarantee for this reference.
    if fps <= 0 or int(s.get("nb_frames") or 0) <= 0:
        raise ValueError("Need CFR reference with frame count")
    if Fraction(s["r_frame_rate"]) != fps:
        raise ValueError("Average/rate mismatch, cannot assert CFR frame times")
    return s, fps, float(info["format"]["duration"])


def analyze_reference(video: Path, expected_sha256: str):
    source_hash=sha256(video)
    if source_hash != expected_sha256:
        raise ValueError("Reference bytes do not match reviewed source identity")
    props,fps,duration=video_properties(video)
    width=int(props["width"]);height=int(props["height"]);frame_count=int(props["nb_frames"])
    cap=cv2.VideoCapture(str(video))
    if not cap.isOpened():raise ValueError("Cannot decode reference")
    entries=[];prev=None;candidate_frames=[]
    try:
        index=0
        while True:
            ok,frame=cap.read()
            if not ok:break
            if frame.shape!=(height,width,3):
                raise ValueError("Decoded reference geometry differs from stream")
            # Hash exact uint8 BGR decoded pixels, not sampled or proxy-sized ones.
            px_hash=hashlib.sha256(frame.tobytes(order="C")).hexdigest()
            # Motion diagnostic is measured across every full-resolution pixel.
            # Significant change is a HEURISTIC, not a cut annotation.
            if prev is None:
                changed=None;change_score=None
            else:
                delta=cv2.absdiff(frame,prev)
                grayscale=cv2.cvtColor(delta,cv2.COLOR_BGR2GRAY)
                changed=float(cv2.countNonZero(cv2.compare(grayscale,24,cv2.CMP_GT)))/(width*height)
                change_score=round(changed,7)
                if changed>0.18:
                    candidate_frames.append(index)
            # This mean is objective frame-wide appearance, NOT semantic UI geometry.
            b,g,r=cv2.mean(frame)[:3]
            entries.append({
                "frame":index,
                "decodedBgrSha256":px_hash,
                "meanBgr":[round(b,3),round(g,3),round(r,3)],
                "changedFractionGt24":change_score,
            })
            prev=frame
            index+=1
    finally:
        cap.release()
    if index!=frame_count:
        raise ValueError(f"Video stream declares {frame_count}, decoded {index}")
    return {
        "schema":"sauce-reference-measurements-v1",
        "sourceSha256":source_hash,
        "sourceType":"third-party public reference; analysis-only",
        "extraction":{
            "decoder":"OpenCV VideoCapture, uint8 BGR, no resize",
            "frameHash":"SHA256 of decoded BGR uint8 frame pixels, row-major",
            "motionDiagnostic":"full-resolution |gray(BGR_diff)| > 24/255",
            "motionSceneThreshold":0.18,
            "cutCandidateStatus":"HEURISTIC_UNVERIFIED",
            "referenceSourceClaim":"encoded presentation only; source edit project and UI layers unavailable",
        },
        "stream":{
            "width":width,"height":height,
            "fpsNumerator":fps.numerator,"fpsDenominator":fps.denominator,
            "declaredFrameCount":frame_count,"decodedFrameCount":index,
            "durationSeconds":duration,
            "frameTimestampRule":"frameIndex * fpsDenominator / fpsNumerator (CFR)",
        },
        "candidateDiscontinuities":[
            {"frame":i,"timeNumerator":i*fps.denominator,"timeDenominator":fps.numerator,
             "status":"UNVERIFIED_POSSIBLE_CUT_OR_LARGE_MOTION"}
            for i in candidate_frames
        ],
        "perFrame":entries,
        "fidelity":{
            "sourceFrameCoverage":"COMPLETE",
            "measuredSourceFrames":index,
            "exactShotBoundaries":"NOT_MEASURED",
            "objectMasksAndTracks":"NOT_MEASURED",
            "cameraAndLayerTransforms":"NOT_MEASURED",
            "referenceMatchedOutput":"NONE",
            "customerReady":"NO",
            "eligibleAsOneToOneTrainingExample":False,
        },
    }


def main():
    p=argparse.ArgumentParser(description="Analysis-only decoded-frame reference ledger")
    p.add_argument("--video",type=Path,required=True)
    p.add_argument("--reference-sha256",required=True)
    p.add_argument("--out",type=Path,required=True)
    args=p.parse_args()
    if not args.video.is_file():raise FileNotFoundError(args.video)
    if not (len(args.reference_sha256)==64 and all(c in "0123456789abcdef" for c in args.reference_sha256)):
        raise ValueError("Reference sha256 must be a canonical lowercase SHA256")
    measured=analyze_reference(args.video,args.reference_sha256)
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(measured,separators=(",",":"))+"\n")
    print(json.dumps({
        "sourceSha256":measured["sourceSha256"],
        "decodedFrames":measured["stream"]["decodedFrameCount"],
        "candidateDiscontinuities":len(measured["candidateDiscontinuities"]),
        "outputBytes":args.out.stat().st_size,
        "oneToOneCertified":measured["fidelity"]["eligibleAsOneToOneTrainingExample"],
    },indent=2))

if __name__=="__main__":main()
