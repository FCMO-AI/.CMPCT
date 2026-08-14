# CMPCT development and version history

This file is the durable historical ledger for CMPCT. It exists so a future agent can understand how the format arrived at its current design without needing the original ChatGPT conversation.

## Historical-status rules

- Versions before **v0.24** were research prototypes developed during the 2026-08-13 campaign. They were not all preserved as Git tags or releases.
- Where an intermediate revision number existed but no independent release note survives, this ledger says so explicitly rather than inventing a precise feature assignment.
- Benchmark numbers in this file are historical measurements, not universal performance guarantees. Machine-readable copies live under `benchmarks/history/`.
- **Hermes was a benchmark corpus, never the product specification.** CMPCT is a general-purpose computer archive/container format.

## Precursors: before CMPCT had a stable name

The project began by asking whether a Zstandard-based archive could beat ordinary ZIP while retaining ZIP-like selective access and utility.

The extracted Hermes integration bundle used as the first corpus contained **455 files**, **127 directories**, and **7,816,826 bytes** of actual file payload. The delivered ZIP was **5,133,594 bytes (~4.896 MiB)**.

Initial whole-archive compressor measurements on that payload included:

| Representation | Size | Compression | Full decode/extract checkpoint |
|---|---:|---:|---:|
| delivered ZIP/Deflate | 4.896 MiB | existing artifact | ~60 ms extraction checkpoint |
| fresh ZIP/Deflate -9 | 4.965 MiB | ~203 ms | ~59.5 ms |
| gzip -9 | 4.670 MiB | ~306 ms | ~51.1 ms |
| bzip2 -9 | 4.213 MiB | ~566 ms | ~277 ms |
| Zstd -3 | 4.202 MiB | ~37 ms | ~21.8 ms |
| Zstd -19 | 4.053 MiB | ~1.44 s | ~25.4 ms |
| Zstd -22 | 4.050 MiB | ~2.99 s | ~18.4 ms (small-sample noise applies) |
| XZ/LZMA2 -9e | 3.946 MiB | ~2.48 s | ~78.9 ms |
| Brotli q11 | 3.830 MiB | ~15.6 s | ~610 ms |

The key conclusion was that **Zstd -3** offered the best practical speed/size base, but ordinary `.tar.zst` did not provide ZIP-like random access.

### Seekable-Zstd precursor

An implementation of the official seekable-Zstandard framing model was built directly against `libzstd` 1.5.7. A TAR byte stream was split into independent frames with an official seek table. The same archives were decoded both by the custom seekable reader and ordinary `zstd -d`.

Historical results on the Hermes TAR stream:

| Frame size | Archive size | Over normal Zstd-3 | Warm selective read: small / medium / large |
|---|---:|---:|---:|
| 64 KiB | 4.769 MiB | +11.22% | 0.045 / 0.053 / 0.624 ms |
| 256 KiB | 4.616 MiB | +7.65% | 0.115 / 0.164 / 0.406 ms |
| 1 MiB | 4.414 MiB | +2.93% | 0.635 / 0.479 / 0.476 ms |
| 4 MiB | 4.320 MiB | +0.74% | 2.331 / 2.287 / 1.602 ms |

The first design recommendation was **1 MiB frames for a general compromise**, or **256 KiB** for very frequent small random reads. This was later superseded by file-aware adaptive framing.

### Indexed 256 KiB direct-container precursor

TAR was then removed from the hot path. A small direct container prototype used independent Zstd-3 frames plus a binary file index containing paths, sizes, permissions, timestamps, offsets, frame references and SHA-256.

On the Hermes corpus:

- size: **4.677 MiB** vs **4.896 MiB ZIP**;
- creation: **28.5 ms** vs **163.5 ms ZIP**;
- index open: **0.202 ms** vs **1.067 ms ZIP**;
- full extraction: **24.9 ms** vs **40.9 ms ZIP**;
- open+read 3.6 KiB: **0.361 ms** vs **1.085 ms ZIP**.

But an already-open tiny-file read still favored ZIP because a 3.6 KiB file forced decoding a whole 256 KiB frame.

### Adaptive/file-aligned precursor

The tiny-file loss disappeared when small files received independent Zstd frames and large files remained chunked. Historical already-open reads:

