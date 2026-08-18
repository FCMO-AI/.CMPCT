Machine-readable status lives in `docs/V030_CONVERGENCE_STATUS.json`.

Current convergence state: this branch remains an integration candidate, not release authority. At the 2026-08-18 hourly check it is **145 commits ahead and 0 commits behind canonical `main`**, with merge-base exactly equal to current `main` (`72e7e6313ffa896b7ef7a14a2f48495754b494f2`). Production remains **v0.29.0 / format revision 24**.

The earlier CI-admission failure is also resolved on the reconciled head. The first page exposes **26 PR-triggered workflow runs**. Authoritative PR-gate run `32105135629` has live jobs: reader/fuzz and the G0-G4 oracle are in progress, while runtime, 15-workload generalization and shared-build rehabilitation are queued. Native-core and external-competitor workflows have also instantiated on the same integration head. Historical green mechanism evidence still does not substitute for these current-head runs.

The frozen v0.30 promotion floor remains unchanged: at least **687,783 B aggregate saving**, at least **3 improved workloads**, **0 regressions**, and **<=8x selected per-member decoded-context amplification**, plus byte-identical shared-build rehabilitation and the runtime/native/portability/external-competitor gates. No threshold may be lowered because a current-head gate is inconvenient.

Merge remains locked until the fresh authoritative matrix completes on this reconciled head and release-level measurements are committed as durable repository evidence. A queued or running workflow is progress toward evidence, not evidence by itself.
