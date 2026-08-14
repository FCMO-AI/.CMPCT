# CMPCT current development state

This document is the **zero-chat-history handoff** for a new agent. Read it together with:

- `README.md` — project mission and quick start;
- `AGENTS.md` — mandatory development behavior;
- `docs/FORMAT.md` — current revision-24 on-disk contract;
- `docs/HISTORY.md` — full surviving development/version history;
- `docs/BENCHMARKS.md` and `benchmarks/history/` — benchmark discipline and raw historical records;
- `docs/PORTABILITY.md` — ZIP-parity UX and first-class Android/desktop integration contract;
- `docs/NATIVE_CORE.md` — current shared native reader/ABI capability and next representation gates;
- `docs/ROADMAP.md` — work required before a defensible 1.0.

## Project objective

CMPCT is intended to become a **general-purpose lossless archive/container format and engine** for arbitrary computer files and filesystems. The target is not merely “smaller ZIP.” The target is a default archive choice with strong size, creation/extraction speed, random access, integrity, crash-safe updates, recovery, filesystem fidelity, remote-read potential, codec agility, and ordinary end-user portability.

Hermes is one useful regression corpus because it mixes source, wheels, nested ZIPs, PCM audio, metadata and duplicates. **Hermes must never define the format or encoder policy.**

## Canonical authority

Repository: `FCMO-AI/.CMPCT`

Branch: `main`

Current canonical revision: **format revision 24 / project v0.24**

Canonical baseline commit: `f59ee8d14ef065e3fedfb032e38a954eea1ff965`

Everything created outside this repository is experimental until reconciled back into `main` with documentation/tests/benchmarks.

## Current implementation architecture

`src/cmpct/codec.py`
: Codec and representation primitives, Zstd/Deflate/FLAC handling, content-defined chunking interface, exact nested-ZIP reconstruction helpers and integrity primitives.

`src/cmpct/builder.py`
: Filesystem scan, candidate/representation selection, deduplication, dictionaries/microblocks, sparse/link handling and physical archive construction.

`src/cmpct/reader.py`
: Archive parsing, index recovery, logical reads, range reads, extraction, verification and salvage-oriented behavior.

`src/cmpct/transactions.py`
: Append generations, mutation journal, rename/delete/update behavior, checkpoints and commit-footer semantics.

`src/cmpct/cli.py`
: User-facing commands including create/info/list/read/range/extract/verify/export-zip/recovery-related operations.

`native/cmpct_cdc.c`
: Optional creation-time content-defined chunk boundary accelerator. The reader does not require it because boundaries are explicit in the archive.

`native/cmpct-core/`
: Memory-safe Rust read-only core. It authenticates and decodes the revision-24 primary index, applies the shared lexical path policy, enumerates logical entries, bounds the base blob table, and exposes an opaque C ABI. The member-access surface reads genuinely range-local slices from direct RAW members and bounded ranges from ordinary direct Zstd members; Zstd currently decodes and SHA-256-authenticates at most one capped direct member before returning the requested slice. CI cross-checks entry enumeration plus RAW/Zstd range bytes against the Python oracle and exercises the shared library from a non-Rust caller. Deflate/dictionary/WAV-FLAC direct blobs, chunked/sparse/virtual member access, sequential streams, journal recovery and full structural preflight parity remain unfinished.

`benchmarks/universal_bench.py`
: Heterogeneous synthetic benchmark harness. Generated corpora/output are not canonical history; durable historical result records belong under `benchmarks/history/`.

`benchmarks/zip_parity_bench.py`
: Fair CMPCT-vs-ZIP regression harness that separates library-to-library timing from fresh-process CLI timing. It exists specifically to expose ZIP advantages without conflating them with benchmark orchestration overhead.

`docs/PORTABILITY.md`
: First-class archive integration contract for Android, Linux, Windows and Apple platforms. It is a release requirement, not a claim that those integrations already ship.

`docs/NATIVE_CORE.md`
: Durable handoff for the shared memory-safe reader and C ABI, including integrity/resource boundaries and the required representation-by-representation conformance order.

## Current format capabilities

Revision 24 currently supports or prototypes:

- logical filesystem entries separated from physical content blobs;
- content-addressed duplicate elimination;
- adaptive RAW/Zstandard/Deflate/WAV-FLAC/Zstd-dictionary representations;
- micro-solid packs for forests of tiny files;
- fixed and content-defined chunk maps for large files;
- byte-range reads without decoding unrelated archive regions;
- sparse extents;
- hardlinks and symlinks;
- UID/GID and extended attributes where available;
- exact reconstruction recipes for profitable nested ZIP/WHL cases;
- direct reuse of exact raw Deflate streams;
- mmap-friendly immutable read paths;
- CRC32 hot-path corruption checks;
- SHA-256 strong identity/verification;
- redundant head/tail indexes plus self-describing blob records;
- transactional append generations and prior-generation fallback;
- ZIP export, including reuse of stored Deflate streams when possible.

