# Bencho free Foley bank

Upstream: https://github.com/cabralorenzo/bencho at 84dfcee170171257a28631402d37ff34900bc773.
The original 24 MIT-licensed recipes are vendored as sounds.ts; sounds.js is the
CommonJS transpilation for offline rendering. See LICENSE and THIRD_PARTY.md
for Lorenzo Cabra and Daniel Belyi notices. No Pro sounds or trademarks included.

Sauce's existing eventFoley renderer defaults to these lossless 48 kHz aliases:
click_crisp = Tick, whoosh_soft = Glide, pop_glass = Plop. Existing event gains
and sample positions remain unchanged. The current event renderer emits click
and movement cues; the pop slot is available but not automatically emitted.
Use --foley-bank procedural for the legacy sound. Other renderer paths retain
their existing audio settings.

Generate the full 24-sound library locally with:
python scripts/build_bencho_foley.py --out PRIVATE_DIR --chromium /path/to/chrome

The generator uses the upstream Web Audio schedule in an offline context,
seeded noise, and peak matching to 0.55 for Sauce gain controls.
catalog.json describes the generated full bank; only three aliases are shipped.
No automatic music, purchases, or remote audio requests are introduced.
