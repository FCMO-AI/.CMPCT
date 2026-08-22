# T00 — Reconcile authoritative v0.30 with canonical main

- **Owner:** v0.30 sole executor
- **Priority:** P0
- **State:** CLAIMED
- **Branch:** `agent/v030-authoritative-integration`

## Objective

Reconcile every canonical-main commit that postdates the current integration merge-base without losing v0.30 mechanisms, current-main hardening, repository instructions, CI topology, public-surface policy, or benchmark substrate fixes.

## Current status

Canonical main reconciliation completed at integration commit `851b2ec3a4c1134c965302330fd0f908c57f481d` against main `72e7e6313ffa896b7ef7a14a2f48495754b494f2`.

`compare main...agent/v030-authoritative-integration` reported **0 commits behind** at that checkpoint. The merge adopted exact then-current-main blobs for all 35 post-merge-base paths while preserving all non-overlapping v0.30 paths.

Semantic overlap decisions:

- `experiments/entropygraph_v029_parallel_portfolio.py`: current main wins because its fsync-backed durable atomic publication is a strict safety superset of the integration copy while retaining the same byte-selection contract.
- `tests/test_v029_parallel_portfolio.py`: current main wins because it includes the integration assertions plus overwrite/durability regression coverage.
- `benchmarks/history/2026-08-17-mosaic-v029-category.json`: current main wins because it is the same evidence/provenance in canonical compact JSON form.

Since `main` can continue moving during v0.30 completion, this checkpoint is not the final reconciliation receipt. The executor must compare and reconcile again immediately before the final exact-candidate evidence wave.

## Owned paths

Repository-wide when conflict resolution/reconciliation is required. The same v0.30 executor owns all active product paths, so cross-task edits are allowed when they close a release blocker; semantic conflicts must still be resolved explicitly rather than by blind overwrite.

## Must not regress

- frozen v0.30 release thresholds;
- current-main AGENTS/instructions and CI topology;
- durable v0.29 histories and reproducibility repairs;
- imported G0–G4, PrefixGraph, reader/recovery, shared-build and release-gate work;
- public-surface discipline.

## Completion evidence

1. [x] A reconciliation checkpoint reached 0 commits behind current main.
2. [x] All three overlapping paths at that checkpoint received explicit semantic resolution; no blind promoted-implementation choices were made.
3. [ ] Fast correctness/public-surface/version/CI-topology checks pass on the final reconciled head.
4. [ ] The exact final reconciled SHA/fingerprint is recorded after fast CI is green.
5. [ ] T01–T03 final evidence runs use that same reconciled candidate rather than a pre-reconciliation artifact.

## Handoff / continuation rule

Keep T00 `CLAIMED` until the final exact-head fast matrix is green. Queued deep/release jobs are not reconciliation blockers unless a failure is causally tied to the merge.

Footnote: the first fresh Engineering Evidence run after the earlier reconciliation failed only because PR #56's body predated the repository's newer material-PR dossier headings. That metadata failure was repaired without changing code, thresholds, or benchmark claims.
