# r25 outer product-scheduling RSS preregistration

Status: **FROZEN BEFORE RESULT-BEARING EXECUTION / FORGE DIAGNOSTIC / NO RELEASE CREDIT**

This preregistration follows the accepted negative result in
`docs/v030-rnd/R25_CANDIDATE_SCHEDULING_RSS_V3_RESULT.md`. V3 retired the inner shipping
G0-G4-vs-PrefixGraph concurrency as the primary Shifted RSS explanation. This experiment moves exactly
one causal boundary outward and must not be edited after any result-bearing execution. A material
change to the question, intervention seam, corpus, thresholds, identity contract, or interpretation
requires a new superseding freeze while preserving this file and any result.

## Worldview under test

The canonical product builder constructs **genuine r24** and the **complete r25 tournament** concurrently
under its outer `cmpct-v030-product` executor, then prices both complete artifacts and publishes the
smaller one. On Shifted versions the r25 product peak remains much larger than either exact r25 candidate
family in isolation, while serializing the inner G0-G4/PrefixGraph overlap did not reduce that peak.

The next lowest-radicality causal hypothesis is therefore:

> A material part of the Shifted product RSS red is owned by simultaneous lifetime of the complete
> genuine-r24 floor build and the complete r25 tournament, not by the already-retired inner r25
> candidate overlap.

This is a product-lifetime hypothesis, not a representation hypothesis. The experiment grants no
release credit and authorizes no production scheduling change by itself.

## Frozen target and source contract

- suite: `resemblance_hostile_v1`
- workload: `01_shifted_versions`
- corpus generator: the same deterministic source path used by the canonical v0.30 release-performance
  authority;
- source identity: must equal the accepted repaired historical Shifted user-tree authority before any
  measurement;
- repetitions: **2 fresh processes per arm**, with execution order alternating AB / BA;
- decisive memory metric: **total fresh-process `ru_maxrss` peak**, not baseline-subtracted arithmetic;
- wall time is charged and reported for every arm;
- correctness/strong verification occurs after the timing/RSS snapshot so reader allocations cannot
  contaminate construction attribution.

## Frozen arms

### Arm A — inherited outer concurrency

Run the exact shipping product builder unchanged. The outer `cmpct-v030-product` executor concurrently
submits:

1. the genuine canonical r24 complete-artifact build; and
2. the exact complete r25 release-candidate tournament.

The inherited inner r25 G0-G4/PrefixGraph scheduling remains untouched.

### Arm B — outer serialization only

Intercept **only** the `ThreadPoolExecutor` construction whose `thread_name_prefix` is exactly
`cmpct-v030-product`, in the module-global namespace where the shipping `build_archive` function
resolves it. Route its two submissions inline in submission order. Every other executor construction,
including the inner `cmpct-v030-prefixgraph` and G0-G4 executors, must remain the inherited shipping
implementation and scheduling.

The serialized intervention is valid only if all of the following are proven in the worker receipt:

- exactly **one** outer `cmpct-v030-product` executor construction was intercepted;
- exactly **two** outer submissions were executed inline;
- the inherited concurrent arm intercepted zero outer constructions/submissions;
- no inner r25 executor seam was patched;
- the exact canonical product/r24/r25 semantic owners used by shipping are unchanged.

A nominal timing/RSS difference from a worker that cannot prove those intervention facts is invalid
evidence.

## Frozen product-identity contract

Both arms must produce the same selected complete product:

- identical selected representation (`r24` or `r25`);
- identical complete archive byte count;
- identical physical archive SHA-256;
- identical strongly verified canonical filesystem user-tree hash;
- identical source canonical filesystem tree before construction.

The experiment must fail closed on any paired identity mismatch. It may not replace genuine r24 with a
historical size constant, skip either complete build, alter the r25 candidate set, or gift away framing,
verification, recovery, locality, decode-unit, metadata, residual, or control costs.

## Frozen intervention boundaries

This experiment changes **only outer product scheduling**. It changes none of:

- r24 or r25 archive bytes/grammar;
- r25 candidate eligibility, admission, selector, verification, or inner scheduling;
- genuine-r24 semantics;
- integrity/authentication/recovery behavior;
- locality or decode-unit ceilings;
- release benchmark/runtime/RSS thresholds;
- competitor settings or corpus identity;
- publication/version/merge state.

The worker/oracle and workflow are diagnostic instruments. `release_credit` must remain `false`.

## Frozen decision rule

Let `C` be median total fresh-process peak RSS of inherited outer concurrency and `S` the corresponding
median for outer serialization. Define `reduction = (C - S) / C`.

- **reduction >= 20%**: supports outer r24-vs-r25 lifetime overlap as a material RSS owner. Advance to a
  Builder/productization design that removes that exported lifetime debt while preserving complete
  r24-vs-r25 pricing and exact output semantics. The Builder still must pass the unchanged full runtime,
  RSS, size, correctness and platform gates; this result alone is not permission to ship serialization.
- **reduction < 10%**: retire outer r24-vs-r25 concurrency as the primary explanation for the tested
  Shifted RSS red. Move one causal layer deeper into retained common/product state and temporary-output
  ownership rather than retuning either scheduling seam.
- **10% <= reduction < 20%**: ambiguous. Do not change production scheduling. Freeze a narrower
  ownership instrument before a Builder intervention.

Wall-time change is always reported and remains real carrying cost. A memory win cannot hide a runtime
loss. The thresholds above are causal decision boundaries only and do not replace the stricter release
performance/RSS gates.

## Negative-evidence law

If this hypothesis loses, preserve the tested regime, exact intervention proof, measured ratios, causal
interpretation and reopening predicate as a scoped negative result. Do not convert a Shifted-specific
loss into universal dogma, and do not rerun the same scheduling family without new causal evidence.

## Next action after freeze

Implement the smallest fail-closed fresh-process worker/oracle and split-classifier/exact-SHA receipt
workflow needed to execute these two frozen arms. The instrument must be able to prove that it patched
the outer product executor in the actual `build_archive` resolution domain; V2 of the inner scheduling
experiment is preserved as the warning that patching a nearby namespace is not causal evidence.
