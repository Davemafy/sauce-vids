"""Reference frame ledgers are exact measurements, not inferred cinema plans."""
from pathlib import Path
import json
import sys
import hashlib

import cv2
import numpy as np
import pytest

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"scripts"))
from reference_frame_ledger import analyze_reference, sha256


def test_exact_frame_identity_no_downsampling(tmp_path):
    p=tmp_path/"synthetic.mp4"
    writer=cv2.VideoWriter(str(p),cv2.VideoWriter_fourcc(*"mp4v"),10.0,(96,64))
    assert writer.isOpened()
    writer.write(np.zeros((64,96,3),np.uint8))
    writer.write(np.full((64,96,3),255,np.uint8))
    writer.write(np.full((64,96,3),255,np.uint8))
    writer.release()

    ledger=analyze_reference(p,sha256(p))
    assert ledger["stream"]["decodedFrameCount"]==3
    assert ledger["stream"]["fpsNumerator"]==10
    assert ledger["stream"]["fpsDenominator"]==1
    assert ledger["perFrame"][0]["changedFractionGt24"] is None
    assert ledger["perFrame"][1]["changedFractionGt24"]>.9
    assert ledger["perFrame"][2]["changedFractionGt24"]<.01
    assert len(ledger["perFrame"][0]["decodedBgrSha256"])==64
    assert ledger["perFrame"][0]["decodedBgrSha256"]!=ledger["perFrame"][1]["decodedBgrSha256"]
    assert [e["frame"] for e in ledger["candidateDiscontinuities"]]==[1]
    assert ledger["fidelity"]["eligibleAsOneToOneTrainingExample"] is False


def test_reference_exact_source_hash_required(tmp_path):
    p=tmp_path/"other.mp4"
    p.write_bytes(b"random bytes")
    with pytest.raises(ValueError,match="do not match reviewed source"):
        analyze_reference(p,"0"*64)


def test_real_arcade_frame_ledger_covers_all_frames_no_fake_certification():
    p=ROOT/"references/arcade-stack-by-ramp.frame-ledger.json"
    obj=json.loads(p.read_text())
    frames=obj["perFrame"]
    assert obj["stream"]["width"]==1920
    assert obj["stream"]["height"]==1080
    assert obj["stream"]["fpsNumerator"]==30
    assert obj["stream"]["fpsDenominator"]==1
    assert obj["stream"]["decodedFrameCount"]==2016
    assert [f["frame"] for f in frames]==list(range(2016))
    assert all(len(f["decodedBgrSha256"])==64 for f in frames)
    assert obj["fidelity"]["sourceFrameCoverage"]=="COMPLETE"
    assert obj["fidelity"]["referenceMatchedOutput"]=="NONE"
    assert not obj["fidelity"]["eligibleAsOneToOneTrainingExample"]


def test_reviewed_cut_frames_match_ledger_and_remain_nonexhaustive():
    ledger=json.loads((ROOT/"references/arcade-stack-by-ramp.frame-ledger.json").read_text())
    review=json.loads((ROOT/"references/arcade-stack-by-ramp.cut-review.json").read_text())
    assert review["decodedFrameLedgerSha256"]==hashlib.sha256(
        (ROOT/"references/arcade-stack-by-ramp.frame-ledger.json").read_bytes()
    ).hexdigest()
    assert review["referenceSha256"]==ledger["sourceSha256"]
    confirmed=[x["incomingFrame"] for x in review["reviewedBoundaries"]]
    candidates=[x["frame"] for x in ledger["candidateDiscontinuities"]]
    assert confirmed==candidates
    assert review["frameCount"]==2016
    assert all(x["precedingFrame"]==x["incomingFrame"]-1 for x in review["reviewedBoundaries"])
    assert not review["allShotsCatalogued"]
    assert not review["productionGeminiEligible"]
    assert not review["oneToOneMotionReconstructionMatched"]
