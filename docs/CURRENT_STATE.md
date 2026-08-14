# CMPCT current development state

This document is the **zero-chat-history handoff** for a new agent. Read it together with:

- `README.md` — project mission and quick start;
- `AGENTS.md` — mandatory development behavior;
- `docs/FORMAT.md` — current revision-24 on-disk contract;
- `docs/HISTORY.md` — surviving development/version history with private provenance generalized;
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

Current canonical revision: **format revision 24 / project v0.24**

`main` HEAD is the canonical implementation state. Do not hard-code one historical commit as the
permanent baseline in this handoff; every accepted change advances that baseline.

Everything created outside this repository is experimental until reconciled back into `main` with
documentation/tests/benchmarks.

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

`native/cmpct_cdc.c`
: Optional creation-time content-defined chunk boundary accelerator. The reader does not require it
  because boundaries are explicit in the archive.

`native/cmpct-core/`
: Memory-safe Rust read-only core. It authenticates and decodes the revision-24 primary index, applies
  the shared lexical path policy, enumerates logical entries, bounds the base blob table, and exposes
  an opaque C ABI. The member-access surface reads genuinely range-local slices from direct RAW
  members, bounded ranges from ordinary direct Zstd/raw Deflate members, range-local fixed/CDC chunk
  maps that decode only intersecting chunks, and sparse maps that synthesize holes while decoding only
  stored chunks in intersecting extents. Native open validates fixed/CDC/sparse blob references,
  declared lengths, sparse ordering/non-overlap and exact logical/extent byte accounting; complete
  mapped reads additionally verify the logical whole-file SHA-256. CI cross-checks the C ABI against
  Python plus builder-independent direct/chunk/sparse/Zstd-dictionary golden archives. Codec-3 reads
  authenticate the index-selected dictionary blob and bound both dictionary and member decode work
  before returning content. WAV-FLAC direct blobs, virtual member access, sequential streams, journal
  recovery and full structural preflight parity remain unfinished.

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

The native core now proves direct, chunked and sparse selective-content paths across the C ABI. Direct
RAW remains range-local; direct Zstd/raw Deflate are capped and whole-object authenticated before
slicing. Fixed and CDC members are validated from authenticated index metadata and answer
cross-boundary ranges by decoding only intersecting chunks. Sparse members validate sorted/non-
overlapping extent maps and exact stored-byte accounting, synthesize holes as zeroes, and decode only
stored chunks in extents intersecting the requested interval. Builder-independent golden archives
mix RAW/Zstd/Deflate chunks; the sparse gate additionally proves that corruption in an untouched
extent does not poison a disjoint range, while touching the corrupted compressed blob fails. Complete
fixed/CDC/sparse reads enforce the logical whole-file SHA-256. This is a portability/conformance
milestone, not yet a claim of representation-complete native reading.

Treat those as **reference behavior**, not yet as a frozen interoperability standard.

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
- native memory-safe high-performance core beyond authenticated primary-index enumeration plus direct RAW/Zstd/Deflate/Zstd-dictionary, fixed/CDC and sparse range reads: complete structural validation, committed-generation recovery, WAV-FLAC codec support, virtual member access, sequential streams and extraction remain unfinished;
- scalable CDC without whole-file memory loading;
- robust Android/Linux/Windows/Apple archive browsing, file association and mount/file-manager integrations defined by `docs/PORTABILITY.md`;
- reversible preprocessing for already-compressed structures where licensing and exactness permit;
- CI that reruns the universal benchmark on controlled hardware/software and archives raw results;
- formal adoption or rejection of the proposed Apache-2.0 license after provenance review.

## Current benchmark interpretation

Historical measurements show that the architecture can outperform ordinary Deflate ZIP dramatically
on some workloads and narrowly on hostile already-compressed ones. They do **not** prove universal dominance.

The current benchmark policy is:

