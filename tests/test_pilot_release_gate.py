import hashlib
import tempfile
import unittest
from pathlib import Path
from scripts.pilot_release_gate import approved, deliver


class PilotReleaseTests(unittest.TestCase):
    def setUp(self):
        self.raw = b"immutable film fixture"
        self.sha = hashlib.sha256(self.raw).hexdigest()
        self.candidate = {"schema": "sauce-pilot-candidate-v1",
                          "technical_verdict": "HUMAN_REVIEW_REQUIRED",
                          "findings": [], "film_sha256": self.sha,
                          "creative_approved": False}
        self.decision = {"schema": "sauce-owner-film-review-v1",
                         "decision": "approved", "film_sha256": self.sha,
                         "reviewer": "operator fixture"}

    def test_review_is_not_approval(self):
        self.assertFalse(approved(self.candidate, {}))
        self.assertFalse(approved(self.candidate, {**self.decision, "decision": "rejected"}))
        self.assertFalse(approved({**self.candidate, "technical_verdict": "REJECT"}, self.decision))
        self.assertFalse(approved({**self.candidate, "findings": [{"code": "STATIC_OPENING"}]}, self.decision))

    def test_approval_is_bound_to_exact_film(self):
        self.assertTrue(approved(self.candidate, self.decision))
        self.assertFalse(approved(self.candidate, {**self.decision, "film_sha256": "0"*64}))
        with tempfile.TemporaryDirectory() as root:
            film, out = Path(root)/"film.mp4", Path(root)/"delivery.mp4"
            film.write_bytes(self.raw + b"tampered")
            with self.assertRaises(ValueError):
                deliver(film, self.candidate, self.decision, out)
            self.assertFalse(out.exists())
            film.write_bytes(self.raw)
            deliver(film, self.candidate, self.decision, out)
            self.assertEqual(out.read_bytes(), self.raw)
            with self.assertRaises(FileExistsError):
                deliver(film, self.candidate, self.decision, out)
