"""Source-true modal reveal cut must only remove observed short source windows."""
from __future__ import annotations
import sys
from pathlib import Path
import pytest

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"scripts"))
from source_true_reveal_cut import validated_cut,MAX_TRANSITION_FRAMES,SAMPLES_PER_FRAME

SESSION={"states":[{"at_ms":1447.0}],
         "events":[
             {"type":"pointerdown","t":2232.9,"x":304.21,"y":360.37},
             {"type":"pointerup","t":2233.6,"x":304.21,"y":360.37},
             {"type":"click","t":2233.7,"x":304.,"y":360.},
             {"type":"pointerdown","t":3515.9,"x":614.,"y":461.},
         ]}


def test_evidence_checked_cut_preserves_click_jcut():
    evidence=validated_cut(SESSION,47,56)
    assert evidence["removedFrames"]==9
    assert evidence["firstRemoved"]==47
    assert evidence["firstRetainedAfter"]==56
    assert evidence["audioHeadSamples"]==48*800
    assert evidence["audioTailSamples"]==57*800
    assert evidence["audioTailSamples"]-evidence["audioHeadSamples"]==9*800
    assert SAMPLES_PER_FRAME==800


@pytest.mark.parametrize("begin,end",[(0,9),(45,56),(47,47),(47,70),
                                     (47,40),(-1,56),(47.1,56)])
def test_rejects_invalid_or_unproved_editorial_cuts(begin,end):
    with pytest.raises(ValueError):
        validated_cut(SESSION,begin,end)


def test_result_event_is_not_mistaken_for_modal_open():
    with pytest.raises(ValueError):
        validated_cut(SESSION,93,100)


def test_only_short_source_windows_can_be_removed():
    assert MAX_TRANSITION_FRAMES==12
    assert validated_cut(SESSION,47,59)["removedFrames"]==12
