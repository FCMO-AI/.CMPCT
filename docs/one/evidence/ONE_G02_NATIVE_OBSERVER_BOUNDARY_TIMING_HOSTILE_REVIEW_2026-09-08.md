# ONE-G0.2 native observer boundary timing hostile review

Date: 2026-09-08
Scope: `research/cmpct1`, ONE-G0.2

## Mission lock

The native-observer boundary-cost falsifier exists to decide whether the repeated whole-writer `native_observe` ownership is primarily the C kernel or material Python/binding overhead. That decision is allowed to redirect implementation work, so the paired timer and isolated component timers must not transfer object-lifecycle work between candidates or samples.

## Hostile-review finding A — full result teardown leaked into kernel timing

The first implementation reused one Python local, `result`, across alternating `full_wrapper` and `kernel_preallocated_zero_copy` samples.

On a `full -> kernel` ordering, the full wrapper returned a Python `Observation` into `result`. During the following kernel timed interval the statement `result = None` decref'd that previous `Observation`. Its tuple/object teardown could therefore be charged to the kernel interval even though it is not C-kernel work.

This contamination is directionally dangerous: it can inflate `kernel/full_wrapper` and make the C kernel look closer to the frozen >=0.90 dominance threshold than it really is.

Commit `bed69f1b664afa6ba94e7c7696a230b6f95dce92` separated the two decision-bearing timed branches. The public-wrapper result is validated and explicitly released only after its own timer has stopped; the kernel interval no longer assigns over or destroys a Python `Observation`.

## Hostile-review finding B — isolated component teardown leaked into the next sample

The generic `_median_timing()` helper also assigned each newly returned component object directly over the previous result while its timer was live. For `marshal_only`, that could charge destruction of the prior Python `Observation` to the next marshalling sample. The same pattern affected the allocation/copy component timers.

That does not alter the decision-bearing kernel/full-wrapper ratio after finding A was repaired, but it can distort the descriptive attribution used to choose the *next* falsifier after a `BOUNDARY_COST_MATERIAL` result.

Commit `f675db967f1ee7c80660ea604950ae75c392161d` now retains each newly constructed object through timer stop and transfers ownership afterward. Component timers therefore measure the preregistered construction/work operation rather than teardown of a previous sample.

## Frozen scientific contract

Neither repair changes the preregistered matrix, the five input families, 256 KiB / 1 MiB sizes, 15 repetitions, semantic/stat parity gates, component definitions, or the 0.90 wall+CPU kernel-dominance threshold.

## Evidence rule

Any native-observer boundary-cost decision produced from source before `f675db967f1ee7c80660ea604950ae75c392161d` is non-authoritative for directing implementation work, even if its workflow is green. Preserve it only as diagnostic history.

A post-repair exact-source run must bind `EVIDENCE_HEAD`, pass semantic/stat parity, and retain the JSON artifact before this experiment may redirect speed work.

## Claim boundary

These corrections change experimental attribution only. They change no ONE representation semantics, stored bytes, reader grammar, locality, recovery, comparator setting, or release authority.
