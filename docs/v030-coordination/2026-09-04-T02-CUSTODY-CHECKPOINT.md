# T02 Custody checkpoint — 2026-09-04

Status: **DURABLE HANDOFF — release authority remains locked**

This note records an exact-head Custody repair and prevents later executors from mistaking classifier-only green workflow cards for release evidence. It changes no benchmark corpus, threshold, comparator, archive grammar, product policy, locality law, timing envelope, or release requirement.

## Authoritative line

- PR: `#56`
- branch: `agent/v030-authoritative-integration`
- pre-repair head: `20ef79f7c50e11ec1034f62552dfe7f07f870f08`
- Custody repair commit: `2b67c94c5277699fdfa42b2e09651fa640b0552c`
- repair: `.github/workflows/v030-release-generalization.yml` now uses the repository-supported push-only exact-receipt custody model (`preserve-running-exact-receipt`) with branch-scoped push, exact `github.sha` evidence binding, exact-head checkout, latest-head diff classification, SHA-keyed non-cancelling workflow concurrency, and unchanged substantive authority jobs.

## Defect and evidence

On pre-repair head `20ef79f7...`, CI-topology run `33867896314`, job `101006825041`, rejected the authoritative generalization workflow because it declared `split-classifier-preserve-receipts` while being push-only. The topology checker requires that split model to be PR-triggered with PR/ref cancelling classifier concurrency plus exact-SHA non-cancelling receipt concurrency; the workflow could not satisfy that declared model as written.

The lowest-sufficient D0 intervention was to retain the push-only trigger and exact-head change classifier but adopt the checker's supported push exact-receipt model. No result-bearing benchmark logic changed.

Exact-head CI-topology run `33871260929`, job `101017549324`, then passed all topology steps on `2b67c94c5277699fdfa42b2e09651fa640b0552c`, including changed-workflow enforcement and topology-policy ratchet.

## Release-truth qualification

The exact-head `CMPCT v0.30 final release authority` run `33871261364` is **classifier-only green**, not release authority. Its `latest-head-impact` job passed, but substantive jobs `contracts`, `runtime-and-selective-read`, `compression-and-product-parity`, and `external-frontier` were all skipped. Do not mint, infer, or rebind release credit from that card.

Likewise, `CMPCT v0.30 authoritative PR gates` run `33871260121` passed its latest-head classifier while `reader-fuzz`, `generalization`, `shared-rehab`, and `runtime` were skipped. This is expected for a workflow-only custody change and is not evidence that those release obligations are complete on the new fingerprint.

Because `.github/workflows/v030-*.yml` is part of `docs/V030_RELEASE_LOCK.json` fingerprint scope, the Custody repair changes the release-critical fingerprint. Historical receipts on the prior fingerprint remain evidence/provenance but do not authorize the new candidate. Regenerate or deliberately dispatch each required result-bearing receipt under existing repository law; never edit source or thresholds merely to wake a workflow.

## Research/Forge boundary at this checkpoint

No Foundry thesis is active. F-01 remains retired.

R41 is terminal as `RETAIN_SPLIT_POLICY_R40_BOUNDARY`: global dictionary effort 9 is not product-admissible under the frozen matrix because Analytics/Database incurs `+59,149 B` versus the level-12 control and the aggregate candidate erodes `+66,071 B` versus dict12, despite real runtime gains and positive transfer on Incremental Backups and ML Artifacts. No scalar-effort R42 sweep is justified. Preserve R39 as local mechanism evidence and R40/R41 as the carrying-cost/product boundary.

## Next decisive action

1. Do not make another release-critical source/workflow edit merely to force CI; stabilize the candidate fingerprint.
2. Let the current exact-head regression suite finish and investigate any real failure rather than rerunning for luck.
3. Obtain result-bearing exact-fingerprint T02 receipts for compression-generalization, shared-build rehabilitation, runtime/memory/selective-read, external competitors, and CI topology through existing admitted/dispatch surfaces.
4. Continue T01/native/ZIP/Android/platform receipts on the same fingerprint; physical ARM64 Android remains mandatory under current portability law.
5. Run strict release authority only after required receipts/task states are durably present. Until it reports `UNLOCKED`, **do not merge, tag, version-bump, or publish v0.30 claims**.
