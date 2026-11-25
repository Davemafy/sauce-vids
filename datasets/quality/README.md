# Sauce quality diagnostics — v1 (25 November 2026)

This is the **negative-example and failure-analysis corpus**, not the production Gemini reference library. No film in this snapshot has an owner-granted premium reference approval. A green encoded test does not establish visual quality.

## Snapshot

- **113 MP4 file occurrences**, deduplicated by SHA-256 to **109 distinct film binaries**. The inventory includes experimental re-renders and API jobs, not 109 independent customer URLs.
- **28 hash-bound machine QA reports:** 21 machine verdict `REJECT`, seven `HUMAN_REVIEW_REQUIRED`. Another **81** films have no trustworthy bound QA: 79 without the expected report and two whose report SHA does not match the actual MP4. They are **unlabeled**, not assumed successes or rejections.
- **Six manually anchored human status annotations** in `curated-reviews-v1.json`: five `creative_reject`, one `unapproved_research`. Annotations are explicitly based on exact film hashes and the verified living handoff, not generated review scores.
- **21 pre-film rejection receipts**, recorded separately as typed controlled reasons. Two unrecognized reasons remain `UNCLASSIFIED_REJECTION`—their source text is deliberately withheld.
- **Three source-claimed, file-hash-verified numeric camera plans** in `diagnostics-v1.json`, plus curated safe public action lists and verified event times for the known films.
- **Zero** owner-approved premium films. No research negative may be promoted to an approved Gemini few-shot exemplar, even when a QA verdict is `HUMAN_REVIEW_REQUIRED`.

Counts apply to the snapshot only and can change as new private experiments are added.

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

Check the diff and QA binding/annotation counts before committing refreshed snapshots; do not silently overwrite someone else's work or automatically commit operational files. The builder reads only completed `master-1080p60.mp4` binaries and typed `rejection.json` files under the **explicitly supplied** roots. It never uses raw user or Gemini text from those files. Build is diagnostic-only, not connected to the production Gemini prompt or model training.

## What this lets us measure

**Engine responsibility:** native recording glitches, frozen opening, missing audio, offscreen/clipped framing, late result hold, camera motion, export integrity. **Director responsibility:** repetitive action selection, content-free documentation tours, failure to find the interactive product, weak observed visual payoff. Some cases involve both; QA codes alone cannot assign blame.

Near-term use: sample **machine-rejected, hash-bound** examples by defect family; open the *private original encoded film* and full-resolution frames; identify the true cause, make one generalizable code change, run a brand-new URL-only experiment, and append a pinned review. Compare by **source and product novelty**, not just render count. Validate approval from the owner and an external premium reference before any positive few-shot ingestion.

## Known limits

This is not a large supervised training dataset: most films lack complete paired source/action evidence, 82 have no trustworthy machine QA, five creative rejections do not prove consistent label coverage, and no positive premium films exist. The numeric camera plan is useful for debugging—not automatically a good motion example. Some reports were generated by older QA logic and must be independently rerun before relying on them to claim a defect was fixed. Rejected or research-only studies are never reference-approved.
