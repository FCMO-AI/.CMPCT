# CMPCT native core

This crate is the first memory-safe native implementation slice for CMPCT revision 24. It exists to
replace CPython startup/parsing in platform handlers and to keep Android, Linux, Windows and Apple
integrations on one parser/ABI rather than four divergent format implementations.

## Implemented in this slice

- open a revision-24 archive from a filesystem path;
- bound primary-index compressed/uncompressed allocation to the same 256 MiB policy ceiling used by
  the Python hardening layer;
- verify header magic/revision, base archive bounds, decompressed index length and index SHA-256;
- decode the MessagePack root index;
- enumerate logical entries with path, kind, mode, mtime and size;
- reject traversal, empty/dot components and cross-separator path aliases with the same lexical rule as
  the Python oracle;
- parse and bound the base blob table against the authenticated base-data span;
- read bounded byte ranges from direct RAW members without materializing the rest of the member;
- cross-check the physical RAW blob frame against authenticated index metadata before returning payload
  bytes;
- expose an opaque C ABI for open/close/revision/count/entry metadata/path and direct-RAW range reads;
- cross-check the native view and RAW range bytes against a Python-built archive in CI, including a
  ctypes caller that uses the produced shared library rather than Rust internals.

## Range-read integrity semantics

A partial RAW range read validates the authenticated primary index, logical bounds, blob-table bounds,
and physical blob framing before reading the requested bytes. It deliberately does **not** claim to
verify the whole blob CRC32 or SHA-256 when only a slice was requested. That matches the selective-read
semantics of the Python RAW fast path; strong whole-file verification remains a separate operation until
the format has authenticated chunk/range proofs.

Representations not yet ported return a typed `Unsupported` status instead of silently materializing or
falling back through Python. Out-of-bounds requests return a typed range status.

## CI acceptance gates

A native-core change is not ready merely because it compiles. The permanent CI gate requires Rust
formatting, clippy with warnings denied, unit tests, a release build, exact entry-view comparison against
a revision-24 archive created by the Python oracle, and a non-Rust ctypes caller opening/enumerating the
produced shared library. Member/range APIs extend those cross-language gates rather than replacing them
with native-only tests.

`Cargo.lock` is committed intentionally. The native handler is becoming a reproducible platform/runtime
component, so conformance CI must not silently resolve a different dependency graph from one run to the
next merely because a transitive crate published a newer compatible release.

## Deliberately not claimed yet

This is **not yet the shipping archive handler**. It does not yet implement tail/journal recovery,
complete structural reference validation, Zstd/Deflate/dictionary/WAV-FLAC decoding, chunked/CDC/sparse
or virtual-container member access, sequential member streams, extraction, verify, remote range sources
or mutation. Those capabilities must be ported incrementally with golden archives and Python-oracle
cross-checks before platform packages depend on them.

The current `open` result is therefore an **authenticated primary-index view with a narrowly validated
RAW read path**, not the final hostile-archive trust decision. Production handlers must not expose
unvalidated storage kinds or bypass the core to parse archive-controlled structures themselves.

The next ABI milestone is representation-complete read-only member access: `list_children`, `stat`,
bounded `read_range` across chunked/compressed storage, and a sequential member stream. Blob decoding
must preserve revision-24 codec fallback semantics and hostile resource limits; platform code must not
bypass the core and parse archive internals itself.