- 3.6 KiB: **~0.01539 ms CMPCT-like prototype vs ~0.01526 ms ZIP** — effectively tied;
- 10.6 KiB: **~0.02592 ms vs ~0.02735 ms** — Zstd slightly ahead;
- 162 KiB: **~0.117 ms vs ~0.553 ms**;
- 2.04 MiB: **~1.38 ms vs ~3.95 ms**.

The file-aligned archive was **5,110,035 bytes** vs **5,133,594 bytes ZIP** while retaining Zstd-based selective access.

These precursor experiments established the principles that later became CMPCT: **file awareness, adaptive representation, strong indexing, and no fixed frame size as dogma**.

---

## v0.1 – v0.4 — research precursor series

No independent durable release artifacts or release notes survive for these revision numbers. They correspond to the exploratory phase above: seekable-Zstd framing, direct indexing, frame-size benchmarking, and file-aligned adaptive layout. They should be treated as **pre-format experiments**, not interoperable CMPCT releases.

## v0.5 — ZIP-family compatibility experiment

v0.5 tested whether CMPCT could physically inhabit the ZIP family rather than merely emulate ZIP APIs.

Key ideas:

- ZIP compression method **93 (Zstandard)** as compatibility substrate;
- CMPCT-specific metadata stored in ZIP-safe extension areas;
- range-seek metadata for large members;
- per-file SHA-256 and recovery information;
- legacy ZIP/ZIPX-compatible view without duplicating payload bytes.

Hermes v0.5 benchmark checkpoint:

| Metric | CMPCT v0.5 | original ZIP |
|---|---:|---:|
| archive size | **5,128,734 B** | 5,133,594 B |
| controlled creation | **159.3 ms** | 168.4 ms |
| open + 3.6 KiB read | **0.699 ms** | 1.100 ms |
| open + 10.6 KiB read | **0.704 ms** | 1.105 ms |
| open + 162 KiB read | **0.845 ms** | 1.673 ms |
| open + 2.04 MiB read | **1.60 ms** | 5.27 ms |
| 4 KiB late range read | **0.117 ms** | 2.85 ms |
| fast member update | **2.44 ms** | 2.71 ms |
| update growth | **1,877 B** | 1,972 B |

Native libarchive 3.7.4 read-through of the same CMPCT bytes as a ZIP-family archive measured about **13.91 ms CMPCT vs 25.37 ms Deflate ZIP** across 50 runs.

The remaining compatibility boundary was old Deflate-only ZIP extractors: they could identify/list method-93 archives but not decode Zstandard entries.

Artifact historical SHA-256 for the Hermes v0.5 file: `73f94d2d5d87b027df4d5a1f5d39e29639ff7115b9c59fe9931854fd7a77520d`.

## v0.6 — native content-aware CMPCT

v0.6 deliberately stopped making ZIP layout a tax on the canonical representation. ZIP became an **export/compatibility endpoint**, while native CMPCT became content-addressed and recursive.

Major changes:

- logical file tree separated from physical stored blobs;
- byte-identical duplicates stored once;
- nested ZIP/WHL virtualization through exact reconstruction recipes;
- PCM WAV stored through exact-reconstruction FLAC when profitable;
- adaptive Zstd for general data;
- dictionaries for small related text/source data;
- SHA-256 per logical content/object;
- dual/redundant archive indexes.

The first v0.6 Hermes build fell to roughly **2.06 MB**, then **~1.923 MB** after dictionary and FLAC tuning — about **62.5% smaller than the original ZIP** — while still verifying all 455 logical files and reconstructing all three source ZIPs and both wheels byte-for-byte.

The weakness was first-read latency for virtual provenance archives: reconstructing the ~2 MiB Jarvis source ZIP could take roughly **52 ms**, far slower than reading it directly from ZIP. That regression directly motivated v0.7.

## v0.7 — speed profile / exact Deflate reuse

v0.7 made existing raw-Deflate streams canonical representations where they were valuable. Top-level files could inflate those streams directly while nested ZIP reconstruction copied the exact compressed bytes without recompression.

Key changes:

- exact raw-Deflate stream reuse for hundreds of payloads;
- libdeflate acceleration with format-independent fallback semantics;
- mmap-backed archive reads;
- selective compressed-stream splicing for nested ZIP range reads;
- continued content-addressed deduplication.

Checkpoint size: **~2.544 MB**, still roughly **50.4% smaller than ZIP**.

Selected measurements during this revision family:

