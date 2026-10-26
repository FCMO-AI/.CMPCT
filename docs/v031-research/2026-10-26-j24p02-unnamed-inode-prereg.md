# J24P02 — Linux unnamed-inode final publication: prospective scoped oracle

Status: PREREGISTERED / result-bearing implementation NOT YET WRITTEN
Date (UTC): 2026-10-26
Owner: independent CMPCT Phased2 research lane; do not alter O179/O181 owner branches.

## Current authority, provenance and collision avoidance

- Released checkpoint is v0.30.0, physical format revision 24; this branch is scientific evidence only.
- Inherited source: O181 negative court PR #514 exact `8b0735912eb6c8062b483ac9279c956294fbac3b`, layered on O179 PR #512. O181 proves a writable-directory actor can substitute a ZIP stage name after the Reader's final identity check, yielding success with unauthenticated output. This prospective experiment does **not** rerun that same negative claim or modify `src/cmpct/reader.py`.
- PR #367 mentions `O_TMPFILE`/`linkat` for a different CDC source-mutation question. No open PR found claiming **Linux ZIP absent-destination descriptor-bound publication**. These claims are limited to one new branch and research instrument.
- Repository `docs/discovery/CONCURRENCY_PROTOCOL.md` and `tools/discovery_claims.py` were not found at the source inspected. Do not assume a missing lock is present. Recheck open PRs/target files before any later shared mutation.
- Linux man-pages primary contracts: https://man7.org/linux/man-pages/man2/open.2.html and https://man7.org/linux/man-pages/man2/linkat.2.html.

## Honest exploratory observation BEFORE preregistration

A local exploratory probe on Debian Linux kernel 6.18 overlayfs, running with root privileges, opened `O_TMPFILE|O_RDWR` and successfully made an unnamed ZIP inode visible with `linkat(..., AT_EMPTY_PATH)`. This is an already-seen feasibility hint, **not** a prospective result or unprivileged/hosted acceptance. No tests or thresholds below are tuned to that outcome.

## Primary question

On a genuine unprivileged Linux GitHub Actions Ubuntu 24.04 runner, can an already-populated **unnamed** regular inode be installed **only when the destination name is absent** by a single kernel `linkat` operation with the file-descriptor source, preserving physical inode/complete ZIP bytes, while any preexisting conflicting name (regular, symlink, hardlink, or competing new entry) causes failure rather than a misleading successful export?

This is an explicitly **create-only / no-clobber** capability experiment. It does not solve POSIX/Windows atomic **replacement** of an existing archive and does not claim full CMPCT product safety.

## Mechanism and strongest controls

- Candidate: `open(output-dir, O_TMPFILE|O_RDWR)` without `O_EXCL`; populate and fsync the descriptor; `linkat(fd, "", dirfd, output_leaf, AT_EMPTY_PATH)`. If `AT_EMPTY_PATH` is unavailable for unprivileged callers and procfs is mounted, use the documented `/proc/self/fd/<fd>` + `AT_SYMLINK_FOLLOW` equivalent, reporting the specific route, not pretending the first route succeeded.
- `dirfd` is opened before staging and passed to `linkat` to bind the **directory inode**, not an attacker-controlled ancestor path. This does not guarantee the directory's original pathname remains stable if renamed.
- Strong simpler controls: direct `open(output, O_CREAT|O_EXCL)` rejects existing outputs but exposes partial bytes to observers; existing O179 named-stage + `os.replace` supports overwrite but has O181 postcheck substitution. The candidate is valuable only if it demonstrates a genuinely narrower atomic creation semantic.
- Never silently fall back to unsafe publication. Unsupported filesystem/kernel/procfs access is a *capability unavailable* result, not a successful security test.

## Frozen case matrix and prospective decision

On Linux only, stdlib ZIP bytes containing `raw.bin` with 64 deterministic bytes:
1. ABSENT: before publish, target does not exist; after publish, regular target (same `st_dev/st_ino` as original fd), complete ZIP SHA and decoded `raw.bin` match, no stage path existed.
2. REGULAR_OCCUPIED: sentinel destination is preserved byte-for-byte and by inode; `linkat` fails with `EEXIST`.
3. SYMLINK_OCCUPIED: destination symlink target and unrelated victim bytes/identity unchanged; `linkat` fails with `EEXIST`.
4. HARDLINK_OCCUPIED: destination is alias of unrelated victim; victim and alias bytes/inode unchanged; `linkat` fails with `EEXIST`.
5. LATE_CREATION: adversarial same-directory actor creates a fully valid alternate ZIP immediately before publication; `linkat` fails with `EEXIST`, never publishes the candidate and never mutates attacker bytes.
6. UNSUPPORTED: strictly classify unsupported `O_TMPFILE`, no procfs fallback, or missing privilege as **UNSUPPORTED**, never PASS. Do not silently skip a required case and declare the claim proven.
7. BOUNDARY_CONTROL: using a parent `dirfd` retains the original **directory-inode** placement after a controlled *rename of the parent path* (when the local filesystem permits it), and proves that the pathname expected by the caller may consequently be stale. This is a deliberately negative delimitation, not a failure of source-inode binding.

Target scientific result: 5/5 specified absent/occupied cases verified on unprivileged hosted Ubuntu plus a completed boundary control. Fail/narrow if `linkat` overwrites any occupied destination, creates the wrong inode, publishes partial ZIP, accepts a symlink/hardlink victim substitution, or cannot operate unprivileged on the designated runner. A PASS is a **Linux scoped primitive**, not product merge evidence.

## Exported costs and omitted product proof

Exact ZIP member bytes, full stored ZIP bytes, inode, parent inode, error classification and publication visibility are measured. CPU/wall, fsync latency, durability across power failure, RSS, encryption, arbitrary output replacement, remote mounts, Windows/macOS portability, POSIX ACL preservation, same-UID fd/proc introspection attacks, and directory ancestry path stability are **not** established by this rung. The candidate may require additional syscalls, a procfs dependency, and a new explicit no-clobber public API. No product code is modified.

## Counterfactual decision

If the scoped result survives, refer it to O179/O181 owners only as an **exact no-overwrite option**. It cannot substitute for arbitrary replacement and must not be merged as a general ZIP export fix. If unprivileged Linux lacks the necessary syscall path, retire this route for portable CMPCT without repeated privilege gardening.

No version, release, benchmark threshold, comparator, historical evidence, discovery policy, or canonical `STATE.json` change is authorized.
