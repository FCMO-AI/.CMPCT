# ONE-G0.2 lazy Segment charged-ingest result — 2026-09-08

## Authority

- branch: `research/cmpct1`
- exact result-bearing source: `ce057eb24bf62a734dba77f1065150cf7de3167d`
- experiment: `benchmarks/one/one_g02_lazy_segment_charged_ingest.py`
- preregistration: `docs/one/prereg/ONE_G02_LAZY_SEGMENT_CHARGED_INGEST_PREREG_2026-09-08.md`
- hostile review: `docs/one/evidence/ONE_G02_LAZY_SEGMENT_CHARGED_INGEST_HOSTILE_REVIEW_2026-09-08.md`
- workflow run: `34224595923`
- job: `102055519343`
- artifact: `one-g02-lazy-segment-charged-ingest-ce057eb24bf62a734dba77f1065150cf7de3167d`
- artifact id: `10055331504`
- artifact digest: `sha256:e1763df4f0565688cd3c7d6a234b287ba23e37a1d99fea1096ac6681c8869c41`

## Mission lock

Test whether the previously advanced lazy Segment-arena scheduling survives a broader writer bill rather than existing only as an allocator microbenchmark.

The paired envelope charges source and target bytes-to-ctypes conversion, SHA-256 of both roots, relation admission, eager-or-conditional Segment allocation, native segmentation when admitted, bounded Law + Surprise Program construction, validation and direct canonical emission. Native build, filesystem/archive traversal, authenticated placement and decode timing remain outside scope.

Only allocation timing differs between arms.

## Frozen decision law

At 1 MiB:

- every admitted row must keep lazy/eager median wall and CPU ratios <= `1.05` and preserve the same Segment capacity;
- every rejected row must keep lazy/eager median wall and CPU ratios <= `0.97` and lazy Segment capacity must remain zero.

At 64 KiB every row has a gross-regression veto of `1.08` on both wall and CPU.

The matrix must be complete and semantic/canonical equality must hold. The benchmark process exits zero only for `ADVANCE_LAZY_SEGMENT_CHARGED_INGEST`.

## Exact result

GitHub Actions run `34224595923` completed successfully on exact source `ce057eb24bf62a734dba77f1065150cf7de3167d`. Exact-source checkout/binding, the frozen decision-law tests, the charged-ingest falsifier and artifact preservation all completed successfully.

Because the benchmark's `main()` returns zero only when `decision == "ADVANCE_LAZY_SEGMENT_CHARGED_INGEST"`, the result is:

> **ADVANCE_LAZY_SEGMENT_CHARGED_INGEST**

Therefore, under the frozen matrix and claim boundary:

- all exact semantic/canonical gates passed;
- all 1 MiB admitted rows remained within the <=1.05 wall and CPU guardrail;
- all 1 MiB rejected rows achieved <=0.97 wall and CPU ratios and allocated zero lazy Segment capacity;
- all 64 KiB rows stayed within the <=1.08 gross-regression veto.

The exact row medians are preserved in the retained JSON artifact and are not reconstructed from CI status prose here.

## Interpretation

Lazy Segment scheduling has now survived two independent scopes:

1. a focused writer timing gate where relation admission, conditional allocation, segmentation, Program construction, validation and canonical emission are charged; and
2. this broader transfer gate, which additionally charges source/target ctypes conversion plus SHA-256 of both roots.

The mechanism is simple: do not allocate the worst-case Segment arena until the cheap relation gate has established that segmentation will execute.

This is a compute/resource scheduling improvement, not a new representation mechanism. Stored ONE bytes and reader semantics are unchanged.

The earlier fresh-process resource experiment remains the peak-memory authority: rejected 1 MiB roots avoided roughly 12.58 MiB of Segment capacity and showed about 26% lower peak RSS. This result does not create a second RSS claim; it adds creation-time transfer evidence.

## Strongest surviving criticism

The charged envelope is still not complete product ingest. It does not charge filesystem traversal, metadata collection, authenticated placement/index construction, native build/process startup or product integration. It also hashes both previous and current roots even though a persistent versioned writer may already possess a trusted previous-root identity.

That dual-root hashing makes this transfer test conservative for the lazy-allocation delta, but it also leaves a causal question unresolved: how much writer time is spent re-proving a previous generation whose identity could be carried as authenticated state?

## Decision / next falsifier

Promote lazy Segment allocation as the preferred scheduling policy in the current temporal research-writer path.

Next, isolate **trusted-prior-root reuse** from current-root authentication. Compare the current conservative `sha256(previous)+sha256(current)` writer bill against a persistent-writer shape where the previous digest is supplied as already-authenticated state and only the new/current root is hashed inside creation. Preserve identical Program/wire/reconstruction semantics and do not call the result a product authentication win until authenticated placement/state transfer is represented.

This next experiment should answer whether the earlier root-hash ownership signal contains avoidable prior-generation rehash work before any authentication+observation fusion is designed.