## Design invariants

These are more important than current encoder thresholds:

1. **Byte-exact losslessness.** Extraction must reproduce file bytes exactly unless a caller explicitly requests a semantic rather than byte-preserving transform.
2. **Reader simplicity over encoder heuristics.** The archive records enough information that future readers do not need to reproduce historical encoder decisions.
3. **Content-driven representation.** Extensions may guide cheap probing but must never dictate the codec if the bytes show a worse result.
4. **Graceful incompressible case.** CMPCT should approach input size + small metadata rather than expand already-compressed/encrypted/random data badly.
5. **Independent access.** Compression improvements must not silently turn the archive into a monolithic stream that makes one-file/range access expensive.
6. **Filesystem fidelity.** Links, sparse holes and metadata are semantics, not duplicate payload bytes.
7. **Crash safety.** A completed mutation must have a clear commit marker; incomplete tails must not destroy the last committed generation.
8. **Recovery as a format property.** Critical metadata should have redundancy/scannability rather than relying on one irreplaceable central directory.
9. **Codec agility.** Zstd is the general codec, not the definition of CMPCT.
10. **No corpus overfitting.** Any threshold change needs at least one adversarial corpus where it could plausibly lose.
11. **ZIP parity is a floor, not a benchmark trick.** A fair reproducible ZIP advantage in size, equivalent-semantics speed, selective access or usability is an engineering gap until evidence justifies otherwise.
12. **Portability is part of the format product.** A technically superior archive that users cannot tap/double-click, browse or extract on ordinary systems is not yet a viable default replacement.

## What is proven enough to use as a development baseline

The current Python reference implementation is able to create/read revision-24 archives and has smoke-tested round trips, range access, links/sparse behavior and CLI opening. Historical experiments also demonstrated the architectural feasibility of exact nested ZIP reconstruction, strong random access, transactional recovery and fast ZIP export.

The fair ZIP-parity harness additionally demonstrates an important measurement rule: library-vs-library and process-start/CLI timing must remain separate. Early mixed-layer measurements overstated several ZIP speed advantages because CMPCT paid fresh-Python startup while ZIP ran inside an already-started benchmark process. Genuine remaining losses must be fixed, not hidden behind that correction. The first five-repeat RAW-chunk extraction optimization reduced the remaining large-binary library extraction result from about 63.8 ms to 55.5 ms while ZIP measured 48.6 ms on the new shared-runner campaign; the ~14% residual is still an active parity defect, not a declared tradeoff.

The native core now proves two end-to-end selective-content paths across the C ABI: a non-Rust caller can open a Python-built revision-24 archive and read an arbitrary bounded slice from an incompressible direct RAW member or an ordinary direct Zstd member, with the bytes checked against the Python oracle. RAW reads remain range-local. Direct Zstd reads are capped at 256 MiB and authenticate exact decompressed length plus SHA-256 before returning bytes. This is a portability/conformance milestone, not yet a claim of representation-complete native reading.

Treat those as **reference behavior**, not yet as a frozen interoperability standard.

## What is NOT yet production-grade or 1.0-ready

A new agent should not mistake prototype breadth for completion. Major open areas include:

- normative byte-level format specification and complete index schema;
- conformance/golden archives and stable cross-version vectors;
- parser fuzzing/property testing and strict resource/bounds limits;
- deterministic archive mode;
- formal codec/transform registry and capability negotiation;
- authenticated encryption and key derivation;
- complete ACL/Windows/macOS metadata/path normalization rules;
- split-volume and streaming/non-seekable creation;
- remote HTTP/object-store range access with partial verification;
- native memory-safe high-performance core beyond authenticated primary-index enumeration and direct RAW/Zstd range reads: complete structural validation, committed-generation recovery, Deflate/dictionary/WAV-FLAC codecs, chunked/sparse/virtual member access, sequential streams, extraction and verification remain unfinished;
- scalable CDC without whole-file memory loading;
- robust Android/Linux/Windows/Apple archive browsing, file association and mount/file-manager integrations defined by `docs/PORTABILITY.md`;
- reversible preprocessing for already-compressed structures where licensing and exactness permit;
- CI that reruns the universal benchmark on controlled hardware/software and archives raw results.

## Current benchmark interpretation

Historical measurements show that the architecture can outperform ordinary Deflate ZIP dramatically on some workloads and narrowly on hostile already-compressed ones. They do **not** prove universal dominance.

