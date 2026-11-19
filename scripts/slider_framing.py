"""Undistorted camera framing driven by a recorded slider and result."""
import math


def slider_framing(event, width, height):
    rects = [event.get(key) for key in ("targetRect", "resultRect")]
    if any(not isinstance(rect, dict) for rect in rects):
        raise ValueError("Slider framing requires measured control and result bounds")
    for rect in rects:
        x, y, w, h = (rect.get(k) for k in ("x", "y", "width", "height"))
        if not all(type(n) in (int, float) and math.isfinite(n) for n in (x, y, w, h)):
            raise ValueError("Invalid slider geometry")
        if x < 0 or y < 0 or w <= 0 or h <= 0 or x + w > width or y + h > height:
            raise ValueError("Slider evidence is outside the source frame")
    left = min(r["x"] for r in rects)
    top = min(r["y"] for r in rects)
    right = max(r["x"] + r["width"] for r in rects)
    bottom = max(r["y"] + r["height"] for r in rects)
    tight = max(1., min(2.55, width / (right - left + width * .055),
                        height / (bottom - top + height * .10)))
    margin_x = max(0., width / tight - (right - left))
    margin_y = max(0., height / tight - (bottom - top))
    focus_x = ((left + right) / 2 - min(width * .008, margin_x / 5)) / width
    focus_y = ((top + bottom) / 2 - min(height * .012, margin_y / 5)) / height
    return min(2.38, tight), tight, focus_x, focus_y
