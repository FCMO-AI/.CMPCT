# ONE-G0.2 native fresh-observer transfer — preregistration

Date: 2026-09-07
Branch: `research/cmpct1`
Experimental version: `ONE-G0.2`

## Mission Lock / Referee

The whole research-writer fused-cache experiment exposed a major confound: ordinary fresh `experiments.one.observe.observe()` owns roughly 98.5-99.1% of that envelope because its fused byte scan, FNV formation, run tracking and Python dictionary/list bookkeeping execute per byte/chunk in Python. The cache's large positional win is real against that baseline, but its architectural value may collapse once the fresh observer becomes a native bulk kernel.

Before conditional caching is treated as broadly promoted, transfer the exact fresh-observer semantics to a bounded native implementation and measure whether the observer itself has a large implementation-level speed reserve.

## Representation rule

This is not a new ONE mechanism. The native kernel must emit the exact same `RunOpportunity`, `ReuseOpportunity` and `ObservationStats` semantics as the Python reference observer. It is an implementation candidate for the same writer-side discovery pass. No reader-visible state or canonical bytes change.

## Frozen semantic model

The native kernel must reproduce the current `observe.py` rules exactly for the tested shapes:

- one forward byte scan;
- run opportunities emitted for maximal same-byte runs with length >= `min_run`;
- aligned fixed-size FNV-1a 64-bit fingerprints;
- chunks wholly explained by the current qualifying run skip reuse lookup;
- first retained source per fingerprint nominates later chunks;
- adjacent source/target nominations coalesce before exact byte proof;
- emitted reuse requires exact byte equality;
- insertion stops at `max_index_entries` while lookup continues;
- source/read/index/resource counters match the reference semantics exactly.

The native hash table is implementation detail only. It may use open addressing, but its observable first-source behavior and insertion bound must match the reference.

## Falsifiable hypothesis

For the now-stable G0.2 observer semantics, a compiled C fresh observer can reproduce exact Python opportunities/stats and reduce median observer wall and process CPU to <=0.25x the Python reference on 64 KiB, 256 KiB and 1 MiB representative roots without increasing algorithmic retained payload or source-read accounting.

This is intentionally a transfer test, not a cache test. If it passes, the fused-cache admission experiment must later be rerun against the native fresh baseline before broad system promotion.

## Frozen matrix

Deterministic roots at 64 KiB, 256 KiB and 1 MiB:

- structured mixed runs/repetition;
- seeded incompressible/random;
- compressed-like deterministic bytes;
- long-run-heavy hostile root;
- near-repeat false-pattern root whose chunks differ by small byte changes and must not acquire false reuse authority.

Semantic vectors also include tiny/tail shapes around `min_run` and `chunk_size`: 0, 1, 7, 8, 9, 63, 64, 65, 127, 128 and 129 bytes, plus a bounded-index exhaustion case and seeded small-input parameter fuzz across multiple `min_run`, `chunk_size`, and index bounds.

## Gates

- exact runs tuple equality on every semantic vector;
- exact reuse tuple equality on every semantic vector;
- exact `ObservationStats` field equality on every semantic vector;
- no crash or out-of-bounds output on empty/tail/index-bound cases;
- for each timed size, geometric family aggregate and every individual family: native/Python median wall <=0.25 and CPU <=0.25;
- native output capacity must be deterministically bounded from input length; no unbounded allocation inside the scan;
- algorithmic retained-index payload remains exactly the same semantics as Python (`8*occupied_buckets + 8*entries`).

No timing gate may move after results.

## Independent evidence

Python `observe()` remains the semantic oracle. The native wrapper converts only already-produced native structs into the same Python dataclasses for comparison; it must not call the Python observer to repair or fill missing native opportunities/stats.

15 paired alternating repetitions per timed row. Compile with the repository's existing hosted C compiler at `-O3`; record compiler command and exact evidence SHA. Wall and process CPU are both authoritative.

## Disproof / terminal decisions

- any semantic/stat divergence -> `INVALIDATE_NATIVE_OBSERVER`;
- semantic pass but any timed row or per-size geometric family aggregate >0.25 wall or CPU -> `HOLD_NATIVE_OBSERVER_TRANSFER`;
- all semantics and timing gates pass -> `ADVANCE_NATIVE_FRESH_OBSERVER`.

## Hostile Reviewer

The strongest expected objection is that easy structured roots can make the Python observer look worse than production material. That is why every timed family must pass individually, including incompressible and near-repeat controls.

A second objection is that C FNV/index acceleration may change collision behavior. The native index therefore retains the first source for a fingerprint exactly as the current Python path effectively does, and exact byte proof remains mandatory before reuse emission. A future explicit collision vector can be added only if a deterministic colliding pair is independently available; absence of such a vector is regression debt and prevents claiming adversarial FNV-collision completeness.

The final architectural objection is more important: even if native fresh observation is far faster, it may still leave cache reuse valuable for expensive future discovery features. This experiment does not retire caching. It establishes the correct optimized baseline against which cache persistence must earn its keep.

## Claim boundary

A pass establishes an exact native implementation candidate for current G0.2 fresh observation on the frozen semantic/timing matrix. It does not establish product-native authority, SIMD optimality, cache superiority, authenticated placement, automatic Law selection, density gains, selective-read gains or v0.29/v0.30 supremacy.
