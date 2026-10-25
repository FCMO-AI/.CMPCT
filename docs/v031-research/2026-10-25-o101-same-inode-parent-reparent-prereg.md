# O101 — Same-inode output-parent reparent adversarial preregistration

Date: 2026-10-25 UTC
Status: PREDICTION FROZEN BEFORE EXPERIMENT
Authority: independent scientific falsifier stacked on O99 PR #455; no O99 product-source ownership or promotion authority.

## Exact baseline / narrow question
Source `agent/phased2-v031-o99-output-parent-dirfd-custody-20261025@2fbdba24d0dfb29231c3710eb9b272a2aea89b9b`; Builder Git blob `7400d0b0c2f8bf664e7022ae499cd0ab07b18968`. Original O96 #454 proved post-scan *different-inode* ancestor symlink rebind into source with O93. O99 captures `os.stat(out.parent)` before source scan, opens the parent at publish, compares `fstat(dev,ino)`, then creates relative to that descriptor. O99 explicitly does not claim protection when **the same directory inode moves** into the source tree.

Question: does parent-inode equality alone preserve the earlier *outside-source* pathname/ancestry authorization when the originally admitted directory is reparented under source between scan and publication?

## Mechanism / predicted result
Use a genuine installed O99 Builder with one 4096-byte fixed public-source leaf. Output path `alias/archive.cmpct` resolves through a parent symlink to a unique external regular directory with inode D; archive leaf is initially absent. Original Builder performs preflight and genuine `scan()`. After scan but before publication, an independent bounded actor (1) renames the **same** external directory into the source tree and (2) atomically replaces the alias symlink to point to its new physical location. The identity `(dev,ino)` of `alias` stays D, but its real path now lies under the previously excluded root.

Prediction: O99 sees equal parent dev/ino and allows leaf creation via `openat`, the Builder returns success, the new CMPCT archive sits **inside source**, the previous original leaf is unchanged and the archive verifies/reconstructs the pre-mutation original tree. A changed-inode swap should still be rejected by unchanged O99 controls. This distinguishes physical-object custody from ancestry containment custody.

## Strong simpler controls / alternative explanations
- Stable external alias should succeed with complete verification, original unchanged.
- A different-inode post-scan symlink switch should be rejected by inherited O99 (not reimplemented or weakened here).
- Record `stat(parent)` before and after mutation, `realpath(parent)`, original source SHA, Builder result, and final tree listing so a mere pathname mismatch or failed actor cannot masquerade as a defect.
- A **different-inode** pivot cannot establish same-inode reparent failure; a bare POSIX micro-oracle cannot establish actual CMPCT behavior.

## Kill / narrowing conditions
If source mutation is refused before publication, parent identity differs, actor fails, original source content changes unexpectedly, archive fails Reader verification, or genuine installed code doesn't match source blob, the headline prediction is falsified/ambiguous. A legitimate race on POSIX is not a Windows claim; no privilege-boundary bypass or general concurrency safety claim.

## Evidence tier and economics
First derive/prove exact same-inode directory-rename mechanism in a local disposable POSIX oracle. Then, only if viable, run an installed-source-bound 2-host Ubuntu 24.04/macOS 14 GitHub Actions scientific court with three tests per host and raw JUnit/JSON artifacts. The test stages mutation entirely in disposable temporary directories and never targets real files. No compression, create-wall, RSS or official r24/ZIP promotion credit. One narrow scientific question, no product edits.

## Decision
A genuine result changes O99's integrity-scope decision and supplies its owner a distinct test for output **ancestor location** versus **parent inode**; it does not itself propose another implementation. If O99 already excludes this case by an unobserved invariant, retire this line and return to another family rather than inventing a positive claim.
