# CMPCT current development state

This document is the **zero-chat-history handoff** for a new agent. Read it together with:

- `README.md` — project mission and quick start;
- `AGENTS.md` — mandatory development and versioning behavior;
- newest applicable note under `docs/releases/` — project-version milestone;
- `docs/FORMAT.md` — current revision-24 on-disk contract;
- `docs/HISTORY.md` — surviving format/development history with private provenance generalized;
- `docs/ENTROPYGRAPH.md` — current v0.25 research frontier;
- `docs/BENCHMARKS.md` and `benchmarks/history/` — benchmark discipline and public historical records;
- `docs/PORTABILITY.md` — ZIP-parity UX and first-class Android/desktop integration contract;
- `docs/NATIVE_CORE.md` — current shared native reader/ABI capability and next representation gates;
- `docs/PUBLIC_SURFACE.md` — public disclosure boundary;
- `LICENSING.md` — non-final Apache-2.0 licensing proposal;
- `docs/ROADMAP.md` — work required before a defensible 1.0.

## Project objective

CMPCT is intended to become a **general-purpose lossless archive/container format and engine** for
arbitrary computer files and filesystems. The target is not merely “smaller ZIP.” The target is a
default archive choice with strong size, creation/extraction speed, random access, integrity,
crash-safe updates, recovery, filesystem fidelity, remote-read potential, codec agility, and ordinary
end-user portability.

Real-world private corpora may be useful regression inputs during development, but **no private corpus
may define the format or public encoder policy**. Public claims must be reproducible on public or
deterministic synthetic workloads.

## Canonical authority

Repository: `FCMO-AI/.CMPCT`

Branch: `main`

Current project version: **v0.25.0**

Current canonical executable format: **revision 24**

Project version and format revision are intentionally independent. v0.25.0 materially advances the
research/benchmark frontier but does not yet promote EntropyGraph's research-only `CMPNX5` grammar
into the canonical revision-24 reader/writer.

`main` HEAD is the canonical implementation state. Do not hard-code one historical commit as the
permanent baseline in this handoff; every accepted change advances that baseline.

Everything created outside this repository is experimental until reconciled back into `main` with
documentation/tests/benchmarks and a material project-version bump.

## v0.25 EntropyGraph research frontier

The v0.25 milestone adds a deliberately public, synthetic neutral/hostile corpus and an executable
research engine under `experiments/entropygraph_v025.py`. It explores an authenticated reconstruction
graph in which the encoder can choose which exact reversible representation should be physically
stored instead of treating every requested file as an independent payload.

The current research mechanisms include:

- global exact compressed-stream federation across related ZIP-like containers;
- entropy-oriented representation inversion, where a required compressed representation can become
  the physical root and a loose logical file is materialized by a cheap exact decoder;
- exact object interning across logical aliases/snapshots;
- generic exact inverse edges for required gzip/xz/zstd/bzip2 sidecars and their loose plaintexts;
- compact implicit micro-pack indexing for forests of tiny files;
- adaptive same-family context audition capped at 512 KiB physical decode units;
- hot/cold stream-root layout so latency-sensitive inverse views avoid a hidden multi-megabyte pool;
- authenticated head/tail metadata recovery that is actually exercised by the research reader;
- explicit strong verification of every physical pack plus the authenticated canonical tree root.

These are **research-proven directions, not canonical format claims**. Promotion requires deliberate
integration into the Python reference reader/writer, format schema, conformance vectors, hostile parser
limits, native core, compatibility/export paths and platform integrations. The public benchmark record
is `benchmarks/history/2026-08-16-entropygraph-v025.json`; private development corpora remain local
regression inputs and do not appear in public evidence.

## Current implementation architecture

`src/cmpct/codec.py`
: Codec and representation primitives, Zstd/Deflate/FLAC handling, content-defined chunking interface,
  exact nested-ZIP reconstruction helpers and integrity primitives.

`src/cmpct/builder.py`
: Filesystem scan, candidate/representation selection, deduplication, dictionaries/microblocks,
  sparse/link handling and physical archive construction.

`src/cmpct/reader.py`
: Archive parsing, index recovery, logical reads, range reads, extraction, verification and
  salvage-oriented behavior.

`src/cmpct/transactions.py`
: Append generations, mutation journal, rename/delete/update behavior, checkpoints and commit-footer semantics.

`src/cmpct/cli.py`
: User-facing commands including create/info/list/read/range/extract/verify/export-zip/recovery-related operations.

