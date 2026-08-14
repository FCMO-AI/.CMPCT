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
- expose an opaque C ABI for open/close/revision/count/entry metadata/path;
- cross-check the native view against a Python-built archive in CI, including a ctypes caller that uses
  the produced shared library rather than Rust internals.

## CI acceptance gates

A native-core change is not ready merely because it compiles. The permanent CI gate requires Rust
formatting, clippy with warnings denied, unit tests, a release build, exact entry-view comparison against
a revision-24 archive created by the Python oracle, and a non-Rust ctypes caller opening/enumerating the
produced shared library. Future member/range APIs must extend these cross-language gates rather than
replacing them with native-only tests.

`Cargo.lock` is committed intentionally. The native handler is becoming a reproducible platform/runtime
component, so conformance CI must not silently resolve a different dependency graph from one run to the
next merely because a transitive crate published a newer compatible release.

## Deliberately not claimed yet

This is **not yet the shipping archive handler**. It does not yet implement tail/journal recovery,
complete structural reference validation, blob decoding, member/range streaming, extraction, verify,
remote range sources or mutation. Those capabilities must be ported incrementally with golden archives
and Python-oracle cross-checks before platform packages depend on them.

The current `open` result is therefore an **authenticated primary-index view**, not the final hostile-
archive trust decision. A platform shell/browser may use it for development and conformance work, but
production handlers must not expose archive-controlled blob/storage references until the native core
also validates those references and recovery semantics to the same or stronger policy as Python
`preflight_archive`.

The next ABI milestone is read-only member access: `list_children`, `stat`, bounded `read_range` and a
sequential member stream. Blob decoding must preserve revision-24 codec fallback semantics and hostile
resource limits; platform code must not bypass the core and parse archive internals itself.
