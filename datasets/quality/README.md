# Sauce quality diagnostics — v1 (25 November 2026)

This is the **negative-example and failure-analysis corpus**, not the production Gemini reference library. No film in this snapshot has an owner-granted premium reference approval. A green encoded test does not establish visual quality.

## Snapshot (refreshed 25 November 2026)

- **121 MP4 occurrences**, deduplicated to **117 distinct binary hashes**. Not 117 independent URL jobs.
- **66 hash-bound historical QA reports:** 43 REJECT, 23 HUMAN_REVIEW_REQUIRED; 51 missing/untrusted. No conflicting verdict/code sets in this snapshot. Older QA versions are not a uniform rerun.
- **Five curated creative rejections**, one unapproved research annotation, zero premium-approved examples.
- **35 pre-film rejection receipts**, nine unclassified. Receipt occurrences can refer to multiple attempts within a job.
- **Eight** films have both bound QA and a release-bound, independently hash-matched source; **ten** have hash-matched numeric camera plans. One release-bound source hash mismatches. Do not confuse a camera-plan match with source verification.

### Recurring patterns

| Finding | Distinct films (of 66 QA-bound) |
|---|---:|
| REPEATED_OR_STATIC_FRAMES | 41 |
| STATIC_OPENING_2S | 39 |
| NO_AUDIO_STREAM | 28 |
| ABRUPT_CUT_CANDIDATE | 2 |
| SILENT_OR_NEAR_SILENT_AUDIO | 1 |

Median reported static fraction among the 41 flagged films: 0.747. Median duration among all 66: 9.5833335s. Findings overlap; lack of a code is not proof of absence, and historical machine verdicts do not equal founder reviews.

Eight release/source-matched records with retained event manifests: median first confirmed payoff 5.39s; median final-result-to-end interval 5.97s (descriptive source-clock sample, not random or representative; the manifest timing is read from retained records). Nine weak-outcome receipts, four insufficient-final-hold receipts, three invalid-model-story receipts, three insufficient-witnessed-outcome receipts, two replan-exhausted, two navigation mismatch, one unstable initial state, one replay mismatch, one target shift/occlusion, nine unclassified. These are not 35 unique customers.

Controlled same-source DataOwl diagnostic: old master 13e0f49ef8538d40e8b621eeca029ceec83e9e104a9392913735c8225c23c4b1 vs localized-hero master 2ae26df737ef3af0095f2aed1514cd9070396754a53112a30d5e3fc248203509. Source, manifest and both referenced plan hashes independently checked against original files. Static fraction 0.870 → 0.779; opening p80 delta unchanged at 0.048. Inspected actual decoded frames at 0, 5.5, 17.8, 19.2, 27s plus compact DataOwl candidate f9f21ed3bc664ceabe2fe71e08283ecbeee9768a28167f749878d1ec6fd6ce4a at 0, 1.5, 3.5, 6, 9s (static fraction 0.755). Local detail improves chart legibility but does not solve a late payoff; even compact cut still waits on mundane picker interaction. No positive approval. Private sheet and locator under quality-audit-v2-20261125.

**Next experiment:** prioritize an early meaningful result and measured useful event density rather than more zoom or arbitrary duration reductions. Investigate safe actual interaction overhead and connected outcomes; preserve readable holds, actual pointer and verified source clocks. Compare same-source renders as regression diagnostics, then blind URLs held out by product. Only owner-approved source-true films may become positive references.

## Files

| File | Purpose |
|---|---|
| `diagnostics-v1.json` | Hash-keyed MP4 inventory and QA evidence; includes safe numeric camera grammar only when the film-plan hash and source-hash claim match |
| `failed-attempts-v1.json` | Pre-encoding typed rejections; makes missing films analytically useful |
| `curated-reviews-v1.json` | Explicit human evidence labels, source-truth public workflow labels and result times for selected hashes |
| `../../scripts/build_quality_dataset.py` | Rebuilds the dataset without exporting raw private artifact paths, prompts or media |
| `../../tests/test_quality_dataset.py` | Guards against untrusted QA, fabricated premium labels, private leakage and broken provenance |

The private film locator index is intentionally **not committed**. The binary SHA is the stable join key between the public diagnostic JSON and the owner's private worker. The `film_sha256`, `source_sha256_claim`, and `plan_sha256_claim` fields mean different things. Only `*_check: sha_match` is independently hash-verified by the builder. A missing hash or missing artifact must never be interpreted as source proof.

## Regenerate on the existing Vultr worker

From the repo working tree, against the existing owner-authorized private stores:

```bash
../.sauce-stagehand-venv/bin/python scripts/build_quality_dataset.py \
  --root research=../.sauce-stagehand-private \
  --root live=/var/lib/sauce-url2video/jobs \
  --annotations datasets/quality/curated-reviews-v1.json \
  --output datasets/quality/diagnostics-v1.json \
  --attempts-output datasets/quality/failed-attempts-v1.json \
  --private-index ../.sauce-stagehand-private/quality-dataset-private-20261125/locator-index.json
```

Check the diff and QA binding/annotation counts before committing refreshed snapshots; do not silently overwrite someone else's work or automatically commit operational files. The builder reads only completed `master-1080p60.mp4` binaries and typed `rejection.json` files under the **explicitly supplied** roots. It indexes encoded QA reports by actual film SHA, rejects conflicting verdict/code sets, prefers the strongest duplicate evidence, and never exports raw user or model text from those files. Build is diagnostic-only, not connected to the production Gemini prompt or model training.

## What this lets us measure

**Engine responsibility:** native recording glitches, frozen opening, missing audio, offscreen/clipped framing, late result hold, camera motion, export integrity. **Director responsibility:** repetitive action selection, content-free documentation tours, failure to find the interactive product, weak observed visual payoff. Some cases involve both; QA codes alone cannot assign blame.

Near-term use: sample **machine-rejected, hash-bound** examples by defect family; open the *private original encoded film* and full-resolution frames; identify the true cause, make one generalizable code change, run a brand-new URL-only experiment, and append a pinned review. Compare by **source and product novelty**, not just render count. Validate approval from the owner and an external premium reference before any positive few-shot ingestion.

## Known limits

This is not a large supervised training dataset: most films lack complete paired source/action evidence, 51 have no trustworthy machine QA, five creative rejections do not prove consistent label coverage, and no positive premium films exist. The numeric camera plan is useful for debugging—not automatically a good motion example. Some reports were generated by older QA logic and must be independently rerun before relying on them to claim a defect was fixed. Rejected or research-only studies are never reference-approved.
