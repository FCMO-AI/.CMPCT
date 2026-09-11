# ONE-G0.2 authenticated-tree resource evidence: exact-head CI preservation

## Mission lock / Referee

The multi-buffer authentication resource-crossover experiment is result-bearing scientific evidence. A completed result must remain bound to one immutable source head. A later documentation or handoff commit must not be able to cancel the older exact-head experiment before its artifact exists.

This receipt records an execution-infrastructure defect and its repair. It changes no ONE representation semantics, authentication bytes, benchmark thresholds, comparator settings, or promotion claim.

## Observed failure

The previously expected resource-crossover run `34104619534` did not execute the frozen benchmark to completion. GitHub records the run as cancelled after approximately one minute. The workflow used a concurrency group scoped to the pull request rather than the immutable result-bearing head, so a later head could cancel an already-started scientific run.

That cancellation is not a scientific FAIL or PASS. It is missing evidence.

## Repair

Commit `502e2e75a0d78ab4d164c3b73188ab804caf17f3` changes only the workflow concurrency identity for:

`.github/workflows/cmpct1-one-g02-auth-tree-multibuffer-resource-crossover.yml`

The group now includes `${{ github.event.pull_request.head.sha || github.sha }}`. Duplicate runs for the same exact head may still cancel each other, but a later branch head cannot intentionally invalidate an already-running older scientific head.

The frozen benchmark and all resource/crossover gates are unchanged.

## Live falsification of the repair

The repair itself triggered exact-head resource run `34109668113` on source head `502e2e75a0d78ab4d164c3b73188ab804caf17f3`.

This receipt is committed *while that run is active*, creating a later branch head. Therefore the strongest immediate disproof of the repair is simple: if run `34109668113` is cancelled merely because this later evidence-only commit exists, the fix is inadequate and must not be relied upon.

If the older run continues independently, the exact-head preservation mechanism has survived this live concurrency test. Its scientific result remains separately governed by the preregistered resource-crossover gates.

## Hostile Reviewer / scope boundary

This is CI evidence-integrity work, not compression performance evidence. It grants no density, speed, CPU, memory, access, portability, or comparator authority. It only prevents one known source of silent evidence loss.

The broader CI fan-out on `research/cmpct1` remains visible debt: a single head can spawn a very large number of workflows, many of which classify and skip. That scheduler pressure is distinct from the exact-head cancellation bug fixed here and should be reduced without weakening required scientific coverage.
