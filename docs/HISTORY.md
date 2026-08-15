# CMPCT development and version history

This file is the durable historical ledger for CMPCT. It exists so a future agent can understand how
the format arrived at its current design without needing private chat history or private development
artifacts.

## Historical-status rules

- Versions before **v0.24** were fast research prototypes and were not all preserved as Git tags or releases.
- Where an intermediate revision number existed but no independent release note survives, this ledger says so explicitly rather than inventing a precise feature assignment.
- Benchmark numbers in this file are historical development measurements, not universal performance guarantees.
- Private corpus identities and private artifact names are intentionally generalized. The technical lesson is durable; unrelated private provenance is not part of the public format contract.
- Public reproducible benchmark records live under `benchmarks/history/`.

## Precursors: before CMPCT had a stable name

The project began by asking whether a Zstandard-based archive could beat ordinary ZIP while retaining
ZIP-like selective access and utility.

Early whole-archive tests on a mixed source/media/archive workload established two facts:

1. Zstd offered an excellent practical speed/size base for general data.
2. A whole-stream `.tar.zst` design sacrificed the selective-access behavior that makes ZIP useful.

That tension drove the format away from “one compressor wrapped around a TAR stream” and toward an
indexed object container.

### Seekable-Zstd precursor

An implementation of the official seekable-Zstandard framing model split a TAR byte stream into
independent frames with a seek table. It demonstrated that frame-level random access was practical,
but also exposed the cost of choosing one global frame size.

The early recommendation of roughly 1 MiB frames as a general compromise, or smaller frames for
frequent tiny reads, was later superseded by file-aware adaptive framing.

### Indexed direct-container precursor

TAR was then removed from the hot path. A small direct container used independent Zstd frames plus a
binary file index containing paths, sizes, permissions, timestamps, offsets, frame references and
SHA-256.

The experiment substantially improved archive open, creation and selective reads against the tested
Deflate-ZIP baseline, but an already-open tiny-file read could still lose when one tiny file forced a
larger fixed frame to be decoded.

### Adaptive/file-aligned precursor

That tiny-file loss disappeared when small files received independent frames while larger files
remained chunked. This established the principles that later became CMPCT:

- file awareness;
- adaptive representation;
- strong indexing;
- no fixed frame size as dogma.

---

## v0.1 – v0.4 — research precursor series

No independent durable release artifacts or release notes survive for these revision numbers. They
correspond to seekable-Zstd framing, direct indexing, frame-size benchmarking and file-aligned adaptive
layout. Treat them as **pre-format experiments**, not interoperable CMPCT releases.

## v0.5 — ZIP-family compatibility experiment

v0.5 tested whether CMPCT could physically inhabit the ZIP family rather than merely emulate ZIP APIs.

Key ideas:

- ZIP compression method **93 (Zstandard)** as compatibility substrate;
- CMPCT-specific metadata stored in ZIP-safe extension areas;
- range-seek metadata for large members;
- per-file SHA-256 and recovery information;
- a legacy ZIP/ZIPX-compatible view without duplicating payload bytes.

The measured checkpoint showed that Zstd-aware ZIP-family bytes could compete well with Deflate ZIP
for size and selective read latency. The remaining compatibility boundary was old Deflate-only ZIP
extractors: they could identify/list method-93 archives but not decode Zstandard entries.

This experiment was valuable but ultimately rejected as the permanent canonical storage layout because
ZIP’s physical model constrained deeper representation choices.

## v0.6 — native content-aware CMPCT

v0.6 deliberately stopped making ZIP layout a tax on the canonical representation. ZIP became an
**export/compatibility endpoint**, while native CMPCT became content-addressed and recursive.

Major changes:

- logical file tree separated from physical stored blobs;
- byte-identical duplicates stored once;
- nested ZIP/WHL virtualization through exact reconstruction recipes;
- PCM WAV stored through exact-reconstruction FLAC when profitable;
- adaptive Zstd for general data;
- dictionaries for small related text/source data;
- SHA-256 per logical content/object;
- dual/redundant archive indexes.