`experiments/entropygraph_v025.py`
: Executable research-only CMPNX5 reader/writer used to test new representation-graph mechanisms before
  they are allowed to mutate the canonical on-disk grammar.

`benchmarks/neutral_hostile_corpus_v1.py`
: Deterministic-per-workload heterogeneous synthetic corpus generator covering developer, office,
  media, analytics/database, logs, backups, incompressible, tiny-file, ML and large-binary workloads.

`native/cmpct_cdc.c`
: Optional creation-time content-defined chunk boundary accelerator. The reader does not require it
  because boundaries are explicit in the archive.

`native/cmpct-core/`
: Memory-safe Rust read-only core. It authenticates and decodes the revision-24 primary index, applies
  the shared lexical path policy, enumerates logical entries, bounds the base blob table, and exposes
  an opaque C ABI plus the small `cmpct-native` process surface. Member access covers genuinely
  range-local direct RAW, bounded ordinary direct Zstd/WAV-FLAC/raw Deflate/Zstd-dictionary,
  range-local fixed/CDC maps, sparse extents, checked micro-solid `S_PACK` slices, and independently
  conformance-gated virtual-ZIP projection for ZIP_STORED plus retained-exact Deflate stream mode 1.
  Native open validates the corresponding authenticated references/accounting; complete mapped,
  sparse, packed (when logical identity is present) and supported virtual reads apply their logical
  SHA-256 boundary. Virtual-ZIP Deflate mode 0 already has a fixed independent oracle and bounded
  authenticated physical-Deflate component but remains deliberately `Unsupported` at archive dispatch
  until projection segments can select physical codec-4 payload bytes. Mode 2 still needs an
  independent exact-byte oracle. Sequential native streams, full native extraction, committed-generation
  recovery and full structural-preflight parity remain unfinished.

`benchmarks/universal_bench.py`
: Heterogeneous synthetic benchmark harness. Generated corpora/output are not canonical history;
  durable public result records belong under `benchmarks/history/`.

`benchmarks/zip_parity_bench.py`
: Fair CMPCT-vs-ZIP regression harness that separates library-to-library timing from fresh-process CLI
  timing. It exists specifically to expose ZIP advantages without conflating them with benchmark
  orchestration overhead.

`docs/PORTABILITY.md`
: First-class archive integration contract for Android, Linux, Windows and Apple platforms. It is a
  release requirement, not a claim that those integrations already ship.

`docs/NATIVE_CORE.md`
: Durable handoff for the shared memory-safe reader and C ABI, including integrity/resource boundaries
  and the required representation-by-representation conformance order.

`site/`
: Source for the human/agent project website, Browser Lab and benchmark viewer. The site is validated in
  CI but publication remains an explicit/manual action until the project is ready to present publicly.

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
13. **Public CMPCT stands alone.** Private/unrelated system context is neither documentation nor benchmark evidence and must not enter the release-facing project surface.
14. **Material work is versioned.** A substantive merged milestone must advance the project version even when the on-disk format revision stays unchanged.

## What is proven enough to use as a development baseline

The current Python reference implementation is able to create/read revision-24 archives and has
smoke-tested round trips, range access, links/sparse behavior and CLI opening. Historical experiments
also demonstrated the architectural feasibility of exact nested ZIP reconstruction, strong random
access, transactional recovery and fast ZIP export.

The fair ZIP-parity harness additionally demonstrates an important measurement rule: library-vs-library
and process-start/CLI timing must remain separate. Early mixed-layer measurements overstated several
ZIP speed advantages because CMPCT paid fresh-Python startup while ZIP ran inside an already-started
benchmark process. Genuine remaining losses must be fixed, not hidden behind that correction. The
five-repeat public RAW-chunk extraction record reduced the remaining large-binary library extraction
result to about 55.5 ms while ZIP measured about 48.6 ms on the same shared-runner campaign; the
residual is still an active parity defect, not a declared tradeoff.

