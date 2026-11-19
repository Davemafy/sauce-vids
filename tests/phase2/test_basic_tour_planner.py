"""Sauce Basic contract and pacing: no AI, no remote network, no media invention."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"scripts"))
from basic_tour_planner import (
    SCHEMA, Link, Section, Page, TourContract, canonical_url,
    discover_routes, hold_seconds, scroll_duration, wheel_steps,
    create_preflight, MAX_SCROLL_SPEED, MAX_SCROLL_ACCEL, WHEEL_HZ,
)


ROOT="https://demo.example.org/"
def page(url=ROOT,title="Home",height=2300,links=(),sections=(),anchors=()):
    return Page(url,title,height,720,tuple(sections),tuple(links),tuple(anchors))


class BasicTourContractTests(unittest.TestCase):
    def test_default_contract_is_bounded_and_silent(self):
        c=TourContract(ROOT)
        self.assertEqual(c.scope,"navigation")
        self.assertEqual(c.max_pages,12)
        self.assertEqual((c.width,c.height,c.fps),(1280,720,60))
        self.assertEqual((c.audio,c.transitions,c.chapters),("silent","hard_cut","metadata"))
        self.assertEqual(c.manifest()["schema"],SCHEMA)

    def test_native_1080p_capture_uses_true_css_viewport(self):
        c=TourContract(ROOT,width=1920,height=1080)
        self.assertEqual((c.width,c.height,c.fps),(1920,1080,60))
        with self.assertRaises(ValueError):
            TourContract(ROOT,width=1920,height=720)

    def test_rejects_unbounded_or_unapproved_contracts(self):
        cases=[
            {"root_url":"file:///etc/passwd"},
            {"root_url":"http://127.0.0.1:8080/?secret=true"},
            {"max_pages":0},{"max_pages":500},{"max_depth":9},
            {"max_minutes":0},{"audio":"music"},{"fps":30},
            {"retention_days":30},{"scope":"random"},{"profile":"turbo"},
        ]
        for overrides in cases:
            params={"root_url":ROOT,**overrides}
            with self.subTest(params=params),self.assertRaises(ValueError):
                TourContract(**params)

    def test_route_security_allowlist_and_anchor_normalization(self):
        for href in ("javascript:alert(1)","data:text/html,hi","mailto:hi@example.com",
                     "https://evil.example/home","//evil.example/home",
                     "/logout","/workspace/delete?id=2","/unsubscribe",
                     "/assets/report.pdf","/pricing?variant=a"):
            with self.subTest(href=href):
                self.assertIsNotNone(canonical_url(ROOT,href)[2])
        self.assertEqual(canonical_url(ROOT,"/#pricing"),
                         (ROOT,"pricing",""))
        self.assertEqual(canonical_url(ROOT,"/features/"),
                         ("https://demo.example.org/features",None,""))

    def test_main_navigation_only_default_with_anchor_chapters(self):
        home=page(anchors=("features","pricing"),links=[
            Link("#features","Features","nav"),
            Link("#pricing","Pricing","header"),
            Link("/product","Product","nav"),
            Link("/blog","Blog","footer"),
            Link("/guide","Guide","body"),
            Link("https://other.org/","Partner","header"),
        ])
        samples=[home,page(ROOT+"product","Product"),page(ROOT+"blog","Blog"),
                 page(ROOT+"guide","Guide")]
        plan=create_preflight(TourContract(ROOT),samples)
        self.assertEqual([p["url"] for p in plan["selected"]],[ROOT,ROOT+"product"])
        self.assertEqual([a["id"] for a in plan["anchors"][ROOT]],["features","pricing"])
        self.assertTrue(any(e["reason"]=="external_or_unsafe" for e in plan["skipped"]))

    def test_invalid_anchor_is_not_fabricated(self):
        source=page(anchors=("present",),links=[
            Link("#missing","Missing","nav"),Link("#present","Present","nav")])
        p=create_preflight(TourContract(ROOT),[source])
        self.assertEqual([x["id"] for x in p["anchors"][ROOT]],["present"])
        self.assertTrue(any(e["reason"]=="unresolved_anchor" for e in p["skipped"]))

    def test_full_mode_includes_footer_and_body_links(self):
        links=(Link("/main","Main","nav"),Link("/article","Article","body"),
               Link("/contact","Contact","footer"))
        pages=[page(links=links),page(ROOT+"main"),page(ROOT+"article"),page(ROOT+"contact")]
        full=create_preflight(TourContract(ROOT,scope="all"),pages)
        self.assertEqual(len(full["selected"]),4)
        home=create_preflight(TourContract(ROOT,scope="homepage"),pages)
        self.assertEqual(len(home["selected"]),1)

    def test_unseen_destinations_and_page_limit_are_reported(self):
        links=[Link("/one","One","nav"),Link("/two","Two","nav"),Link("/three","Three","nav")]
        samples=[page(links=links),page(ROOT+"one"),page(ROOT+"two")]
        manifest=create_preflight(TourContract(ROOT,max_pages=2),samples)
        self.assertEqual(len(manifest["selected"]),2)
        self.assertTrue(any(x["reason"]=="page_limit" for x in manifest["skipped"]))
        other=create_preflight(TourContract(ROOT,max_pages=6),samples)
        self.assertTrue(any(x["reason"]=="not_observed_or_unreachable" for x in other["skipped"]))

    def test_scroll_speed_and_acceleration_math_stays_bounded(self):
        for d in (100,600,3000,6500):
            t=scroll_duration(d)
            self.assertLessEqual(1.875*d/t,MAX_SCROLL_SPEED+1e-6)
            self.assertLessEqual(5.774*d/t**2,MAX_SCROLL_ACCEL+1e-6)
            steps=wheel_steps(0,d)
            self.assertEqual(len(steps),int(__import__("math").ceil(t*WHEEL_HZ)))
            self.assertAlmostEqual(sum(s["dy"] for s in steps),d,places=3)
            self.assertTrue(all(s["dy"]>=0 for s in steps))
            self.assertTrue(all(a["at_ms"]<b["at_ms"] for a,b in zip(steps,steps[1:])))

    def test_readability_holds_are_density_sensitive_and_bounded(self):
        for profile in ("relaxed","balanced","quick"):
            self.assertLess(hold_seconds(4,profile),hold_seconds(100,profile))
        self.assertGreater(hold_seconds(90,"relaxed"),hold_seconds(90,"balanced"))
        self.assertGreater(hold_seconds(90,"balanced"),hold_seconds(90,"quick"))
        self.assertLessEqual(hold_seconds(100000,"relaxed"),5.4)

    def test_preflight_plan_is_unchanged_on_repeat_and_budget_is_real(self):
        samples=[page(sections=(Section("hero",0,650,10),Section("copy",800,1000,118)),
                      links=(Link("/tour","Tour","nav"),)),
                 page(ROOT+"tour",height=3200)]
        contract=TourContract(ROOT,max_minutes=1)
        a=create_preflight(contract,samples)
        b=create_preflight(contract,samples)
        self.assertEqual(a,b)
        self.assertEqual(a["schema"],SCHEMA)
        self.assertEqual(len(a["page_breakdown"]),2)
        self.assertTrue(all(abs(x["wheel_ms"]+x["hold_ms"]-x["total_ms"])<0.01
                            for x in a["page_breakdown"]))
        self.assertIsInstance(a["skipped_by_reason"],dict)
        self.assertEqual(len(a["chapters"]),2)
        duration=sum(p["duration_ms"] for p in a["timeline"])+350
        self.assertLess(abs(a["estimated_seconds"]*1000-duration),0.51)
        self.assertTrue(a["source_fingerprint"])
        self.assertEqual(a["status"],"preflight_only")
        self.assertGreater(a["estimate_range_seconds"][1],a["estimated_seconds"])

    def test_nested_section_stops_do_not_double_count(self):
        # Parent section + children at similar Y should not create two holds.
        sections=tuple(Section(f"nested-{i}",i*85,300,35) for i in range(20))
        p=page(height=2800,sections=sections)
        a=create_preflight(TourContract(ROOT),[p])["timeline"][0]
        self.assertEqual(a["holds"],5)
        self.assertEqual(a["holds"],sum(s["kind"]=="hold" for s in a["steps"]))
        self.assertLess(a["hold_ms"],16000)

    def test_reason_summary_agrees_with_manifest_entries(self):
        from collections import Counter
        source=page(links=[Link("/one","One","nav"),
            Link("/two","Two","nav"),Link("https://outside.org","Off","nav")])
        p=create_preflight(TourContract(ROOT,max_pages=2),
            [source,page(ROOT+"one"),page(ROOT+"two")])
        self.assertEqual(p["skipped_by_reason"],
            dict(sorted(Counter(row["reason"] for row in p["skipped"]).items())))

    def test_segment_recorder_uses_shared_wheel_plan_without_recalculation(self):
        from basic_tour_segment_experiment import scheduled_wheels
        source=page(height=1650,sections=(Section("a",0,620,80),))
        planned=create_preflight(TourContract(ROOT),[source])["timeline"][0]
        timestamps=scheduled_wheels(planned)
        expected=sum(len(x["steps"]) for x in planned["steps"] if x["kind"]=="wheel")
        self.assertEqual(len(timestamps),expected)
        self.assertAlmostEqual(sum(x[1] for x in timestamps),1650-720,places=2)
        self.assertTrue(all(x[0]<=y[0] for x,y in zip(timestamps,timestamps[1:])))
        self.assertLessEqual(timestamps[-1][0],planned["duration_ms"])
        self.assertEqual(timestamps,scheduled_wheels(planned))

    def test_height_clamped_and_missing_pages_cannot_be_invented(self):
        high=page(height=110000)
        contract=TourContract(ROOT)
        a=create_preflight(contract,[high])
        self.assertEqual(a["timeline"][0]["capped"],"height_limit")
        with self.assertRaisesRegex(ValueError,"Root page"):
            create_preflight(contract,[page(ROOT+"unknown")])

if __name__=="__main__":
    unittest.main()