The key weakness was first-read latency for some virtual nested archives: exact reconstruction could be
much slower than reading the original container directly. That regression directly motivated v0.7.

## v0.7 — speed profile / exact Deflate reuse

v0.7 made existing raw-Deflate streams canonical representations where they were valuable. Top-level
files could inflate those streams directly while nested ZIP reconstruction copied the exact compressed
bytes without recompression.

Key changes:

- exact raw-Deflate stream reuse;
- libdeflate acceleration with format-independent fallback semantics;
- mmap-backed archive reads;
- selective compressed-stream splicing for nested ZIP range reads;
- continued content-addressed deduplication.

This revision established an enduring rule: compressed bytes from legacy formats may be useful data in
a modern format when reusing them improves latency/compatibility without making them mandatory.

## v0.8 — internal reader optimization checkpoint

No independent release note survives. This revision number was an intermediate reader/mmap/index
optimization step rolled into v0.9. Do not infer a stable external contract from it.

## v0.9 — index de-duplication and faster open

The archive index had duplicated SHA-256 values in multiple metadata structures. v0.9 removed
redundant hashes while keeping the authoritative blob/content hash available to logical files.

The result reduced random metadata overhead and improved archive-open latency without weakening
content identity.

## v0.10 – v0.13 — transactional/update and creation-performance series

These were internal checkpoint revisions; individual feature-to-revision assignment was not
independently preserved. The surviving development record shows this interval added and refined:

- append-only transactional generations;
- commit footer as the atomic generation marker;
- recovery to the prior generation after interrupted tails;
- compact delta journal instead of writing a full index on every mutation;
- periodic checkpoints to limit delta-chain depth;
- two-phase durable updates;
- fair `fsync` comparison against ZIP;
- faster dictionary training and archive creation.

The important benchmark lesson was not one number: mutation timings are meaningless unless durability
semantics are equivalent. A non-durable append is not a fair baseline for a crash-safe commit.

## v0.14 — hot-path integrity split and extraction optimization family

v0.14 separated integrity duties:

- CRC32 for cheap ordinary read/extraction corruption detection;
- SHA-256 retained for explicit strong verification/content identity.

This avoided paying cryptographic hashing cost on every hot-path read while preserving strong
verification.

The same development family hardened and optimized:

- hardlink preservation;
- symlink preservation;
- large ordinary-file chunk seeking;
- corruption salvage;
- path traversal rejection;
- recovery after head/tail index damage;
- sparse-file storage and extraction;
- fast legacy ZIP export through Deflate-stream reuse.

Synthetic sparse/link tests showed why filesystem semantics belong in the data model: representing a
hardlink as a relationship and a sparse hole as a hole can be dramatically smaller and faster than
materializing duplicate payload bytes or huge zero ranges.

## v0.15 – v0.17 — hardening and representation-policy checkpoints

No independent surviving release notes distinguish these three internal revisions. Work in this
interval consolidated the v0.14-era recovery, link, sparse, range-read, extraction and compatibility-
export changes. They were superseded by the explicit v0.18 representation contract.

## v0.18 — exact nested-Deflate recipe refinements

The surviving reference-code lineage records v0.18 behavior around exact nested ZIP reconstruction:

- deterministic zlib level recorded when an exact Deflate stream was reproducible;
- exact stream retained only when latency/size policy justified it;
- cold/small Deflate streams could be regenerated from raw content + recorded level rather than always stored verbatim;
- nested archive reconstruction remained byte-exact.

This revision marks the transition toward **representation competition** rather than fixed codec rules.

## v0.19 – v0.22 — universalization series

These were fast research revisions without individually preserved release notes. The surviving
technical record attributes the following general-purpose work to this interval:

- **microblocks** for thousands of tiny files, preserving selective lookup while approaching solid compression;
- content-driven codec competition rather than extension-driven codec selection;
- refusal to virtualize nested archives when simply grouping their exact bytes compressed better;
- direct/raw storage for already-compressed or incompressible media where recompression lost;
- faster `scandir` filesystem traversal;
- broader synthetic/adversarial corpora so no one private workload dominated policy.

