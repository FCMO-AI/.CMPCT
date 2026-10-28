Machine-readable status lives in `docs/V030_CONVERGENCE_STATUS.json`. That file is a point-in-time custody record; the live authoritative head must always be recovered from PR #56 before work or evidence is credited.

Current convergence state: `agent/v030-authoritative-integration` is the **only active v0.30 engineering line** and remains an integration candidate, not release authority. Production remains **v0.29.0 / format revision 24**. The authoritative line is reconciled to current `main` ancestry; do not reuse an old ahead/behind count from this prose as evidence because the long-lived branch advances continuously.

The previous task-slot/branch scheduler and temporary Agent-00 validation machinery have been removed. T00–T04 are one dependency graph owned end to end by the same executor; CI is evidence infrastructure only.

The accepted repaired v0.29 aggregate identity is **137,499,525 B**. The inherited absolute v0.30 saving hurdle remains **687,783 B**, with at least **3** improved workloads, **0** inherited byte regressions and **<=8x** selected r25 member decoded-context amplification. Canonical r25 must additionally be strictly smaller than genuine r24 for the same original filesystem tree; exact ties keep r24.

The current provisional r25 productization line includes content-agnostic implicit-v4 filesystem-control admission behind the canonical selector. Builder-independent explicit-filesystem and implicit-v4 G04/PrefixGraph vectors are custody boundaries, not generated snapshots of the product writer. The canonical authority must reject drift in those independent vectors before any r25 result is credited.

PR #56 is open for exact-head validation. A green workflow wrapper whose substantive jobs were skipped is only a classifier result. Running, queued, stale-head or classifier-only jobs are diagnostic until the exact candidate has durable receipts from the jobs that actually executed the frozen product, runtime, competitor, recovery, native and platform contracts.

Merge, tag and public v0.30 claims remain locked until the complete runtime/native/portability/recovery/competitor/site matrix is durable on one frozen candidate and `python -m experiments.entropygraph_v030_release_lock_strict` reports `UNLOCKED`.
