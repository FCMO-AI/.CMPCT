# CMPCT current development state

This document is the **zero-chat-history handoff** for a new agent. Read it together with:

- `README.md` — project mission and quick start;
- `AGENTS.md` — mandatory development behavior;
- `docs/FORMAT.md` — current revision-24 on-disk contract;
- `docs/HISTORY.md` — full surviving development/version history;
- `docs/BENCHMARKS.md` and `benchmarks/history/` — benchmark discipline and raw historical records;
- `docs/ROADMAP.md` — work required before a defensible 1.0.

## Project objective

CMPCT is intended to become a **general-purpose lossless archive/container format and engine** for arbitrary computer files and filesystems. The target is not merely “smaller ZIP.” The target is a default archive choice with strong size, creation/extraction speed, random access, integrity, crash-safe updates, recovery, filesystem fidelity, remote-read potential, and codec agility.

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

`benchmarks/universal_bench.py`
: Heterogeneous synthetic benchmark harness. Generated corpora/output are not canonical history; durable historical result records belong under `benchmarks/history/`.

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

## What is proven enough to use as a development baseline

The current Python reference implementation is able to create/read revision-24 archives and has smoke-tested round trips, range access, links/sparse behavior and CLI opening. Historical experiments also demonstrated the architectural feasibility of exact nested ZIP reconstruction, strong random access, transactional recovery and fast ZIP export.

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
- native memory-safe high-performance core;
- scalable CDC without whole-file memory loading;
- robust mount/file-manager integrations;
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
- never use one Hermes number as a general format claim.

See `docs/HISTORY.md` and `benchmarks/history/2026-08-13-development-campaign.json` for the complete surviving first-campaign measurements.

## Immediate high-value development missions

### Mission 1 — conformance and hostile-parser foundation

Create golden revision-24 archives and byte-exact vectors for every storage description/codec. Add fuzz/property tests for corrupt headers, indexes, blob sizes, chunk maps, sparse extents, nested recipes, journal generations, path traversal and decompression-bomb/resource limits. This is the most important prerequisite before increasing format complexity.

### Mission 2 — benchmark CI and reproducible result archive

Run the universal corpus in controlled CI. Record CPU, OS, filesystem, Python/native library versions, cache state, codec settings, durability and metadata semantics. Commit every accepted benchmark dataset under `benchmarks/history/` with the commit SHA that produced it.

### Mission 3 — deterministic mode and normative schema

Turn revision 24’s working format document into a byte-level interoperable contract: canonical integer encodings, ordering, path normalization, endianness, bounds, index schemas and deterministic creation rules.

### Mission 4 — native core

Move parser/read/write hot paths into a memory-safe native implementation (Rust is a strong candidate) while keeping the Python implementation as readable executable specification and cross-check oracle. Native code must produce/consume conformance-identical archives.

### Mission 5 — size frontier without random-access regression

Investigate reversible preprocessing for Deflate and other common compressed structures, but only with licensed/audited techniques and exact reconstruction. Also improve cheap candidate probing so expensive codecs are not run just to discover that RAW or ordinary Zstd wins.

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
- benchmark optimizations that only help Hermes.

## When to bump the format revision

Bump the on-disk revision when a reader must understand a new physical field/record/storage-description/codec semantic to read newly created archives. Encoder-only heuristic changes that still emit the exact same revision-24 grammar do **not** require a format revision, but they do require benchmark/regression documentation.

Any format bump must update, in the same commit:

- `docs/FORMAT.md`;
- `docs/HISTORY.md`;
- this file;
- conformance vectors/tests;
- benchmark record if performance/size claims are involved.

## Definition of a good next agent

A good next agent should be comfortable saying **“this new idea loses on corpus X, so I am not merging it”**. CMPCT’s goal is not to accumulate clever codecs. It is to become the strongest boring default: small, fast, random-accessible, faithful, recoverable, secure, portable and independently implementable.
