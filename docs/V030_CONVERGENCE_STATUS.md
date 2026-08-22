Machine-readable status lives in `docs/V030_CONVERGENCE_STATUS.json`.

Current convergence state: `agent/v030-authoritative-integration` is the **only active v0.30 engineering line** and remains an integration candidate, not release authority. Current `main` ancestry has been reconciled; the observed pre-status-write relation was **382 commits ahead and 0 behind**, with merge-base/current main `11e6497781becab8dc0c92c9af981920b56aa5b1`. Production remains **v0.29.0 / format revision 24**.

The previous task-slot/branch scheduler and temporary Agent-00 validation machinery have been removed. T00–T04 are one dependency graph owned end to end by the same executor; CI is evidence infrastructure only.

The current T03 repair replaces process-global canonical profile mutation with isolated canonical module namespaces backed by the exact existing Geometry/PrefixGraph/reader source files. The reviewed canonical implementation body is preserved in `entropygraph_v030_canonical_final_impl.py`; `entropygraph_v030_canonical_final.py` is now the isolation wrapper, with concurrency/import-order regression coverage in `tests/test_v030_profile_isolation.py`.

PR #56 is open for exact-head diagnostic validation. Running or queued jobs remain diagnostic until final source is frozen and required evidence is committed with the exact release fingerprint.

The frozen promotion floor remains unchanged: historical accepted-v0.29 aggregate **137,501,815 B**, at least **687,783 B** historical saving, at least **3** improved workloads, **0** inherited byte regressions and **<=8x** selected r25 member decoded-context amplification. Canonical r25 must additionally be strictly smaller than genuine r24 for the same original filesystem tree; exact ties keep r24.

Merge, tag and public v0.30 claims remain locked until the complete runtime/native/portability/recovery/competitor/site matrix is durable on one frozen candidate and `python -m experiments.entropygraph_v030_release_lock_strict` reports `UNLOCKED`.
