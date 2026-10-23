# v0.31 — real-r24 capability-root extraction court (2026-10-23)

**Status:** prospective independent implementation/scientific court; NOT a shipping security fix. Branch: `agent/phased3-v031-capability-root-real-archive-court-20261023`. Base: `agent/v031-development@4545d7d5b2a0b712b4b00f5a9c291d4a3a9e169b`. Source Reader expected blob `e716233403dabd0966863c45635e18fa5ac6afb8`. Existing scientific owner: PR #264, interim preflight owner #269, issue #265. Adjacent owners #255/#256/#262/#268/#270 must not be modified.

## Distinct question
Can the authentic revision-24 Builder/Reader be used to reconstruct a multi-kind filesystem tree with operations anchored to a single opened destination directory and no-follow descent, preserving exact bytes, symlink safety and hardlink inode identity under a **deterministic symlink-pivot inserted after initial inspection**? The isolated POSIX control in #264 is not enough: this court must use real archive objects, actual Reader.read and SHA checks, correct physical tree operations, and inherited content semantics.

## Prediction and disproof
1. For a valid nested ordinary member, a symlink parent inherited at start or substituted during a deterministic pre-operation hook must not cause any write to a separate external victim. The code must explicitly use directory handles and no-follow for every descendant; an exception without unchanged victim bytes/inode is not a pass.
2. Regular members must be written to exclusive fixed-length temporary names in the same pinned parent, verified by independent SHA and length **before** atomic rename. Existing leaf symlinks must not be followed. A deliberately corrupted content-hash response must preserve the existing leaf and leave no staging files.
3. Direct ordinary, multiple files, directories, safe archived relative symlinks, and hardlink owner/alias ordering must reconstruct on a clean destination with exact logical bytes and hardlink inode identity. Hardlink aliases must resolve to a pinned regular owner, not a symlink.
4. Non-POSIX environments and unavailable `O_NOFOLLOW`/`dir_fd` must refuse the strict experimental route, never silently fall back to vulnerable path semantics.
5. Any filesystem source-format kind not safely accounted (sparse/large/metadata) must be explicitly outside claim or rejected. No format, Reader/Builder, release-gate, benchmark or competitor change.

## Alternatives
- Static pathname `lstat` preflight: already implemented by owner #269, and independently falsified against concurrent swaps.
- Atomic leaf only: CDC scientific court in #264 proves parent pivots remain.
- Linux `openat2` via syscall: strong beneath resolution but unnecessary ABI/platform complexity for this cheap rung; test descriptor-relative Python primitives first. No promise of immobility when an attacker can rename the underlying opened directory inode itself.

## Evidence and economics
Smallest decisive rung: genuine package Builder/Reader + distinct POSIX fd-walker + hostile TemporaryDirectory filesystem tests, with source pinning, no external files touched and raw failure output. Trace memory: direct `Reader.read` candidate may materialize a full member, so enforce a strict `max_member_bytes` budget; this is NOT a constant-memory extraction claim. Account for path walk/open/close syscalls, staging I/O and SHA; do not claim performance or full-platform readiness from green tests. Full CI, memory, large sparse, hostile concurrent rename, xattr, native and portability evaluations remain promotion debt.

## Coordination
Do not update shared `docs/discovery/STATE.json`: this is a separate bounded implementation question and older cache is stale relative to hosted #236/#239/#242 evidence. Stay in this branch, deliver independent scientific evidence/negative. If another branch takes ownership of rooted extraction, coordinate on issue #265 and avoid parallel product writes.