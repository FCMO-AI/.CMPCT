# CMPCT EntropyGraph — v0.25 research milestone

Date: 2026-08-16

## Result

This pass deliberately stopped optimizing against any single development corpus and introduced a fixed, deterministic, hostile mixed-workload suite. The experimental engine now treats an archive as an authenticated reconstruction graph rather than merely a bag of independently compressed files.

The fixed neutral/hostile suite contains **8,529 files / 172,447,100 logical bytes across 10 workloads**. CMPNX5 v0.25 research candidate stores **90,383,940 bytes (52.41% ratio; 47.59% saved)**. On the same exact trees:

- ZIP + Zstandard method 93: 108,186,167 B
- ZIP + Deflate-9: 111,420,511 B
- solid tar + Zstandard-19 diagnostic: 97,097,211 B

Therefore the candidate is **16.46% smaller than ZIP/Zstd-93**, **18.88% smaller than ZIP/Deflate-9**, and **6.91% smaller than the monolithic solid tar+Zstd-19 diagnostic in aggregate**. It wins 8/10 workloads against ZIP/Zstd-93 and 6/10 against solid tar+Zstd-19. Losses are retained in the report rather than hidden.

Worst adversarial expansion is the intentionally incompressible/encrypted-like workload: **+0.1086%**. That remaining cost is chiefly the price of paths/index/recovery/integrity, not failed payload compression.

## Fixed hostile corpus

The corpus is generated with independent deterministic per-workload PRNG seeds. Each workload can be regenerated in isolation without changing its bytes.

1. Developer repository: source, tests, package lock, compiled ELF binaries, simulated Git compressed objects.
2. Office workspace: valid DOCX/XLSX/PPTX/PDF plus standalone JPEG/PNG assets.
3. Media library: JPEG/PNG, valid H.264/AAC MP4, WAV, FLAC, MP3.
4. Analytics/database: CSV, JSONL, SQLite, NumPy NPY/NPZ.
5. Logs/telemetry: raw logs beside gzip/xz/zstd compressed rotations.
6. Incremental backups: mostly shared snapshots plus a ZIP containing exact snapshot members.
7. Incompressible/encrypted-like: random blobs and many random tiny objects.
8. Many tiny files: 5,000 structured/random items.
9. ML artifacts: q4-like weights, scales, tokenizer JSON, training log.
10. Large mixed binary: a 32 MiB mixed-entropy disk-image-like object.

Promotion rule: every workload is reported; use byte-weighted and macro results; report the worst workload; never drop an inconvenient corpus.

## New representation architecture

### 1. Global compressed-stream federation

ZIP-like containers are inspected globally rather than judged only by local duplicate-stream savings. A document family can therefore share exact compressed member streams across DOCX/PPTX/XLSX siblings.

### 2. Entropy-oriented representation inversion

When two required logical objects are exact reversible views of the same information, the encoder is free to choose which direction is physically stored.

Example: if a standalone JPEG is exactly the plaintext of a Deflate member whose exact compressed stream is already required to reconstruct a PPTX, CMPCT stores the required Deflate stream once and materializes the loose JPEG by cheap inflation. It does **not** store the JPEG again or recompress it during extraction.

This is generalized to exact compressed sidecars such as gzip/xz/zstd/bzip2 when a required compressed file deterministically decodes to another required loose file.

### 3. Exact object interning

Identical logical payloads across snapshots are physically stored once. Aliases retain independent names but add no duplicate payload.

### 4. Proof-carrying reconstruction graph

Per-file SHA-256 values that duplicated already-authenticated truth were removed. Strong identity is instead formed by:

- SHA-256 on every physical pack;
- authenticated reconstruction metadata;
- authenticated canonical tree root;
- exact deterministic reconstruction recipes.

Normal extraction uses CRC32 as the hot corruption tier for ZIP-comparable cost. Explicit strong verification authenticates every physical pack and then reconstructs and checks the canonical tree hash.

### 5. Implicit micro-pack index

For tiny files physically concatenated in one pack, offsets are mathematical consequences of preceding lengths. The on-disk metadata stores the pack once and an ordered `(path, length)` table rather than repeating `plain -> slice -> pack -> offset -> length` for thousands of files.

### 6. Adaptive bounded-context audition

