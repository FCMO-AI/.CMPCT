# J24G42 — Darwin hidden compression xattr visibility O0 (prospective preregistration)

Date: 2026-10-29 UTC. Research-only, independent scientific probe; no product mutation, format/version/release credit, and no change to #757 owner.

## Starting authority and collision check
- Independent basis: #757 J24G41 exact source HEAD `911e66053bd997ad0c85895cf61da02f9ce06625`, stacked on O72 #428, v0.30.0/r24 released `main`.
- Current #757 physical native-xattr court establishes ordinary binary/empty file xattrs; it does *not* establish macOS filesystem-compression metadata fidelity. No open PR found for `XATTR_SHOWCOMPRESSION` / `com.apple.decmpfs` as of this preregistration.
- The exact child branch owns only a read-only research script/workflow/doc. It does not edit native adapter, Builder, Reader, frozen tests or shared discovery STATE.

## Primary question
On a **real** Apple system-volume compressed regular file with OS `UF_COMPRESSED` flag, do standard Darwin `listxattr` options hide `com.apple.decmpfs` / `com.apple.ResourceFork` that `XATTR_SHOWCOMPRESSION` can reveal? If yes, the existing native `_xattrs.listxattr(..., follow_symlinks=False)` is not a complete *physical-metadata* enumerator even though J24G41 correctly preserves ordinary explicitly writable xattrs. That does not imply logical-file-byte loss or authorize blindly applying compression attributes during extraction.

## Why this is worth one cheap rung
Apple's later `listxattr(2)` man-page documents `XATTR_SHOWCOMPRESSION` as exposing HFS+ compression extended attributes. J24G41's native bridge requests only `XATTR_NOFOLLOW` (0x0001), never the special visibility flag (0x0020). Mature libarchive has explicit special handling of `com.apple.decmpfs`, indicating this metadata has nonordinary restore semantics.
Strongest simpler control: the existing #757 ordinary binary-file xattr preservation; prospective false explanation: compressed metadata could be intrinsically hidden/unreadable on current APFS or runners may have no accessible compressed files.

## Frozen disproof / classification
- Enumerate **only public system binaries/libraries**, not user or private files, with bounded path count/time; independently identify compressed regular files via `stat.UF_COMPRESSED` (or documented 0x20); do not mutate them.
- Query the same inode with native `listxattr(path, options=XATTR_NOFOLLOW)` and `listxattr(path, options=XATTR_NOFOLLOW|XATTR_SHOWCOMPRESSION)`. Keep errno, flags and raw counts; compare native default listing with the installed #757 provider only when possible.
- Use a separate, synthetic local noncompressed file with a writable binary xattr as positive control of native flag handling. No shelling out in production; research may use native OS helpers.
- **VISIBILITY_GAP_POSITIVE** only if an actually stat-flagged compressed regular file shows a compression-related name exclusively with SHOWCOMPRESSION. **NO_GAP_OBSERVED** only if enough accessible compressed files are examined with both options and none differs; distinguish lack of evidence from impossibility. **INCONCLUSIVE** on unavailable APIs, no accessible compressed files, or ambiguous permission failures.
- Never create, write, remove or set attributes on Apple system files. SHA-256 of content is unnecessary to test enumeration and would export I/O cost.
- Save raw JSON, system/ABI identity, source HEAD, test assertions. A green workflow with INCONCLUSIVE is **not** positive scientific evidence.

## Outcome decision and limits
A positive narrows the **metadata-fidelity claim**, not the existing J24G41 ordinary-xattr product proof. Do not invent a product fix: preserving OS-managed transparent-compression state and a decompressed file may be unsafe, nonportable and format-specific. Need a separately preregistered charged product/semantic question before implementation. Negative narrows only current host/sample. Neither earns release/benchmark credit.