- commit the exact benchmark harness/version;
- commit public machine-readable results under `benchmarks/history/`;
- record semantics (durability, metadata restoration, warm/cold cache, process startup, integrity work);
- preserve losing cases;
- never compare a richer CMPCT operation against a weaker ZIP operation without saying so;
- never compare fresh-process CMPCT against in-process ZIP as if it were one timing layer;
- never use one private-corpus number as a general format claim;
- never publish private corpus identity/artifact provenance merely to decorate the engineering history.

See `docs/BENCHMARKS.md` and `benchmarks/history/` for public reproducible evidence.

## Immediate high-value development missions

### Mission 1 — conformance and hostile-parser foundation

Create golden revision-24 archives and byte-exact vectors for every storage description/codec. Add
fuzz/property tests for corrupt headers, indexes, blob sizes, chunk maps, sparse extents, nested
recipes, journal generations, path traversal and decompression-bomb/resource limits. This is the most
important prerequisite before increasing format complexity.

### Mission 2 — benchmark CI and reproducible result archive

Run the universal corpus in controlled CI. Record CPU, OS, filesystem, Python/native library versions,
cache state, codec settings, durability and metadata semantics. Commit every accepted public benchmark
dataset under `benchmarks/history/` with the commit SHA that produced it. Keep
`benchmarks/zip_parity_bench.py` as the explicit gate for every fair ZIP advantage.

### Mission 3 — deterministic mode and normative schema

Turn revision 24’s working format document into a byte-level interoperable contract: canonical integer
encodings, ordering, path normalization, endianness, bounds, index schemas and deterministic creation rules.

### Mission 4 — native core

Continue the memory-safe Rust core now present under `native/cmpct-core/` while keeping Python as the
readable executable specification and cross-check oracle. The current native slice authenticates/
decodes the primary index, applies lexical path policy, enumerates entries, bounds base blobs, exposes
a tested C ABI, reads direct RAW ranges without decoding unrelated data, reads bounded ordinary
direct-Zstd/raw-Deflate ranges with whole-member authentication, and serves fixed/CDC/sparse maps
range-locally across mixed codecs while preserving logical SHA checks for complete reads.
Zstd-with-dictionary direct blobs cross the fixed C-ABI oracle with dictionary/member corruption
refusal. Next add WAV-FLAC direct blobs and virtual ZIPs; then sequential member streams,
committed-generation recovery and extraction. Native code must remain conformance-identical, and the
same core must expose the list/stat/read/range/stream/extract surface required by platform handlers so
portability does not fork format semantics.

### Mission 5 — size frontier without random-access regression

Investigate reversible preprocessing for Deflate and other common compressed structures, but only with
licensed/audited techniques and exact reconstruction. Also improve cheap candidate probing so
expensive codecs are not run just to discover that RAW or ordinary Zstd wins.

### Mission 6 — erase practical ZIP advantages and ship first-class archive UX

Treat stable fair ZIP wins as performance defects. Prioritize creation/extraction hot paths,
startup/import overhead, fused validation and native read-only startup until ZIP has no unexplained
material advantage on the parity corpus. In parallel, implement the `docs/PORTABILITY.md` contract:
Android DocumentsProvider/app integration, Linux MIME/browser integration, Windows file
association/browser support, and Apple UTType/document integration, all backed by the shared native
core. Do not claim platform support until the corresponding package passes conformance archives on
that platform/emulator.

### Mission 7 — public-release readiness

Keep `tools/check_public_surface.py` green, maintain the website as a self-contained project front door,
finish third-party provenance review, and resolve the non-final Apache-2.0 proposal before public
release. Publication must be an explicit action rather than an accidental side effect of ordinary
`main` pushes.

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
- a permanent hidden ZIP shadow inside every CMPCT archive merely to gain legacy file-manager recognition.

## When to bump the format revision

Bump the on-disk revision when a reader must understand a new physical field/record/storage-description/
codec semantic to read newly created archives. Encoder-only heuristic changes that still emit the
exact same revision-24 grammar do **not** require a format revision, but they do require benchmark/
regression documentation.

Any format bump must update, in the same commit:

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
