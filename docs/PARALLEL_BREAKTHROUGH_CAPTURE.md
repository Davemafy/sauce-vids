# Parallel breakthrough — capture source-clock / DOM QA

2026-11-19. Isolated **main-only** Vultr checkout; **local commit only**. This lane does not change film direction, compositor, deployed capture, production assets or other workspaces.

## Scope and provenance

- Base GitHub main: `06453d127fada315459595549fb2939e1ba4a2de`, verified equal to `origin/main` at checkout.
- Private input (read-only): `/var/lib/sauce-steward/qa-logs/market-film-20261118/capture/linear-workflow-dpr2-source-60.mp4`; SHA256 `7a539dd06e90257f237db0ad602301ca3fd8cc2db96ac802613904d010a8a454`, matching `docs/SAUCE_REFS_MARKET_FILM_20261118.md`.
- Real public source: `https://linear.app/` interactive marketing preview, **not authenticated Linear**. Private events file `capture/linear-workflow-dpr2-events.json`; existing source receipt reports three clicks, 19 events, 368 pointer samples. Source script `/var/lib/sauce-steward/qa-logs/market-film-20261118/capture.py` (read only) launched Chromium with DPR2 and an X11grab `-framerate 60` capture. Its `film.epoch=time.monotonic()` is established about 0.28 seconds after ffmpeg subprocess startup; this is *not* a measured shared hardware frame epoch.
- Probe: encoded 2640×1440, `60/1`, exactly 1,110 frames / 18.50 seconds; no observed presentation-timestamp gap. There is **no basis to certify 60 independently refreshed source pictures/second**.

## Frame-by-frame audit and qualified result

Command (exact source remains private):
```bash
ffmpeg -hide_banner -loglevel error -threads 2 \
  -i /var/lib/sauce-steward/qa-logs/market-film-20261118/capture/linear-workflow-dpr2-source-60.mp4 \
  -an -vf 'scale=330:180:flags=area,format=gray' \
  -f framemd5 /tmp/sauce-capture-framehash-26be.txt
```
All 1,110 decoded frames hashed after downsampling (a **visual proxy**, not byte-identical full-resolution comparison). Result: 552/1,109 adjacent frame transitions had identical hashes (49.7746%); 183 distinct scaled-gray hashes overall. CFR PTS are monotonic with zero >1.5-frame gaps. Some repeats are expected in static UI holds. Thus neither 49.77% duplication nor the distinct count is an estimate of actual browser paint FPS. **Gate fails under a conservative 25% duplicate-transition threshold**, but that threshold is diagnostic and must not be conflated with display drop measurement.

## Implementation

- `scripts/capture_source_qa.py`: reusable `parse_framemd5`, `clock_report`, `outcome_report`, `Geometry.source_hotspot`, and `Geometry.cursor_sprite_origin`. Fail-closed PTS/event chronology, absent outcome/evidence, click-pointer mismatch, invalid viewport/crop/hotspot geometry. Exact duplicate counting of supplied framemd5 checksums. No modified render pixels.
- Pointer coordinates are **CSS relative to the page viewport** or the private Linear manifest's **capture-crop-relative physical pixels**; never mix them implicitly. For a DPR2 viewport at 1440×900 CSS with capture crop at physical origin (105,180) and size 2640×1440, physical point is `(css_x*2-105, css_y*2-180)` before sprite hotspot correction. The existing Linear X11 script already stores private crop-local pointer and target rectangles. Geometry calculations have synthetic calibration tests, not an independently photographed X11 hardware tip validation.
- Existing real Linear result check: all **3 click → observed DOM state-change** pairs have evidence and a same-manifest, crop-local pointer sample within 250 ms of click inside the genuine target rect. First click has a 186.3ms stationary dwell before click; a 150ms requirement incorrectly rejected this valid stationary approach. This broader threshold still rejects missing/stale (>250ms) or out-of-target samples. The source contains no separately measured browser-to-encoded-frame epoch; **cross-clock subframe sync is unproven**.

## Tests and reproducibility

```bash
cd capture-main
PYTHONDONTWRITEBYTECODE=1 /opt/sauce-vids/.venv/bin/python -m pytest \
  -p no:cacheprovider tests/test_capture_source_qa.py -q
# 11 passed in 0.03s
python3 - <<'PY'
import sys,json
sys.path.insert(0,'scripts')
from capture_source_qa import clock_report,parse_framemd5,outcome_report
j=json.load(open('/var/lib/sauce-steward/qa-logs/market-film-20261118/capture/linear-workflow-dpr2-events.json'))
print(outcome_report(j['events'], j['pointer_samples']))
print(clock_report(parse_framemd5('/tmp/sauce-capture-framehash-26be.txt'), 60))
PY
```

Negative tests include duplicate frames, PTS jump, repeated PTS, missing/unevidenced DOM result, outside-target pointer, unsorted events, invalid crop and pointer out of viewport. No new live browser session was claimed. The existing source is a public-browser recorded proof. No inference calls or paid API usage.

## Remaining P0 capture engineering

1. At recorder launch, write a paired monotonic-clock synchronization receipt (browser `performance.timeOrigin + performance.now()`, parent `time.monotonic_ns()`, ffmpeg video PTS or observed frame pulse with uncertainty bounds). Current `time.sleep(.28)` startup guess is insufficient.
2. Capture frame-paint telemetry or a visible changing calibration patch outside the product crop to independently measure *actual captured-new-frame cadence*. Distinguish duplicate static content from lost screen updates before calling any source native 60fps.
3. Store and verify exact Chromium viewport/devicePixelRatio, X11 window/crop bounds, XFixes pointer image hotspot and cursor raster dimensions in a privacy-safe receipt, with tolerances at source scale. This module supplies math and rejection primitives but does **not** yet instrument XFixes.
4. Integrate these optional QA checks into the authorized source-capture admission path with strict backward compatibility. This local worker did **not** wire production or claim integration.

**Status:** bounded reusable QA implementation and real source diagnostic, **not** proof of native unique 60fps, a new live record, production adoption or visually approved film. No generated media or private evidence committed.
