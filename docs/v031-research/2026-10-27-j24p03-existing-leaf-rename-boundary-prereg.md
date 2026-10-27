# J24P03 — prospective boundary test for authenticated **existing-target** replacement

**Date:** 2026-10-27 UTC. **Evidence class:** research/kernel oracle only; no product/release credit.
**Base:** CMPCT `FCMO-AI/.CMPCT` exact J24F12 PR #559 commit `dd723d128b5a020f154b4c9f7d37c6eedc929f24`; source and release unchanged. The inherited Linux fresh-target candidate J24F11 #557 is create-only by design. Issue #528 and J24F02 #527 establish the original named-stage post-verification substitution; J24P02 #523 establishes O_TMPFILE+linkat no-clobber for an **absent** destination. Neither establishes security for replacing an **existing** destination with a verified physical inode.

## One question / prediction, frozen before writing the new instrument
**Can an already authenticated O_TMPFILE inode become an atomic, safe replacement of a pre-existing file by first publishing an intermediate stage name with `linkat` and then calling `os.replace` or `renameat2(RENAME_EXCHANGE)`, when a separate same-UID process can mutate names in that parent directory?**

**Prediction:** No. The first kernel operation authenticates the source inode identity, but exposing an intermediate name separates that custody from the *second* pathname-based rename. After a deliberately synchronized separate-process stage-name substitution, both native rename modes will publish the attacker-selected inode, while the original O_TMPFILE fd still contains authenticated bytes. Uncontended versions should succeed. The inherited direct fd-to-absent-name `linkat(AT_EMPTY_PATH)` should publish the correct inode, and occupied-name `linkat` must refuse EEXIST without modifying the prior leaf. Direct rename from `/proc/self/fd/N` is a separately attempted candidate that may fail with EXDEV because rename cannot treat a procfs symlink as the original filesystem source inode.

## Cheaper alternatives / causal counter-hypothesis
1. **Simple fstat/lstat before second rename:** it can pass before an interposed pathname rename; #527 already falsifies this control.
2. **Reuse the existing J24P02 no-clobber primitive:** secure for absent outputs under its specified threat model; it does not implement overwrite.
3. **Use O_TMPFILE plus a short-lived link then os.replace:** selected experiment. If substitution cannot change the published inode, retain as a candidate for productization; do not assume vulnerability without a real kernel test.
4. **Use RENAME_EXCHANGE instead of ordinary rename:** separate second syscall/control; may preserve the old destination under a temporary name, but must still prove verified-source custody.
5. **Define a narrower threat model or refuse hostile existing overwrites:** possible product direction if the two-step proposals fail; does not imply general impossibility of every future OS/platform mechanism.

## Prospective test and validity constraints
Run as an ordinary unprivileged Linux runner on a disposable filesystem. In each test allocate distinct GOOD, BAD and OLD byte payloads, create an O_TMPFILE without O_EXCL, keep its fd open and record dev/ino and SHA. For two-step cases, `linkat(AT_EMPTY_PATH)` must expose a visible stage hardlink referring to the original fd inode; a separate Python subprocess performs `os.rename(stage, quarantine)` then writes a different regular inode with BAD bytes at exactly stage; only then may the parent invoke the actual `os.replace` or libc `renameat2`. Assert actor exit code, original inode retained in quarantine, successful kernel rename, destination inode equals foreign inode and BAD SHA (negative result), original fd SHA remains GOOD, and preexisting OLD was initially the target. Repeat both rename modes with no actor and require original GOOD bytes. For direct no-clobber, assert exact fstat dev/ino identity after absent publication and EEXIST preservation when existing. Use no monkeypatched fake rename.

The instrument must record syscalls/errno, process UID, filesystem, verified source identity, all SHA and inode outcomes, exact source Git SHA, plus a JSON result and honest negative labels. Do not leave only human prose; retain raw hosted artifact. Narrow Linux kernel primitive results do not imply actual installed CMPCT overwrite safety. No benchmark, comparator, semantic contract, release gate, product source or historical vector may be changed.

## Kill/narrow conditions
- If the actor cannot replace the stage due permission or race orchestration, the instrument is **INCONCLUSIVE**, not safe.
- If no-attack source inode/bytes differ from the fd, the comparison is invalid.
- If `renameat2` rejects an otherwise valid no-attack setup, treat as unsupported rather than claiming security.
- If both attacks publish original GOOD from original fd despite stage substitution, hypothesis is falsified and this replacement path merits follow-up.
- If both publish BAD, **RETIRE this two-syscall existing-target publication family under same-parent same-UID writer threat**; preserve no-clobber as separate.
- Unsupported O_TMPFILE or linkat is an infrastructure/FS capability blocker for this experiment, not product failure.

## Whole-system debt / scope
No claim about race probability, hostile ancestor changes, different UID, privileges/capabilities, network mounts, Windows/macOS, complete CMPCT Reader, metadata/xattr/hardlinks, durability/fsync, large RSS/CPU, ZIP64, selective read or official release performance. No permission to merge or publish. Any follow-up product candidate must preserve exact archive SHA, direct-base semantics, strong adverse actors, and fail-closed existing-target behavior.

**Prospective decision boundary:** Does the attacker change published physical identity despite a retained authenticated anonymous inode? The shortest proof is an authentic syscall sequence with one independently scheduled adversary, not another global performance benchmark.
