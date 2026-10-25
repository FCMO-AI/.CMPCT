# O67b prospective candidate refinement — selected-tree alias only

Date: 2026-10-25 UTC. Follow-up to the **unchanged** O67 preregistration at `280ebd050640620c4012233fbf6f6dba360c4ab5`.

## Why refinement is necessary

The exact-source original negative test has already run on [Actions #40173599150](https://github.com/FCMO-AI/.CMPCT/actions/runs/40173599150): Ubuntu 4/4 and macOS 4/4 including a physically real same-inode symlink pair and a valid archive that reconstructs two different symlink inodes. The unchanged candidate source predictably failed its fail-closed assertion on those POSIX hosts, while Windows ran 2/4 and skipped two POSIX cases. These are ORIGINAL negative measurements, not a candidate fix.

The initial O67 prospective sketch proposed rejecting any symlink with `st_nlink>1`. A new counterexample is evident from filesystem topology alone: a source tree may contain **only one** alias of a symlink inode whose other hardlink names are *outside* the selected root. That selected tree is exactly representable as one symlink, so rejecting it would needlessly restrict the supported source set.

## Narrower implementation hypothesis

Within `Builder.scan`, remember `(st_dev, st_ino) -> first selected rel` only for symlink rows reporting `st_nlink>1`. If a **second selected symlink** with the same identity appears, reject with `OSError` before archive publication. If there is just one selected alias, keep the ordinary symlink behavior, even when its global link count exceeds one. Keep regular-file `inode_first` separate: `K_HARDLINK` between regular files remains supported.

**Prediction:** fail-closed on the actual lossy two-name source; accept the legitimate one-name in-root / one-name out-of-root control; continue to accept two separately allocated same-target symlinks; preserve regular-file hardlinks and reproducible archive bytes. No new filesystem syscalls are required; worst-case extra map entries <= number of symlink rows with `st_nlink>1`. Runtime/memory cost beyond this bound is UNMEASURED.

**Kill:** if an original and a candidate succeed with incorrect alias topology; if a valid external-only alias is rejected; if regular hardlink identity changes; if Windows's provenance claims POSIX coverage; or if a recorded archive is mutated upon rejection. The existing mutable-source race (O52), unsupported platform namespace variants and full release gates remain outside this narrow claim.

This addendum is prospective for **the candidate and the new outside-root control**, and does not rewrite the original O67 prediction or its genuine source evidence.
