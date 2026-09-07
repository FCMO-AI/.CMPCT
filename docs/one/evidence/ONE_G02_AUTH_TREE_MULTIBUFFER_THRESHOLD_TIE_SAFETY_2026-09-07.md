# ONE-G0.2 — auth-tree multi-buffer crossover threshold tie safety

Date: 2026-09-07
Branch: `research/cmpct1`
Result-bearing code head before this receipt: `8a67e64efb0facf32a2c93ad8801545b1a9bbf47`
Experimental version: `ONE-G0.2`

## Mission lock

The resource-crossover experiment learns a deployment rule of the form `node_count >= T -> use multi-buffer SHA`. The learner must therefore evaluate exactly the population that such a threshold would dispatch.

Hypothesis under review: sorting observations by `node_count` and scanning suffixes is sufficient to learn a safe threshold.

Disproof condition: construct two observations with the same `node_count` where one exceeds the wall-time gate and the later one passes; if the learner can start a suffix at the later tied row and still return that shared node count, the learned rule is unsound because deployment would route both observations.

## Hostile-review finding

The previous implementation could start a candidate suffix at any row index after sorting. With duplicate node counts, that allowed a suffix to begin in the middle of an equivalence class. A bad first `node_count=N` observation could therefore be excluded from the learned suffix while the returned deployment rule remained `node_count >= N`, which would include that bad observation in production.

This is a fail-open evidence-selection bug, not a timing optimization result.

## Repair

`_learn_threshold` now considers candidate starts only at the first row of each distinct node-count class. Therefore every observation that would satisfy the eventual dispatch predicate is included in the qualifying suffix.

A hostile unit test pins the counterexample:

- node 10: baseline-losing control;
- node 20 row A: `1.01x` wall (must block threshold 20);
- node 20 row B: `0.89x` wall;
- node 30: `0.87x` wall.

The only safe learned threshold is 30. A local logic check of the patched selector returns 30.

## Scope / costs

This repair changes no archive bytes, reader semantics, SHA authenticated bytes, tree geometry, workspace, selective access, or decoder behavior. It only prevents an unsafe writer-side performance dispatch threshold from being inferred from contradictory equal-coordinate observations.

## Evidence truth

The exact hosted `CMPCT1 ONE-G0.2 auth-tree multi-buffer resource crossover` workflow for head `8a67e64efb0facf32a2c93ad8801545b1a9bbf47` was created as run `34104619534` and was still queued when this receipt was written. No native crossover speed/CPU result is claimed here.

The earlier `auth-tree multi-buffer SHA A/B` run associated with the preceding head completed with overall workflow success but its result-bearing `multibuffer-sha` job was skipped by the latest-commit classifier; it therefore supplied no performance authority.

## Next decisive action

Consume the exact-head resource-crossover artifact when run `34104619534` finishes. Promote a node-count dispatch principle only if the preregistered discovery, CPU, workspace and independent holdout gates all pass. Otherwise preserve the loss and move to a causally different batching/workspace strategy rather than weakening the threshold.
