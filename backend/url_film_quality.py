"""Source-evidence quality gate for URL-produced software films.

A successful link click and a playable MP4 are not evidence of a product
workflow. This module does not modify captured pixels or make creative claims.
It is deliberately dependency-free so dirty production and versioned main
can use the same conservative contract after a controlled integration.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from urllib.parse import urlsplit


@dataclass(frozen=True)
class UrlFilmAssessment:
    eligible_product_demo: bool
    actual_product_action_candidates: int
    navigation_only: bool
    bad_camera_targets: int
    opener_seconds: float
    source_is_native_master: bool
    source_is_native_fps: bool
    reasons: tuple[str, ...]

    def as_receipt(self) -> dict:
        return asdict(self)


def _same_document_anchor(url: str, href: str) -> bool:
    base = urlsplit(url)
    target = urlsplit(href)
    return bool(
        target.fragment and target.scheme == base.scheme
        and target.netloc.lower() == base.netloc.lower()
        and target.path.rstrip("/") == base.path.rstrip("/")
        and not target.query
    )


def assess_url_film(
    inspection: dict,
    scenes: list[dict],
    *,
    source_size: tuple[int, int],
    source_fps: float,
    output_size: tuple[int, int] = (1920, 1080),
    output_fps: float = 60,
) -> UrlFilmAssessment:
    """Fail closed when the observed interactions are only navigation.

    A candidate on-page button is not itself proof of real application value.
    The assessor only establishes whether a film might qualify for subsequent
    human creative review. It never grants premium-quality approval.
    """
    url = inspection.get("url", "")
    if not isinstance(url, str) or not url.startswith(("https://", "http://")):
        raise ValueError("Missing authoritative public source URL")
    if not isinstance(scenes, list) or not scenes:
        raise ValueError("No recorded scenes")
    if (not isinstance(source_size, tuple) or len(source_size) != 2
        or not all(isinstance(x, int) and x > 0 for x in source_size)
        or not isinstance(output_size, tuple) or len(output_size) != 2
        or not all(isinstance(x, int) and x > 0 for x in output_size)
        or not (source_fps > 0 and output_fps > 0)):
        raise ValueError("Invalid recorded/export stream metadata")

    controls = {c.get("id"): c for c in inspection.get("controls", [])
                if isinstance(c, dict) and c.get("id")}
    navigation = []
    candidates = 0
    bad_targets = 0
    first_action_ms = None
    for scene in scenes:
        if not isinstance(scene, dict):
            raise ValueError("Invalid scene evidence")
        box = scene.get("focusBox")
        if isinstance(box, dict) and box:
            if (float(box.get("width", 0)) < 90
                or float(box.get("height", 0)) < 30):
                bad_targets += 1
        action_id = scene.get("actionId")
        if not action_id:
            continue
        control = controls.get(action_id)
        if not control or not scene.get("transitionVerified"):
            continue
        if first_action_ms is None:
            first_action_ms = float(scene.get("startMs", 0))
        is_nav = (control.get("kind") == "link"
                  and _same_document_anchor(url, control.get("href", "")))
        navigation.append(is_nav)
        is_product_control = (control.get("kind") == "button"
                              or control.get("role") in ("button", "tab"))
        if (not is_nav and is_product_control
            and scene.get("actualAction") in ("click", "type_demo")):
            candidates += 1
    navigation_only = bool(navigation) and all(navigation)
    native_size = (source_size[0] >= output_size[0]
                   and source_size[1] >= output_size[1])
    native_fps = source_fps + 0.05 >= output_fps
    reasons: list[str] = []
    if navigation_only:
        reasons.append("Only same-document navigation was recorded; no application workflow verified")
    elif not candidates:
        reasons.append("No source-verified on-page product action candidate")
    if bad_targets:
        reasons.append("Camera target dimensions too small for legible action composition")
    opener_seconds = (first_action_ms / 1000 if first_action_ms is not None
                      else -1.0)
    if opener_seconds > 4:
        reasons.append("No meaningful recorded action during the first four seconds")
    if not native_size:
        reasons.append("Source video is below master dimensions and must be upscaled")
    if not native_fps:
        reasons.append("Output frame rate resamples a lower-rate browser recording")
    return UrlFilmAssessment(
        eligible_product_demo=bool(candidates and not navigation_only
                                   and bad_targets == 0 and opener_seconds <= 4),
        actual_product_action_candidates=candidates,
        navigation_only=navigation_only,
        bad_camera_targets=bad_targets,
        opener_seconds=opener_seconds,
        source_is_native_master=native_size,
        source_is_native_fps=native_fps,
        reasons=tuple(reasons),
    )
