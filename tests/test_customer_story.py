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
            return validated_selection(json.dumps({"ids":ids,"story":"A connected workflow","hero_action_id":ids[0]}),self.catalog)
        self.assertEqual([x["id"] for x in validate(["a0","a3","a2","a1"])["actions"]],["a0","a3","a2","a1"])
        for ids in (["a0","a1"],["a1","a2","a3","a4"],["a0","a1","a1","a2"],["a0","a1","a2","invented"],[x["id"] for x in self.catalog]):
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

def test_action_schedule_reserves_final_result_budget():
    from backend.customer_story import action_start,SECONDS
    for count in (3,4):
        times=[action_start(i,count) for i in range(count)]
        assert times==sorted(set(times))
        assert times[0]<1 and SECONDS-times[-1]>=10

def test_native_screen_proof_is_raw_until_persisted(tmp_path,monkeypatch):
    import numpy as np
    from PIL import Image
    import backend.customer_story as s
    monkeypatch.setattr(s,"W",16);monkeypatch.setattr(s,"H",8)
    monkeypatch.setattr(s.ImageGrab,"grab",lambda **kw:Image.new("RGB",(32,16),(20,80,150)))
    a=s.screen(":42")
    assert a.shape==(8,16,3) and a[0,0].tolist()==[150,80,20]
    assert s.pixels(a) is a
    s.persist_screen(tmp_path/"proof.png",a)
    np.testing.assert_array_equal(s.pixels((tmp_path/"proof.png").read_bytes()),a)


def test_homepage_entry_candidates_are_observed_safe_and_robots_allowed():
    from backend.customer_story import observed_product_entry_links
    from urllib.robotparser import RobotFileParser
    class A:
        def __init__(self,text,url,visible=True):
            self.text=text;self.url=url;self.visible=visible
        def is_visible(self):return self.visible
        def evaluate(self,expr):return True
        def inner_text(self,timeout=None):return self.text
        def get_attribute(self,name):return self.url if name=='href' else None
    class L:
        def __init__(self,items):self.items=items
        def all(self):return self.items
    class P:
        url='https://example.com/'
        def locator(self,selector):
            assert selector=='a[href]'
            return L([
                A('Try editor','/editor/theme'),
                A('Private editor','/editor/private'),
                A('Do not open','https://othersite.com/editor'),
                A('Auth app','/account/settings'),
                A('Tracking','/editor/theme?token=abc'),
                A('Section','/editor/theme#secret'),
                A('Hidden editor','/editor/hidden',False),
                A('Docs','/docs'),
            ])
    robots=RobotFileParser();robots.parse(['User-agent: *','Disallow: /editor/private'])
    found=observed_product_entry_links(P(),P.url,robots)
    assert found==[{'id':'r0','url':'https://example.com/editor/theme','label':'Try editor'}]


def test_gemini_only_selects_a_real_observed_entry_id(monkeypatch,tmp_path):
    import backend.customer_story as s
    from contextlib import contextmanager
    from urllib.robotparser import RobotFileParser
    class Page:pass
    class FakeConv:
        calls=1
        def __init__(self,reply):self.reply=reply
        def ask(self,*args,**kwargs):
            assert kwargs['phase']=='observed-product-entry'
            assert 'r0' in args[0] and '/editor/theme' in args[0]
            return json.dumps({'id':self.reply,'reason':'Observed product interface'})
    @contextmanager
    def fake_browser(url,include_robots=False):
        assert url=='https://example.com/'
        assert include_robots
        yield Page(),RobotFileParser()
    monkeypatch.setattr(s,'browser',fake_browser)
    monkeypatch.setattr(s,'observed_product_entry_links',lambda *args:[{
        'id':'r0','url':'https://example.com/editor/theme','label':'Try It Now'}])
    monkeypatch.setattr(s,'shot',lambda p:b'image')
    monkeypatch.setattr(s,'media',lambda b:{'test':'image'})
    got=s.resolve_public_product_entry('https://example.com/',tmp_path,FakeConv('r0'),'brief')
    assert got=='https://example.com/editor/theme'
    receipt=json.loads((tmp_path/'entry-route.json').read_text())
    assert receipt['submitted_url']=='https://example.com/'
    assert receipt['model_selected'] is True
    other=tmp_path/'unknown';other.mkdir()
    assert s.resolve_public_product_entry('https://example.com/',other,FakeConv('made_up'),'brief')=='https://example.com/'
    assert json.loads((other/'entry-route.json').read_text())['model_selected'] is False