The current benchmark policy is:

- commit the exact benchmark harness/version;
- commit machine-readable results under `benchmarks/history/`;
- record semantics (durability, metadata restoration, warm/cold cache, process startup, integrity work);
- preserve losing cases;
- never compare a richer CMPCT operation against a weaker ZIP operation without saying so;
- never compare fresh-process CMPCT against in-process ZIP as if it were one timing layer;
- never use one Hermes number as a general format claim.

See `docs/HISTORY.md` and `benchmarks/history/2026-08-13-development-campaign.json` for the complete surviving first-campaign measurements.

## Immediate high-value development missions

### Mission 1 — conformance and hostile-parser foundation

Create golden revision-24 archives and byte-exact vectors for every storage description/codec. Add fuzz/property tests for corrupt headers, indexes, blob sizes, chunk maps, sparse extents, nested recipes, journal generations, path traversal and decompression-bomb/resource limits. This is the most important prerequisite before increasing format complexity.

### Mission 2 — benchmark CI and reproducible result archive

Run the universal corpus in controlled CI. Record CPU, OS, filesystem, Python/native library versions, cache state, codec settings, durability and metadata semantics. Commit every accepted benchmark dataset under `benchmarks/history/` with the commit SHA that produced it. Keep `benchmarks/zip_parity_bench.py` as the explicit gate for every fair ZIP advantage.

### Mission 3 — deterministic mode and normative schema

Turn revision 24’s working format document into a byte-level interoperable contract: canonical integer encodings, ordering, path normalization, endianness, bounds, index schemas and deterministic creation rules.

### Mission 4 — native core

Continue the memory-safe Rust core now present under `native/cmpct-core/` while keeping Python as the readable executable specification and cross-check oracle. The current native slice authenticates/decodes the primary index, applies lexical path policy, enumerates entries, bounds base blobs, exposes a tested C ABI, reads direct RAW ranges without decoding unrelated data, and reads bounded ordinary direct-Zstd ranges with whole-member SHA-256 authentication. Next add direct Deflate, then fixed/CDC chunk maps so compressed large-file ranges become range-local, followed by sparse maps, dictionary/WAV-FLAC direct blobs and virtual ZIPs; then sequential member streams, committed-generation recovery and extraction. Native code must remain conformance-identical, and the same core must expose the list/stat/read/range/stream/extract surface required by platform handlers so portability does not fork format semantics.

### Mission 5 — size frontier without random-access regression

Investigate reversible preprocessing for Deflate and other common compressed structures, but only with licensed/audited techniques and exact reconstruction. Also improve cheap candidate probing so expensive codecs are not run just to discover that RAW or ordinary Zstd wins.

### Mission 6 — erase practical ZIP advantages and ship first-class archive UX

Treat stable fair ZIP wins as performance defects. Prioritize creation/extraction hot paths, startup/import overhead, fused validation and native read-only startup until ZIP has no unexplained material advantage on the parity corpus. In parallel, implement the `docs/PORTABILITY.md` contract: Android DocumentsProvider/app integration, Linux MIME/browser integration, Windows file association/browser support, and Apple UTType/document integration, all backed by the shared native core. Do not claim platform support until the corresponding package passes conformance archives on that platform/emulator.

## Known historical traps

Do not reintroduce these without new evidence:

- fixed 256 KiB frames for every file;
- TAR as the canonical internal archive;
- forcing every file through Zstd;
- always using FLAC for WAV/PCM;
- always virtualizing nested archives;
- duplicating SHA-256 in multiple indexes;
- mandatory libdeflate/native helpers;
- SHA-256 on every ordinary read;
- ZIP physical layout as permanent canonical-storage overhead;
- benchmark optimizations that only help Hermes;
- a permanent hidden ZIP shadow inside every CMPCT archive merely to gain legacy file-manager recognition.

## When to bump the format revision

Bump the on-disk revision when a reader must understand a new physical field/record/storage-description/codec semantic to read newly created archives. Encoder-only heuristic changes that still emit the exact same revision-24 grammar do **not** require a format revision, but they do require benchmark/regression documentation.

Any format bump must update, in the same commit:

- `docs/FORMAT.md`;
- `docs/HISTORY.md`;
- this file;
- conformance vectors/tests;
- benchmark record if performance/size claims are involved.

## Definition of a good next agent

A good next agent should be comfortable saying **“this new idea loses on corpus X, so I am not merging it”**. CMPCT’s goal is not to accumulate clever codecs. It is to become the strongest boring default: small, fast, random-accessible, faithful, recoverable, secure, portable, independently implementable, and ordinary to open on the devices people actually use.
