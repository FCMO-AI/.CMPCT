# T00 — Reconcile authoritative v0.30 with canonical main

- **Owner:** v0.30 sole executor
- **Priority:** P0
- **State:** CLAIMED
- **Branch:** `agent/v030-authoritative-integration`

## Objective

Reconcile every canonical-main commit that postdates the current integration merge-base without losing v0.30 mechanisms, current-main hardening, repository instructions, CI topology, public-surface policy, or benchmark substrate fixes.

## Current status

Canonical main reconciliation was refreshed at integration merge commit `0313258a25f1a87f78fdddfbb445d4a41e25f734` against main `dd0c12cd6ee2dbb859464ea5c6be221ad34b9fdf` through reconciliation PR #85.

`compare main...agent/v030-authoritative-integration` reports **0 commits behind** at this checkpoint; `dd0c12c...` is the merge base. The newly imported main delta comprised 29 commits / 11 effective paths and adds the canonical v0.29 Shipping-vs-Frontier public benchmark/surface at `SURFACE_REVISION` 0.29.l.

Semantic overlap decisions for this checkpoint:

- `tools/check_public_surface.py`: the integration branch wins. Its exact-canonical-line legal attribution exception is a stricter safety implementation than main's broader label/path allowlist and therefore preserves main's public-attribution intent without widening the disclosure exemption.
- `tests/test_public_attribution.py`: current main wins. Its only delta from the integration copy updates the asserted public surface revision from 0.29.k to the imported canonical 0.29.l state.
- `site/src/assets/experience.js`: current main wins because the only imported semantic delta is the canonical `shipping-frontier-v029.js` assembly import.
- `SURFACE_REVISION`: current main wins at 0.29.l.
- the seven newly added Shipping-vs-Frontier workflow/benchmark/site/test files are imported byte-for-byte from current main.

An earlier reconciliation checkpoint at `851b2ec3a4c1134c965302330fd0f908c57f481d` against main `72e7e6313ffa896b7ef7a14a2f48495754b494f2` remains historical provenance. Its overlap decisions were:

- `experiments/entropygraph_v029_parallel_portfolio.py`: current main won because its fsync-backed durable atomic publication was a strict safety superset while retaining the same byte-selection contract.
- `tests/test_v029_parallel_portfolio.py`: current main won because it included the integration assertions plus overwrite/durability regression coverage.
- `benchmarks/history/2026-08-17-mosaic-v029-category.json`: current main won because it was the same evidence/provenance in canonical compact JSON form.

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
2. [x] Every overlapping path at the latest checkpoint received explicit semantic resolution; no blind promoted-implementation choices were made.
3. [ ] Fast correctness/public-surface/version/CI-topology checks pass on the final reconciled head.
4. [ ] The exact final reconciled SHA/fingerprint is recorded after fast CI is green.
5. [ ] T01–T03 final evidence runs use that same reconciled candidate rather than a pre-reconciliation artifact.

## Handoff / continuation rule

Keep T00 `CLAIMED` until the final exact-head fast matrix is green. Queued deep/release jobs are not reconciliation blockers unless a failure is causally tied to the merge.

Footnote: the first fresh Engineering Evidence run after the earlier reconciliation failed only because PR #56's body predated the repository's newer material-PR dossier headings. That metadata failure was repaired without changing code, thresholds, or benchmark claims.