Each file family auditions 32/64/128/256/512 KiB same-family solid contexts with a cheap probe. Wider context is allowed only when it materially improves size, and 512 KiB is a hard physical decode ceiling.

This reduced the developer workload from 790,184 B in the prior candidate to 746,524 B, and the 5,000-tiny-file workload to 420,322 B.

### 7. Hot/cold stream roots

Global stream federation originally created one multi-megabyte shared pool, which looked good in aggregate extraction but hurt single-file reads. CMPNX5 corrects this:

- latency-sensitive streams used to materialize loose inverse views become stream-aligned **hot roots**;
- hot roots are stored directly in <=512 KiB slabs to avoid an extra decompression layer;
- cold container-only streams may share bounded slabs and compete against cheap Zstd-3;
- no stream federation pack exceeds the normal 512 KiB target.

Measured examples on the office workload:

- 495,699 B derived JPEG: CMPCT ~0.69 ms median vs ZIP/Zstd-93 ~0.37 ms;
- 3,753,100 B PPTX: CMPCT ~1.55 ms vs ZIP/Zstd-93 ~5.50 ms.

A derived 163,840 B backup blob measured ~0.120 ms for CMPCT vs ~0.123 ms for ZIP/Zstd-93.

### 8. Recovery that actually recovers

Earlier experimental artifacts wrote authenticated tail metadata but opened only the primary copy. CMPNX5 makes the redundant copy operational. The reader first authenticates primary metadata; on failure it reads and authenticates the tail copy, derives the pack-table start, and continues.

Two deliberate corruption tests passed full strong verification:

- primary compressed metadata byte corrupted;
- header magic corrupted.

## Where CMPCT still loses

The suite intentionally preserves these losses:

- Developer repository: solid tar+Zstd-19 remains ~3.5 KiB smaller than the candidate.
- Media: solid tar+Zstd-19 remains ~3 KiB smaller; ZIP/Deflate-9 is also slightly smaller.
- ML artifacts: ZIP/Zstd-93 and solid tar+Zstd-19 are both slightly smaller.
- Large mixed binary: ZIP/Zstd-93 and solid tar+Zstd-19 are slightly smaller.
- Analytics `features.npy` inverse view is much smaller in archive size but has ~15 ms selective materialization vs ~5.4 ms from ZIP in the current Python prototype because it requires decoding a multi-megabyte Deflate-derived representation across several bounded slabs.

These are next targets, not exclusions.

## Research context and next frontier

Microsoft's `preflate-rs` demonstrates that exact DEFLATE bitstreams can be represented as plaintext plus compact reconstruction corrections and rebuilt bit-exactly. That validates a future avenue for removing deterministic DEFLATE shadows when inversion alone is not enough. This v12 prototype **does not implement Preflate**; its gains come from exact stream federation and directional inverse-view storage.

A second likely runtime upgrade is replacing stock Python/zlib inflation on hot Deflate views with `libdeflate`, whose upstream implementation is specifically optimized for whole-buffer DEFLATE decompression. That is an implementation speed opportunity rather than a change to the information model.

The larger design direction is to formalize CMPCT as an **information-graph compiler**:

- nodes = required logical byte objects plus admissible latent representations;
- edges = exact reversible transforms with measured storage/create/read costs;
- roots = physically stored representations;
- optimization = choose roots, transforms, pack topology, and dependency directions that minimize bytes under hard recovery, dependency-depth, create-time, full-extract, and selective-read budgets.

The current heuristics are already a working approximation of that compiler. A future revision should make the cost graph explicit and solve the representation choice globally rather than through sequential local gates.

## Status

Project **v0.25.0** publishes this work as a reproducible research milestone while the canonical executable format remains **revision 24**. `CMPNX5` is an experimental benchmark engine, not a claim that its reader-visible semantics are already canonical. Promotion still requires integration with filesystem fidelity, CLI/API, portability, fuzzing, conformance, and compatibility layers of the main implementation.

## Publication boundary

Only the neutral/hostile generator, generalized engineering conclusions, and independently rerunnable public measurements belong in the repository. Private development corpora may continue to serve as local regression signals, but their names, paths, hashes, artifact filenames, contents, or organization-specific provenance must never enter public release notes or benchmark history.