- ~2 MiB nested ZIP read: **3.20 ms CMPCT vs 5.11 ms ZIP**, later **1.67 ms vs 2.84 ms** with libdeflate;
- 162 KiB file: **0.36 ms vs 0.56 ms** after libdeflate;
- full logical read: **21.7 ms CMPCT vs ~30.1 ms ZIP**, later ~20.2 ms with mmap;
- nested-file already-open range/read path: ~1.41 ms in the mmap optimization checkpoint.

## v0.8 — internal reader optimization checkpoint

No independent release note survives. This revision number was an intermediate reader/mmap/index optimization step rolled into v0.9. Do not infer a stable external contract from it.

## v0.9 — index de-duplication and faster open

The archive index had duplicated SHA-256 values in multiple metadata structures. v0.9 removed redundant hashes while keeping the authoritative blob/content hash available to logical files.

Hermes size reached **2,513,752 bytes**, approximately **51% smaller than the original ZIP**, while archive-open latency fell to about **0.32 ms**.

## v0.10 – v0.13 — transactional/update and creation-performance series

These were internal checkpoint revisions; individual feature-to-revision assignment was not independently preserved. The surviving development record shows this interval added and refined:

- append-only transactional generations;
- commit footer as the atomic generation marker;
- recovery to the prior generation after interrupted tails;
- compact delta journal instead of writing a full index on every mutation;
- periodic checkpoints to limit delta-chain depth;
- two-phase durable updates;
- fair `fsync` comparison against ZIP;
- faster dictionary training and archive creation.

Historical update measurements:

- first safe append design: **~11.2 ms and +17.9 KiB**, worse than a non-durable ZIP duplicate-entry append;
- delta journal: **+1,486 B CMPCT vs +1,883 B ZIP**;
- fair durable comparison: **~9.4 ms CMPCT two-phase crash-safe update vs ~14.1 ms ZIP with final fsync**;
- optimized creation checkpoint: **~153 ms CMPCT vs ~183 ms controlled ZIP build** on Hermes.

## v0.14 — hot-path integrity split and extraction optimization family

v0.14 separated integrity duties:

- CRC32 for cheap ordinary read/extraction corruption detection;
- SHA-256 retained for explicit strong verification/content identity.

This avoided paying cryptographic hashing cost on every hot-path read while preserving strong verification. Metadata overhead was only around **1.5 KiB** on Hermes.

The same development family optimized full extraction by removing redundant filesystem checks, reaching roughly **27.8 ms CMPCT vs 42.9 ms ZIP** for byte materialization in the repeated local test; metadata-restoring mode remained only slightly slower.

This era also hardened:

- hardlink preservation;
- symlink preservation;
- large ordinary-file chunk seeking;
- corruption salvage;
- path traversal rejection;
- recovery after head/tail index damage.

A synthetic **16 MiB incompressible file + hardlink + symlink** produced **~16.78 MB CMPCT vs ~50.35 MB Python ZIP** because CMPCT preserved link semantics instead of materializing targets. A late 4 KiB range read measured **~0.0043 ms vs ~22.9 ms**.

Sparse-file support was also established in this development line. A **256 MiB logical sparse image with ~2 MiB real data** produced about **2.00 MiB CMPCT vs 2.25 MiB ZIP**, created in **~181 ms vs 1.80 s**, extracted sparsely in **~1.74 ms**, and read a 4 KiB hole in **~0.008 ms**. The ZIP comparison had to inflate the large logical member to reach the same range.

Legacy ZIP export was accelerated by reusing existing raw Deflate streams: Hermes export dropped from roughly **187 ms to 66.6 ms**, with **315** payloads copied directly into ordinary Deflate ZIP records.

## v0.15 – v0.17 — hardening and representation-policy checkpoints

No independent surviving release notes distinguish these three internal revisions. Work in this interval consolidated the v0.14-era recovery, link, sparse, range-read, extraction and compatibility-export changes. They were superseded by the explicit v0.18 representation contract.

## v0.18 — exact nested-Deflate recipe refinements

The surviving reference-code lineage records v0.18 behavior around exact nested ZIP reconstruction:

- deterministic zlib level recorded when an exact Deflate stream was reproducible;
- exact stream retained only when latency/size policy justified it;
- cold/small Deflate streams could be regenerated from raw content + recorded level rather than always stored verbatim;
- nested archive reconstruction remained byte-exact.

