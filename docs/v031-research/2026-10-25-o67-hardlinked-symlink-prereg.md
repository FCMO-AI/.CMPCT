# O67 preregistration — hardlinked symbolic-link source fidelity

Date: 2026-10-25 (UTC). **Prospective: no source/product experiment has yet been run on GitHub.**

## Fixed authority and question

Source: O50 composition [PR #405](https://github.com/FCMO-AI/.CMPCT/pull/405), exact base commit `17c96603e33b02b3f2f9e0079eec2b128f293be8`, Builder blob `21a9ec696df13961c25301654feb607a7e161a4c`. Released v0.30.0/r24 is not changed. Other Builder owners O47/O48/O50/O57/O64/O65 and source-lifetime research O52 are independent.

**Question:** On POSIX, when two distinct directory entries hardlink the *same symlink inode* (`os.link(..., follow_symlinks=False)`), can the genuine Builder report successful r24 creation while the genuine Reader extracts two *different* symlink inodes? If so, can an explicit fail-closed admission guard prevent publishing a falsely exact archive without changing r24?

## Mechanism and controls

The currently frozen O50 `Builder.scan` handles `S_ISLNK` before its `st_nlink>1` physical-owner branch, which only handles regular files. Two symlinks with identical targets but distinct inodes are legitimate and must *not* be unified; two hardlinks to one symlink inode are physically different. The r24 `K_HARDLINK` extraction path relies on `os.path.exists(target)` and `os.link(target,full)`; it is not a proven general implementation of symlink-inode hardlink reconstruction. Fail closed, rather than advertising a new format capability.

Controls: (1) one genuine regular-file hardlink pair remains physically shared after extraction; (2) two independently created symlinks with the same target remain independent; (3) ordinary symlinks and file bytes remain exact; (4) source inode/link-count preconditions are asserted before running the Builder; (5) installed-outside-checkout package provenance, exact Git SHA/blob and actual pytest JUnit evidence are recorded. Test Windows conservatively and skip POSIX-only alias creation if not supported; never treat skip as PASS.

## Prospective predictions / kill conditions

- **Original negative prediction:** if OS creates two symlink names with equal `lstat(st_dev,st_ino)` and link count >=2, O50 will create a valid and verifiable r24 archive whose extracted symlink identities are distinct. If the Builder rejects or original extraction shares symlink inode correctly, the loss claim is false.
- **Candidate prediction:** adding an explicit check of `S_ISLNK` and `st_nlink>1` before content capture rejects the unsupported symlink-inode alias, preserving any pre-existing output archive unchanged. Ordinary independent symlinks, genuine *regular* hardlinks, exact content and reproducible bytes are unaffected.
- **Kill/narrow:** failure to construct a genuine same-inode pair means no conclusion on that host. Any regression of ordinary symlinks/regular hardlinks or unexpected Windows rejection blocks promotion. This does not solve active source rename/pivot races (O52), xattr capture errors (O65), or all platform-specific reparse-point semantics. No release claim without official gates.

## Alternatives and evidence ladder

1. Pretend equal targets imply physical identity: invalid for independent symlinks.
2. Emit `K_HARDLINK` targeting `K_SYMLINK`: requires Reader, validator, dangling target, extraction and cross-platform semantics investigation beyond a safe narrow fix.
3. Freeze/clone full filesystem: disproportionate and still requires a contract for hardlinked symlinks.
4. **Selected:** source-exact two-host installed negative falsifier, then minimal fail-closed candidate with inherited positive controls; compare exact package behavior and measure incidental normal-tree cost before any release. No change to benchmark fixture/comparator/frozen evidence.

Evidence tier is a genuine installed-product semantic test (not size/performance benchmark). The original and candidate should be run with stable physically realized trees and a real CMPCT archive. Positive controls are not allowed to mask a fixture skip.

## Concurrency and decision

O67 owns only this narrow symlink-inode hardlink admission class on an isolated branch stacked on O50. It will not edit O50/O57/O64/O65 branches, canonical release, discovery state, evaluator, or format. An observed original loss justifies a minimal candidate and a notification to O50; a blocked host or valid negative preserves uncertainty. A green test of the candidate earns **candidate semantic** credit only.
