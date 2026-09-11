# ONE-G0.2 interval packed authenticated-range proof — preregistration

Date: 2026-09-08
Branch: `research/cmpct1`
Experimental version: `ONE-G0.2`

## Mission lock

The first packed-range proof candidate is preserved as `HOLD_PACKED_AUTH_PROOF`: semantics were exact and 64 KiB requests consistently improved, but too many 4 KiB rows paid a small packed lookup/slicing tax to satisfy the frozen broad non-regression gate.

Mechanism review found avoidable work in that candidate and in the materialized Python reference: requested leaves always form one contiguous interval, but proof discovery repeatedly constructs/scans Python sets containing every selected node at every tree level. For a binary tree, ancestors of a contiguous leaf interval remain contiguous, so at each level only the left and right interval boundaries can require external sibling hashes.

Hypothesis: replacing per-level selected/needed sets with two integer boundaries removes enough high-level control overhead to keep the packed sidecar broadly non-regressing even for 4 KiB proofs, while preserving exactly the same `RangeProof` bytes and exact one-digest-per-sibling traffic.

Disproof: any proof mismatch, any extra digest read, any full-tree materialization, any 1 MiB row >1.10x reference wall/CPU, fewer than 14/16 decisive rows non-regressing on both, or any 256 KiB row >1.15x.

## Candidate / control

Control: prebuilt Python `AuthTree` + existing `prove_range()`.

Candidate: prebuilt packed `NativeAuthTree` + `prove_range_packed_interval()`.

Both tree builds remain outside proof-generation timing. This does not borrow the already-proven native construction win.

`prove_range_packed_interval()` must derive the selected leaf interval `[lo, hi]`; emit payload slices for that interval; at each level emit `lo-1` only when `lo` is odd and emit `hi+1` only when `hi` is even and that sibling exists; then replace `[lo,hi]` by `[lo//2,hi//2]`. Digest emission order must remain byte-identical to sorted reference sibling coordinates.

## Frozen matrix

Same matrix as the HOLD for direct rehabilitation evidence:

- source sizes: 256 KiB and 1 MiB;
- leaf sizes: 80, 96, 112, 192 bytes;
- requests: first 4 KiB, middle 4 KiB, final 4 KiB, middle 64 KiB;
- 21 paired alternating repetitions after two warmups;
- deterministic source generation;
- decision scale: 1 MiB.

## Frozen semantic/resource gates

Every row must prove:

- native/reference roots exact;
- candidate `RangeProof` byte-for-byte equal to reference;
- `verify_range()` reconstructs exactly the requested bytes;
- candidate reads exactly one 32-byte packed digest for every emitted sibling and no other tree digest;
- candidate does not call full `levels()` expansion.

## Frozen performance decision

`ADVANCE_INTERVAL_PACKED_AUTH_PROOF` only if:

1. complete exact matrix;
2. every 1 MiB row has median candidate/reference wall <=1.10 and CPU <=1.10;
3. at least 14 of 16 1 MiB rows have wall <=1.00 **and** CPU <=1.00;
4. every 256 KiB row has wall <=1.15 and CPU <=1.15.

Otherwise `HOLD_INTERVAL_PACKED_AUTH_PROOF`; semantic/traffic/matrix failure => `INVALIDATE_INTERVAL_PACKED_AUTH_PROOF`.

This gate is stricter than the first packed candidate's 12/16 non-regression requirement because the mechanism specifically claims to remove its small-read control overhead. A second broad HOLD means do not threshold-tune the same Python proof extractor again; move proof traversal native/batched or retain materialized proof state where justified.

## Claim boundary

A green result rehabilitates the packed in-memory sidecar for generic source-range proof construction. It still does not prove proof-verification throughput, peak RSS, canonical disk placement, remote I/O/cache-line traffic, or libcrypto portability.