This revision marks the transition toward **representation competition** rather than fixed codec rules.

## v0.19 – v0.22 — universalization series

These were fast research revisions without individually preserved release notes. The surviving development log attributes the following general-purpose work to this interval:

- **microblocks** for thousands of tiny files, preserving selective lookup while approaching solid compression;
- content-driven codec competition rather than extension-driven codec selection;
- refusal to virtualize nested archives when simply grouping their exact bytes compressed better;
- direct/raw storage for already-compressed or incompressible media where recompression lost;
- faster `scandir` filesystem traversal;
- broader synthetic/adversarial corpora so Hermes stopped being the dominant benchmark.

Historical corpus results:

- 3,200 tiny-file corpus: **~177 KiB CMPCT vs ~674 KiB ZIP**, all-file read **~2.5 ms vs ~32 ms**;
- 600-file source/config corpus: **~13.3 KiB CMPCT vs ~140 KiB ZIP**, all-file read around **0.4 ms vs ~5.2 ms** in one checkpoint;
- hostile already-compressed media corpus: **4,224,967 B CMPCT vs 4,230,623 B ZIP**, with CMPCT creation around **29 ms vs ~87 ms ZIP**;
- 12 nested ZIP corpus: grouped/indexed Zstd representation **796,725 B** vs normal outer ZIP **808,393 B**.

A key lesson from this series: **the format must choose the smallest/fastest exact representation based on measured bytes, not a filename extension or ideology about one codec.**

## v0.23 — universal benchmark baseline

v0.23 was the mature pre-CDC prototype used to assemble the heterogeneous universal benchmark harness. It already contained the content-aware representation strategy, microblocks, sparse/link semantics, nested archive handling, transactional updates, recovery, compatibility export and multiple codec paths.

This is the point at which the project explicitly changed its evaluation target from “beat ZIP on Hermes” to “be an excellent default archive for arbitrary computer data.”

## v0.24 — current canonical baseline

v0.24 is the **first revision imported into the official `FCMO-AI/.CMPCT` Git repository as canonical source**.

Major additions and canonicalization work:

- content-defined chunking for large evolving files, with explicit recorded boundaries so readers do not depend on the chunker algorithm;
- optional native CDC helper, with a fixed-chunk fallback so it is never a reader dependency;
- UID/GID and extended-attribute capture where available;
- modular Python package split into codec/representation, builder, reader, transactions and CLI;
- portable benchmark harness with no `/mnt/data` dependency;
- `libdeflate` made an optional acceleration rather than a format/runtime requirement;
- explicit `AGENTS.md`, working format specification, roadmap, benchmark discipline and general-purpose design principles;
- smoke tests for round-trip/range access, links/sparse behavior and CLI open/info behavior.

Canonical import commit: `f59ee8d14ef065e3fedfb032e38a954eea1ff965` (`Establish CMPCT canonical v0.24 baseline`).

v0.24 remains **pre-1.0**. The reader/writer contract is working but not frozen. See `docs/CURRENT_STATE.md`, `docs/FORMAT.md`, and `docs/ROADMAP.md` before changing on-disk semantics.

---

## Historical design conclusions that must not be lost

1. **TAR + Zstd is not the canonical design.** It gives up too much file-aware random access and metadata utility.
2. **Fixed 256 KiB framing is not universal.** It created a needless tiny-file latency disadvantage.
3. **One codec is not the format.** Zstd is the general workhorse, not a religion; RAW, Deflate reuse, FLAC and future transforms are valid when they measurably win.
4. **ZIP compatibility is an endpoint.** Canonical CMPCT should not permanently carry ZIP layout overhead merely for legacy tools.
5. **Nested archives are optimization opportunities, not always targets for virtualization.** Sometimes exact-byte grouping is smaller and faster.
6. **Strong integrity does not require strong hashing on every hot read.** CRC32 can detect routine corruption; SHA-256 remains authoritative for strong verification/content identity.
7. **Content semantics matter.** Sparse regions, hardlinks and symlinks should not be silently materialized as duplicate bytes.
8. **Encoder complexity must not infect the reader.** Chunking/representation heuristics may evolve; stored descriptions must make old archives readable without reproducing old heuristics.
9. **Do not optimize for Hermes.** Hermes remains a useful regression corpus only.
10. **Benchmark losses are development inputs.** A workload where CMPCT loses should become a corpus/test, not be hidden.
