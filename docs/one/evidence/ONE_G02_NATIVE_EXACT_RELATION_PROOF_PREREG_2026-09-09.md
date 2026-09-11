# ONE-G0.2 Native Exact Relation Proof — Preregistration (2026-09-09)

## Mission lock / Referee

V4 made relation nomination cheap enough that exact byte proof is now the dominant positive-path cost: representative 1 MiB combined-input rows spend roughly 45–49 ms in Python `grow_relation_spans()` exact verification, while the sparse gate and seed transfer together are around 1.1 ms.

This experiment changes **implementation only**, not proof semantics. It asks whether the exact proof boundary can be moved to a bounded native bulk kernel while reproducing the Python oracle's precise first-mismatch frontier, comparison count, accepted spans, rejected seed count, and sparse-crack recovery.

## Hypothesis

A native exact verifier using 16-byte bulk comparison where available plus scalar first-mismatch refinement can reproduce the Python oracle exactly and reduce exact-proof CPU by at least 4x on genuine relation spans without increasing false-seed work.

## Candidate contract

`experiments/one/native_relation_span_growth.py`:

- accepts the same parent/child bytes, op/value, nominations, seed size, and extension size as `grow_relation_spans()`;
- uses zero-copy read-only pointers into immutable Python `bytes`;
- performs no discovery;
- returns the same `RelationGrowthResult` fields;
- counts the mismatching byte exactly as the Python oracle does;
- never rereads an accepted extension chunk;
- coalesces adjacent runs identically;
- provides scalar fallback when SSE2 is unavailable.

Exact proof remains mandatory before a Law is stored.

## Matrix

Use deterministic sizes 64 KiB, 256 KiB, and 1 MiB with both add8 and XOR over:

1. exact relation across the full input;
2. sparse single-byte cracks at deterministic non-aligned positions;
3. early mismatch immediately after a 64-byte valid seed;
4. late mismatch near the end of a 4 KiB extension;
5. false seed with first-byte mismatch;
6. multiple separated valid regions requiring later nominations to resume after cracks.

Use dense aligned 64-byte nominations to exercise skip/covered-region behavior.

## Hard semantic gate

For every row, native result must equal Python oracle exactly for:

- `runs`;
- `compared_bytes`;
- `accepted_bytes`;
- `rejected_seeds`.

Any mismatch => `INVALIDATE_NATIVE_EXACT_RELATION_PROOF`.

## Performance gate

Alternating order, GC disabled, compile/warmup excluded from timed samples.

On `exact`, `sparse_cracks`, and `multi_region` rows:

- median native/Python proof CPU <= **0.25x**;
- no productive row > **0.50x**.

On false/early/late mismatch rows:

- native `compared_bytes` must remain exactly equal to Python;
- median native/Python CPU <= **1.00x**;
- no row > **1.50x**.

Native source traffic is modeled as exactly the same `compared_bytes` proof contract as Python; SIMD loads that cover bytes beyond the first mismatch are implementation-level memory traffic and must be called out separately if used. The kernel may not claim fewer proof bytes than the semantic oracle merely because a vector load inspected several lanes at once.

## Hostile review

Reject any implementation that changes mismatch frontier, skips exact proof, uses hashes as proof, weakens sparse-crack recovery, copies full inputs inside the timed native path, or reports vector lanes as fewer semantic comparisons than the Python oracle.

## Decision vocabulary

- `ADVANCE_NATIVE_EXACT_RELATION_PROOF`
- `HOLD_NATIVE_EXACT_RELATION_PROOF`
- `INVALIDATE_NATIVE_EXACT_RELATION_PROOF`

An ADVANCE is a bulk implementation improvement to the same ONE proof semantics; it introduces no new reader-visible mechanism.
