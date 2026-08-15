# Roadmap to CMPCT 1.0

## P0 — make the prototype defensible

- Convert the monolithic Python prototype into a small reference package without changing on-disk
  semantics accidentally.
- Add golden conformance archives and byte-exact round-trip vectors.
- Add property/fuzz testing for parser bounds, corrupt indexes, corrupt blob headers, malicious paths,
  truncated generations, chunk maps, sparse extents and nested recipes.
- Make all optional accelerators genuinely optional, with clear feature discovery and fallbacks.
- Re-run the universal benchmark in reproducible CI rather than relying on one development machine.

## P0 — format completeness

- Freeze a codec/transform registry.
- Specify deterministic mode.
- Define ownership, timestamps, xattrs, ACLs, Windows metadata and path normalization precisely.
- Design authenticated encryption and key derivation; do not inherit weak legacy ZIP crypto.
- Define split-volume archives and streaming/non-seekable creation.
- Define remote HTTP/object-store range access and partial verification.

## P1 — size frontier

- Integrate a licensed, audited reversible DEFLATE preprocessor (preflate-class technique) so
  entropy-dense nested Deflate streams can be represented as plaintext + compact reconstruction data
  instead of being stored verbatim.
- Generalize reversible preprocessors for other common already-compressed structures only when they
  are demonstrably worthwhile and byte-exact.
- Improve adaptive representation selection with cheap probes so expensive codecs are not run merely
  to discover they lose.
- Explore cross-archive/global content-addressed stores as an optional layer; standalone `.cmpct`
  archives must remain self-contained by default.

## P1 — performance frontier

- Native Rust/C++ core with memory-safe parser boundaries and SIMD-friendly codec dispatch.
- Parallel create/extract/verify with deterministic ordering.
- Zero-copy mmap/range-backed reads where the stored representation permits it.
- Efficient content-defined chunking on multi-gigabyte inputs without reading entire files into RAM.

## P1 — ecosystem

- Stable CLI and library API.
- FUSE/WinFsp read-only mount before 1.0; writable mount after transactional semantics are proven.
- Native file-manager integrations where practical.
- Import/export for ZIP, tar, tar.zst and 7z where licensing/tooling permits.
- MIME/media type registration and platform file association after the 1.0 byte contract is frozen.

## Rule for new features

A new feature is accepted only if it improves a meaningful workload without causing an unexplained
regression elsewhere. Optional complexity must be capability-gated. The canonical format should stay
small, inspectable, recoverable and implementable by third parties.
