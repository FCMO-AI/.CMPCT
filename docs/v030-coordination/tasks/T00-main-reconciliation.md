# T00 — Reconcile authoritative v0.30 with canonical main

- **Owner:** slot-00
- **Priority:** P0
- **State:** CLAIMED
- **Branch:** `agent/v030-authoritative-integration`

## Objective

Reconcile every canonical-main commit that postdates the current integration merge-base without losing v0.30 mechanisms, current-main hardening, repository instructions, CI topology, public-surface policy, or benchmark substrate fixes.

## Current status

Canonical main reconciliation completed at integration commit `851b2ec3a4c1134c965302330fd0f908c57f481d` against main `72e7e6313ffa896b7ef7a14a2f48495754b494f2`.

`compare main...agent/v030-authoritative-integration` now reports **0 commits behind**. The merge adopted exact current-main blobs for all 35 post-merge-base paths while preserving all non-overlapping v0.30 and cooperation-slot paths.

Semantic overlap decisions:

- `experiments/entropygraph_v029_parallel_portfolio.py`: current main wins because its fsync-backed durable atomic publication is a strict safety superset of the integration copy while retaining the same byte-selection contract.
- `tests/test_v029_parallel_portfolio.py`: current main wins because it includes the integration assertions plus overwrite/durability regression coverage.
- `benchmarks/history/2026-08-17-mosaic-v029-category.json`: current main wins because it is the same evidence/provenance in canonical compact JSON form.

## Owned paths

Repository-wide only for conflict resolution/reconciliation. slot-00 is the only agent authorized to merge/rebase canonical `main` into the authoritative integration branch.

## Must not regress

- frozen v0.30 release thresholds;
- current-main AGENTS/instructions and CI topology;
- durable v0.29 histories and reproducibility repairs;
- imported G0–G4, PrefixGraph, reader/recovery, shared-build and release-gate work;
- public-surface discipline.

## Completion evidence

1. [x] `compare main...agent/v030-authoritative-integration` reports no behind commits.
2. [x] All three overlapping paths have explicit semantic resolution; no blind ours/theirs promoted implementation choices.
3. [ ] Fast correctness/public-surface/version/CI-topology checks pass on the reconciled head.
4. [ ] Coordination status records the exact reconciled SHA after fast CI is green.
5. [ ] T01–T03 dependencies record the reconciled SHA before their final evidence runs.

## Handoff

Keep T00 `CLAIMED` until the fresh exact-head fast matrix is green. Do not treat queued deep/release jobs as reconciliation blockers unless a failure is causally tied to the merge.

Footnote: the first fresh Engineering Evidence run failed only because PR #56's body predated the repository's newer material-PR dossier headings. That metadata failure is being repaired without changing code, thresholds, or benchmark claims.
