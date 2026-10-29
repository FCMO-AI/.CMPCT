# J24I11 — Windows hardlink census provenance (preregistration)

Date: 2026-10-29 UTC
Status: PREDICTION FROZEN BEFORE PRODUCT/TEST CHANGES
Exact parent: `65d8b1681bc9ae00d48c3c362f2ab1dc9e2ed91d` (PR #728; inherited product from PR #725 `96989c923ed8a01f6cd6a6ca8bf69002a2409685`)
Issue: #729. Related: #312 and private compaction owner #723. Independent staged-name race #726 is explicitly outside this experiment.

## Baseline, question and hard invariant
On Windows Server 2022/Python 3.11, physically linked files have equal (st_dev,st_ino), `os.stat(...).st_nlink == 2`, but `DirEntry.stat(follow_symlinks=False).st_nlink == 0` (#728 run 40815209584, independently parsed artifact 12871349353). Current `Builder.scan` only recognizes a hardlink when the latter count exceeds one, so archive indexes contain two K_FILE records with content deduplication but **no link topology**. We ask whether a narrow, **non-following Windows-only second stat for unknown link count** restores authenticated K_HARDLINK topology without changing POSIX hot paths, direct bytes of distinct regular copies, or compaction safety.

### Mechanism and strongest controls
Selected: after obtaining the `DirEntry.stat`, only for Windows regular entries with `st_nlink == 0`, ask `os.stat(entry.path, follow_symlinks=False)` for a trustworthy count, reject an identity/type change during sampling, and fail closed if it still cannot determine link count. Pass the trusted result into the existing inode-owner path. No new encoding modes.
Simpler competing control: use `(st_dev,st_ino)` alone for Windows when `st_nlink == 0`; faster but would treat an unknown/weak inode source as authority and risks false aliases when the filesystem uses sentinel identities. Another control is treating equal logical bytes as linked; rejected because ordinary copies are not hardlinks.
Alternative explanation: the scanner's stat mismatch might be specific to this Windows runner or the test source tree, or the Reader/extractor might have independent hardlink faults. The installed wheel must prove each boundary separately.

### Predeclared tests / kill rules
1. Same-source installed-wheel Ubuntu 24.04, macOS 14, Windows 2022: physically linked two-path input must become one K_FILE owner plus one K_HARDLINK alias in source and compacted revision-24 archives, verified by Reader and by actual extraction inode identity wherever supported. A same-content pair of independent files must remain two K_FILE paths and **two distinct physical inodes** on extraction.
2. Show source OS `os.stat` and `DirEntry.stat` link count/identity witnesses. On Windows patched builder must not flatten links. On Unix the scan hot path and archive semantics must remain unchanged.
3. Guard no-follow: scanner encountering a symlink remains K_SYMLINK; an identity change across the second stat rejects instead of promoting a forged owner.
4. Retain the previous four-case J24I07 compaction/safe-symlink court, including source/sentinel invariants. Correct only the fingerprint/source identity check in a *new* workflow, never the historical archived gate.
5. Record same-host, same-input **diagnostic** builder wall/CPU, output bytes and peak RSS on many independent files and on physical hardlinks. Compare the exact historical candidate against the new candidate; preserve raw repetitions. A meaningful create-time regression disqualifies promotion pending repair; no experimental result earns official benchmark credit.
6. If `os.stat` does not return a trustworthy positive link count on supported Windows, or if the link topology remains wrong, this proposed fix is falsified and stays draft. Green code/test alone does not permit merge or release.

## Decision and concurrency
Question/family: J24I11 / Win32 filesystem source identity, **not** J24I09 stage-name custody or PR #629 Reader materialization. #725/#723 own the composed compaction product; this isolated child branch will preserve their code and propose a focused Builder donor. No changes to `main`, format, frozen release gate, `STATE.json` or existing experiments. Scientific ownership will be visible through branch/PR and exact-head CI.
