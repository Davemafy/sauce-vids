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

## 2026-11-17: Source-backed result-camera payoff (opt-in)

The first evidence-driven implementation retained **96 frozen final frames**
(1.6 seconds), then faded for 21 frames. It was readable, but the extra
runtime did not *direct attention*; the entire modal simply sat still.
This was a deliberate editorial mistake, not a rendering or test failure.

Use `--result-aware-editorial --result-payoff-push` to replace that flat
tail when the last verified dialog actually contains a visible, non-private
`pre`, `output`, or semantic code/result element. The browser supplies only
its bounding rectangle and the live dialog rectangle; the renderer never
copies command text into a synthetic card or creates an unrecorded click.
When the final outcome has no reliable result element, the prior conservative
hold remains available instead of guessing a target.

The implemented payoff reuses the **same original DPR=2 Chromium screenshot**
and verified dialog-free H0 background plate captured in the last frame.
For each camera frame it re-warps the original browser pixels with Lanczos4
and re-renders the actual elevated H60 dialog through
`CinematicStage.render`. It does *not* rescale an encoded MP4, draw new text,
flatten the modal into a 2D screenshot, alter the 180/24/1 camera physics of
the recorded interaction, or synthesize command/copied success.

For the verified Brimble Codex result, the recorded element is a real
`<pre>` at CSS x=487, y=471, w=334, h=52 in the modal at x=440, y=122,
w=400, h=476. Its source-derived focal point uses 65% of the command
center and 35% of dialog context. The new camera moves from the settled
1.31x full-dialog pose to 1.7554x, centered at (649.1,449.05). The
cursor fades out during the non-interactive editorial dolly, after the
real click is completed, so it cannot cover the command.

The frame-locked grammar at 60fps is deliberately short:

- **8 frames** (0.133s) of original final composition, preserving continuity
  at the edit.
- **36 frames** (0.600s) of quintic-eased, native H0/H60 camera re-render,
  with stationary acceleration at both ends.
- **42 frames** (0.700s) of the *new* sharp, enlarged command close-up.
- **12 frames** (0.200s) of eased fade to dark.

Output therefore has 197 original action frames + 98 payoff frames =
**295 frames (4.916667s)**. The Foley track is padded to exactly
**236,000 samples at 48kHz** (800 per frame); the four original Foley
cues, source events, and action cut at frame 125 are unchanged.
The preview player may report 4.933s because it uses a separate downscaled
encode; the 1080p master and frame count remain authoritative.

Proof: https://devmcp.davemafy.xyz/sauce-motion-phase2/result-payoff-camera/
and its exact
https://devmcp.davemafy.xyz/sauce-motion-phase2/result-payoff-camera/master-1080p60.mp4 .
Contact:
https://devmcp.davemafy.xyz/sauce-motion-phase2/result-payoff-camera/payoff-contact.jpg .
Native command close-up:
https://devmcp.davemafy.xyz/sauce-motion-phase2/result-payoff-camera/native-command-250.jpg .
Previous 5.23s master remains available separately. This opt-in result
shot has not been declared the universal default or artistically
approved for every target site.
