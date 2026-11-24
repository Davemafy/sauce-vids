import unittest
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

if __name__=="__main__":unittest.main()
