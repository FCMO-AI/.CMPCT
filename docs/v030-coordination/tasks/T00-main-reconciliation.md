# T00 — Reconcile authoritative v0.30 with canonical main

- **Owner:** slot-00
- **Priority:** P0
- **State:** CLAIMED
- **Branch:** `agent/v030-authoritative-integration`

## Objective

Reconcile every canonical-main commit that postdates the current integration merge-base without losing v0.30 mechanisms, current-main hardening, repository instructions, CI topology, public-surface policy, or benchmark substrate fixes.

## Current observed debt

At coordination bootstrap the integration branch was diverged from `main` by approximately 122 commits ahead / 35 commits behind. Re-resolve immediately before work; these numbers are not immutable evidence.

## Owned paths

Repository-wide only for conflict resolution/reconciliation. Slot-00 is the only agent authorized to merge/rebase canonical `main` into the authoritative integration branch.

## Must not regress

- frozen v0.30 release thresholds;
- current-main AGENTS/instructions and CI topology;
- durable v0.29 histories and reproducibility repairs;
- imported G0–G4, PrefixGraph, reader/recovery, shared-build and release-gate work;
- public-surface discipline.

## Completion evidence

1. `compare main...agent/v030-authoritative-integration` reports no behind commits.
2. All conflicts have explicit semantic resolution; no blind ours/theirs promoted implementation choices.
3. Fast correctness/public-surface/version/CI-topology checks pass on the reconciled head.
4. Coordination status records the exact reconciled SHA.
5. T01–T03 agents are told through Git task dependencies which new reconciled SHA to rebase/cherry-pick onto before final evidence.

## Handoff

When ready, set state to `REVIEW` only if an independent reconciliation audit is useful; otherwise slot-00 may mark `DONE` after evidence above exists because it owns the authoritative branch.
