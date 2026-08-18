# v0.30 execution quickstart

Read `docs/V030_EXECUTION_MODEL.md` and `docs/v030-coordination/START_HERE_FOR_V030_EXECUTOR.md` first.

This directory is the durable execution state for the single authoritative v0.30 completion line.

## On resume

1. Resolve the current head of `agent/v030-authoritative-integration` and current `main`.
2. Read `AGENTS.md`, `docs/V030_EXECUTION_MODEL.md`, `docs/V030_RELEASE_GATES.md`, `docs/V030_RELEASE_LOCK.json`, and every task file here.
3. Work T00–T04 as one dependency graph; fix the highest-value release blocker where it actually lives.
4. Keep task states truthful. `DONE` requires implementation plus the exact durable evidence demanded by the release lock.
5. Reconcile current `main` before the final evidence wave.
6. Freeze release-critical source before minting final receipts; any later release-critical edit invalidates affected receipts.
7. Do not communicate project-critical state only through chat. Put generalized technical state, blockers, decisions, and evidence in Git.

CI and automation are execution/evidence tools, not task owners.
