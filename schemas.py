"""Explicit model-facing tool contracts."""
CAPTURE = {
    "name": "sauce_capture",
    "description": "Record real public HTTPS product interactions through Chromium video, return a run ID and observed action log. No synthetic product footage.",
    "parameters": {"type": "object", "properties": {
        "url": {"type": "string", "description": "Public product URL on an approved domain"},
        "actions": {"type": "array", "description": "Observed browsing actions in order; click selectors must point to real links, no forms or credential entry", "items": {
            "type": "object", "properties": {
                "type": {"type": "string", "enum": ["wait", "scroll", "hover", "click_link", "click_tab"]},
                "selector": {"type": "string"},
                "pixels": {"type": "integer"},
                "seconds": {"type": "number"},
                "expected_visible_heading": {
                    "type": "string",
                    "description": "Optional exact accessible heading to wait for after click_link. Helpful on React/SPA pages that render after DOMContentLoaded.",
                    "minLength": 1,
                    "maxLength": 160
                }
            }, "required": ["type"]}},
        "project": {"type": "string", "description": "Short lowercase project identifier"}
    }, "required": ["url", "project"]}
}
RENDER = {
    "name": "sauce_render",
    "description": "Encode genuine Sauce Vids browser recording as an MP4. Optionally use an operator-provided licensed background image. No generated visuals.",
    "parameters": {"type": "object", "properties": {
        "run_id": {"type": "string"},
        "background_asset": {"type": "string", "description": "Optional licensed PNG or JPG in SAUCE_ASSET_DIR"},
        "use_edit_plan": {"type": "boolean", "description": "Apply an edit decision list created by sauce_plan"},
        "music_asset": {"type": "string", "description": "Optional licensed MP3/WAV/OGG/M4A in SAUCE_ASSET_DIR"}
    }, "required": ["run_id"]}
}
INSPECT = {
    "name": "sauce_inspect",
    "description": "Read actual captured or rendered video metadata and recorded event receipts for Hermes to critique.",
    "parameters": {"type": "object", "properties": {"run_id": {"type": "string"}}, "required": ["run_id"]}
}

SCOUT = {"name":"sauce_scout","description":"Observe real headings, verified selectors and screenshots on an approved public HTTPS page.","parameters":{"type":"object","properties":{"url":{"type":"string"},"project":{"type":"string"}},"required":["url","project"]}}
PLAN = {"name":"sauce_plan","description":"Write reproducible video cuts and zoom edit plan for an existing recorded run.","parameters":{"type":"object","properties":{"run_id":{"type":"string"},"shots":{"type":"array","minItems":1,"maxItems":12,"items":{"type":"object","properties":{"start_s":{"type":"number"},"end_s":{"type":"number"},"zoom":{"type":"number"},"focus_x":{"type":"number"},"focus_y":{"type":"number"},"label":{"type":"string"}},"required":["start_s","end_s"]}}},"required":["run_id","shots"]}}
REVIEW = {"name":"sauce_review","description":"Extract video frames and detect blank footage for visual review.","parameters":{"type":"object","properties":{"run_id":{"type":"string"}},"required":["run_id"]}}
