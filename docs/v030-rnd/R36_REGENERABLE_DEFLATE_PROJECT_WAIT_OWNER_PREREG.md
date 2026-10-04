# R36 — Regenerable-Deflate Project Wait-Owner Attribution Preregistration

Status: **FROZEN BEFORE RESULT-BEARING EXECUTION**

Parent evidence: terminal R35 `LOCK_CALLER_LOCALIZED`, preserved in `R35_REGENERABLE_DEFLATE_LOCK_CALLER_ATTRIBUTION_RESULT.md`.

## Forge question

R35 localized the residual synchronization debt to `threading.Condition.wait`, but that standard-library sink is not a lawful product mutation site. Which **CMPCT-owned Python frame** is on-stack while the excess Condition waits occur, and does the same project frame own transferable positive excess on both the full Incremental Backups target and the isolated `snapshot_2.zip` projection?

This is an R0 attribution experiment. It may authorize a later lowest-sufficient Builder only if it identifies a bounded project-owned scheduling boundary. It grants no product or release credit itself.

## Frozen substrate

R36 inherits the exact R35 scientific substrate and must bind before execution:

- R32 product/corpus/arm substrate: `0b1f3cd653f0e2489964b93cdd19fa8324adda2e`;
- accepted R34 result: `7c1bbaf272ac286180c6876d996c18d3d04b9748`;
- terminal R35 result and immutable artifact identity;
- targets: full `06_incremental_backups` and isolated `snapshot_2.zip`;
- arms: `release-all-exact`, `full-search`, `no-ordinary-zstd`;
- repetitions: three fresh processes per arm per target;
- same exact strong-verification and deterministic same-run archive identity law as R35.

No corpus, comparator, codec policy, locality law, runtime materiality threshold, or archive representation may change in this diagnostic.

## Instrument

During each fresh-process R32 arm build, temporarily wrap `threading.Condition.wait` only for the measured build call. For each invocation:

1. capture the Python stack immediately before entering the original `Condition.wait`;
2. call the original method unchanged with the same arguments;
3. measure elapsed wall time around that original call;
4. attribute the elapsed wait to the **nearest repository-owned production frame** in the captured stack.

Repository-owned production frames are files under the repository root excluding:

- `benchmarks/**`;
- `tests/**`;
- `docs/**`;
- `.github/**`;
- the R36 diagnostic itself.

A frame signature is normalized as `<repo-relative-path>:<function>`. Line numbers are retained as supporting evidence but are not part of the identity, so harmless source-line drift cannot split one semantic owner.

If no eligible repository production frame exists for a wait, attribute it to `<no-project-frame>`; such waits cannot authorize a product mutation.

The wrapper must be restored in `finally` even on build failure.

## Frozen measurements

For every arm/target/repetition record:

- complete archive bytes and SHA-256;
- strong verification and product-tree identity;
- total build wall time;
- total Condition.wait call count and elapsed wait time;
- per-project-frame wait call count and elapsed wait time;
- representative retained line numbers for each normalized frame.

For each project-frame signature, compute medians across the three fresh processes, then candidate-minus-release deltas for `no-ordinary-zstd` vs `release-all-exact` separately on both targets.

## Identity / validity law

R36 is interpretable only if all of the following hold:

1. every repetition strongly verifies the exact product tree;
2. each arm is deterministic within this run;
3. `full-search` and `no-ordinary-zstd` are byte-identical on each target;
4. the candidate remains strictly smaller than release on each target;
5. wait instrumentation is present and restored cleanly;
6. at least one Condition wait is observed in every measured arm.

Violation of 1–4 yields `SUBSTRATE_OR_SAME_RUN_IDENTITY_FAILURE`. Violation of 5–6 yields `WAIT_INSTRUMENTATION_UNRESOLVED`.

## Frozen localization law

A project frame is a transferable localized owner only when the same normalized signature has:

- isolated `snapshot_2.zip` candidate-minus-release median attributed wait-time delta **>= 0.010 s**; and
- full Incremental Backups candidate-minus-release median attributed wait-time delta **> 0 s**.

The 10 ms nested floor is inherited from R35. No post-result threshold adjustment is allowed.

## Terminal grammar

Exactly one terminal decision is emitted:

1. **`PROJECT_WAIT_OWNER_LOCALIZED`** — at least one eligible project-owned frame satisfies the frozen cross-target localization law;
2. **`PROJECT_WAIT_OWNER_DISTRIBUTED_OR_BELOW_FLOOR`** — instrumentation and identity are valid, but no project frame satisfies the law;
3. **`PROJECT_WAIT_OWNER_UNRESOLVED`** — the qualifying wait excess is attributable only to `<no-project-frame>` or cannot be mapped to a production frame despite valid instrumentation;
4. **`WAIT_INSTRUMENTATION_UNRESOLVED`** — wrapper/restoration/observation law fails;
5. **`SUBSTRATE_OR_SAME_RUN_IDENTITY_FAILURE`** — byte/tree/determinism law fails.

## Interpretation / next action

- `PROJECT_WAIT_OWNER_LOCALIZED`: freeze a lowest-sufficient Builder that modifies only the identified CMPCT scheduling boundary and requires exact byte identity to the byte-winning control, strong verification, locality, RSS, and no material runtime regression on both protected targets before any broader transfer test.
- `PROJECT_WAIT_OWNER_DISTRIBUTED_OR_BELOW_FLOOR`: retire single-owner scheduling surgery under this instrumentation; return to R0/R1 attribution or test a clearly distinct causal hypothesis.
- `PROJECT_WAIT_OWNER_UNRESOLVED`: do not edit generic threading/executor internals; improve attribution at the project/runtime boundary.
- instrumentation/identity failure: repair Custody or supersede the freeze without changing this historical grammar.

Generic worker-count sweeps, arbitrary executor replacement, standard-library threading edits, filename/workload dispatch, or threshold relaxation remain forbidden.

## Strongest preregistered self-critique

Wrapping `Condition.wait` perturbs the measured synchronization path and stack capture adds overhead. Therefore absolute build time in R36 is diagnostic only. The transferable claim is relative **wait attribution** under identical instrumentation across arms in fresh processes, plus exact same-run byte identity. Any later Builder must rerun uninstrumented runtime measurements under the existing material-regression law before receiving product credit.
