# T02 current-fingerprint supersession — 2026-09-04

Status: **authoritative zero-history correction for the T02 fingerprint ledger; T02 remains CLAIMED and all frozen gates remain unchanged.**

This note supersedes only the `Current exact-fingerprint release gap ledger — 2026-09-04` fingerprint/status paragraph in `docs/v030-coordination/tasks/T02-evidence-performance.md`. It does not alter the frozen T02 benchmark grammar, corpus, comparator, locality accounting, timing envelope, external-competitor semantics, task state, or release threshold.

## Current release-critical fingerprint

The prior `c119dbae83a8eae6d09dbf48e764a4bc9679452cef4381cb031dc3444ecfbc69` floor is historical. Subsequent release-critical native dependency/workflow custody corrections changed the fingerprint without changing compression product bytes or any frozen benchmark threshold.

Current fingerprint, independently reproduced by exact-source native-authority and ZIP-portability result-bearing jobs:

`67c5f6009d3fa34c56c6d1706597060f56196eca4019a64f97ca5735021a68fa`

Exact evidence source for both promoted mechanism receipts:

`52ebabc63c7ea74a1665a5720359977e552ad5c2`

Fingerprint-neutral receipt/coordination descendants may move the branch SHA while retaining this release-critical fingerprint. They do not authorize evidence emitted for another fingerprint.

## Current accepted machine receipts

`native-r25` is now bound to:

- run `33906151331`, result-bearing job `101131475053`;
- durable evidence `docs/v030-release-evidence/native-r25-52ebabc63c7ea74a1665a5720359977e552ad5c2.json`;
- evidence SHA-256 `0a537409833c146f765696e0b9fbca86a75d9d952223b0d978896f06d1cddcf2`;
- candidate fingerprint `67c5f600...a68fa`;
- pinned portable dependency lock `3a4babc7a43ef0aadca37ac0a49695b185419dd8aa2cbebcb5653202ed6a71a2`.

`zip-portability` is now bound to:

- run `33906151346`, result-bearing job `101131485307`;
- durable evidence `docs/v030-release-evidence/zip-portability-52ebabc63c7ea74a1665a5720359977e552ad5c2.json`;
- evidence SHA-256 `103ad6e4b19cdb69c1839c4f3350af2aaf4376f0a52e69f66b77baaf323bdb12`;
- the same candidate fingerprint and portable dependency lock.

Native-core run `33906151295`, result-bearing job `101131444236`, independently checked out the same source SHA and completed its full matrix with committed native-core lock SHA-256 `007f963ed4e135c6dcacb09cd353064ddda87453af481990ca17f7a221402cc1`. Native-core does not itself mint the release-fingerprint JSON, so this note does not pretend otherwise.

## T02 release gaps remain RED

No current-fingerprint T02 receipt is promoted by the native/ZIP convergence above. The following manifest obligations remain absent until deliberate result-bearing runs on `67c5...` produce durable strict JSON and are converted into machine receipts:

- `compression-generalization`;
- `shared-build-rehab`;
- `runtime-memory-selective`;
- `external-competitors`;
- `ci-topology`.

The push-side classifiers observed after fingerprint-neutral coordination/receipt commits correctly skipped expensive result-bearing generalization/runtime/fuzz work. Those greens are routing evidence only and earn zero release credit.

The repository's authoritative generalization lane permits a deliberate `workflow_dispatch` to bypass latest-file impact classification while keeping the exact immutable candidate binding. Where an execution environment cannot issue that dispatch, preserve the blocker rather than modifying release-critical source merely to wake CI.

## Adjacent stale authority explicitly revoked

The older public-proof/version-discipline receipt at fingerprint `c119...` has been reclassified as historical only. Current-fingerprint public/version proof and live-publication authority remain separate missing release obligations.

## Decision

T02 remains **CLAIMED**. Do not move it to DONE until all five machine receipts above are current-fingerprint green and every original T02 completion condition remains satisfied. No aggregate result may hide a losing row, and no threshold/workload/comparator mutation is authorized by this supersession.

**MERGE / TAG / VERSION-BUMP / PUBLISH remains LOCKED.**
