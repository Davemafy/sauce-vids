"""Client-authored story arcs guide, but never authorize, a source-bound film."""
import json
import sys
from pathlib import Path
import pytest

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"scripts"))
from client_creative_brief import load_client_creative_brief


def proposal(host="refit.davemafy.xyz"):
    return {
      "schema":"sauce-creative-brief-v1",
      "project":"Refit — Model Migration Demo",
      "sourceUrl":"https://"+host,
      "output":{"targetDurationSeconds":80,"orientation":"landscape",
                "width":1920,"height":1080,"fps":60,"platform":"X"},
      "creativeDirection":{"goal":"Show an agent's migration and what survived"},
      "story":{"hook":"Changing models can break agent behavior",
               "payoff":"Verify before export"},
      "scenes":[
        {"id":"landing","role":"hook","targetSeconds":9,
         "actions":[{"type":"navigate","target":"/"},
                    {"type":"scroll","target":"recorded results"}],
         "recordedEvidence":{"original":"24/24","replacement":"13/24"}},
        {"id":"run","role":"demonstration","targetSeconds":12,
         "actions":[{"type":"click","target":"Run refund agent"},
                    {"type":"observe","target":"new run"}],
         "caption":"A real agent"},
        {"id":"verify","role":"resolution","targetSeconds":15,
         "actions":[{"type":"show","target":"Export verified configuration"}],
         "condition":"export_available"}
      ],
      "audio":{"mode":"narrated","script":["This is a client-authored idea, not evidence."]},
      "acceptance":{"sourceTrue":True,"humanCreativeReviewRequired":True}
    }


def test_refit_story_brief_is_only_unverified_client_intent(tmp_path):
    file=tmp_path/"refit-brief.json"
    file.write_text(json.dumps(proposal()))
    result=load_client_creative_brief(file,"https://refit.davemafy.xyz/")
    assert result["schema"]=="sauce-unverified-client-story-intent-v1"
    assert result["trust"]=="unverified_user_supplied_director_ideas_not_browser_evidence"
    assert result["clientBrief"]["scenes"][0]["recordedEvidence"]["original"]=="24/24"
    assert result["requestedDurationSeconds"]==80
    assert "Only actualCapture.verifiedEvents" in result["sourceTruthRule"]


def test_story_brief_cannot_direct_another_product(tmp_path):
    file=tmp_path/"refit.json";file.write_text(json.dumps(proposal()))
    with pytest.raises(ValueError,match="hostname"):
        load_client_creative_brief(file,"https://uicolors.app/generate/demo")


@pytest.mark.parametrize("mutation",[
    lambda p:p.update(schema="sauce-film-plan-v1"),
    lambda p:p.update(sourceUrl="http://refit.davemafy.xyz"),
    lambda p:p.update(sourceUrl="https://user:password@refit.davemafy.xyz"),
    lambda p:p.update(output={"orientation":"portrait"}),
    lambda p:p.update(scenes=[]),
    lambda p:p["scenes"][0]["actions"].append({"type":"purchase"}),
])
def test_brief_is_checked_not_executed(tmp_path,mutation):
    p=proposal();mutation(p)
    file=tmp_path/"invalid-brief.json";file.write_text(json.dumps(p))
    with pytest.raises(ValueError):
        load_client_creative_brief(file,"https://refit.davemafy.xyz")
