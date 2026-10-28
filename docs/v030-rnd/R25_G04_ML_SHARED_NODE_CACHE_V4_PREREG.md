# r25 G0-G4 ML shared-node-cache v4 preregistration

Status: **PREREGISTERED / RESEARCH ONLY / NO RELEASE CREDIT**

This document freezes the decision boundary before the cross-member reuse census is adjudicated. It does not assert that v4 is worthwhile and does not authorize a product change.

## Causal question

The current Rust G0-G4 reader creates a fresh `DecodeContext` for each member. The v3 research candidate shared decoded physical records across members, but retained a member-local logical-node cache. The shipping Python reader keeps both record and node caches operation-scoped. The pre-v3 native baseline failed to complete a useful ML A/B within roughly 45 minutes, while v3 also failed to complete within roughly three hours; therefore v3's shared-record mutation is not sufficient evidence that record decode alone owns the native pathology.

The next question is deliberately narrower: **does canonical ML contain enough exact cross-member logical-node reuse to justify building one bounded operation-scoped shared-node-cache candidate?**

## Frozen census decision rule

The research-only census measures duplicate logical-node reconstruction implied by authenticated archive metadata. It is not a timing benchmark and receives no product or release credit.

Let `node_reconstruction_reuse_fraction = cross_member_repeated_node_bytes / per_member_node_closure_bytes`.

- **GO / build one v4 candidate** only if `node_reconstruction_reuse_fraction >= 0.20`.
- **KILL shared-node-cache as the next route** if `node_reconstruction_reuse_fraction <= 0.05`.
- **AMBIGUOUS / do not productize** for `0.05 < fraction < 0.20`; require a differently rooted diagnostic rather than threshold tuning.

These thresholds are frozen before reading the census result. Absolute byte counts, node-reference counts, and record-reuse counts remain explanatory diagnostics only; they cannot override the fraction gate after the fact.

## Candidate boundary if GO

A v4 candidate may change only operation-scoped execution reuse in the native reader:

1. decoded logical node values may be shared across members within one verify/extract operation;
2. cached nodes remain bounded by the existing native memory contract unless a separately preregistered memory change is justified;
3. a node-cache hit must preserve locality accounting by charging the physical-record dependency closure that would have been touched by reconstructing that node; cached work may not disappear from locality accounting;
4. representation bytes, grammar, selector, integrity checks, reconstruction identity, decode-unit limits, path/transaction semantics, and publication budgets are frozen;
5. no fixture path/name/hash identity may participate in admission or caching policy.

## v4 timing adjudication if built

The candidate must be tested on the canonical deterministic ML workload on the same runner against the shipping Python reader, with library load/build outside the timed operation but archive open, FFI call, verification/reconstruction, and extraction work inside the same boundaries as the v3 preregistration.

A valid candidate must complete correctness first. Then use at least five alternating Python/native pairs for both verify and extract.

- **ADVANCE headroom** only if native median verify **and** native median extract are each at least **20% faster** than Python, with exact semantic identity and all resource/locality laws intact.
- Otherwise: `G04_ML_FFI_SHARED_NODE_CACHE_HEADROOM_NOT_SUPPORTED`.
- Infrastructure, timeout, malformed candidate, identity failure, or resource-law failure: `CANDIDATE_INVALID`, not a product loss.

A GO from the static census only authorizes building the candidate. It does not relax this timing bar and grants no release credit.

## Anti-Goodhart / stopping rule

No threshold changes after seeing the census or v4 timing result. If v4 fails its frozen timing bar, retire this cache-reuse family and move down into the remaining exact reconstruction work (preflate/reconstruction/orchestration) rather than adding another cache layer by default.
