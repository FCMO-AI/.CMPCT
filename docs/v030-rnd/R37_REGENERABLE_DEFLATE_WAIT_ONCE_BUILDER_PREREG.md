# R37 — Regenerable-Deflate Wait-Once Scheduling Builder Preregistration

Status: **FROZEN BEFORE RESULT-BEARING EXECUTION**

Parent authority: terminal R36 `PROJECT_WAIT_OWNER_LOCALIZED`, preserved in `R36_REGENERABLE_DEFLATE_PROJECT_WAIT_OWNER_RESULT.md` from exact evidence head `078b9b11e95a876b7174239e59bc3fa38d168286`.

## Forge question

R36 localized the transferable synchronization excess to the candidate-encoding scheduling boundary in `src/cmpct/builder.py:build`. The current product boundary consumes `ThreadPoolExecutor.map` in deterministic input order, which can repeatedly block on individual future results. Is the lowest-sufficient change to submit the same ordered candidate set, wait once for the bounded batch to complete, and then collect future results in the original order?

This is an R1 Builder test of one bounded CMPCT-owned scheduling boundary. It does not change representation, candidate generation, codec policy, worker count, grammar, corpus, or locality accounting.

## Frozen substrate

R37 inherits unchanged:

- R32 product/corpus/representation substrate and the `release-all-exact` / `no-ordinary-zstd` byte-winning arms;
- the exact full `06_incremental_backups` target and isolated unchanged `snapshot_2.zip` projection used by R34-R36;
- R36's accepted same-run identity and project-owner localization;
- three fresh processes per arm per target;
- public strong verification and operation-derived virtual-member locality.

The result is invalid if the inherited substrate, R36 result, or scheduling-boundary semantics drift before execution.

## Frozen arms

1. **`release-all-exact`** — inherited R32 release control, unchanged scheduling.
2. **`candidate-map-control`** — inherited R32 `no-ordinary-zstd` byte-winning candidate with the current `ThreadPoolExecutor.map` scheduling boundary.
3. **`candidate-wait-once`** — the exact same R32 candidate and worker count, except the one Builder candidate-encoding map call is replaced for the measured build by: submit the same ordered items to the same `ThreadPoolExecutor`; wait once for all submitted futures; collect `Future.result()` in original submission order.

The candidate arm must observe exactly one patched map call. No worker-count sweep, executor replacement, unordered materialization, batching/chunksize search, filename/path/workload dispatch, codec change, representation change, or threshold change is permitted.

## Frozen measurements

For every fresh-process repetition record:

- complete archive bytes and SHA-256;
- build wall time measured without Condition/stack instrumentation;
- peak RSS;
- strong verification and product-tree identity;
- every virtual ZIP/WHL public member-read decoded-context amplification;
- patched-map call count for `candidate-wait-once`.

Compute medians across the three fresh processes for bytes, wall time and RSS. Runtime materiality remains the existing release law: a regression is material only when it exceeds **both 5% relative and 3 ms absolute**. RSS may not exceed the paired control by more than **10%**. Hard locality remains **<=8.0x** for every measured virtual member. Size tolerance is **0 bytes**.

## Frozen identity and promotion law

R37 is interpretable only if every repetition strongly verifies, every arm is deterministic within-run, `candidate-map-control` and `candidate-wait-once` are byte-identical on each target, the candidate remains strictly smaller than `release-all-exact` on each target, all locality data are present, and the wait-once arm observes exactly one patched Builder map call per build.

Exactly one terminal decision is emitted:

1. **`PROMOTE_WAIT_ONCE_SCHEDULING_BOUNDARY`** — identity/locality pass; wait-once is strictly faster than map-control on both targets; nested-only median improvement is **>=0.010 s**; wait-once has no material runtime regression versus `release-all-exact` on either target; and wait-once RSS is <=110% of map-control on both targets.
2. **`WAIT_ONCE_INSUFFICIENT`** — identity/locality/RSS remain lawful, but the runtime recovery fails any promotion condition without creating a material regression.
3. **`WAIT_ONCE_RUNTIME_OR_RSS_REGRESSION`** — exact bytes/locality pass but wait-once materially regresses runtime versus release on either target or exceeds the 10% RSS ceiling versus map-control.
4. **`WAIT_ONCE_LOCALITY_FAILURE`** — exact bytes pass but any measured virtual member exceeds 8x.
5. **`SUBSTRATE_OR_IDENTITY_FAILURE`** — strong verification, determinism, candidate byte identity, candidate strict byte win, map-call count, or inherited substrate fails.

## Interpretation / next action

- `PROMOTE_WAIT_ONCE_SCHEDULING_BOUNDARY`: productize only the bounded Builder scheduling change (`submit` -> one wait -> ordered result collection), then regenerate exact-head protected/global authority. No representation or worker-policy change is authorized.
- `WAIT_ONCE_INSUFFICIENT`: retire this specific wait-once primitive as insufficient under the tested regime; preserve R36 localization and return to the same boundary with a genuinely distinct causal scheduling hypothesis.
- regression/locality failure: reject the intervention and preserve the byte-winning control.
- substrate failure: repair Custody or supersede the freeze; never rewrite this historical grammar.

## Strongest preregistered self-critique

R36 localized observed waiting to `Builder.build`, but the apparent excess may reflect useful parallel work finishing behind the ordered consumer rather than avoidable scheduler overhead. A single aggregate wait could therefore merely move where blocking occurs, not remove it. R37 demands uninstrumented fresh-process timing and a material nested recovery precisely to distinguish a real scheduling win from relabeled waiting.
