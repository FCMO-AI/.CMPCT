# ONE-G0.2 fused-observation cache integrity-hash accounting correction — 2026-09-07

## Mission lock

The fused-observation cache is writer-only discovery state. It may reduce repeated observation work, but it earns no promotion unless its exact semantics match the independent `observe()` oracle and its resource ledger charges the work it actually performs. No archive bytes, reader semantics, locality, integrity, recovery, or comparator requirements may be weakened to make the cache look faster.

## Hostile-review finding

`experiments/one/cache_fused_observe.py::_seal_message_bytes()` undercounted the bytes fed into SHA-256 when validating a reused cached block.

The seal serialization hashes, after the content digest:

- seven packed `u64` scalar fields: 56 B;
- `suffix_value` and `whole_same`: 2 B;
- the fingerprint count: 8 B;
- fingerprint payload: 8 B per fingerprint;
- one byte per chunk run-gate flag;
- the internal-run count: 8 B;
- internal-run payload: 24 B per run.

The accounting helper included the 56 B scalar group and variable payloads but omitted the two one-byte fields and both 8-byte sequence counts. The result was a deterministic **18 B undercount per successfully verified reused block**.

This is an evidence-meter defect, not an archive-semantic defect: `_valid_cached()` already hashes the full serialization and rejects invalid seals. The bug was in the resource counter exposed by `cache_integrity_hash_bytes`.

## Fix

Commit `c755fc2db11d7fef46f047f89665428b0ef9c23e` makes the accounting formula isomorphic to the bytes supplied to `_seal()` without changing the seal format or any threshold.

Commit `2e49420181d2bbeb4af9af35c1d0f8e1640ef0f4` adds an independent public-metric regression test. The fixture deliberately contains fingerprints, run gates, and internal runs; the test computes the expected byte count from the documented serialization rather than calling the private accounting helper.

## Magnitude

The correction is exactly `18 * reused_blocks` bytes of integrity-SHA input traffic.

For an exact repeat of a 1 MiB input with 4 KiB observation blocks, 256 reused blocks imply **4,608 B** of previously omitted SHA input accounting. With 1 KiB blocks, the same 1 MiB root would imply **18,432 B**. These are deterministic accounting deltas, not measured wall-time or CPU regressions.

## Falsifier / promotion boundary

The existing fused-observation resource gates remain frozen. The candidate must be re-run with the corrected ledger. A prior or future wall/CPU result is not enough if the evidence object reports incomplete cache work.

If the corrected hosted experiment still passes its preregistered size/resource/semantic gates, the next step is to profile the full repeated-observation cost into current-content SHA validation, cache-seal hashing, cached feature payload traffic, exact reuse verification, and feature recomputation. If it fails, do not lower a threshold: identify which charged component owns the loss and reform or retire the mechanism.

## Scope

Unchanged by this correction:

- canonical ONE representation and stored bytes;
- Law + Surprise semantics;
- reader grammar and reader discovery obligations (none added);
- decode throughput;
- selective-read amplification;
- reconstruction work and failure blast radius;
- frozen v0.29 / deferred-v0.30 comparator authority.

The correction only makes writer-side resource evidence more truthful.

## Evidence truth at preservation

The source fix and hostile regression test are committed on `research/cmpct1`. No completed exact-head hosted fused-observation resource artifact had been positively identified at preservation time, so this receipt makes no CI-green or performance-pass claim.
