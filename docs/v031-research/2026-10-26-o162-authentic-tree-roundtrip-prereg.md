# O162 — Authentic CMPCT r24 filesystem topology roundtrip (preregistration)

Date: 2026-10-26 (UTC)  
Status: PREDICTION BEFORE INSTRUMENT / NO RESULTS  
Ownership: independent child of O155 PR #496; **no mutation** of O155's claimed oracle, Builder, Reader, legacy digest, format, test thresholds, historical receipts or discovery cache.

## Source / question

Base: `FCMO-AI/.CMPCT` O155 `19976530ab7cc3e9652c071f9d9ab85fb6ccea8a`; released v0.30.0/r24 baseline product code. Source Git blobs to bind: Builder `663ef0922992b1fbb8f19e6eea88d55c10a56044`, Reader `e716233403dabd0966863c45635e18fa5ac6afb8`, O155 oracle `0bef46e8d1944ff327063c66edc9bbc29fa58481`, historical `transactions.py` `964f4dcf8c25cdd5885b6c43bbf3d92d16dd252c`.

O155 demonstrates synthetic false equivalences in the historical `tree_digest` and defines a stronger static POSIX oracle. **Unanswered narrower product question:** for a supported *quiescent* tree combining hardlinked files, regular symlinks, directory symlinks, subdirectories, empty directories, Unicode names, modes, and content, does the genuine installed Builder -> r24 archive -> genuine installed Reader roundtrip preserve the O155 strict manifest (not merely payload)?

## Hypothesis and falsifier

Predict exact strict-manifest equality on Ubuntu 24.04 and macOS 14 for one explicitly supported tree. The source and extracted directory names/inode numbers differ but the in-tree hardlink-equivalence partition must remain invariant. Independently assert content SHA, `os.path.samefile` for a two-name hardlink, `os.readlink` targets, entry types and modes.

After successful extraction **only as a negative control**, sever one restored hardlink by unlinking the alias and replacing it with a regular copy of identical contents and mode. Predict `transactions.tree_digest` does not notice that topology loss, while O155 `strict_digest` does. This tests the historical witness's blind spot in a genuine reconstructed tree, not a synthetic-only pair.

**Disproof:** source/extract strict digests differ; source input rejected; any content, hardlink, symlink, directory or mode test fails; the historical digest does in fact distinguish the hardlink severing; the strict witness fails to distinguish it; or source and installed code identities disagree. Preserve unexpected negatives as evidence, not as product promotion.

## Cheapest honest rung / competing controls

Static source review predicts normal POSIX paths can carry these kinds. Existing O155 synthetic courts establish oracle discrimination but do **not** establish real CMPCT Builder/Reader tree fidelity. The strongest simple controls are direct readlink/samefile/stat/byte checks; strict manifest integrates them with deterministic relative paths. No new compression, sorting heuristic, benchmark corpus or schema. Build one small tree rather than consuming an expensive full matrix.

## Boundaries and costs

Not an atomic hostile-race test, cross-host archive portability comparison, Windows/NTFS/ADS/xattr/ACL/uid/gid/time/sparse physical-layout test, special-file preservation or full release conformance. In particular, unsupported FIFO-source handling already has O48 PR #402 and MUST NOT be rediscovered as a new family. No claim of universal tree fidelity, ZIP interchangeability, or performance gains. Record complete archive byte count and subprocess wall time as noncomparative observables only; no full-product credit. Preserve raw machine-readable receipts even on failure, and do not mutate the O155 parent branch. The dedicated host workflow must bind exact source identities and run an installed distribution from outside the checkout.

## Decision and counterfactual

If exact, O155 gains authentic product-roundtrip evidence in its narrow domain and offers a regression instrument for future integrated Reader/Builder owners; no release credit. If not, isolate a concrete product defect by file-type and compare to original controls before proposing a fix. Any O155 method/process revision requires repeated durable causal evidence, not this single experiment. This is a bounded independent child PR; no merge/release/format bump.
