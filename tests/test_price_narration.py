import unittest

from backend.price_narration import price_lines
from scripts.slider_framing import slider_framing


class VerifiedPricingTests(unittest.TestCase):
    def test_narration_quotes_grounded_values_and_waits_for_result(self):
        event = {"t": 3.4, "price_change": {"before": "$20", "after": "$35", "period": "month"}}
        first, last = price_lines(event, "Show the monthly price update")
        self.assertIn("20 dollars", first["text"])
        self.assertEqual(first["deadline"], 3.4)
        self.assertIn("35 dollars", last["text"])
        self.assertGreater(last["start"], 3.4)
        self.assertFalse(price_lines(event, "Show the sign-in workflow"))
        event["price_change"]["period"] = "year"
        self.assertFalse(price_lines(event))

    def test_framing_holds_the_control_and_result_inside_the_crop(self):
        control = {"x": 624, "y": 366, "width": 672, "height": 20}
        result = {"x": 680, "y": 579, "width": 249, "height": 126}
        opening, close, x, y = slider_framing(
            {"targetRect": control, "resultRect": result}, 1920, 1080)
        self.assertGreater(opening, 1.5)
        self.assertGreater(close, opening)
        for rect in (control, result):
            self.assertGreaterEqual(rect["x"], x * 1920 - 960 / close)
            self.assertLessEqual(rect["x"] + rect["width"], x * 1920 + 960 / close)
            self.assertGreaterEqual(rect["y"], y * 1080 - 540 / close)
            self.assertLessEqual(rect["y"] + rect["height"], y * 1080 + 540 / close)