The native core now proves direct, chunked, sparse, packed and selected virtual-ZIP content paths
across the C ABI. Direct RAW remains range-local; direct Zstd/WAV-FLAC/raw Deflate/Zstd-dictionary are
capped and whole-object authenticated before slicing. Codec 2 reconstructs the original WAV
prefix/PCM/suffix byte-for-byte, validates FLAC stream properties against authenticated reconstruction
metadata, and crosses the same fixed archive through the public C ABI with physical-hash corruption
refusal. Fixed and CDC members are validated from authenticated index metadata and answer
cross-boundary ranges by decoding only intersecting chunks. Sparse members validate
sorted/non-overlapping extent maps and exact stored-byte accounting, synthesize holes as zeroes, and
decode only stored chunks in extents intersecting the requested interval. `S_PACK` now has checked
slice parsing plus complete and non-zero-offset C-ABI regression coverage; its remaining conformance
gap is provenance, because the pack fixture is Builder-derived rather than a frozen independent
archive. Builder-independent golden archives cover direct RAW/Zstd/Deflate/WAV-FLAC/Zstd-dictionary,
fixed/CDC/sparse, stored virtual ZIP and retained-exact Deflate virtual-ZIP mode 1. Deflate mode 0 has
an independent fixed archive and authenticated physical-stream component, with archive dispatch still
intentionally gated. This is a portability/conformance milestone, not yet a claim of
representation-complete native reading.

The v0.25 EntropyGraph experiment additionally proves on its public neutral/hostile suite that global
reconstruction relationships can materially improve aggregate storage without requiring a monolithic
solid stream. It also proves that poor physical stream-pool topology can create selective-read
regressions, which is why hot roots and the 512 KiB slab ceiling are part of the research design.
Treat this as an integration target, not canonical revision-24 behavior.

Treat canonical revision-24 behavior as **reference behavior**, not yet as a frozen interoperability standard.

## What is NOT yet production-grade or 1.0-ready

A new agent should not mistake prototype breadth for completion. Major open areas include:

- normative byte-level format specification and complete index schema;
- complete conformance/golden archives and stable cross-version vectors;
- parser fuzzing/property testing and strict resource/bounds limits;
- deterministic archive mode;
- formal codec/transform registry and capability negotiation;
- authenticated encryption and key derivation;
- complete ACL/Windows/macOS metadata/path normalization rules;
- split-volume and streaming/non-seekable creation;
- remote HTTP/object-store range access with partial verification;
- native memory-safe high-performance core beyond the implemented direct codecs, fixed/CDC, sparse, `S_PACK` and selected virtual-ZIP range reads: virtual-ZIP Deflate mode 0 dispatch and mode 2 exact regeneration, independent pack conformance, complete structural validation, committed-generation recovery, sequential streams and extraction remain unfinished;
- scalable CDC without whole-file memory loading;
- robust Android/Linux/Windows/Apple archive browsing, file association and mount/file-manager integrations defined by `docs/PORTABILITY.md`;
- deliberate promotion or rejection of EntropyGraph storage semantics after canonical conformance/security integration;
- CI that reruns the universal and neutral/hostile benchmarks on controlled hardware/software and archives raw results;
- formal adoption or rejection of the proposed Apache-2.0 license after provenance review.

## Current benchmark interpretation

Historical measurements show that the architecture can outperform ordinary Deflate ZIP dramatically
on some workloads and narrowly on hostile already-compressed ones. They do **not** prove universal dominance.

The v0.25 neutral/hostile record adds a broader adversarial checkpoint: its research candidate beat
ZIP/Zstd-93 on 8/10 workloads and the solid tar+Zstd-19 diagnostic on 6/10 in that recorded environment,
while deliberately preserving losses on media, ML artifacts, the large mixed binary and selected
selective-read cases. Aggregate wins do not erase those losses.

The current benchmark policy is:

- commit the exact benchmark harness/version;
- commit public machine-readable results under `benchmarks/history/`;
- record semantics (durability, metadata restoration, warm/cold cache, process startup, integrity work);
- preserve losing cases;
- never compare a richer CMPCT operation against a weaker ZIP operation without saying so;
- never compare fresh-process CMPCT against in-process ZIP as if it were one timing layer;
- never use one private-corpus number as a general format claim;
- never publish private corpus identity/artifact provenance merely to decorate the engineering history.

See `docs/BENCHMARKS.md`, `docs/ENTROPYGRAPH.md` and `benchmarks/history/` for public reproducible evidence.

## Immediate high-value development missions

### Mission 1 — conformance and hostile-parser foundation

Create golden revision-24 archives and byte-exact vectors for every storage description/codec. Add
fuzz/property tests for corrupt headers, indexes, blob sizes, chunk maps, sparse extents, nested
recipes, journal generations, path traversal and decompression-bomb/resource limits. This is the most
important prerequisite before increasing format complexity.

### Mission 2 — benchmark CI and reproducible result archive

Run the universal and neutral/hostile corpora in controlled CI. Record CPU, OS, filesystem,
Python/native library versions, external encoder versions, cache state, codec settings, durability and
metadata semantics. Commit every accepted public benchmark dataset under `benchmarks/history/` with
the commit SHA that produced it. Keep `benchmarks/zip_parity_bench.py` as the explicit gate for every
fair ZIP advantage.

