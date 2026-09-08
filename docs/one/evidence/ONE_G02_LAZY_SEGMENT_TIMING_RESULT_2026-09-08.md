# ONE-G0.2 Lazy Segment Timing — Exact-Head Result

**Date:** 2026-09-08  
**Experimental version:** `ONE-G0.2`  
**Result-bearing source:** `bb60c3f144c722c8aadd2a0608d0c1585db96e57`  
**Workflow run:** `34222401430`  
**Job:** `102048367658`  
**Artifact:** `one-g02-lazy-segment-timing-bb60c3f144c722c8aadd2a0608d0c1585db96e57`  
**Artifact id:** `10054407943`  
**Artifact digest:** `sha256:03fb9400b15a90f902c10807edf85bb8f9f8153001189d7d0ded1e1f8bf33739`

## Mission lock

Test whether moving the native `Segment` arena allocation behind relation admission is not only a reject-path peak-memory improvement, but also a creation-time improvement under the current preferred ONE temporal research-writer envelope.

The candidate changes allocation scheduling only. It does not add a reader-visible mechanism, alter Law + Surprise semantics, weaken validation, change canonical bytes, or change the relation-admission rule.

## Frozen falsifier

The result-bearing benchmark is `benchmarks/one/one_g02_lazy_segment_timing.py` as bound at the exact source SHA above.

Decision matrix:

- 1 MiB roots;
- 21 paired alternating repetitions;
- admitted: `shift_plus1`, `shift_plus1_damage_quarter`, `fragmented_every96`;
- rejected: `fragmented_every32`, `independent_random`;
- every admitted row must have lazy/eager median wall **and** CPU <= `1.05x` and preserve identical arena capacity once admitted;
- every rejected row must have lazy/eager median wall **and** CPU <= `0.95x` and allocate **zero** lazy `Segment` capacity;
- exact semantic/canonical equivalence is mandatory;
- incomplete matrices cannot advance.

The benchmark's process exit contract is deliberately strict: exit code 0 occurs **only** when `decision == "ADVANCE_LAZY_SEGMENT_TIMING"`; `HOLD` and `INVALIDATE` return nonzero.

## Exact CI truth

GitHub Actions run `34222401430` is completed with conclusion `success` at exact head `bb60c3f144c722c8aadd2a0608d0c1585db96e57`.

Every evidence-lane stage passed:

1. exact source checkout;
2. exact evidence/falsifier binding;
3. Python/test environment provisioning;
4. reachability + matrix contract;
5. synthetic proof of the frozen decision law;
6. frozen lazy-segment timing falsifier;
7. exact-head artifact preservation.

Therefore, under the frozen executable decision law, the authoritative verdict is:

> **`ADVANCE_LAZY_SEGMENT_TIMING`**

This permits the following bounded statements even without copying numeric medians out of the retained JSON artifact:

- semantic gates passed;
- all three admitted 1 MiB rows stayed within `1.05x` eager on both median wall and CPU and retained equal required arena capacity;
- both rejected 1 MiB rows improved to at most `0.95x` eager on both median wall and CPU;
- both rejected rows allocated zero lazy Segment-arena capacity;
- the complete five-row matrix was present.

No more precise timing ratio is asserted by this receipt unless recovered directly from the retained JSON.

## Interpretation

Lazy allocation is now supported by two independent operational dimensions:

1. the preceding fresh-process resource experiment showed that avoiding the eager 1 MiB Segment arena on rejected roots removes roughly 12.58 MB of modeled allocation and reduced reject-path peak RSS by about 26%; and
2. this exact-head timing gate proves that the same scheduling change also clears the preregistered speed requirement on rejected roots without materially regressing admitted roots.

This is unusually attractive because the gain does not require a new Law primitive, Surprise encoding, reader opcode, cache, or format branch. The writer simply avoids paying for a large segmentation workspace until relation admission proves segmentation will actually run.

## Hostile review / claim boundary

Do **not** inflate this into a complete ingest-speed claim.

The paired interval excludes source/target ctypes conversion, native compilation, and root-digest preparation. It charges relation admission, conditional Segment allocation, segmentation, bounded Program construction, validation, and canonical emission. Decode is used for semantic verification outside timing.

The result therefore promotes **segment-arena scheduling inside the current native research-writer envelope**. It does not prove:

- full archive ingest throughput;
- product/native writer authority;
- new stored-byte gains;
- reader-speed gains;
- authenticated selective access;
- recovery/portability authority;
- v0.29 or v0.30 superiority.

The exact numeric row medians remain in artifact `10054407943`; this receipt intentionally does not invent numbers that were not independently recovered during handoff.

## Decision

**Promote lazy Segment-arena allocation as the preferred research-writer scheduling policy.**

Reopening eager allocation as the preferred shape requires new causal evidence showing that early reservation improves a broader charged writer envelope enough to overcome the proven reject-path CPU/wall and memory cost.

## Next decisive experiment

Transfer the promoted scheduling rule into a broader charged creation envelope that includes source conversion and current-root authentication, preserves the same direct final-buffer canonical emission and validation semantics, and measures wall, CPU and peak RSS across tiny, ordinary and 1 MiB roots.

The purpose is not to re-prove the allocator micro-effect. It is to determine how much of the local win survives once the currently unavoidable ingest costs are charged, while ensuring low-opportunity/rejected data retains the memory advantage.