Representative synthetic checkpoints from this development family included:

- 3,200 tiny-file corpus: roughly **177 KiB CMPCT vs ~674 KiB ZIP**, with much faster all-file reads in the measured prototype;
- 600-file source/config corpus: roughly **13.3 KiB CMPCT vs ~140 KiB ZIP** in one prototype checkpoint;
- hostile already-compressed media corpus: CMPCT stayed very close to ZIP size while creating faster in the measured prototype;
- 12 nested ZIP corpus: grouping exact archive bytes into an indexed Zstd object slightly beat a normal outer ZIP, demonstrating that nested virtualization should be adaptive.

A key lesson from this series: **the format must choose the smallest/fastest exact representation based
on measured bytes, not a filename extension or ideology about one codec.**

## v0.23 — universal benchmark baseline

v0.23 was the mature pre-CDC prototype used to assemble the heterogeneous universal benchmark harness.
It already contained the content-aware representation strategy, microblocks, sparse/link semantics,
nested archive handling, transactional updates, recovery, compatibility export and multiple codec paths.

This is the point at which the project explicitly changed its evaluation target from beating one early
workload to being an excellent default archive for arbitrary computer data.

## v0.24 — current canonical baseline

v0.24 is the **first revision imported into the official `FCMO-AI/.CMPCT` Git repository as canonical source**.

Major additions and canonicalization work:

- content-defined chunking for large evolving files, with explicit recorded boundaries so readers do not depend on the chunker algorithm;
- optional native CDC helper, with a fixed-chunk fallback so it is never a reader dependency;
- UID/GID and extended-attribute capture where available;
- modular Python package split into codec/representation, builder, reader, transactions and CLI;
- portable benchmark harness with no private scratch-path dependency;
- `libdeflate` made an optional acceleration rather than a format/runtime requirement;
- explicit `AGENTS.md`, design principles, benchmark discipline and roadmap documents;
- working revision-24 specification derived from executable reference behavior;
- parser hardening/preflight work and builder-independent conformance vectors;
- a growing Rust memory-safe native read core exposed through a C ABI;
- explicit portability contracts for Android, Linux, Windows and Apple platforms;
- fair ZIP-parity benchmarks that separate library timing from fresh-process CLI timing;
- a repository-generated website with browser-side portable archive writing/inspection gates;
- a public-surface policy preventing unrelated private provenance from becoming part of the format story;
- a **non-final Apache-2.0 license proposal** awaiting provenance/ownership review.

Revision 24 remains a **pre-1.0 working contract**. Format bytes may still change under a new revision;
1.0 requires a normative byte-level specification and compatibility policy.

## Public benchmark baseline after canonicalization

The durable public parity records under `benchmarks/history/` use deterministic/synthetic corpora and
record their environment/semantic caveats. They deliberately preserve cases where ZIP wins.

The public evidence currently supports a nuanced conclusion:

- CMPCT has strong size/creation/extraction advantages on several structured workloads;
- it can remain close to ZIP on already-compressed media;
- sparse/link semantics can produce very large practical wins because richer filesystem meaning is preserved;
- some CLI/process-start and large-binary extraction cases still favor mature ZIP tooling;
- those losses remain engineering targets rather than being removed from the record.

## Privacy/provenance transition

Early research used private mixed-workload data. That work influenced architecture, but the public
project no longer carries the private corpus record or unrelated artifact identifiers. Public
benchmarks are expected to be independently reproducible. See `docs/PUBLIC_SURFACE.md`.

## Revision-history rule going forward

For every material format/version change:

1. update `docs/FORMAT.md` if reader-visible bytes/semantics change;
2. update this file with what changed and why;
3. update `docs/CURRENT_STATE.md` so a zero-context agent has the current frontier;
4. add/adjust conformance tests and golden vectors;
5. add durable public benchmark evidence when performance/size motivates the change;
6. keep private provenance out of release-facing documentation/data;
7. keep the Browser Lab writer hard-gated to the revision it actually implements.

History should preserve mistakes and losing experiments. It should not preserve unrelated confidential
context merely because that context happened to be present during development.
