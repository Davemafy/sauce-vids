import json
import os
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from backend.customer_story import validated_selection, execute_story, StoryRejected, intersection, W,H
from backend.url_engine import execute,NoVerifiedProductAction

class CustomerStoryTests(unittest.TestCase):
    def setUp(self):
        self.catalog=[{"id":f"a{i}","kind":"option" if i==0 else "tab","label":f"Observed {i}"} for i in range(7)]
        self.url="https://example.com/"

    def test_requires_distinct_observed_actions_and_core_change(self):
        def validate(ids):
            return validated_selection(json.dumps({"ids":ids,"story":"A connected workflow"}),self.catalog)
        self.assertEqual([x["id"] for x in validate(["a0","a3","a2","a1"])["actions"]],["a0","a3","a2","a1"])
        for ids in (["a0","a1","a2"],["a1","a2","a3","a4"],["a0","a1","a1","a2"],["a0","a1","a2","invented"],[x["id"] for x in self.catalog]):
            self.assertIsNone(validate(ids))
        self.assertIsNone(validated_selection("not JSON",self.catalog))

    def test_customer_entry_uses_story_with_only_url(self):
        with TemporaryDirectory() as d, patch.dict(os.environ,{"SAUCE_CUSTOMER_STORY_SECONDS":"30"}), patch("backend.url_engine.validate_public_url"), patch("backend.customer_story.execute_story",return_value={"status":"needs_review"}) as story, patch("backend.url_engine.inspect") as short:
            self.assertEqual(execute(self.url,Path(d),intent="product_demo")["status"],"needs_review")
            self.assertEqual(story.call_args.args[:2],(self.url,Path(d)))
            self.assertEqual(story.call_args.kwargs,{"audio":"auto","brief":""})
            short.assert_not_called()

    def test_failed_exploration_cannot_capture_or_render(self):
        with TemporaryDirectory() as d, patch("backend.customer_story.explore",side_effect=StoryRejected("No verified workflow")), patch("backend.customer_story.capture") as capture,patch("backend.customer_story.render") as render:
            with self.assertRaises(NoVerifiedProductAction):
                execute_story(self.url,Path(d),lambda _:None)
            capture.assert_not_called();render.assert_not_called()

    def test_shared_result_region_must_be_large(self):
        a={"x":100,"y":100,"width":1500,"height":900}
        b={"x":200,"y":150,"width":1600,"height":800}
        self.assertEqual(intersection(a,b),{"x":200,"y":150,"width":1400,"height":800})
        with self.assertRaises(StoryRejected):
            intersection(a,{"x":1800,"y":20,"width":100,"height":50})

if __name__=="__main__":unittest.main()

def test_creative_brief_preserves_bounded_customer_preferences():
    from backend.customer_story import director_brief,StoryRejected
    import pytest
    assert "world-class motion design studio" in director_brief()
    assert "focus on visual payoff" in director_brief("focus on visual payoff")
    with pytest.raises(StoryRejected):director_brief("a"*2001)

def test_observed_redirect_chain_is_scoped(monkeypatch):
    import backend.customer_story as s
    monkeypatch.setattr(s,'validate_public_url',lambda u:u)
    root='https://example.com/themes'
    end='https://example.com/editor'
    assert s.admitted_initial_route(root,[root,end],end)
    for bad in ('https://other.com/editor',end+'?token=x','https://example.com/account','https://example.com/%2e%2e/admin'):
        assert not s.admitted_initial_route(root,[root,bad],bad)
    assert not s.admitted_initial_route(root,[end],end)

def test_preview_frame_route_is_narrow_and_robots_checked():
    from backend.customer_story import preview_frame_allowed
    from urllib.robotparser import RobotFileParser
    r=RobotFileParser();r.parse(['User-agent: *','Disallow: /preview/private'])
    origin='https://example.com/editor'
    assert preview_frame_allowed('https://example.com/preview/demo',origin,r)
    for u in ('https://other.com/preview/demo','https://example.com/preview/demo?token=x','https://example.com/preview/private','https://example.com/account'):
        assert not preview_frame_allowed(u,origin,r)

def test_balanced_catalog_exposes_distinct_capabilities():
    from backend.customer_story import balanced_menu_catalog
    groups=[('Style',['A','B','C']),('Color',['D','E','F']),('Radius',['G'])]
    rows=balanced_menu_catalog(groups,5)
    assert [r['group'] for r in rows]==['Style','Color','Radius','Style','Color']
    assert [r['id'] for r in rows]==['m0','m1','m2','m3','m4']
