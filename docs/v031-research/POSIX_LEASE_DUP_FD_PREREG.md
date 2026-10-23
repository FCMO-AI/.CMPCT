# O3 — locked open-file-description ownership for journal append

Date: 2026-10-23. **Preregistered before product mutation**. Inherited candidate Writer blob `fd2aa03f37c76cce71ae92ff7d6ca460ecfd5a92`. Stronger prior results: replacement attack run 40033668963 falsified the early post-commit-only guard; exact-head descriptor check and locked-inode offset test run 40034137147 passed 10/10 on this bounded POSIX regime.

## Question and prediction
A POSIX archive-inode lock acquired through an independently opened read-only FD remains a different open-file-description from the later append FD. Even with pre-write `fstat` equality, a pathname must be reopened for append, introducing an avoidable namespace trust boundary. Can one `O_RDWR|O_APPEND` archive descriptor be acquired+locked **before the Reader snapshot**, and then `dup` that exact same open-file-description when writing each committed generation? With fully charged original footer fsync, compressed/archive bytes should be unchanged. The stronger ownership test will forbid any further archive pathname `os.open` inside `_append_generation` while still requiring a successful full physical rename. The current independent-open candidate should fail that test; the dup-based route should pass.

## Controls / kill
- Identical Builder archive, Reader hash and complete wire bytes between the original authorized source and the new source under the same deterministic update.
- Retain POSIX interprocess hardlink and symlink alias serializability, forced replacement-victim SHA, offset-rebind control, fsync-failure recovery and crashed-owner lock release.
- `flock` locks attach to open-file descriptions, not filenames; duplicating the held descriptor is structurally stronger than recreating a path-derived append FD. Linux man-pages reference: https://man7.org/linux/man-pages/man2/flock.2.html
- NFS exclusive `flock` may require write-open descriptor; `O_RDWR` addresses this prerequisite but **does not** prove NFS operation. CIFS/SMB can enforce mandatory cross-description locking; shared description may help but portability still **UNMEASURED**.
- Inherited Writer requires read and write access already, but switching the OS open flags can regress unusual permission modes. An observed case defeats promotion.
- The unlocked internal `_append_generation` helper may retain a separate path fallback; public `append_update/delete/rename` must always operate with leased FD.
- No credible fix yet for external mutation of a locked inode by uncooperative writers; durability under power failure and Windows parity not claimed.

## Evidence hierarchy
Structural proof and focused installed-package court decide whether to keep this candidate. A hosted positive does not grant full release credit, performance superiority, untrusted-namespace security or Windows/NFS compatibility. Preserve the negative A/B outcome if the initial path-reopen method is defeated as predicted; do not change comparator semantics.
