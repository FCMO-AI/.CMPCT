# O77 — Linux openat2 source-root custody: preregistration

**Date:** 2026-10-25 (UTC). **Evidence class:** research primitive/micro, not product. **Immutable baseline:** `agent/v031-development@4545d7d5b2a0b712b4b00f5a9c291d4a3a9e169b`; Builder blob `663ef0922992b1fbb8f19e6eea88d55c10a56044`; released r24 untouched.

## Scope and ownership
Issue #408 / PR #407 already proves post-stat symlink escape and FIFO hang. O52b already proves a per-component rooted `openat` control; **do not duplicate its claim or modify any Builder code**. This episode asks a different, narrower architectural/economic fork: on a Linux kernel supporting `openat2`, can ONE rooted kernel resolution eliminate path-following ambiguity and blocking special-file admission with less syscall work than component-by-component `openat`? O52 remains owner of actual Builder integration. This experiment is deliberately independent and limited to an `os.open`-equivalent regular-file source accessor, not a full source snapshot or archive builder.

## Invariants
Opened regular content must belong to an object addressed under the pinned source root at lookup; all intermediate and final symlink components are rejected; `..` escape rejected; named pipes cannot block before type rejection; exact file bytes and inode identity of static positive inputs preserved. Explicitly **not** guaranteed: snapshot immutability of an already opened inode, faithful metadata under mutation, safe access through symlinks, platform portability, all Builder paths (sparse/ZIP hardlink/xattr), source enumeration stability, atomic tree capture.

## Competing hypotheses and controls
- H1: `openat2(rootfd, relative, O_RDONLY|O_CLOEXEC|O_NONBLOCK, RESOLVE_BENEATH|RESOLVE_NO_SYMLINKS)` + `fstat` rejects final/intermediate symlinks, traversal, and FIFO without blocking, preserving ordinary nested file bytes.
- H2: a single kernel resolution materially reduces per-open syscall and wall costs on nested file trees compared with a strict `openat(dirfd, O_DIRECTORY|O_NOFOLLOW)` walk; the strong control is the same-safe rooted component walk. The weak baseline is `open(relative absolute path)` (not safety-equivalent, never credited as equal).
- Alternative explanation: latency difference may be Python/ctypes overhead, CPU cache, filesystem layout, or kernel policy cost; a single syscall is not necessarily fastest.
- Kill/narrow: any outside-root read, symlink-follow, FIFO block, fd leak, inconsistent positive byte/inode result, or unsupported kernel kills/narrows H1. If controlled depth-4+ timing does not clearly beat component walk on repeated runs, abandon an economic advantage claim and preserve only the semantics observation. Never reinterpret a primitive test as end-to-end product evidence.

## Cheapest decisive evidence
Source-independent Linux stdlib/ctypes microcourt with authentic Linux kernel syscalls and a DIFFERENT implementation of the safe component-walk control. Tests: ordinary ASCII and non-ASCII names, final and intermediate symlink to outside, traversal, nested FIFO nonblocking, and after-open same-inode mutation negative. Then paired randomized-order repeated opens at depth 1/4/8 with raw samples, syscall count model, wall/CPU costs and inode comparison. Report kernel arch, source of syscall number, exact environment, exception/error codes. `openat2` may be unavailable: mark UNSUPPORTED, do not report false green. A hosted Linux court, if dispatched, must leave run identity, source SHA, raw artifact and unearned results explicitly pending.

## Promotion boundary
Even a winning primitive cannot be promoted without real Builder integration, source-exact concurrency adversaries, all source-reading paths, full-size create/read/extract/RSS/temp I/O, macOS/Windows fallback, exact-head CI and unchanged release gates. No new format or release authorized.
