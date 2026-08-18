Machine-readable status lives in `docs/V030_CONVERGENCE_STATUS.json`.

Current convergence warning: this branch is an integration candidate, not release authority. At the 2026-08-18 hourly check it was **120 commits ahead and 35 commits behind canonical `main`**, with merge-base `8e26ad6cd5001c2ea88f0c548dc7d0e0670a4cd1`. Production is **v0.29.0 / format revision 24**. The observed integration head had **0 PR-triggered workflow runs**, so green historical v0.30 mechanism evidence is not current release evidence. This status refresh deliberately touches the authoritative PR-gate path to force a fresh validation attempt on the current head.

The frozen v0.30 promotion floor remains unchanged: at least **687,783 B aggregate saving**, at least **3 improved workloads**, **0 regressions**, and **<=8x selected per-member decoded-context amplification**, plus byte-identical shared-build rehabilitation and the runtime/native/portability/external-competitor gates. No threshold may be lowered to accommodate reconciliation.

Merge remains locked until the 35 canonical-main commits are reconciled and the complete authoritative matrix reruns on the reconciled head. A workflow badge without an instantiated job is infrastructure state, not benchmark evidence.
