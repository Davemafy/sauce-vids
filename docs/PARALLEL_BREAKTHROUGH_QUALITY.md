# Parallel breakthrough — independent Sauce quality supervisor

**2026-11-19 | owner workstream: quality only | baseline GitHub main `06453d127fada315459595549fb2939e1ba4a2de`.**

## Real artifacts inspected
- CMOkit rejected film (read-only): `/var/www/sauce-film-review/cmokit-900-20261118/master-1080p60.mp4`; SHA256 `36ff7f461fb0970b4d50a5a52acfdce1e490e3528357ba892777e7215df00c9d`; 15.000s, 1920x1080, 60fps, video and audio streams. Original report: `qa-results/cmokit-15s.json`.
- Linear public preview film (read-only): `/var/lib/sauce-steward/qa-logs/market-film-20261118/linear-refs-final-1080p60.mp4`; SHA256 `ed53e8ff8a1120eae23e86f0bb01f6db8f6437ed6d132bd12266e838256e831b`; 15.267s, 1920x1080. Original report: `qa-results/linear-15s.json`.
- Original CMOkit film is rejected by `docs/SAUCE_CMOKIT_QUALITY_AUDIT.md`: navbar-only actions, tiny targets, false native-60 provenance, no verified product operation. The private review directory contains MP4/poster/watch HTML **but no EDL, source capture, recorded event manifest or independently authenticated source receipt**. It is not an admissible automatic-repair input. Never pass unrelated Linear source/EDL to it.
- Linear has `market-linear-edl.json`, `linear-preflight-state-manifest.json`, and known private capture artifacts. This is **not** a substitute for provenance of the rejected CMOkit movie.

## New deterministic runner
`scripts/quality_preview_supervisor.py` detects first-2s inactivity (10fps luma-frame differences), large bright low-contrast frames, abrupt change candidates, repeated/static samples, sparse texture risk, missing/near-silent audio, small focus when independently supplied, and hash/path failures in source-event claims. These are **machine warnings / stop conditions**, not assertions of creative quality. Dark Linear UI was flagged low-detail at this threshold: **manual reviewer must assess whether this is a false positive**.

`supervise` is an isolated, opt-in invocation. It takes a pre-existing, independently issued capture receipt binding real source and event manifest paths/hashes. Missing or mismatched evidence stops **before render**. It attempts at most twice. The sole automatically permitted EDL change is a shorten-by-up-to-90-frames edit to a **verified event-free static opener** whose camera has a single constant key; source actions, cursor, outcomes, all other shots and camera keyframes remain unchanged. It emits at most a **240-frame (4-second) private excerpt** through the existing renderer, then remeasures, compares and returns HUMAN_REVIEW_REQUIRED or REJECT/STOP. It never silently approves or replaces the full master. This limited policy intentionally cannot fix washed-out footage, bad source resolution, unsound camera targets, questionable cut grammar or missing provenance. Those defects require capture/editorial human attention.

**Important integration gap:** main does not contain the dirty production StoryArc renderer. No live Studio repair has been wired, pushed or deployed. CMOkit rerender **stopped at missing authoritative EDL/source evidence**. No substitute UI, fictitious pointer, fabricated event, new VM, inference or public film was created.

## Reproducible checks
```bash
/opt/sauce-vids/.venv/bin/python -m pytest tests/test_quality_preview_supervisor.py tests/test_url_film_recovery.py -q
# 26 passed
python3 scripts/quality_preview_supervisor.py /var/www/sauce-film-review/cmokit-900-20261118/master-1080p60.mp4
python3 scripts/quality_preview_supervisor.py /var/lib/sauce-steward/qa-logs/market-film-20261118/linear-refs-final-1080p60.mp4
# On a separately VERIFIED real source/event/EDL bundle:
python3 scripts/quality_preview_supervisor.py FILM.mp4 --source SOURCE.mp4 --manifest EVENTS.json --edl EDIT.json --evidence-receipt CAPTURE_RECEIPT.json --out-dir PRIVATE_QA_DIR --attempts 2 --render
```

## Exact measured defects / visual verdict
- **CMOkit:** opening 2s measured luma delta p80 = 0.318 (threshold 1.3), static/repeated sampled adjacent pairs 69.1% (threshold 55%). No independently supplied provenance to this invocation. **REJECT**. This newly measured 15s film is distinct from the earlier documented 30s CMOkit artifact. Automated diagnostics alone do not prove all frames are repeated at the native frame clock; sampled stillness may be deliberate, but the inert opening was previously human-rejected.
- **Linear:** sampled low-detail fraction 80.7% (standard-deviation threshold 24), likely due to source's dark UI. No independently supplied provenance to this invocation. **REJECT pending source receipt and human review**. Treat this as a potential threshold false positive, not evidence Linear is worse than CMOkit.
- **Both:** encoded MP4 resolution is not proof of native capture quality or source-real 60fps. The checker does not pretend to inspect underlying DOM when no event receipt is available.
- **Unresolved:** per-scene reading area, font pixel height, intentional vs accidental cut classification, and exact native-frame duplication require event geometry and reference-based human frame review; not inferred from sampled luminance.

## Tests and negative cases
The test suite rejects absent events, malformed event times, clicks in any region proposed for trimming, moving-camera edits, too-short shots, missing provenance, falsified SHA256 values and inconsistent source paths. It tests immutability of original EDL/manifest and that only an allowed opener source range changes. The original film is preserved byte-for-byte.

## Coordination
Scope contains only new `scripts/quality_preview_supervisor.py`, `tests/test_quality_preview_supervisor.py`, this report and small JSON metric receipts. Other agents can integrate these from this isolated local **main** commit; coordinator owns production integration. Do not confuse a private locally measured QA report with creative approval.
