# R35 regenerable-Deflate lock-caller attribution preregistration

Status: **FROZEN BEFORE RESULT-BEARING EXECUTION**

R35 is a Forge R0 diagnostic that follows the accepted R34 result. R34 localized the residual R32 create-time debt to `_thread.lock.acquire`, but cProfile's built-in-function row did not identify the Python synchronization owner safe to mutate. R35 changes only the attribution resolution. R32 representation/product semantics and R34 same-run identity law remain unchanged.

## Forge allocation

- strict objective: retain the R32 byte gain while removing its material create-time debt; no ZIP/Zstd-19 or release claim is granted by this diagnostic
- active local red: Full Backups `release-all-exact` 8,088,617 B / 0.538504413 s versus `no-ordinary-zstd` 8,056,197 B / 0.568245724 s in accepted R34; candidate is **32,420 B smaller** but **+29.741311 ms / +5.52295% slower**
- nested transfer control: candidate is **33,746 B smaller** but **+53.505955 ms / +16.04493% slower**
- diagnosis: **D2 execution architecture**, with exact safe mutation point still unresolved
- radicality: **R0 attribution**; R1/R2 mutation is not yet justified
- saturation: no S1-S4 retirement trigger is active; this is breakthrough-debt isolation under the rehabilitation law
- Forge RPS: **85/100** = necessity 12/15, upside 16/20, root-cause fit 14/15, generality 8/10, information gain 14/15, decisive efficiency 9/10, product survival 8/10, simplicity 4/5

The RPS is allocation telemetry, not evidence.

## Frozen question

Which Python caller(s), if any, own the transferable excess `_thread.lock.acquire` time measured by R34 for the regenerable-Deflate candidate?

A useful result must identify an implementation-level caller signature before any product synchronization policy is changed. Generic worker-count tuning, disabling parallelism, changing representation bytes, workload-name dispatch and threshold relaxation are explicitly out of scope.

## Frozen substrate and targets

Reuse without edits the exact R32 product/corpus substrate bound at `0b1f3cd653f0e2489964b93cdd19fa8324adda2e` and the R34 experiment contract:

- targets: frozen Full Backups corpus and isolated `snapshot_2.zip`
- arms: `release-all-exact`, `full-search`, `no-ordinary-zstd`
- repetitions: **3 fresh processes per arm per target**
- strong verification and exact source-tree reconstruction required
- within-run deterministic `(archive_bytes, archive_sha256)` required for every target/arm
- `full-search` and `no-ordinary-zstd` must be byte-identical on each target
- their archive must remain strictly smaller than `release-all-exact`

Failure yields `SUBSTRATE_OR_SAME_RUN_IDENTITY_FAILURE`; caller timing may not be interpreted.

## Frozen profiler/caller law

Use deterministic `cProfile` / `pstats` caller data from the exact built-in signature:

`~:0:<method 'acquire' of '_thread.lock' objects>`

For each fresh process retain the caller map supplied by `pstats.Stats.stats[lock_signature][4]`. Normalize Python caller signatures as `<basename>:<line>:<function>`. For each target/arm, compute per-caller medians across the three repetitions for:

- caller-attributed lock call count;
- caller-attributed lock internal time;
- caller-attributed lock cumulative time.

Use **caller-attributed cumulative time into the lock acquire callee** as the attribution quantity; do not use the caller function's total cumulative time as a substitute.

The instrument must also retain the complete lock-row internal/cumulative time so caller attribution can be checked against the same measured phase R34 localized. Missing/unparseable caller data is not permission to guess an owner.

## Frozen localization threshold

A Python caller is a transferable lock owner only if the same normalized caller signature has:

- nested-only candidate-vs-release median caller-attributed lock-time delta **>= 0.010 s**; and
- Full Backups candidate-vs-release median caller-attributed lock-time delta **> 0 s**.

This intentionally reuses R34's preregistered 10 ms nested transfer floor rather than selecting a new threshold after seeing caller results.

Sort localized callers by descending nested delta.

## Terminal grammar

- `LOCK_CALLER_LOCALIZED` — identity law passes and at least one Python caller clears the frozen transfer threshold
- `LOCK_CALLER_DISTRIBUTED_OR_BELOW_FLOOR` — identity law passes, caller data is usable, but no caller clears the threshold
- `LOCK_CALLER_UNRESOLVED` — identity law passes but the profiler cannot supply a trustworthy Python caller map for the localized lock phase
- `SUBSTRATE_OR_SAME_RUN_IDENTITY_FAILURE` — any source/reconstruction/determinism/output-dead/strict-byte-benefit prerequisite fails

## Interpretation law

`LOCK_CALLER_LOCALIZED` authorizes only the lowest-sufficient Forge mutation at the localized synchronization owner, followed by a fresh Builder that must retain exact bytes/reconstruction/locality and close the existing material runtime regression under the unchanged >5% **and** >3 ms materiality rule.

`LOCK_CALLER_DISTRIBUTED_OR_BELOW_FLOOR` or `LOCK_CALLER_UNRESOLVED` blocks direct lock surgery. A new diagnostic method or higher-level execution-architecture hypothesis is required; generic concurrency tuning is not an allowed rescue.

`SUBSTRATE_OR_SAME_RUN_IDENTITY_FAILURE` blocks all caller interpretation.

No R35 outcome grants product, competitor or release authority.

## Strongest pre-mortem

The strongest alternative explanation is that built-in lock time is a scheduler symptom spread across `concurrent.futures`/`threading` internals, not redundant synchronization owned by one product-level call site. If so, caller attribution should fail the transfer threshold or point only to generic runtime internals. That is a useful falsifier: it prevents an unsafe R1 patch and forces a higher-level R2 scheduling experiment instead.
