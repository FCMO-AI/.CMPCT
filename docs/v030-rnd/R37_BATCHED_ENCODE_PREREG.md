# R37 — deterministic batched candidate encoding preregistration

Status: **FROZEN BEFORE RESULT**. Research evidence only; no product/release credit.

## Parent evidence

R36 localized transferable excess `threading.Condition.wait` time to `src/cmpct/builder.py:build`, at the per-candidate `ThreadPoolExecutor.map` materialization boundary. R37 asks whether the scheduling granularity itself is causal enough to justify a product Builder surgery.

## Hypothesis

CMPCT currently exposes one executor work item per encoded candidate even though archive determinism depends only on the final sorted-hash result order. If contiguous deterministic candidate slices are encoded as at most one work item per worker and then flattened in slice order, encoded candidate tuples remain exactly identical while executor scheduling overhead falls materially.

## Frozen arms

1. `itemwise`: inherited one-candidate-per-Executor.map-item behavior.
2. `batched`: the identical `_encode_candidate` function over contiguous sorted-hash slices, with at most one slice per worker.

Both arms share one prepared `Builder` state in each target. R37 does not alter codecs, candidate admission, Deflate ownership, candidate order, worker count, format bytes, or product Builder code.

## Targets and repetitions

Use the same deterministic `full-backups` and `nested-only` source families built by the R34/R36 substrate. Use 8 workers and 7 measured repetitions per arm after one warm identity pass. Alternate arm order each repetition to avoid systematically gifting the second arm warmer caches.

## Mandatory identity

Every encoded tuple `(content_hash, codec, compressed_payload, metadata)` must be exactly equal between arms and across repetitions. Any identity drift kills the batching implementation class in its present form regardless of timing.

## Decision law

- `BATCHING_TRANSFERS`: median batched encode time is strictly lower than itemwise time on **both** full-backups and nested-only, with exact tuple identity.
- `BATCHING_DOES_NOT_TRANSFER`: identity holds but either target has zero/negative median time saved.
- Any identity failure is a substrate/implementation failure, not a timing result.

A positive result authorizes only a minimal product Builder implementation and an uninstrumented same-archive full-build benchmark. It does **not** itself earn runtime, release, or domination credit.

## Strong alternative explanation / risk

Equal-count contiguous slices can create load imbalance when candidate encoding costs differ sharply. Therefore a negative R37 result does not prove that all coarse scheduling is useless; it specifically kills naive equal-count contiguous batching as the next product move. A later scheduling design would require a new causal reason (for example a deterministic cost-balanced partition) rather than worker-count tuning.

## Product promotion boundary

Any later Builder change must preserve archive bytes exactly against the inherited candidate and must demonstrate uninstrumented end-to-end improvement without exporting unacceptable CPU, RSS, I/O, extraction, locality, recovery, portability, or determinism cost. R37 timing is mechanism evidence only.
