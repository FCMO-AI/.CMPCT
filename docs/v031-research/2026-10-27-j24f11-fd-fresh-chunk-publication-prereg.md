# J24F11 preregistration — descriptor-bound fresh chunk extraction publication

Date: 2026-10-27
Status: PRE-IMPLEMENTATION SCIENCE / PRODUCT CANDIDATE; not release authority.

## Exact control and collision check
Parent is J24F09 PR #552 at `20d752c8c19d700512a38bcc7026d3d9b3b72b16` (Reader blob `a6a74068b34d726fc38bc151e5f191ce2dd45993`). J24F02 #527 / issue #528 has reproduced publication of a foreign inode after indexed SHA was checked: close(fd), rename stage-name to a foreign inode, `os.replace(stage_name, destination)`. J24P02 #523 already owns the **Linux O_TMPFILE/linkat create-only primitive** for ZIP; this episode attempts its distinct productization in authentic revision-24 S_CHUNKS/S_CDC extraction on an initially absent destination, without modifying #523 or claiming existing-target overwrite protection. J24F10 #556 owns direct RAW read_range, no overlap here.

## Primary falsifiable question
On Linux filesystems supporting anonymous temporary inodes and `linkat(AT_EMPTY_PATH)`, can the real CMPCT chunk extractor write, authenticate, and publish the *same physical descriptor-held inode* in one create-only syscall with no attacker-visible stage pathname, without altering the prior destination when the final leaf is concurrently occupied?

### Prediction
For genuine Builder-independent r24 S_CHUNKS and S_CDC, Linux fresh destination: all bytes reconstructed exactly with `fd` inode equal to published inode, and **no `.cmpct-part-` pathname exists** during transfers. A concurrent same-directory adversary attempting to replace stage by pathname has no such stage. A concurrent final-leaf writer should result in `EEXIST`, preserving the foreign existing leaf and failing closed (not force-overwriting or falling back to unsafe `os.replace`). Non-Linux / unsupported O_TMPFILE preserves historical behavior explicitly; pre-existing targets preserve current replacement semantics with the acknowledged #528 vulnerability.

### Controls / disproof
Compare authentic inherited J24F09 behavior on stage substitution (negative) and candidate on absent destination, late-created leaf, initially occupied regular and symlink leaf, corruption, and directory movement (parent fd versus original path). A candidate that silently publishes the wrong inode, overwrites a concurrently inserted destination, violates SHA, leaks temporary inode, changes format bytes, or suppresses historical failure evidence is falsified. Different-root check: independent `os.stat` (dev,ino) and SHA of the target, not only Reader's return value. Test on non-root Linux CI, not only local privileged overlayfs.

## Alternatives
- More `lstat/fstat` before `os.replace`: cannot close source-name TOCTOU.
- Mode-0700 directory: does not constrain same-UID writer or privileged actor.
- Reverify target after replace: detection is after victim damage and is racy.
- O_TMPFILE unnamed fd, single `linkat` publication: strong create-only identity, but cannot atomically overwrite existing destination. Chosen as scoped reversible capability; cannot satisfy full issue #528.
- Cross-platform private atomic replacement: deferred; no portable syscall equivalent established.

## Honest costs / restrictions
Linux O_TMPFILE may be unavailable per filesystem; retain current named-stage fallback but report it as **not protected**. More syscalls/import overhead and no-clobber race semantics are added; measure complete extraction wall/CPU/RSS before promotion. Successful publication is safe only *at the link syscall*, not forever against an actor permitted to replace the final pathname or rename its parent. Symlink/hardlink ancestor rights remain separate. This research does not solve existing-target publication, Windows/macOS, malformed/mmap non-RAW paths, or all-Reader ownership.

## Promotion boundary
Research-only Draft PR, no merge/release/version/format changes. Preserve release r24, existing exact-source frozen checks, all negative evidence, and original v0.30 general suite gates. If hosted evidence fails, record failure. No experimental benefit is product release credit.
