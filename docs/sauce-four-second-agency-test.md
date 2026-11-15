# Sauce — four-second agency comparison

**New four-second narrated film:** https://devmcp.davemafy.xyz/sauce-four-second/
**1080p60 master:** https://devmcp.davemafy.xyz/sauce-four-second/master-1080p60.mp4
**Previous silent v19:** https://devmcp.davemafy.xyz/sauce-engine-v19/

## What is actually being tested

This is **one complete four-second real-product interaction**, not another
optics demonstration. It uses the independently verified Brimble session,
two original mouse-down events and the real resulting command.

- **0.16–1.52 s:** "Connect it to Brimble" (existing offline Kokoro voice).
  Recorded Connect click at **0.7859 s**, real modal opens at **0.9157 s**.
- **2.08–3.60 s:** "Copy the setup command." Actual Codex click at
  **2.0689 s**, command revealed by the product, not invented by Sauce.
- One small ambient harmonic texture and understated foley derived from
  the real click times. Voice is synthetic, not claimed to be human.
- Two clean Inter captions, no bottom pill, no karaoke word flashing.
  ASS subtitle times are tested against exact narration phrase envelopes.

## The camera defect found and fixed

The first closeup was wrong: the camera used only the modal's *initial*
DOM rectangle (400×360 CSS). Clicking Codex expands the modal to
400×476 CSS; the old 1.69× zoom clipped its head and foot.

The modified `scripts/editorial_closeup_camera.py` requires **observed
post-click DOM evidence** and refuses to guess the second state.
Playwright / HAR replay confirmed:

- initial dialog: x440, y180, width400, height360;
- after Codex: x440, y122, width400, height476;
- 'Copied. Paste it into your terminal' is a genuine DOM element.

The camera smoothly approaches 1.67× for the first modal and begins a
deliberate pullback when the recorded pointer approaches the Codex
option. At the actual second click, zoom is already 1.30×, so the
expanded modal fits in the 1480×832 stage with about 58px vertical
padding on each side. No camera movement occurs before actual initial
cursor motion.

## Objective QA passed

- 4.000 seconds; 240 video frames; 1920×1080 60fps H.264/AAC.
- 720p30 preview downscaled with FFmpeg Lanczos, about 0.6 MB.
- 2× Chromium-source capture, fixed time-step spring camera, original
  real DOM and visible presentation cursor.
- 3 semantic action checks + 3 native pixel-region checks passed.
- All 6 original browser state hashes verified.
- Mono narration and original understated click foley are muxed and
  audible (AAC audio stream present).
- Caption pixels verified at 0.65s and 2.8s; absent during 1.9s voice
  gap and at 3.9s.
- The rounded window, ambient stage and 32×39px cursor are preserved.
- Export and preview fully decode; the expanded dialog fits.
- `python3 -m unittest discover -s tests -q` covers editorial
  geometry and caption timestamp construction.

The comparative examples were downloaded and watched privately on the
Vultr worker. No copyrighted comparison videos are republished by Sauce.

## Actual references and results

1. **Screen Studio product demo**:
   https://screen.studio/videos/hero/hero-demo.mp4 (6.3 seconds).
   Stronger focus and reading scale across the sheet, natural voice,
   synchronized captions, purposeful zoom and a visible human presenter.
   Our four-second cut now has voice, timed captions and real action
   framing, but not equivalent cinematic storytelling or presenter warmth.
2. **Opzami Coding Agents Launch**:
   https://cdn.opzami.com/agency-showcase/work/coding-agents-launch.mp4.
   First four seconds establish the thesis through massive animated
   typography. Our demo enters the real product earlier; it does not
   have an equally strong high-level visual concept.
3. **Opzami Integrations Launch**:
   https://cdn.opzami.com/agency-showcase/work/integrations-launch.mp4.
   First four seconds use a coherent visual metaphor for disconnected
   ideas and centralization. Our cut uses a straight product workflow,
   not that level of conceptual motion.

**Verdict:** this is a more legitimate, complete test than the
silent v19 proof, but **not evidence that Sauce beats agency films**.
The first-4-second comparison is not like-for-like: agency launch films
serve different goals than a screen-recorded interaction. A consistent
superiority claim would require matched goals, three or more distinct
products, blinded reviewers, and criteria covering comprehension,
readability, timing, narrative, sound and perceived craft.

The next bottleneck is **creative direction and quality gating**, not
additional WebGL shaders. Presets should be judged by their actual
resulting video, not by a checklist of effects.

## Reproduce

The source capture, existing synthetic voice WAV and observed DOM receipt
are private on the Vultr worker. See the published scripts:

```bash
../.sauce-render-env/bin/python scripts/build_agency_challenge_audio.py \
  --voice studio/.tmp/film-05/narration.wav \
  --voice-json studio/.tmp/film-05/voice.json \
  --session studio/.tmp/brimble-reference-v16-ink/session.json \
  --out studio/.tmp/sauce-agency-challenge/narration-and-foley.wav

../.sauce-render-env/bin/python scripts/produce_cinematic_demo.py \
  --session studio/.tmp/brimble-reference-v16-ink \
  --workflow tests/fixtures/brimble-cinematic-workflow.json \
  --out studio/.tmp/sauce-agency-challenge/four-second-safe \
  --seconds 4.0 --editorial-closeup \
  --editorial-geometry studio/.tmp/sauce-agency-challenge/dialog-evidence.json \
  --audio-track studio/.tmp/sauce-agency-challenge/narration-and-foley.wav \
  --cursor-style ink --cursor-scale .56 \
  --presentation-hide-selector 'img[src*="bee-cutout"]' \
  --no-webgl-optics --no-parallax

../.sauce-render-env/bin/python scripts/finish_four_second_test.py \
  --dir studio/.tmp/sauce-agency-challenge/four-second-safe \
  --audio-meta studio/.tmp/sauce-agency-challenge/narration-and-foley.json

../.sauce-render-env/bin/python scripts/qa_four_second_film.py \
  --dir studio/.tmp/sauce-agency-challenge/four-second-safe \
  --audio-meta studio/.tmp/sauce-agency-challenge/narration-and-foley.json \
  --geometry studio/.tmp/sauce-agency-challenge/dialog-evidence.json
```

The production operator must run the finisher exactly once on a fresh
raw production export to avoid redundant compression; historical
re-renders are intentionally not overwritten. The test uses source
evidence, not invented interaction states.
