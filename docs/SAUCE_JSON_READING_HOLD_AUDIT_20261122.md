# Sauce — JSON/result-reading hold verification (2026-11-22)

Status: bounded source-true editorial QA improvement, not a premium film or new production launch. Main only.

## Concrete failure revealed by the original encoded films

Existing classical Resend coverage and the new reference-paced 10.2167-second camera film can pass source/geometry tests and full video/audio decode, yet their real source-backed price close-ups provide too little stable *large-result framing*. The new evidence-based audit (using only confirmed source time and the exact existing stage projection) measured at 1920x1080 native 60fps with original result rectangles requiring >=360px projected width, >=57px projected height, >=97.5% projected visibility, max 2.5px/60fps-frame camera movement and >=0.55s uninterrupted hold:

- Classic restrained: event result hold 0.4333s / 0.6167s / 1.75s.
- Cinematic paced: 0.35s / 0.3833s / 1.6667s. This was a *regression* for intermediate reading holds even though its peak camera motion dropped to 30.67px/frame. Original results were not enough to make it premium.
- A separate private-source-clock held-composition experiment reused the exact same real 613 source frames and three true events, with no fake cursor or events. It produced 2.0833s / 2.2833s / 2.4s stable result holds, max stage motion 27.2px/frame and genuine recorded cursor tip visible at each actual press. However it was *worse editorially*, with 66.3% sampled near-static frame intervals. Existing encoded QA REJECT: REPEATED_OR_STATIC_FRAMES. Film SHA256 124eab82aade5a73e4b75168ef58e678844f23a0f96bcf50bcd1b9cfabad7d84, 1920x1080 H264 60fps613f + AAC48kHz, full decode; never promote this rejected one-off as a preset or gold reference.
- Signed temporary owner-only held experiment (72 hours): https://devmcp.davemafy.xyz/sauce-expiring-review/tweakcn-20261120/sauce-resend-held-reading-rejected-20261122.mp4?md5=uIARa0oY_Dp1_1JIjIW3GQ&expires=1795639545 (signed HTTP200/unsigned403). Negative example only.

Original source SHA256 6973a247624d514aa75b8d10c45a01a022942f2597f251c65aeb7d91a95ff586 and manifest SHA256 efd1843cd6668b089f1fd41dfbd3db0263432a6da82e453daaf66d3d776e9168 are unchanged; 325 original pointer samples, $35/$160/$350 observed actual price changes and unchanged native 60fps source clock.

## Implementation and behavior

- scripts/studio_result_hold_audit.py is a reusable opt-in evidence-linked physical film-plan checker. It samples the already implemented stage camera quad for each authentic source frame between one verified result and the next; measures visible real result rectangle, projected real pixel dimensions, motion velocity, and longest uninterrupted result-reading hold. A camera cut cannot masquerade as a smooth dwell. It never invents a screenshot or edits a source event. Its footprint threshold is an objective shot-composition *proxy*, not proof of legible letters or audience comprehension.
- scripts/source_director_preflight.py includes measured sourceResultReadingHolds observations for 8s+ multi-action studio stories. It emits source-backed RESULT_READING_HOLD_TOO_SHORT findings for wide/text-like original result rectangles ONLY when enforce_reading_holds=True. This opt-in protects legacy non-model coverage; no default result is rewritten or rejected.
- scripts/auto_direct_studio_film.py, the EXISTING bounded model JSON pipeline, explicitly enables the strict reading-hold check. Its existing source-grounded feedback mechanism gives the model exact original event index/timestamp and measured physical hold deficiency on rejected JSON, while the existing encoded-video inspector independently vetoes too-static output after rendering. This closes a specific failure mode without claiming to have solved automatic cinematic taste or adding a speculative new model framework.
- tests/phase2/test_studio_result_hold_audit.py: source-frame duration, stationary-but-small and large-but-moving failures, no smoothing across cuts, invalid/unverified event denial, opt-in safety and concrete model feedback. No private source media committed.

## Creative verdict

Neither of the compared videos is a premium director-approved product film. The ideal balance remains unproven. Still too much dark unused space, unreadable small source typography on mobile, no strong hook or narrative ending. Visual-quality approval ZERO, public production deployment unchanged. Next experimental pass should feed both precise rejections to a stronger multimodal director with verified source footage and authentic premium reference film, then test the generated JSON against a *new/unfamiliar* website, not claim a general solution from Resend alone.

Full targeted and Phase2 regression on same current-main code: 474 passed, 10 skipped, 29 subtests passed (to be reverified before final commit); no API inference requested for this scoped audit.

