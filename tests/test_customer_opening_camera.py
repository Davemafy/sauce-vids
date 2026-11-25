"""Native customer opening: observed pointer motion and verified-result dolly."""
import json
from unittest.mock import patch

import backend.customer_story as story


class Handle:
    def __init__(self,box,visible=True):
        self.box=box;self.visible=visible
    def is_visible(self):return self.visible
    def bounding_box(self):return self.box


def test_first_action_anchor_uses_only_real_menu_geometry():
    planned={"actions":[{"kind":"option","group":"Theme","label":"Actual choice"}],"picker":None}
    rect={"x":200,"y":100,"width":300,"height":60}
    with patch.object(story,"menu_triggers",return_value=[("Theme",Handle(rect))]):
        assert story.first_action_anchor(object(),planned)==(350,130)
    with patch.object(story,"menu_triggers",return_value=[("Other",Handle(rect))]):
        assert story.first_action_anchor(object(),planned) is None
    with patch.object(story,"menu_triggers",return_value=[("Theme",Handle({"x":-20,"y":10,"width":30,"height":20}))]):
        assert story.first_action_anchor(object(),planned) is None
    with patch.object(story,"menu_triggers",return_value=[("Theme",Handle(rect,False))]):
        assert story.first_action_anchor(object(),planned) is None


def test_single_real_picker_or_tab_anchor_only(monkeypatch):
    h=Handle({"x":300,"y":400,"width":100,"height":60})
    monkeypatch.setattr(story,"discover",lambda page:[{"label":"Theme","locator":h}])
    plan={"actions":[{"kind":"option","label":"Doom"}],"picker":"Theme"}
    assert story.first_action_anchor(object(),plan)==(350,430)
    plan["actions"]=[{"kind":"tab","label":"Dashboard"}]
    monkeypatch.setattr(story,"tabs",lambda page:[("Dashboard",h)])
    assert story.first_action_anchor(object(),plan)==(350,430)


def test_opening_pointer_move_is_real_bounded_and_without_click():
    samples=[];when=[]
    assert story.opening_pointer_approach(
        lambda x,y:samples.append((x,y)),when.append,(320,250))==12
    assert len(samples)==12 and len(when)==12
    assert min(x for x,y in samples)>=0 and max(x for x,y in samples)<=story.W
    assert when[0]>.12 and abs(when[-1]-.70)<.00001
    assert all(b>a for a,b in zip(when,when[1:]))
    assert abs(samples[-1][0]-294)<.001 and abs(samples[-1][1]-238)<.001
    assert story.opening_pointer_approach(lambda *_:None,lambda *_:None,None)==0


def test_long_story_camera_never_zoom_before_verified_result():
    from pathlib import Path
    import tempfile
    from unittest.mock import patch
    import sys
    sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
    from source_event_director import direction
    # Only verified original source event geometry, no fabricated DOM in film.
    events=[]
    for i,(start,t) in enumerate(((3.,5.),(9.,11.),(16.,18.),(23.,25.))):
        events.append({"start":start,"end":start+.1,"t":t,"evidence":"Verified change",
          "kind":"click","targetRect":{"x":220,"y":270,"width":120,"height":60},
          "resultRect":{"x":450,"y":200,"width":3000,"height":1500}})
    with tempfile.TemporaryDirectory() as d:
        source=Path(d)/"real.mp4";source.write_bytes(b"source for isolated director schema check")
        manifest=Path(d)/"events.json";manifest.write_text(json.dumps({"cursorless":True,
                     "pointer_samples":[{"t":1.,"x":350,"y":300},{"t":26.,"x":360,"y":300}],
                     "events":events}))
        packet={"actualCapture":{"durationSeconds":30.,"resolution":[3840,2160],
                "nativeFps":60,"pointerProvenance":{"recordedPointerTrackAvailable":True}}}
        with patch("film_director_capabilities.build_contract",return_value=packet):
            plan=direction(source,manifest)
    keys=plan["studioStage"]["camera"]
    assert keys[0]["viewScale"]==1.
    for k in keys[1:-1]:
        if k["viewScale"]>1:
            assert any(k["startAt"]>=e["t"] for e in events)
            assert k["viewScale"]==1.065
    assert keys[-1]["viewScale"]==1.
    assert not any(k.get("cut") for k in keys)
