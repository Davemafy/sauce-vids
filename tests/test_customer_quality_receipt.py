"""Customer preview quality is NOT creative acceptance or action verification."""
import unittest

from backend.url_engine import customer_quality_summary


def verified_release(**changes):
    d = {
        "source_verified": True,
        "film_mode": "showcase",
        "observed_actions": [],
        "encoded_quality_verdict": "REJECT",
        "encoded_quality_findings": [
            "STATIC_OPENING_2S", "REPEATED_OR_STATIC_FRAMES", "NO_AUDIO_STREAM"],
        "recorded_source_fps": "25/1",
        "master_fps": 60,
        "creative_approved": False,
    }
    d.update(changes)
    return d


class CustomerQualityReceiptTests(unittest.TestCase):
    def test_real_blackbox_failure_must_be_disclosed(self):
        response = customer_quality_summary(verified_release())
        self.assertEqual(response["quality"], "encoded-qa-rejected")
        self.assertEqual(response["encoded_quality_verdict"], "REJECT")
        self.assertEqual(len(response["encoded_quality_findings"]), 3)
        self.assertEqual(response["film_kind"], "public-website-preview-only")
        self.assertFalse(response["real_product_action_recorded"])
        self.assertFalse(response["creative_approved"])
        self.assertFalse(response["release_eligible"])
        self.assertEqual(response["source_capture_fps"], "25/1")
        self.assertEqual(response["output_fps"], 60)

    def test_even_green_codecs_cannot_creatively_approve_a_film(self):
        r = customer_quality_summary(verified_release(
            encoded_quality_verdict="HUMAN_REVIEW_REQUIRED",
            encoded_quality_findings=[]))
        self.assertEqual(r["quality"], "human-review-required")
        self.assertFalse(r["creative_approved"])
        self.assertFalse(r["release_eligible"])

    def test_actual_public_actions_remain_candidates_not_approval(self):
        r = customer_quality_summary(verified_release(
            film_mode="interactive",
            observed_actions=[{"kind": "button", "verified": False}]))
        self.assertTrue(r["real_product_action_recorded"])
        self.assertEqual(r["film_kind"], "product-interaction-candidate")
        self.assertFalse(r["release_eligible"])

    def test_showcase_cannot_become_a_demo_by_a_misleading_action_list(self):
        r = customer_quality_summary(verified_release(
            film_mode="showcase", observed_actions=[{"kind": "link"}]))
        self.assertFalse(r["real_product_action_recorded"])
        self.assertEqual(r["film_kind"], "public-website-preview-only")

    def test_missing_encoded_qa_remains_not_evaluated(self):
        d = verified_release()
        del d["encoded_quality_verdict"]
        del d["encoded_quality_findings"]
        r = customer_quality_summary(d)
        self.assertEqual(r["encoded_quality_verdict"], "NOT_EVALUATED")
        self.assertEqual(r["quality"], "encoded-qa-not-evaluated")
        self.assertFalse(r["release_eligible"])

    def test_unverified_or_malformed_source_fails_closed(self):
        with self.assertRaises(ValueError):
            customer_quality_summary(verified_release(source_verified=False))
        with self.assertRaises(ValueError):
            customer_quality_summary(verified_release(encoded_quality_verdict="PREMIUM"))
        with self.assertRaises(ValueError):
            customer_quality_summary(verified_release(encoded_quality_findings="REJECT"))
        with self.assertRaises(ValueError):
            customer_quality_summary(verified_release(recorded_source_fps=25))
        with self.assertRaises(ValueError):
            customer_quality_summary(None)


if __name__ == "__main__":
    unittest.main()
