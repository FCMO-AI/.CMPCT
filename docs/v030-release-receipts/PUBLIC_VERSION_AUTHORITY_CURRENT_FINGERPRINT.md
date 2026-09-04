# v0.30 public/version authority receipt — historical fingerprint only

Status: **HISTORICAL / STALE FOR CURRENT RELEASE AUTHORITY.** This file preserves a valid exact-source public-proof/version-discipline result for an older candidate, but it grants **zero** authority to the current v0.30 fingerprint and does not unlock release.

## Historical candidate binding

- immutable evidence source: `631216979c01627a8a3bc2bc598327c4f065e6ca`
- historical candidate fingerprint: `c119dbae83a8eae6d09dbf48e764a4bc9679452cef4381cb031dc3444ecfbc69`
- authoritative integration PR: `#56` / `agent/v030-authoritative-integration`

The branch has since undergone release-critical native dependency/workflow custody corrections. The current release fingerprint is now independently reproduced by native-authority and ZIP-portability evidence as:

`67c5f6009d3fa34c56c6d1706597060f56196eca4019a64f97ca5735021a68fa`

Therefore the `c119...` public/version result below is mechanism/history evidence only. Fingerprint-neutral coordination descendants may move the branch SHA without invalidating `67c5...`, but no result from a different release fingerprint may be rebound to it.

## Historical public proof surface

Exact-source workflow:

- workflow: `CMPCT public proof contract`
- run: `33871982707`
- job: `proof-surface` (`101019915807`)
- conclusion: `success`

That historical job checked out `631216979c01627a8a3bc2bc598327c4f065e6ca` directly and asserted `HEAD == EVIDENCE_HEAD` before executing the substantive contract.

Observed successful mechanism evidence included:

- disclosure guard clean across 1,544 tracked text files;
- deterministic site build and enhancement;
- coherent `cmpct-public-evidence-v1` / release-evidence contract for the then-current candidate;
- browser JavaScript syntax checks;
- browser-writer smoke readable by canonical Python while retaining canonical-v24 compatibility;
- responsive render matrix green for 16/16 physical viewport classes;
- responsive artifact ID `9936401188`, ZIP SHA-256 `f159e805a6bc43c6143f8a38bc7c342803bea46677099d1081d7ada9a7e6b1cd`.

The workflow's main-publication receipt steps were skipped, so even on `c119...` this never established live-site publication authority.

## Historical version discipline

Exact-source workflow:

- workflow: `CMPCT version discipline`
- run: `33871982869`
- job: `version-discipline` (`101019862707`)
- conclusion: `success`

Historical terminal output:

`version discipline: core stays 0.29.0; surface=0.29.l; 311 presentation/repository path(s)`

That was the intended unreleased state for the older candidate. Because version/public-surface paths participate in the release fingerprint, the result must be regenerated before current-fingerprint release credit can be granted.

## Current Custody decision

- `c119...` public proof/version discipline: **preserved as historical mechanism evidence**.
- `67c5...` native-r25 and ZIP portability: **current machine-checkable release receipts**.
- current-fingerprint public proof/version discipline: **RED / missing until regenerated**.
- live-site publication: **RED / never granted by this receipt**.

No benchmark, format, locality, recovery, integrity, platform, version or publication requirement is weakened by this correction.

**MERGE / TAG / VERSION-BUMP / PUBLISH remains LOCKED.**
