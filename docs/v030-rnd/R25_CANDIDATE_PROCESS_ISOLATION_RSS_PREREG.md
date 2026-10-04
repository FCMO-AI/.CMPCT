# r25 PrefixGraph process-isolation RSS A/B — frozen Forge preregistration

Status: **FROZEN BEFORE RESULT-BEARING EXECUTION / Forge R2 diagnostic / no release credit**.

## Causal predecessor

The exact candidate-reclaim experiment at `5f2633c016304f4743359fb841727c10c85628b6` returned `GENERIC_RECLAIM_RETIRED_AS_PRIMARY`: `gc.collect()` changed neither live RSS nor complete-process peak, while `gc.collect()+malloc_trim(0)` returned a median **153,996 KiB** of live RSS after PrefixGraph completion but still reduced complete-process `ru_maxrss` by **0%**. The same-process serialized scheduler had already failed to lower peak RSS.

This establishes a narrower execution-architecture question. Generic reclamation inside the same process cannot reset all candidate-era lifetime/allocator state before the later candidate work recreates the high-water. Process lifetime is a stronger reclamation boundary, but it may not receive false credit by merely moving memory into an uncharged child process.

## Frozen question

On deterministic `resemblance_hostile_v1 / 01_shifted_versions`, can running the exact canonical PrefixGraph candidate to completion in a disposable subprocess **before** exact canonical G0-G4 construction materially reduce the **whole process-tree peak RSS** while preserving the exact selected product bytes/tree and exposing the wall-time debt?

This is an R2 execution-architecture diagnostic. It does not change production scheduling or claim release credit.

## Arms

1. **shipping-control** — unmodified promoted product build, including inherited concurrent PrefixGraph/G0-G4 candidate construction.
2. **isolated-serialized-pg** — intercept only the canonical-final executor construction whose `thread_name_prefix == "cmpct-v030-prefixgraph"`. Its one PrefixGraph submission is executed synchronously in a fresh Python subprocess using the exact canonical semantic owner. The subprocess must exit before the caller continues into G0-G4. Every non-PrefixGraph executor is delegated unchanged.

The isolated arm deliberately uses process exit, not `malloc_trim`, as the lifetime boundary. It is expected to pay extra wall time because candidate overlap is removed; that debt remains visible.

## Honest memory boundary

Parent-only `ru_maxrss` is **diagnostic only** for this experiment because subprocess isolation could otherwise manufacture an apparent win by moving allocations into a child.

The decisive metric is sampled **whole-process-tree live RSS**:

`parent VmRSS + VmRSS of every transitive descendant currently alive`

A sampler in the fresh worker must track the parent and all descendants throughout the measured build at <=10 ms intervals. This includes the isolated PrefixGraph child and any canonical G0-G4 process-pool workers. Every valid repetition must collect >=100 samples and report no sampler errors.

The sampler may use Linux `/proc` because this experiment is diagnostic only. A production intervention would still require a portable implementation and the ordinary release memory authority.

## Frozen identity and intervention proof

Every valid row must prove:

- exact semantic owners: `canonical.RC.PG is PROFILE_ISOLATION.PG`, `canonical.RC.G04 is PROFILE_ISOLATION.SHARED`, and exact release reader owner;
- strong final verification against the canonical filesystem user-tree identity;
- same final selected representation across arms;
- paired complete archive bytes, physical SHA-256, verified tree, format revision, r24 price and r25 price are identical;
- isolated arm intercepts exactly one PrefixGraph executor construction and one submission;
- isolated arm launches exactly one child PrefixGraph build, receives successful child stats and observes child process exit before returning the future;
- non-PrefixGraph executor constructions are delegated unchanged;
- shipping-control performs no routing intervention.

A mismatch invalidates the experiment; it does not become a performance loss or win.

## Workload, repetitions and order

- deterministic shifted-version corpus generated once by the parent oracle;
- two fresh-process repetitions per arm;
- alternating order: control -> isolated, then isolated -> control;
- same runner and dependency setup;
- whole-process-tree sampled peak RSS is decisive;
- parent `ru_maxrss`, wall time, sample count and candidate stats are retained as diagnostics/debt.

## Frozen decision bands

Let `tree_peak_reduction = 1 - isolated_tree_peak / control_tree_peak` using medians.

- **>=20%**: `PROCESS_LIFETIME_BOUNDARY_SUPPORTED` — process lifetime materially removes the candidate-overlap/lifetime RSS debt. This supports a production-design follow-up, not promotion.
- **<10%**: `PROCESS_ISOLATION_RETIRED_AS_PRIMARY` — even an honest process-lifetime boundary cannot remove enough whole-system memory to explain/fix the Shifted peak.
- **10–20%**: `PROCESS_ISOLATION_AMBIGUOUS` — preserve the evidence; do not change production scheduling without narrower evidence.

Wall time does not alter the causal classification, but it is mandatory debt. A supported memory result whose isolated median wall time exceeds control by >15% is explicitly `SUPPORTED_WITH_MAJOR_CREATE_DEBT` and cannot be promoted without a second rehabilitation step.

## Invariants

No archive grammar, representation, candidate eligibility, winner selection, locality/decode-unit limit, verification/integrity rule, recovery guarantee, corpus, competitor, benchmark threshold or release fingerprint may be weakened. The experiment grants **no release credit**.

## Hostile-review boundary

A parent-only RSS improvement is not evidence. A result is useful only if the sum of parent and descendant live RSS falls materially. Likewise, process exit may lower steady-state residency after PrefixGraph, but if the process-tree peak still occurs while the child is alive or later G0-G4 reaches a similar system peak, the hypothesis loses.

## Next decision

If supported, the next Builder step is not immediately “ship subprocesses.” First quantify portability/startup/create-time carrying cost and test the same mechanism on ML where PrefixGraph is ineligible; a Shifted-only process architecture may be too expensive globally. If retired, stop scheduler/reclaim permutations and return to candidate-internal allocation/representation work, guided by exact phase ownership.

This preregistration, its worker/oracle and workflow become immutable once substantive result-bearing execution begins. Any material correction requires a superseding freeze preserving this evidence surface.
