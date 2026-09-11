# ONE-G0.2 packed authenticated-range proof — exact-source result

Date: 2026-09-08
Experimental version: `ONE-G0.2`
Source branch: `research/cmpct1`
Exact result-bearing source: `556b7599448efd11a689c6bccc20e995428a2c00`
Frozen comparators remain: v0.29 `02b8b27cb2d97af7c6e0797984a898e8fa8a8e5d`; deferred v0.30 `f4b158a55a08b9b18b50e4e4abe4b9251048c772`

## Exact CI authority

Workflow run: `34243185277`
Job: `102118329774`
Workflow: `CMPCT1 ONE-G0.2 packed auth proof`
Artifact: `10063104654`
Artifact name: `one-g02-packed-auth-proof-556b7599448efd11a689c6bccc20e995428a2c00`
Artifact ZIP SHA-256: `b4ab08bfd05a8b70c48d0e4bff7b23617b0f5d3c10bbee7350fd69421e5d4216`

The workflow's semantic/decision suite completed with 56 passing tests. The benchmark then produced its exact JSON evidence and exited nonzero because the frozen decision was `HOLD_PACKED_AUTH_PROOF`; artifact preservation still completed successfully. This is a scientific HOLD, not an infrastructure failure.

## Frozen decision

`HOLD_PACKED_AUTH_PROOF`

All tested proofs remained semantically exact: native/reference roots agreed, candidate `RangeProof` objects matched the independent Python reference, verification reconstructed the requested bytes exactly, and the candidate read exactly one 32-byte packed digest per emitted sibling rather than expanding the complete tree.

The performance gate did not pass. At the 1 MiB decision scale every row remained inside the frozen 1.15x wall/CPU hard ceiling, but fewer than the required 12 of 16 rows were non-regressing on both wall and CPU. The exact result contains roughly seven decisive rows satisfying the joint <=1.00 condition.

The row pattern is causal rather than random:

- 4 KiB first/middle proofs usually pay a small packed-index lookup/slicing tax, generally a few percent over the already-materialized Python reference;
- final 4 KiB proofs are near parity and sometimes slightly favorable;
- middle 64 KiB proofs consistently benefit, typically by roughly 6-8% in the exact hosted result.

Representative exact-result ratios include:

- leaf 80, first 4 KiB: ~1.071 wall / ~1.073 CPU;
- leaf 80, middle 4 KiB: ~1.045 / ~1.046;
- leaf 80, final 4 KiB: ~0.989 / ~0.989;
- leaf 80, middle 64 KiB: ~0.937 / ~0.938;
- leaf 96, first 4 KiB: ~1.046 / ~1.046;
- leaf 96, middle 64 KiB: ~0.945 / ~0.945;
- leaf 112, first 4 KiB: ~1.032 / ~1.032;
- leaf 112, middle 64 KiB: ~0.933 / ~0.933.

Exact row medians and all remaining ratios remain authoritative in the retained JSON artifact.

## Interpretation

The packed native tree remains a valid construction representation, but direct packed proof generation does **not** advance as an unconditional replacement for the already-materialized Python proof path. The control is intentionally strong because its level tuples already exist before proof timing; the candidate is not allowed to hide proof overhead behind the previously proven native construction win.

The useful surviving signal is range-size dependent. Larger selective requests amortize packed digest indexing and benefit from avoiding broader Python object traversal, while tiny 4 KiB requests are sensitive to per-sibling Python slicing/index overhead. A future candidate may therefore explore a size-gated or batched extraction path, but only if it compiles to the same generic proof semantics and earns a new preregistered gate. Do not promote a threshold post hoc from this result.

## Claim boundary

This HOLD does not revoke `ADVANCE_NATIVE_AUTH_TREE_BATCH`. Construction-speed evidence remains valid. It only blocks the stronger claim that the current Python `prove_range_packed()` implementation should replace the materialized proof path across all selective reads.

No reader-visible format, integrity grammar, authentication domain, stored-byte policy, or comparator requirement changed.
