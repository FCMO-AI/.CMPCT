Machine-readable status lives in `docs/V030_CONVERGENCE_STATUS.json`.

Current convergence warning: this branch is an integration candidate, not release authority. At the 2026-08-18 hourly check it was **118 commits ahead and 35 commits behind canonical `main`**, with merge-base `8e26ad6cd5001c2ea88f0c548dc7d0e0670a4cd1`. Production is **v0.29.0 / format revision 24**. Do not interpret green historical v0.30 mechanism evidence as current release evidence until the branch is reconciled with `main` and the complete authoritative gate matrix reruns on the reconciled head.

The frozen v0.30 promotion floor remains unchanged: at least **687,783 B aggregate saving**, at least **3 improved workloads**, **0 regressions**, and **<=8x selected per-member decoded-context amplification**, plus byte-identical shared-build rehabilitation and the runtime/native/portability/external-competitor gates. No threshold may be lowered to accommodate reconciliation.