### Mission 3 — deterministic mode and normative schema

Turn revision 24’s working format document into a byte-level interoperable contract: canonical integer
encodings, ordering, path normalization, endianness, bounds, index schemas and deterministic creation rules.

### Mission 4 — native core

Continue the memory-safe Rust core now present under `native/cmpct-core/` while keeping Python as the
readable executable specification and cross-check oracle. The current native slice authenticates/
decodes the primary index, applies lexical path policy, enumerates entries, bounds base blobs, exposes
a tested C ABI, reads direct RAW ranges without decoding unrelated data, reads bounded ordinary direct
Zstd/WAV-FLAC/raw-Deflate/Zstd-dictionary ranges with whole-member authentication, serves
fixed/CDC/sparse maps range-locally, restores checked micro-solid `S_PACK` slices, and reconstructs
stored plus retained-exact-Deflate-mode-1 virtual ZIP ranges through the public ABI. Deflate mode 0
already has its independent archive oracle and authenticated physical-stream primitive; wire that
physical source into virtual projection next without weakening its current typed-Unsupported gate.
Then freeze/prove Deflate mode 2 and an independent pack archive, followed by sequential member streams,
extraction, full structural-preflight parity and committed-generation recovery. Native code must remain
conformance-identical, and the same core must expose the list/stat/read/range/stream/extract surface
required by platform handlers so portability does not fork format semantics.

### Mission 5 — integrate EntropyGraph without random-access regression

Promote EntropyGraph one representation at a time rather than copying the research grammar wholesale.
First formalize the reconstruction DAG and dependency/resource bounds; then integrate exact object
interning, compact micro-pack indexing, global virtual-container federation and inverse views behind
explicit canonical storage descriptions. Every promoted edge must have independent golden vectors,
hostile cycle/depth/bomb tests, bounded selective-read accounting, recovery behavior, ZIP export or
compatibility semantics, and native-core parity before it can justify a format-revision bump.

For exact DEFLATE shadow removal, investigate licensed/audited bit-exact reconstruction approaches only
when the stored correction data plus replay latency beat retained-stream alternatives under the public
hostile suite. Do not buy ratio with an unbounded recompression step.

### Mission 6 — erase practical ZIP advantages and ship first-class archive UX

Treat stable fair ZIP wins as performance defects. Prioritize creation/extraction hot paths,
startup/import overhead, fused validation and native read-only startup until ZIP has no unexplained
material advantage on the parity corpus. In parallel, implement the `docs/PORTABILITY.md` contract:
Android DocumentsProvider/app integration, Linux MIME/browser integration, Windows file
association/browser support, and Apple UTType/document integration, all backed by the shared native
core. Do not claim platform support until the corresponding package passes conformance archives on
that platform/emulator.

### Mission 7 — public-release readiness

Keep `tools/check_public_surface.py` and `tools/check_version_discipline.py` green, maintain the website
as a self-contained project front door, finish third-party provenance review, and resolve the non-final
Apache-2.0 proposal before public release. Publication must be an explicit action rather than an
accidental side effect of ordinary `main` pushes.

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
- benchmark optimizations that only help one private development corpus;
- a permanent hidden ZIP shadow inside every CMPCT archive merely to gain legacy file-manager recognition;
- global stream federation implemented as one giant decode unit;
- exact recompression recipes promoted without replay-latency accounting.

## Project-version and format-revision rules

Every material merged milestone must advance the project version and add the matching
`docs/releases/vX.Y.Z.md` note. CI enforces this for material paths. A project-version bump does **not**
by itself imply an on-disk format change.

Bump the on-disk revision when a reader must understand a new physical field/record/storage-description/
codec or reconstruction semantic to read newly created canonical archives. Encoder-only heuristic or
research changes can keep revision 24 while still requiring a new project version, benchmark/regression
evidence and a release note.

Any format bump must update, in the same versioned change:

- `docs/FORMAT.md`;
- `docs/HISTORY.md`;
- this file;
- conformance vectors/tests;
- benchmark record if performance/size claims are involved;
- browser-writer revision gate when that writer remains enabled.

## Definition of a good next agent

A good next agent should be comfortable saying **“this new idea loses on corpus X, so I am not merging
it.”** CMPCT’s goal is not to accumulate clever codecs. It is to become the strongest boring default:
small, fast, random-accessible, faithful, recoverable, secure, portable, independently implementable,
and ordinary to open on the devices people actually use.
