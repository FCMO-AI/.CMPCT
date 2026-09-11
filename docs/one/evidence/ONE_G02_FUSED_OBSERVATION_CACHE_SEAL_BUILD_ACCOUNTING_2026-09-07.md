# ONE-G0.2 fused observation cache — seal-build accounting audit

Date: 2026-09-07
Branch: `research/cmpct1`
Status: result-bearing audit/gate added; hosted artifact pending at receipt creation

## Mission Lock / referee

Hypothesis: the fused observation-cache resource ledger can undercharge integrity work on fresh or changed blocks because `_compute_block()` creates a SHA-256 seal for every newly computed cached block while `IncrementalObservationStats.cache_integrity_hash_bytes` has historically been incremented only when validating a reused cached block.

Disproof test: independently reconstruct the exact seal message size from the returned public cache shape, classify in-process blocks as reused only when the observer preserves the prior block object, and charge both (a) verification of reused state and (b) construction of fresh/recomputed state. The scientific charge must never be smaller than this independently reconstructed total. Exact repeats must have zero build-side seal cost; a one-byte sparse edit must expose both verification and build-side costs.

This audit does not change ONE bytes, Law/Surprise semantics, reader behavior, locality semantics, comparator settings, or any frozen performance threshold.

## Finding

The implementation performs seal creation inside `_compute_block()` for every recomputed block. The existing exposed integrity-hash counter is incremented on the reuse-validation path. Therefore fresh creation and sparse changes can omit build-side seal SHA input from that particular causal meter even though the SHA work actually occurs and is already present in wall/process CPU measurements.

This is a scientific-accounting defect, not a data-integrity defect: the cache seal itself is still created and checked. The risk is an optimistic explanation of *why* incremental creation costs what it costs, especially when comparing verification overhead with feature recomputation.

## Builder

Added `experiments/one/fused_cache_cost_ledger.py` as an independent, non-circular oracle. It reconstructs:

- expected reused-state seal verification SHA input;
- expected new/recomputed-state seal construction SHA input;
- independently expected total integrity SHA input;
- currently reported integrity SHA input;
- any accounting gap;
- a conservative charged value equal to the larger of reported and independently expected total.

The oracle intentionally does not call the implementation's private `_seal_message_bytes()` helper. It derives the SHA message length from the seal wire shape: domain, policy framing/text, digest, seven u64 scalar fields, two one-byte values, fingerprint count/payload, run-gate payload, internal-run count, and three-u64 internal-run records.

Added hostile tests covering:

1. independent structural seal-size accounting;
2. fresh creation (build cost only);
3. exact repeat (verification cost only);
4. one-block sparse edit (both verification and build cost);
5. incompatible compiler policy (all current seals treated as builds).

Added deterministic benchmark `benchmarks/one/one_g02_fused_cache_integrity_ledger.py` for 256 KiB and 1 MiB roots with 4 KiB observation blocks. It emits JSON for fresh, exact-repeat, and one-byte sparse-update cases and fails if the independent charge undercounts reconstructed work.

Added exact-path workflow `.github/workflows/cmpct1-one-g02-fused-cache-integrity-ledger.yml` to run both hostile tests and the deterministic audit and retain the JSON artifact.

## Hostile reviewer

The independent oracle is intentionally scoped to in-process experiment auditing. It identifies a reused positional block by object identity because the current observer admits reuse by assigning the exact prior `FusedObservationBlock` object. That is exact for this implementation path but is not a serialized-cache protocol and must not be mistaken for one.

The conservative `charged_hash_bytes = max(reported, independently_expected)` rule is forward-compatible with a future core-meter fix: once the observer itself reports build-side seal hashing, this audit should stop showing a positive gap rather than double-charge it.

This correction does **not** establish that fused caching is efficient. It makes the cost decomposition harder to fool. The real promotion question remains whether avoided fused observation/discovery work pays for current-content SHA validation, seal verification/build hashing, cached-feature traffic, exact reuse proof, changed-block recomputation, cache residency, and eventual full-ingest interaction.

## Promotion boundary

No density, create-throughput, decode-throughput, RSS, selective-read, reconstruction, or 15-workload claim follows from this receipt. Frozen v0.29 and deferred-v0.30 comparator authority is unchanged. The September 11 same-input Genesis evaluation remains authoritative.

Do not weaken existing fused-cache wall/CPU/resource gates because this audit raises the charged integrity-work total. If the corrected decomposition makes the mechanism unattractive, preserve that negative result and change the mechanism rather than the threshold.

## Next decisive action

Consume the hosted JSON and then profile the fused cache into five explicit cost owners:

1. current-content SHA validation;
2. cached-state seal verification and new-state seal construction;
3. cached-feature payload traffic;
4. exact reuse proof;
5. changed-block fused-feature recomputation.

If the first two dominate, share or reuse authentication work already required by ONE rather than adding another validation pass. If cached-feature traffic dominates, reduce/pack discovery state. If recomputation still dominates on sparse edits, changed-cone granularity is too coarse. Only after this decomposition survives hostile workloads should fused observation caching move into a full ONE writer/ingest A/B.
