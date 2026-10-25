# O118 — Reader extraction source-archive inode alias (prospective preregistration)

Date: 2026-10-25  
Status: FROZEN BEFORE IMPLEMENTATION / RESULT UNMEASURED  
Base: `agent/v031-development@4545d7d5b2a0b712b4b00f5a9c291d4a3a9e169b`; Reader blob `e716233403dabd0966863c45635e18fa5ac6afb8`. Released v0.30.0 / physical revision 24 unchanged.

## Baseline, distinct ownership and question

The original `CMPCT.extractall(dest)` opens regular destinations with `O_TRUNC`, and unlinks destination leaves when installing symlinks/hardlinks, but does not compare these objects to its **own still-open archive inode**. Suppose a valid archive contains a member `payload.bin` and the physical archive is itself named `<dest>/payload.bin`, or that destination is a hardlink/symlink to the archive. Does extraction destroy its *own input* (or make its mapped reader unsafe) rather than refuse the non-reconstructible operation? This is endogenous extractor-to-archive aliasing, distinct from external same-inode truncation in O103/#459, generic external hardlink destination safety in #294, static symlink pivots in #269, or source/archive replacement during a separate writer transaction.

## Prediction and falsifier

Predict **baseline failure**: the archive bytes change, the open Reader loses availability, or extraction partially destroys its own input. Strong no-harm control: extraction to a disjoint clean destination must preserve the source archive SHA-256 and reproduce the member exactly.

Predict a surgical fail-closed guard can refuse *preexisting static* destination aliases of the archive's `fstat` inode before any mutations. A candidate succeeds only if the archived input remains byte-identical, refusal is explicit (not a fatal process signal/hang), regular disjoint outputs still reconstruct, and both direct and symlink/hardlink static aliases are detected. Any lost accepted archive bytes, false refusal on clean output, or source mutation falsifies the candidate. Check sparse/chunked/direct storage, and a symlink member replacing the archive pathname when practical.

## Controls and alternatives

- Baseline: original source, same physical archive, separate disposable subprocess to contain mmap fatal faults and prevent parent hangs.
- Stronger simple control: copy archive to disjoint immutable location before extraction; this avoids source aliasing but incurs archive-sized storage/I/O and weakens the usability objective.
- Naive lexical path comparison misses hardlinks, symlinked destinations and archive symlink path identities.
- A pre-write physical `fstat` comparison after `O_TRUNC` is too late.
- Snapshot/atomic-replace extraction requires a separate product-architecture evaluation, not assumed as a free fix.
- A pre-write static `stat` scan cannot guarantee safety against actively racing directory renames/symlink substitutions; do not claim it does.

## Cheapest evidence and cost obligations

First construct one valid authentic Builder archive, three static destination conditions (same path, hardlink, symlink), and a clean control. Bind the source SHA-256 and check output and process exit in disposable children. Then test a minimal static guard without altering Reader codec/parser/recovery/format. Charge any extra per-file filesystem `stat` work and indicate that large-tree build/extraction benchmarks remain owed; inspect whether an inode-bound write-open redesign would be more cost-effective for a later release.

## Scope, concurrency and decision rule

Own only the *source archive vs destination leaf physical identity* rule, initially for static POSIX filesystems. No edits to #269/#294/#297/#459 or their assertions; notify their owners if a result changes shared extraction architecture. The candidate is not a hostile concurrent filesystem custody guarantee or a full release. Preserve any negative and expose exact-source CI evidence; no merged source/format/frozen benchmark/threshold modification authorized by this preregistration.
