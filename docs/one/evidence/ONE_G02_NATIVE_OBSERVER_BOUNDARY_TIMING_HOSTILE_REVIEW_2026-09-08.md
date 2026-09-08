# ONE-G0.2 native observer boundary timing hostile review

Date: 2026-09-08
Scope: `research/cmpct1`, ONE-G0.2

## Mission lock

The native-observer boundary-cost falsifier exists to decide whether the repeated whole-writer `native_observe` ownership is primarily the C kernel or material Python/binding overhead. That decision is allowed to redirect implementation work, so the paired timer itself must not transfer work between candidates.

## Hostile-review finding

The first implementation reused one Python local, `result`, across alternating `full_wrapper` and `kernel_preallocated_zero_copy` samples.

On a `full -> kernel` ordering, the full wrapper returned a Python `Observation` into `result`. During the following kernel timed interval the statement `result = None` decref'd that previous `Observation`. Its tuple/object teardown could therefore be charged to the kernel interval even though it is not C-kernel work.

This contamination is directionally dangerous: it can inflate `kernel/full_wrapper` and make the C kernel look closer to the frozen >=0.90 dominance threshold than it really is.

## Repair

Commit `bed69f1b664afa6ba94e7c7696a230b6f95dce92` separates the two timed branches. The public-wrapper result is validated and explicitly released only after its own timer has stopped; the kernel interval no longer assigns over or destroys a Python `Observation`.

The preregistered matrix, 15 repetitions, semantic gates, component definitions, and 0.90 wall+CPU dominance threshold are unchanged.

## Evidence rule

Any native-observer boundary-cost result produced from source before `bed69f1b664afa6ba94e7c7696a230b6f95dce92` is non-authoritative for the `KERNEL_DOMINATES_NATIVE_OBSERVER` versus `BOUNDARY_COST_MATERIAL` decision, even if its workflow is green. Preserve it only as diagnostic history.

A post-repair exact-source run must bind `EVIDENCE_HEAD`, pass semantic parity, and retain the JSON artifact before this experiment may redirect speed work.

## Claim boundary

This correction changes experimental attribution only. It changes no ONE representation semantics, stored bytes, reader grammar, locality, recovery, comparator setting, or release authority.
