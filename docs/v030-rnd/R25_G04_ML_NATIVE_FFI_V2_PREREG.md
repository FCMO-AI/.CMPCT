# R25 G0-G4 ML native in-process FFI reader v2 preregistration

Status: **FROZEN BEFORE RESULT-BEARING EXECUTION**

This supersedes only the invalid v1 candidate-transport instrument documented in
`R25_G04_ML_NATIVE_FFI_V1_INVALID_RESULT.md`. It does not supersede or alter the scientific question, corpus,
comparator, thresholds, archive semantics, or claim boundary.

## D0 diagnosis and worldview

The v1 run never constructed its candidate because its committed patch was not syntactically valid. No A/B result
exists. The unresolved Forge question is therefore unchanged:

> On the canonical `neutral_hostile_v1/09_ml_artifacts` workload, does operation-scoped reuse of authenticated,
> decoded G0-G4 physical records make the already-existing Rust semantic owner materially faster than the canonical
> Python reader when both are exercised through the same in-process FFI boundary?

The mechanism under test is execution reuse only. It must not change representation bytes or move required work
outside the charged operation.

## Frozen experiment

- Source: the exact authoritative commit that triggers the v2 workflow.
- Target: exactly `neutral_hostile_v1/09_ml_artifacts`.
- Shipping archive: canonical r25 G0-G4 selected by the unchanged product builder.
- Comparator: inherited canonical Python `_stream_g04`.
- Candidate: inherited `cmpct-portable` G0-G4 reader with a bounded operation-scoped physical-record cache reused
  across sequential full-archive member reads.
- FFI: inherited `cmpct-g04-ffi`; one-time dynamic-library load remains outside timing, while each archive open,
  FFI call, verify/extract operation, integrity work, and caller output-budget preflight remain inside timing.
- Rounds: exactly 5 alternating Python/native pairs.
- Decision statistic: median wall time for Python verify, native verify, Python extract, and native extract.

Frozen terminal decision:
- `G04_ML_FFI_SHARED_CACHE_HEADROOM_SUPPORTED` only if **both** native median verify and native median extract improve
  by at least **20%** versus their Python medians and every exactness/safety gate passes.
- `G04_ML_FFI_SHARED_CACHE_HEADROOM_NOT_SUPPORTED` if the experiment is valid but either improvement is below 20%.
- `CANDIDATE_INVALID` if the candidate cannot be constructed or any prerequisite/exactness/safety invariant fails.

No noise-band substitution or post-result threshold change is allowed.

## Immutable semantic and safety invariants

The candidate may not change:
- archive bytes, archive grammar, product selector, or canonical profile identity;
- logical tree, complete member SHA-256/CRC enforcement, payload authentication, corruption rejection, or fail-closed
  behavior;
- 8 MiB decode-unit limit;
- 8x member decoded-context locality limit;
- record/node memory ceilings or caller extraction output budget;
- transactional publication semantics;
- Python comparator or target corpus.

Cache hits remain charged to member-local decoded-context accounting. Node materializations and member-local touched
record accounting may not be gifted across member boundaries.

## Sole v2 instrument repair

The malformed v1 diff is not modified. v2 constructs the temporary candidate by:

1. applying only the exact-current G0-G4 hunks from the already-valid
   `benchmarks/patches/v030_g04_operation_record_cache.patch`;
2. running `benchmarks/v030_g04_shared_record_cache_candidate_v2.py`, a fail-closed exact-snippet mutator that routes
   canonical G0-G4 regular-file extraction through the shared bounded record cache while leaving PrefixGraph
   extraction unchanged;
3. checking the resulting diff, compiling it, running the inherited G0-G4 Rust and Python correctness suites, then
   running the unchanged scientific oracle;
4. restoring all patched product sources before job completion.

The v2 preserved-result concurrency group is exact `github.sha`, satisfying repository queue custody. These are
mechanical instrument repairs only.

## Claim boundary and next state

This experiment has **zero release credit**. A positive result authorizes an explicit Builder integration attempt
for the ML G0-G4 reader hot path; that Builder must then re-earn parser/fuzz/recovery/native/platform/Android/runtime
authority and global carrying-cost review. A valid negative retires this shared-record-cache execution family for
this exact ML/full-archive/in-process regime unless new causal evidence supplies a reopening predicate.
