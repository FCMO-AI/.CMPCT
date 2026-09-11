# ONE Genesis candidate exact-tree semantics preregistration — 2026-09-10

**Mission Lock / Referee:** prevent a complete-archive candidate from claiming exact reconstruction after checking only regular-file bytes and path names.

## Defect found by hostile review

The CMPCT1 product worker's whole-read path currently verifies every regular file digest and that the archive path universe equals the source path universe, then emits `exact: true`. It does not independently compare entry kind, POSIX mode, or symlink target. A malformed writer/reader pair could therefore preserve names and file bytes while changing a directory/file/symlink kind, mode, or symlink destination and still receive an exactness claim.

No Genesis workload needs to be executed to expose or repair this defect.

## Falsifiable hypothesis

If the fresh-process whole-read worker builds an independent semantic manifest from `lstat`/`readlink` on the executor-owned input and compares it to the opened archive manifest before emitting `exact: true`, then path/type/mode/symlink drift cannot be silently accepted.

## Required semantics

For every path under the supplied tree:

- path identity is canonical and identical;
- entry kind is identical (`file`, `dir`, `symlink`);
- POSIX permission mode is identical;
- symlink target is identical without following the link;
- regular-file length and SHA-256 are identical;
- regular-file reconstructed bytes remain independently SHA-256 checked.

The comparison must ignore compression/authentication implementation metadata such as root IDs and AuthTree serialization because those are representation state, not source-tree semantics.

## Disproof tests

Reject the change if any of these can still emit `exact: true`:

1. archive entry mode differs from source;
2. archive symlink target differs from source;
3. archive entry kind differs from source;
4. archive has an extra/missing path;
5. regular-file content differs;
6. transfer-fixture operation becomes production evidence;
7. Genesis inputs, comparisons, scoring, or winner selection are executed during the repair.

## Acceptance boundary

This hardening proves only that the ONE worker can validate the source-tree semantics it claims to preserve on transfer/synthetic trees. It does not certify the general ONE product boundary and does not establish parity with historical comparator metadata semantics; those remain gate evidence questions.
