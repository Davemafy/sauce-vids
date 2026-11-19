"""Render editorial evidence directly from the captured source pixels."""
from __future__ import annotations

import math
import textwrap
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

COLORS = ("#54c6ff", "#ffca75", "#a6e896", "#f8a7e6")
BACKGROUND = "#15191e"
INK = "#f1f3f5"


def _box(rect, scale=1, x=0, y=0):
    return (x + math.floor(rect["x"] * scale), y + math.floor(rect["y"] * scale),
            x + math.ceil((rect["x"] + rect["width"]) * scale),
            y + math.ceil((rect["y"] + rect["height"]) * scale))


def render_contact_sheet(plan: dict, destination: Path, source: Image.Image | None,
                         action_crop: Image.Image | None = None) -> None:
    """Annotate a thumbnail and show the exact crops at one image pixel per CSS pixel."""
    beats = plan.get("beats", [])
    gap, left_width = 26, 310
    right = left_width + gap * 2
    rows = [(_box(b["source_rect"]), COLORS[i]) for i, b in enumerate(beats)]
    display = None
    if source is not None:
        scale = min(left_width / source.width, 1900 / source.height, 1)
        display = source.resize((max(1, round(source.width * scale)),
                                 max(1, round(source.height * scale))), Image.Resampling.LANCZOS)
    width = max(820, right + gap + max((box[2] - box[0] for box, _ in rows), default=0))
    height = max(190, 110 + (display.height if display else 0),
                 110 + sum(box[3] - box[1] + 105 for box, _ in rows))
    sheet = Image.new("RGB", (width, height), BACKGROUND)
    draw = ImageDraw.Draw(sheet)
    title = ImageFont.load_default(size=25)
    body = ImageFont.load_default(size=16)
    draw.text((gap, 22), plan["url"], fill=INK, font=title)
    draw.text((gap, 57), plan["status"] + ("  /  " + plan["reason"] if "reason" in plan else ""),
              fill="#b4bec8", font=body)
    if display is not None:
        sheet.paste(display, (gap, 96))
        scale = display.width / source.width
        for beat, (_, color) in zip(beats, rows):
            action = beat.get("interaction")
            if action:
                draw.rectangle(_box(beat["source_rect"], scale, gap, 96),
                               outline=color, width=1)
            rect = action["target_rect"] if action else beat["source_rect"]
            x0, y0, x1, y1 = _box(rect, scale, gap, 96)
            draw.rectangle((x0, y0, x1, y1), outline=color, width=2)
            badge_x = x1 - 18 if action else x0
            draw.rectangle((badge_x, y0, badge_x + 18, y0 + 20), fill=color)
            draw.text((badge_x + 5, y0), str(beat["beat_index"]), fill=BACKGROUND, font=body)

    y = 96
    for beat, (box, color) in zip(beats, rows):
        draw.text((right, y), f'{beat["beat_index"]}  {beat["role"]}  ·  {beat["score"]:g}',
                  fill=color, font=title)
        reason = beat["reason"]
        if beat.get("interaction"):
            reason = beat["interaction"]["verified_mutation"] + " · " + reason
        lines = textwrap.wrap(reason, max(48, (width - right - gap) // 9))
        for i, line in enumerate(lines[:3]):
            draw.text((right, y + 32 + 19 * i), line, fill=INK, font=body)
        crop = action_crop if beat.get("interaction") and action_crop is not None else source.crop(box)
        sheet.paste(crop, (right, y + 86))
        y += box[3] - box[1] + 105
    sheet.save(destination, optimize=True)
