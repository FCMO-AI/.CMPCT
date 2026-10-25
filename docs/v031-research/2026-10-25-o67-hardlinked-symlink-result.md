# O67/O67b — symlink-inode hardlink source fidelity: result

Date: 2026-10-25 UTC. **Status: focused candidate correctness verified, not merged or released.** Material source PR: [#421](https://github.com/FCMO-AI/.CMPCT/pull/421), stacked on [O50 #405](https://github.com/FCMO-AI/.CMPCT/pull/405).

## Authority and immutable hypothesis

The original prospective [O67 preregistration](2026-10-25-o67-hardlinked-symlink-prereg.md) was committed at `280ebd050640620c4012233fbf6f6dba360c4ab5` **before** experimental tests and observed data. Baseline is actual O50 source `17c96603e33b02b3f2f9e0079eec2b128f293be8`, Builder blob `21a9ec696df13961c25301654feb607a7e161a4c`. [O67b narrow-admission addendum](2026-10-25-o67b-selected-root-alias-guard-prereg.md) at `82c8731653b959643dc3b867a654bd64899236f5` was committed **before** modifying product source.

Primary falsifiable question: does the original Builder lose physical sharing of an authentic POSIX symlink inode when two hardlink names exist under the selected source root, even while r24 bytes and Reader verify? **Yes, directly demonstrated on Ubuntu 24.04 and macOS 14.**

## Genuine original product negative — preserved

[Initial source-exact A/B, Actions #40173599150](https://github.com/FCMO-AI/.CMPCT/actions/runs/40173599150) uses installed `cmpct` outside checkout, exact baseline source SHA and asserted Builder Git blob. On Ubuntu and macOS, `os.link(symlink, alias, follow_symlinks=False)` successfully creates two names whose `lstat(st_dev,st_ino)` and positive link count prove shared *symlink inode*, not merely matching target text. Original Builder creates an r24 archive, Reader verifies it, extraction recreates the same symlink target text under **distinct** `lstat` inode identities. Baseline tests **4/4 PASS on each POSIX host**; Windows **2 PASS / 2 POSIX SKIP**. The original unchanged candidate (no fix yet) deliberately failed the fail-closed expectation (**1 FAIL / 3 PASS** on each POSIX host), proving the test discriminates the intended mechanism. Not a crypto collision: archive bytes validly represent the wrong physical topology.

## Narrow correction and stronger control

A global `st_nlink>1` rejection was rejected **before product modification**, because the only symlink selected may have other hardlink names *outside the selected tree*. O67b recognizes the smallest representable boundary: maintain a per-Builder `(st_dev,st_ino) -> first selected path` map for symlink entries reporting link count >1; reject on a **second selected** name with the same inode. Do not deduplicate equal target text, do not alter regular-file hardlink ownership. No on-disk or Reader change.

Product source commit `a2abe6af318cda93e8f6023ab20627e8eb8eac16` modifies only `src/cmpct/builder.py` from baseline blob `21a9ec696df13961c25301654feb607a7e161a4c` to **`636cacef95c518b5ad67c101a5430de5b68d45c6`**. Test verifies refusal and untouched preexisting output sentinel. Extra positive test admits a one-name-in-tree symlink when its physical sibling is outside root, despite global nlink 2. Independent equal-target symlinks continue to extract as distinct objects; regular-file hardlinks retain inode sharing; ordinary source files exact and reproducible bytes.

## Installed six-job O67 + inherited O48/O50 composition evidence

Final **result-bearing executable HEAD `7a6ee478e7df7ccb517047c8461a3d01dd286c8e`**; [GitHub Actions #40174181153](https://github.com/FCMO-AI/.CMPCT/actions/runs/40174181153), all six matrix jobs SUCCESS. All JUnit XML test counts explicitly rechecked independently after invoking `python -m pytest` on an **installed package imported outside checkout**. The workflow copies, without modifying, original O48 special-file tests and O50 combined Builder tests, and checks out the **actual historical** O50 source for its baseline arm.

| Installed host | Historical O50 | Candidate O67 |
| --- | --- | --- |
| Ubuntu 24.04 | 11 PASS / 0 SKIP | 11 PASS / 0 SKIP |
| macOS 14 | 11 PASS / 0 SKIP | 11 PASS / 0 SKIP |
| Windows 2025 | 4 PASS / 7 POSIX SKIP | 4 PASS / 7 POSIX SKIP |
| **All arms** | **26 PASS / 7 SKIP** | **26 PASS / 7 SKIP** |

**66 collected tests; 52 PASS, 14 platform-appropriate SKIP, 0 FAIL/ERROR.** Original Builder SHA always `17c966...` / blob `21a9ec...`; candidate final HEAD `7a6ee...` / same new Builder blob `636cace...`. The original-source "loss confirmed" test and candidate "loss refused" test have *different explicit branch-variant predictions*, rather than making the baseline appear fixed. Tests also guard POSIX non-skips and Windows exactly seven skips, so no fabricated cross-platform credit.

An earlier smaller [court #40174070436](https://github.com/FCMO-AI/.CMPCT/actions/runs/40174070436) with the same Builder blob and only five O67 tests also succeeded in all six matrix jobs (**24 PASS / 6 SKIP**). The later eleven-test court adds untouched O48/O50 composition evidence.

## Strongest negative / known limits

- This is a **fail-closed admission mechanism**, not preservation of hardlinked symlink inode sharing within r24. It narrows accepted input on the physically nonrepresentable source case but preserves the single-selected-alias case.
- Windows omitted actual POSIX symlink-hardlink construction; its 4 PASS/7 SKIP per arm are not a Windows claim about that topology. NTFS streams/reparse semantics need their separate owners.
- Scanning `stat` identities is not a trusted immutable snapshot. Post-stat source pivots and concurrent modifications are owned by O52 [#408](https://github.com/FCMO-AI/.CMPCT/issues/408). No TOCTOU fix claimed.
- Physical inode collision/fidelity on exotic or network filesystems has not been proved. No race/hostile symbolic-link graph theorem is claimed.
- No full current product size/create/extract/CPU/RSS, installed release matrix, or canonical merge evidence has been produced. Existing v0.30.0/r24 unchanged.
- Builder neighbors O57 (regular-file NTFS ADS), O64 (directory ADS), O65 (xattrs), O60/O63 (deferred VZIP) still need actual mixed-branch composition. This PR does not overwrite them.
- `docs/discovery/STATE.json` is staleable and was intentionally not edited; the exact-head receipts here carry the decision.

## Decision, counterfactual, and next executable action

**Scientific outcome:** O50 silently loses symlink-inode physical aliases in valid source trees (confirmed).
**Product candidate outcome:** selected-tree-only fail-closed prevents the loss in exact installed package tests without rejecting legitimate external-only aliases (confirmed within POSIX controls).
**Promotion:** BLOCKED. No merge/release allowed on this evidence alone.

Cheapest original discriminator would have been two symlink names linked with `follow_symlinks=False` plus before/after `lstat` identity, not another full benchmark or same-target copy check. The narrow alternate one-in-tree/one-outside link reveals why the first global-link-count guard was overbroad. This is a transferable prospective fixture-design lesson, but there is insufficient repeated evidence to change discovery policy.

**Next:** owner O50 to incorporate as an isolated amendment (or stacked path) only after running the entire mixed-source Builder O47/O48/O50/O57/O64/O65 union, exact-head full general tests, portably installed packages, and official r24/ZIP promotion gate. If such union shows cost, use a measured source-faithful A/B; never weaken source fidelity or rewrite frozen checks.
