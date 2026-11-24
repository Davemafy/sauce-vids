import unittest
import json
import tempfile
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError
import cv2
import numpy as np
from backend.story_discovery import focused_routes
from backend.route_outcome_discovery import candidates, local_url

class RouteOutcomeTests(unittest.TestCase):
    def test_observed_routes_only_and_no_sensitive_destinations(self):
        base="https://example.com/"
        links=[{"kind":"link","text":label,"href":url} for label,url in [
            ("Try It Now",base+"editor/theme"),("Community",base+"community"),
            ("Try demo",base+"pricing"),("Try demo",base+"%61uth/demo"),
            ("Try demo",base+"login/demo"),("Try demo",base+"editor?token=x"),
            ("Try demo","https://evil.test/editor"),("Sign In",base+"editor"),
            ("Try demo",base+"editor/theme#preview")]]
        self.assertEqual(set(focused_routes(links,base)),{base+"editor/theme",base+"community"})

    def test_candidates_interleave_routes_and_exclude_auth(self):
        def c(i, text, auth=False):
            return {"id":i,"text":text,"kind":"tab",
                "policy":{"class":"reversible_local_ui","requires_authorization":auth}}
        r={"requested_url":"https://example.com/","pages":[
            {"url":"https://example.com/","controls":[c("a1","Home sample")]},
            {"url":"https://example.com/editor","controls":[c("a1","Dark mode"),c("a2","Preview"),c("a3","Auth",True)]},
            {"url":"https://evil.test/editor","controls":[c("a1","Preview")]}]}
        self.assertEqual([(p["url"],x["text"]) for p,x in candidates(r)],
            [("https://example.com/editor","Preview"),("https://example.com/","Home sample"),
             ("https://example.com/editor","Dark mode")])
        self.assertEqual(local_url("https://example.com/editor/"),local_url("https://example.com/editor"))


    def test_resume_reuses_verified_pairs_without_browser(self):
        from backend.route_outcome_discovery import run, resume_review
        from backend.outcome_editorial_gate import sha
        url="https://example.com/"
        target=url+"editor"
        control={"id":"a1","text":"Preview","kind":"tab","in_form":False}
        observed={**control,"policy":{"class":"reversible_local_ui","requires_authorization":False}}
        research={"requested_url":url,"pages":[{"id":"p0","url":url,"title":"Example","controls":[]},
                     {"id":"p1","url":target,"title":"Editor","controls":[observed]}]}
        report={"url":target,"controls":[control]}
        def discover(url, directory, **kw):
            directory.mkdir()
            (directory/"research.json").write_text(json.dumps(research))
            return research
        def inspect(url,directory):
            directory.mkdir()
            (directory/"inspection.json").write_text(json.dumps(report))
            return report
        def probe(url,report,cid,directory,**kw):
            directory.mkdir()
            proof={"schema":"sauce-source-action-preflight-v1","decision":"visible_outcome_candidate",
                   "source_url":url,"source_control_id":cid,"viewport_shift_px":0}
            for name,value in (("steady",0),("after",150)):
                p=directory/(name+".png")
                cv2.imwrite(str(p),np.full((120,160,3),value,np.uint8))
                proof[name+"_sha256"]=sha(p.read_bytes())
            (directory/"outcome.json").write_text(json.dumps(proof))
            return proof
        def unavailable(*args):
            raise HTTPError("https://example.test",503,"unavailable",{},None)
        def recovered(*args):
            return json.dumps({"selected_id":"a1","decision":"admit","reason":"Core preview",
                    "assessment":[{"id":"a1","status":"core_visible","evidence":"Visible change"}]}),{"finishReason":"STOP"}
        with tempfile.TemporaryDirectory() as tmp, patch.dict("os.environ",{
                "SAUCE_DIRECTOR_MODEL":"gemini-test-a","SAUCE_CURIOUS_FALLBACK_MODEL":"gemini-test-a"}):
            out=Path(tmp)/"run"
            with patch("backend.route_outcome_discovery.discover_public_product",side_effect=discover), \
                 patch("backend.route_outcome_discovery.inspect",side_effect=inspect), \
                 patch("backend.route_outcome_discovery.probe_public_action",side_effect=probe), \
                 patch("backend.outcome_editorial_gate.time.time",return_value=1000):
                first=run(url,out,request=unavailable)
            self.assertIsNone(first["selected"])
            self.assertEqual(first["editorial"]["state"],"provider_deferred")
            with patch("backend.route_outcome_discovery.discover_public_product",side_effect=AssertionError("recrawled")), \
                 patch("backend.route_outcome_discovery.inspect",side_effect=AssertionError("reinspected")), \
                 patch("backend.route_outcome_discovery.probe_public_action",side_effect=AssertionError("reprobed")), \
                 patch("backend.outcome_editorial_gate.time.time",return_value=1900):
                second=resume_review(out,request=recovered)
            self.assertEqual(second["selected"]["route"],target)
            self.assertEqual(len(second["editorial"]["model_attempts"]),2)
            self.assertFalse(second["creative_approved"])


if __name__=="__main__":unittest.main()
