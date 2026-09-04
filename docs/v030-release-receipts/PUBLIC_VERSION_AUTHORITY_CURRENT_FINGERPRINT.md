# v0.30 current-fingerprint public/version authority receipt

Status: **accepted Custody receipt for the current immutable candidate fingerprint; this is not live-site publication authority and does not unlock release.**

## Exact candidate binding

- immutable evidence source: `631216979c01627a8a3bc2bc598327c4f065e6ca`
- current candidate fingerprint: `c119dbae83a8eae6d09dbf48e764a4bc9679452cef4381cb031dc3444ecfbc69`
- authoritative integration PR: `#56` / `agent/v030-authoritative-integration`

The current-fingerprint source map is the one recorded by `docs/CURRENT_STATE.md`: coordination-only descendants may move the branch head without changing this immutable candidate source/fingerprint pair. This receipt grants no authority to a different archive fingerprint.

The fingerprint above is cross-checked against the machine-checkable `native-r25` and `zip-portability` receipts for the same immutable source. Those receipts independently bind their durable strict-JSON evidence to `c119dbae83a8eae6d09dbf48e764a4bc9679452cef4381cb031dc3444ecfbc69`. A prior prose-only typo at this path used `c119cc2...`; that value had no machine-checkable receipt authority and is superseded by this correction.

## Public proof surface

Exact-source workflow:

- workflow: `CMPCT public proof contract`
- run: `33871982707`
- job: `proof-surface` (`101019915807`)
- conclusion: `success`

The job checked out `631216979c01627a8a3bc2bc598327c4f065e6ca` directly and asserted `HEAD == EVIDENCE_HEAD` before executing the substantive contract.

Observed successful authority steps:

- disclosure guard clean across **1,544 tracked text files**;
- deterministic site build and enhancement completed;
- public proof contract reported `cmpct-public-evidence-v1` coherent;
- release-evidence contract reported coherent with shipping core version `0.29.0` and surface revision `0.29.l`;
- browser JavaScript syntax checks passed;
- browser-writer smoke archive was readable by canonical Python, with `19,823` input bytes -> `889` archive bytes, 3 logical files / 2 unique blobs, while retaining canonical v24 compatibility;
- responsive render matrix passed **16/16 physical viewport classes**, from `320x568` through `2560x1440`;
- responsive artifact `cmpct-responsive-matrix-631216979c01627a8a3bc2bc598327c4f065e6ca` uploaded as artifact ID `9936401188`, ZIP SHA-256 `f159e805a6bc43c6143f8a38bc7c342803bea46677099d1081d7ada9a7e6b1cd`.

### Deliberate limit

The workflow's `Stamp validated main publication receipt` and `Upload validated main publication receipt` steps were **skipped** on this PR evidence run. Therefore this receipt closes the exact-candidate public proof/build/browser/responsive evidence lane only. It does **not** claim that `main`, `gh-pages`, or any live deployment has been promoted to v0.30, and it must not be used as live-site publication authority.

## Version discipline

Exact-source workflow:

- workflow: `CMPCT version discipline`
- run: `33871982869`
- job: `version-discipline` (`101019862707`)
- conclusion: `success`

The job checked out the same immutable candidate source directly, asserted exact `HEAD == EVIDENCE_HEAD`, and compared against base `dd0c12cd6ee2dbb859464ea5c6be221ad34b9fdf`.

Terminal contract output:

`version discipline: core stays 0.29.0; surface=0.29.l; 311 presentation/repository path(s)`

This is the intended pre-release state: v0.30 work remains unreleased, so the shipping core version is not bumped and no v0.30 public release claim is manufactured.

## Custody interpretation

This receipt materially retires the current-fingerprint **public proof/build/browser/responsive** and **version-discipline** evidence gaps for the immutable candidate above. It does not retire Python correctness/range recovery, integrity, Android/physical-platform requirements, external competitor/runtime frontier, shared-build, CI topology/manifest, live-site publication, or the final direct strict-release-lock receipt.

**MERGE / TAG / VERSION-BUMP / PUBLISH remains LOCKED** until all remaining current-fingerprint authority is present and the direct strict release contract reports `UNLOCKED`.
