"""Validate an aspirational client film brief without treating any claim as source truth.

A client-supplied scene list is narrative intent, NEVER a browser action permit.
Only a separately recorded video + verified event manifest can authorize scenes.
"""
from __future__ import annotations
import json
from pathlib import Path
from urllib.parse import urlsplit

MAX_BRIEF_BYTES=28_000
KNOWN_ACTIONS={"navigate","scroll","click","observe","open_tab","expand",
               "select_filter","inspect","show","hover","drag","type_demo"}
MAX_SCENES=12


def load_client_creative_brief(path, observed_source_url):
    p=Path(path)
    if not p.is_file() or p.stat().st_size>MAX_BRIEF_BYTES:
        raise ValueError("Client creative brief must be a small JSON file")
    try:
        intent=json.loads(p.read_text(encoding="utf-8"))
    except (UnicodeError,json.JSONDecodeError) as exc:
        raise ValueError("Client creative brief must be valid UTF-8 JSON") from exc
    if not isinstance(intent,dict) or intent.get("schema")!="sauce-creative-brief-v1":
        raise ValueError("Expected sauce-creative-brief-v1 client intent")
    supplied=intent.get("sourceUrl")
    wanted=urlsplit(supplied) if isinstance(supplied,str) else None
    observed=urlsplit(observed_source_url)
    if (not wanted or wanted.scheme!="https" or wanted.username or wanted.password
        or wanted.hostname!=observed.hostname or wanted.port not in (None,443)
        or observed.scheme not in ("http","https")):
        raise ValueError("Client story target must match the actual recorded source hostname")
    scenes=intent.get("scenes")
    if not isinstance(scenes,list) or not 1<=len(scenes)<=MAX_SCENES:
        raise ValueError("Creative brief requires 1..12 story scene intentions")
    for scene in scenes:
        if not isinstance(scene,dict) or not isinstance(scene.get("role"),str):
            raise ValueError("Every client scene needs an editorial role")
        actions=scene.get("actions",[])
        if not isinstance(actions,list) or len(actions)>7:
            raise ValueError("Client scene has too many unverified action suggestions")
        for action in actions:
            if (not isinstance(action,dict) or action.get("type") not in KNOWN_ACTIONS):
                raise ValueError("Unrecognized client-suggested action")
    output=intent.get("output",{})
    if not isinstance(output,dict):
        raise ValueError("Client film output preferences must be an object")
    if output.get("orientation","landscape")!="landscape":
        raise ValueError("Only landscape flagship is supported by this director")
    # Proposed run result, recorded results and platform captions are
    # UNVERIFIED client-provided text. Never merge with actualCapture.
    return {
        "schema":"sauce-unverified-client-story-intent-v1",
        "trust":"unverified_user_supplied_director_ideas_not_browser_evidence",
        "sourceHost":wanted.hostname,
        "requestedDurationSeconds":output.get("targetDurationSeconds"),
        "clientBrief":intent,
        "sourceTruthRule":"A suggested scene, UI text, navigation route, statistic, "
         "fallback, success, result and timing have zero evidence status until "
         "they independently exist in the SHA-pinned original browser capture. "
         "Only actualCapture.verifiedEvents, nativeFrames and source pixels may "
         "authorize any shot in a sauce-film-plan-v1 JSON. Skip unsupported "
         "proposals; never invent intermediate events or UI.",
    }
