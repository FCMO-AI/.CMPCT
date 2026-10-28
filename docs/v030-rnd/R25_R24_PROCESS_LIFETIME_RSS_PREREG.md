# r25 Shifted r24 process-lifetime RSS preregistration

Status: **FROZEN BEFORE RESULT-BEARING EXECUTION / DIAGNOSTIC ONLY / NO RELEASE CREDIT**

## Causal predecessor

`docs/v030-rnd/R25_PG_ISOLATED_R24_PREBUILD_BARRIER_RSS_RESULT.md` retired a simple r24-prebuild barrier: finishing genuine r24 before the remaining Shifted candidate path recovered only 0.72237% of whole-product high-water. That result does not distinguish logically finished r24 work from allocator/Python pages retained because the r24 builder lived in the same long-lived process.

Earlier evidence has already retired profile capture, isolated exact G0-G4/PrefixGraph ownership, inner candidate serialization, outer scheduling as the primary owner, generic post-candidate GC/allocator trimming, G0-G4 process isolation and the r24-prebuild barrier. This experiment therefore tests a narrower ownership question; it is not another search over scheduler parameters.

## Question

On the exact repaired Shifted workload, does **terminating the genuine-r24 builder process before r25 construction begins** remove a material live-memory class that same-process serialization cannot release, while preserving the exact canonical selected product?

## Frozen arms

Every arm starts in a fresh Python process and uses the exact canonical semantic owners and accepted repaired Shifted source identity.

1. `inherited`: unchanged canonical product construction, including inherited outer r24/r25 overlap.
2. `same-parent-serialized`: the exact canonical r24 build completes first and the exact canonical r25 build then runs in the same parent process. This is the causal control for scheduling without process-lifetime release.
3. `r24-child-serialized`: the exact canonical r24 builder runs in a child process, writes the same candidate artifact and returns its original stats; that child must exit before the exact canonical r25 build starts in the parent. No representation or selection rule changes.

The child-process boundary is diagnostic. It receives no product or release credit merely for reducing the parent high-water.

## Decisive measurement

The authoritative memory metric is **whole process-tree resident RSS sampled at <=10 ms intervals**. Parent `ru_maxrss` and child `ru_maxrss` are diagnostic only. This prevents a subprocess boundary from hiding memory rather than removing system-level overlap.

Two repetitions are required. Arm order is forward then reversed. Every row must have >=100 tree samples and no sampler errors.

All six outputs must be identical in:

- selected representation;
- complete archive bytes and SHA-256;
- canonical user-tree SHA-256;
- format revision;
- genuine-r24 complete bytes;
- r25 complete bytes.

The exact selected product must remain strongly verified. PrefixGraph/G0-G4/reader semantic-owner identity must match the promoted private canonical graph.

## Frozen interpretation

Let:

- `I` = median whole-tree peak RSS of inherited;
- `S` = median whole-tree peak RSS of same-parent serialization;
- `C` = median whole-tree peak RSS of r24-child serialization;
- `total = 1 - C/I`;
- `lifetime = 1 - C/S`.

Decision bands are frozen as:

- `R24_PROCESS_LIFETIME_SUPPORTED` only when `total >= 20%` **and** `lifetime >= 10%`;
- `R24_PROCESS_LIFETIME_RETIRED_AS_PRIMARY` when `total < 10%` **or** `lifetime < 5%`;
- otherwise `R24_PROCESS_LIFETIME_AMBIGUOUS`.

Wall time is always reported. A memory-positive result with large wall debt still requires a separate productization decision and cannot weaken the release runtime gate.

## Claim boundary

This test may support or retire one narrow explanation: memory retained solely because genuine-r24 construction shares a process lifetime with later r25 construction. It does not prove which allocator, Python object, codec buffer or r25 structure owns any remaining peak. It changes no archive grammar, candidate bytes, selector, locality/decode-unit ceiling, recovery/integrity rule, benchmark threshold or production source.

If supported, the next prerequisite is a portable productization design that pays process-launch/runtime/platform carrying cost and re-earns exact runtime, native and Android authority. If retired, stop pursuing r24 lifetime/process isolation and move to live allocation ownership inside the r25 parent path.
