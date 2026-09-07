# ONE-G0.2 incremental fingerprint-cache falsifier — 2026-09-07

## Mission Lock / Referee

**Question.** Can ONE-07 safely reuse an actual fused-observation feature family across related roots with enough margin to justify native work after current-byte validation, cache integrity, persistent-state cost, and hostile invalidation are charged?

**Candidate.** `experiments/one/cache_fingerprints.py` caches the aligned fixed-chunk FNV64 fingerprint stream used as an early observation/discovery signal. The cache is writer-only. It does not change ONE0 bytes, Program semantics, reader work, selective reads, authentication semantics, or the Law + Surprise representation principle.

**Falsifiable hypothesis.** Expensive observation features can be reused on content-identical blocks while changed blocks are conservatively recomputed, and the saved feature work can dominate the cost of verifying current content plus validating cached feature state.

**Disproof.** Reject or reform this cache shape if any incremental fingerprint stream differs from a fresh independent oracle; if policy/shape/corrupt state can be reused; if validation/cache bookkeeping removes the compute benefit; or if the persistent cache footprint is too large relative to the saved work. A Python win is only permission to build a native falsifier, never native/product evidence.

## Fixed semantics and accounting

- Every current block is SHA-256 hashed before reuse. `validation_read_bytes == len(input)` is therefore mandatory; unchanged bytes are never claimed as unread.
- `block_size` must be an exact multiple of `chunk_size`, so local cached streams concatenate to exactly the global aligned fingerprint stream.
- Reuse requires policy identity, geometry identity, content digest/length identity, structural bounds, and a domain-separated SHA-256 seal over the derived fingerprint payload.
- Cache corruption fails closed to recomputation.
- Shifted insertion receives no relocation shortcut in this seed; positional block identity is deliberately conservative.
- Persistent payload is charged as a lower bound of `72 + 8 * fingerprint_count` bytes per block, excluding Python/container-object overhead.
- With the preregistered 4096-byte block and 64-byte chunk, a full block holds 64 fingerprints and therefore at least **584 B** of persistent cache payload, **14.26% of source bytes**. This is a first-class cost, not hidden metadata.

## Independent hostile semantics

`tests/one/test_cache_fingerprints.py` uses an independent aligned-FNV oracle and attacks:

1. fresh and exact-repeat equivalence;
2. a sparse single-block edit;
3. correct content digest paired with corrupted derived feature state;
4. policy invalidation;
5. block-geometry invalidation;
6. misaligned block/chunk geometry;
7. shifted insertion without false relocation reuse;
8. current-content SHA provenance.

Any divergence is a correctness failure regardless of speed.

## Frozen Python viability experiment

`benchmarks/one/one_incremental_fingerprint_cache.py` uses:

- input sizes: 64 KiB, 256 KiB, 1 MiB;
- 4096-byte cache blocks;
- 64-byte aligned fingerprints;
- 15 repetitions per measurement;
- exact repeat and one-block-edit cases;
- median wall time from `perf_counter_ns`;
- median process CPU from `process_time_ns`;
- fresh/incremental exact fingerprint equality before timing.

For every case at **>=256 KiB**, cached creation must be **<=0.50x fresh wall time and <=0.50x fresh process CPU**. The bar is intentionally severe because the Python FNV kernel is far slower than a competent native bulk implementation. A weaker Python result would be poor evidence that the mechanism can survive native optimization of the baseline.

Passing this gate means only `ADVANCE_TO_NATIVE_FALSIFIER`. It does not promote the cache, alter the September 11 Genesis scoreboard, or establish native creation speed.

## First hosted-run truth

Exact-head run `34132055350` bound successfully to `5e0ba3e16f0ddfeb7d02ae33b14aa0c0a88100ff`, but the hostile test step failed before executing tests because the hosted Python environment did not contain `pytest` (`No module named pytest`). The benchmark was consequently skipped and no artifact was produced. This is an infrastructure failure, **not** a candidate pass/fail.

The workflow was repaired at commit `cad3efb1ddd3de0624fd5a5d3b5a93dede987309` by explicitly provisioning pytest before the semantic tests. No scientific gate was changed.

## Hostile Reviewer / strongest concern

The main threat is not correctness but economics. This seed still reads and SHA-hashes the complete source, while its persistent fingerprint payload is already ~14.3% of source size at the frozen geometry. The candidate therefore needs to replace substantially more expensive discovery work than a native fingerprint pass alone. A spectacular Python ratio would be easy to overinterpret because byte-at-a-time Python FNV is deliberately expensive relative to native hashing and vectorizable fingerprinting.

A native follow-up, if permitted, must charge source traffic, SHA/content-identity work, cache lookup/seal verification, cache RSS/payload, feature recomputation, and total writer wall/CPU. If those costs erase the advantage, the right response is to reform the cache identity/feature granularity or share authentication work already required elsewhere—not to relax the gate.

## Comparator / representation truth

This experiment changes no stored ONE representation and earns no density, decode, selective-access, reconstruction, failure-domain, v0.29, or deferred-v0.30 advantage by itself. Frozen comparator authority remains unchanged. The September 11 same-input full-matrix decision remains the only Genesis supersession gate.
