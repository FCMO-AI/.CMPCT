# r25 dual-candidate process-isolation RSS A/B — frozen Forge preregistration

Status: **FROZEN BEFORE RESULT-BEARING EXECUTION / Forge R2 diagnostic / no release credit**.

## Causal predecessor

`R25_CANDIDATE_PROCESS_ISOLATION_RSS_V2_RESULT.md` established under valid custody that placing the exact canonical PrefixGraph build behind a disposable process lifetime, waiting for that child to exit, and only then running G0-G4 reduces the honestly charged Shifted whole-process-tree peak from **400,958 KiB to 289,300 KiB (-27.8478%)** while preserving exact final product identity. The isolated arm paid **1.179814x** wall time and therefore carries preregistered major create debt.

This leaves a sharply bounded question: is the remaining ~289 MiB peak primarily G0-G4's own process lifetime / allocator history, such that the same lifetime boundary around G0-G4 removes another material tranche without changing representation bytes?

## Frozen question

On deterministic `resemblance_hostile_v1 / 01_shifted_versions`, after PrefixGraph has already been built in a disposable child and exited, does executing exact canonical G0-G4 in a second disposable child materially lower the **whole live process-tree peak RSS** relative to the accepted PrefixGraph-only isolation architecture, while preserving the exact selected product bytes/tree and exposing all wall-time debt?

This is an R2 diagnostic. It changes no production source and grants no release credit.

## Arms

1. **pg-isolated-control** — reproduce the accepted V2 intervention: exact PrefixGraph runs synchronously in one fresh child, exits, then exact canonical G0-G4 runs in the parent process; canonical selection/publication proceeds unchanged.
2. **dual-isolated** — exact PrefixGraph runs synchronously in one fresh child and exits; exact canonical G0-G4 then runs synchronously in a separate fresh child and exits; the parent retains only returned stats plus the complete candidate artifact files needed by unchanged canonical winner selection/publication.

Both arms run through the same promoted complete-product builder. Only the G0-G4 process-lifetime boundary differs.

## Honest memory boundary

The decisive metric remains sampled **whole-process-tree live RSS**:

`parent VmRSS + VmRSS of every transitive descendant currently alive`

Sample interval must be <=10 ms throughout the measured build, including G0-G4 grandchildren/process-pool workers. Parent-only `ru_maxrss` is diagnostic only. Each valid repetition requires >=100 samples and zero sampler errors.

No process may receive free memory by being excluded from the tree charge.

## Exact identity / intervention proof

Every valid row must prove:

- exact semantic owners for PrefixGraph, G0-G4 and reader policy;
- strong final verification against canonical filesystem user-tree identity;
- identical final selected representation, complete archive bytes, physical SHA-256, verified tree, format revision, r24 complete-product price and r25 complete-product price across all rows;
- both arms intercept exactly one PrefixGraph executor/submission and launch exactly one successful PrefixGraph child that exits before G0-G4 begins;
- `pg-isolated-control` performs no G0-G4 routing and calls the canonical G0-G4 owner in the parent;
- `dual-isolated` launches exactly one G0-G4 child through the exact canonical semantic owner, receives successful stats/archive identity, and observes the child exit before winner selection continues;
- all patched callables/executors are restored after the build;
- no archive grammar, representation, candidate eligibility, winner rule, locality/decode-unit rule, verification/recovery rule, comparator or threshold changes.

Any mismatch invalidates the experiment rather than becoming a win/loss.

## Repetitions and order

- same accepted repaired Shifted source identity;
- two fresh-process repetitions per arm;
- alternating order: pg-isolated-control -> dual-isolated, then dual-isolated -> pg-isolated-control;
- same runner/dependency setup;
- total whole-tree live RSS is decisive;
- parent peak, child peaks/lifetimes, sampler process count and wall time remain diagnostic/debt.

## Frozen decision bands

Let `incremental_reduction = 1 - dual_peak / pg_only_peak` using median whole-tree peaks.

- **>=20%**: `G04_PROCESS_LIFETIME_SUPPORTED` — the remaining V2 peak contains a material G0-G4 process-lifetime component. Advance to rehabilitation/product-architecture evaluation, not promotion.
- **<10%**: `G04_PROCESS_LIFETIME_RETIRED_AS_PRIMARY` — adding another process boundary cannot explain/remove enough of the remaining peak; stop process-boundary proliferation and move inside the remaining phase.
- **10–20%**: `G04_PROCESS_LIFETIME_AMBIGUOUS` — preserve the evidence; no production architecture change.

Wall-time debt is mandatory. If supported and `dual_wall / pg_only_wall > 1.10`, classify `G04_PROCESS_LIFETIME_SUPPORTED_WITH_ADDITIONAL_CREATE_DEBT`; the accepted predecessor already carries major debt, so even a smaller incremental slowdown matters.

## Carrying-cost law

A supported result is not automatically a product design. Two sequential subprocesses add startup, IPC, cancellation/error propagation, temporary-file, Windows/Android/platform and packaging complexity. Any later production proposal must justify those global costs and recover create-time debt without reintroducing the memory overlap. Process isolation is valuable only if it buys a large enough hard-resource benefit to pay that portfolio cost.

## Hostile review boundary

This experiment must not compare parent-only RSS, must not skip G0-G4 because PrefixGraph wins, and must not infer that the selected representation owns all build memory. Both candidates are still fully priced exactly as canonical selection requires. The only question is whether resetting G0-G4's process lifetime changes the whole-system high-water.

## Next decision

If supported, the next Forge step is to determine whether a portable candidate-worker architecture can amortize startup while preserving the measured memory reset, and separately whether ML (G0-G4 only) benefits from the same G0-G4 isolation. If retired, retain PrefixGraph process lifetime as a Shifted-specific positive but stop adding process boundaries; the remaining ~289 MiB then belongs inside G0-G4 or parent publication/verification work and should be instrumented directly.

This preregistration, worker/oracle and workflow become immutable once substantive result-bearing execution starts. Any material correction requires a superseding freeze preserving this evidence.
