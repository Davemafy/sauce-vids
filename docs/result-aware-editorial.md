# Evidence-driven modal focus and readable result endings

Sauce is a source-faithful software-demo film renderer, not a synthetic
interface animator. This optional editorial pass addresses two observed
Brimble defects without changing the verified original 3.28s release.

## Modal-first camera behavior

The Playwright session recorder observes newly mounted semantic
`[role="dialog"]` / `[aria-modal="true"]` overlays and bounded
high-z-index floating panels after actual click events. It records a
`dialog-visible` event with its real bounding box, a boolean click link and
a measured trigger latency only when that delay is within **300ms**.
Full-screen backdrop nodes and support widgets are not treated as dialogs.

`cameraRig.ts` examines the recorded, verified HeroMoment sequence.
When a click is followed by an actual modal within 300ms, the trigger button
is **not** a camera destination. The camera holds its existing composition
while the dialog mounts, then targets the actual dialog center using the
existing exact 180/24/1 mass-spring integrator and 1200px perspective.
It does not invent a modal from click intent or start a pre-click push.
Unrelated or later-opening modals retain ordinary action targeting.

For the recorded Brimble trace, the trigger is at 2232.9ms, and the dialog
is observed at 2362.7ms (**129.8ms response**). Its source viewport box
is x=440, y=182.59, width=400, height=360. The new camera sits at
center (640,360), scale 1.0 through frame 53 and springs to the modal:
frame 55: scale 1.00679, frame 65: 1.2332, frame 90: 1.31041, settled
at (640,362.59). The former sideways nudge toward the Connect Agent
trigger is removed.

## Result-aware final hold

During capture and replay, a privacy-constrained probe compares visible
dialog text and geometry before and after **actual DOM-executed clicks**.
Text stays exclusively in the original Chromium page for the comparison;
the trace, release report and JS/Python bridge contain only a change
boolean, safe event timing, growth and bounded dwell metadata.
Inputs, password fields, editable controls and private regions are excluded.

A new result is supported by a visible text change or >=16px container
expansion. On the **final click** only, when the resulting state is still
visible near the cut, Sauce can append a reading hold dynamically:
1200–1800ms, depending on newly visible text-node count and height growth.
A distinct 350ms cosine-eased fade follows. No result evidence means
**zero extra frames**; it does not add automatic dead air to every video.

The opt-in CLI is `--preset 3d-launch --result-aware-editorial`.
The exporter appends unmodified final-frame raw BGR bytes **before**
FFmpeg encoding, not via a second lossy transcode; the 48kHz Foley WAV
is extended with silence to the final film frame count. All existing
event cue offsets remain on their 800 samples-per-60fps-frame boundary.
No synthetic results or invented UI appear in the held footage.
The original 197-frame planning clock remains intact; the source-backed
readable outro is separately counted in the release receipt.
The opt-in flag is intentionally not combined with the experimental
canonical-orbit cache until that independent output contract supports tails.

## Brimble acceptance

The real Codex click expanded the verified dialog by 116px and mounted
five new visible text nodes; the normal export's event-driven replay
qualified a 1600ms hold. The finished film contains:

- 197 real planned frames (3.283s).
- 96 full-sharp cloned final-state frames (1.600s).
- 21 progressively faded frames (0.350s).
- **314 total frames, 1920×1080 at 60fps, 5.233333s.**
- A 48kHz stereo Foley track padded to **251,200 samples** exactly
  (314 frames × 800 samples); source events and the frame-125 cut unchanged.

Verified new preview and master:
https://devmcp.davemafy.xyz/sauce-motion-phase2/modal-first-result-dwell/
and https://devmcp.davemafy.xyz/sauce-motion-phase2/modal-first-result-dwell/master-1080p60.mp4 .
Opening before/after:
https://devmcp.davemafy.xyz/sauce-motion-phase2/modal-first-result-dwell/opening-before-after.jpg .
Full contact sheet:
https://devmcp.davemafy.xyz/sauce-motion-phase2/modal-first-result-dwell/qa-contact-20frames.jpg .
Native final-state crop:
https://devmcp.davemafy.xyz/sauce-motion-phase2/modal-first-result-dwell/qa-codex-native-crop-215.jpg .

Independent live Chromium replay is not generally deterministic: web
hydration and per-run compositing may change pixels. The sharp-held frames
within one encoded master originate from the exact same final source BGR
buffer and are not independent screenshots.

**Remaining visual limitation:** The partial terminal/window overlap during
Brimble's native modal transition around 0.72–0.82s is present in the
previous master as well. This pass does not claim that transitional
source-animation artifact is fixed. Resolving it requires a separate
source-true modal-transition cleanup, not a fabricated UI frame.
