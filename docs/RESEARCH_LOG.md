# CMPCT research and decision log

This document records the most important experimental conclusions behind the current design. It is
intentionally more explanatory than `docs/HISTORY.md`: the goal is to prevent future agents from
repeating already-resolved experiments without new evidence. Private development-corpus identities
are intentionally generalized because the engineering conclusion matters; unrelated private
provenance does not.

## Decision 1 — Zstd is the general compressor, not the archive format

Early whole-archive testing on a mixed source/media/archive workload showed Zstd-3 to be a very strong
speed/size default. It compressed and extracted much faster than Deflate ZIP while also producing a
smaller whole-archive stream in that experiment.

But plain `.tar.zst` lost ZIP-like selective access and file indexing. Therefore the project separated:

- **container/index semantics** from
- **compression codec choice**.

CMPCT must stay codec-agile. Zstd is the workhorse, not the definition.

## Decision 2 — fixed-size frames are not universal

A 256 KiB frame size looked attractive for random access, but a 3.6 KiB file inside a shared 256 KiB
frame forced decoding far more data than ZIP’s independent entry model.

File-aligned small frames removed that disadvantage. Larger files can still be chunked for range access.

**Rule:** framing/chunking must be adaptive and file-aware. No global frame size is sacred.

## Decision 3 — TAR is not the canonical internal container

Seekable Zstd over TAR proved that random access was possible, but TAR itself contributed historical baggage:

- filename lookup required a separate index;
- file updates shifted logical offsets;
- selective access was byte-range based rather than object-native;
- the archive layer did not naturally express content-addressed deduplication, sparse extents or transactional generations.

TAR remains a possible import/export target. It is not CMPCT’s canonical structure.

## Decision 4 — content semantics beat extension folklore

A file extension can be used as a cheap hint, but must never dictate storage representation.

Examples from development:

- PCM WAV sometimes compressed extremely well with FLAC, but on adversarial periodic audio a general compressor could beat FLAC.
- already-compressed/random media should often be stored RAW rather than recompressed;
- nested ZIPs sometimes benefit from virtualization/deduplication, but a group of exact nested archive bytes sometimes compresses better as one indexed Zstd group.

**Rule:** the encoder may probe multiple exact representations and choose according to size/latency policy.

## Decision 5 — tiny-file forests need microblocks

Thousands of tiny source/config files create per-entry metadata and compressor-reset overhead. Giving
every tiny file its own independent frame preserved selective access but wasted compression opportunity.

Microblocks group related tiny files into small independently decodable packs while the file index
points to each member’s byte range inside the microblock.

Historical result on a 3,200-file synthetic corpus:

- ordinary ZIP: ~674 KiB;
- CMPCT microblock prototype: ~177 KiB;
- reading all files: ~32 ms ZIP vs ~2.5 ms CMPCT in the measured checkpoint.

**Rule:** solid compression is acceptable only in bounded microblocks that preserve practical selective access.

## Decision 6 — canonical storage should understand duplicate content

An early mixed-workload corpus exposed many byte-identical files in build/output trees. Ordinary ZIP
stores each path as a separate compressed payload. CMPCT separated logical names from physical content
blobs, allowing many paths to reference one stored object.

This generalized naturally to:

- hardlinks;
- duplicate files;
- nested archive members shared with top-level files;
- future global/object-store deduplication.

**Rule:** deduplication is content-addressed and transparent; a standalone archive remains self-contained unless explicitly using an external store mode.

## Decision 7 — nested archives require adaptive treatment

Three strategies were tested conceptually and in prototypes:

1. treat nested archive as opaque bytes;
2. virtualize it into member payloads + exact reconstruction recipe;
3. group exact nested archive bytes with similar archives into a compressed indexed object.

No one strategy always wins.

Virtualization is powerful when nested members duplicate top-level or cross-archive content. It can be
a latency loss when exact Deflate streams must be regenerated. Exact raw-Deflate reuse solved much of
that latency, but carrying every stream verbatim can hurt size.

**Rule:** nested-container introspection is an encoder optimization, never a semantic requirement. The original bytes must be recoverable exactly.

## Decision 8 — exact Deflate reuse is useful even in a non-ZIP canonical format

A substantial portion of the early mixed-workload corpus consisted of nested ZIP/WHL Deflate streams.
Those compressed bytes are entropy-dense and do not recompress well with Zstd.

When the same logical payload is needed both as a top-level file and inside a nested ZIP, preserving one exact Deflate stream can be efficient:

- top-level read inflates it;
- nested ZIP reconstruction copies it directly;
- legacy ZIP export copies it directly.

libdeflate made decoding faster, but the stored representation remains ordinary Deflate. Therefore
libdeflate is an optional acceleration, not a format dependency.

A reversible Deflate preprocessor can sometimes reduce the storage cost of exact Deflate streams by
storing a transform that reconstructs the original bytes bit-exactly. v0.28 now experiments with this
through a pinned memory-safe preflate bridge, but that transform remains **research-only** until its
reader-visible contract, resource bounds and native portability are independently specified.

## Decision 9 — strong integrity belongs in the format, but not necessarily every hot read

Early designs risked SHA-256 work on every file extraction/read. That was unnecessarily expensive for routine corruption detection.

The design split integrity:

- CRC32: cheap hot-path corruption check;
- SHA-256: authoritative content identity and explicit strong verification;
- index/footer hashes: metadata integrity/commit validation.

**Rule:** expensive cryptographic verification is available and authoritative, but normal reads need not pay for it unless policy requests it.

## Decision 10 — recovery must not depend on one central directory

ZIP has mature repair tooling, but its normal open path depends heavily on the central directory.

CMPCT experiments demonstrated stronger internal recovery through:

- head and tail indexes;
- self-describing blob records;
- independent chunk/frame boundaries;
- transactional commit footers;
- fallback to previous committed generation;
- scanning physical blobs when indexes are damaged.

**Rule:** the latest committed logical state should be recoverable after plausible metadata-tail damage, and corruption of one chunk should not unnecessarily poison unrelated chunks.

## Decision 11 — updates are transactional, not just appendable

A naive append update was initially slower/larger than ZIP. The fix was not to drop crash safety; it was to improve the journal design.

A compact delta journal reduced update growth below the measured ZIP append while preserving a commit
marker and old-generation fallback. Fair `fsync` comparison also showed that durability semantics
matter: non-durable ZIP append timings are not equivalent to durable CMPCT commits.

**Rule:** benchmark mutations only under equivalent durability semantics.

## Decision 12 — sparse holes and link semantics are data-model features

ZIP-like tools often materialize sparse zero ranges and link targets. That can explode size and extraction work.

CMPCT treats:

- sparse extents as logical holes + real data extents;
- hardlinks as multiple names for one filesystem object relationship;
- symlinks as links, not copied target bytes.

This produced very large wins on synthetic sparse/link workloads while also being semantically more faithful.

**Rule:** filesystem semantics must not be silently flattened into duplicate payload bytes.

## Decision 13 — content-defined chunking is for evolving large files

Fixed chunk boundaries lose deduplication after insertions/deletions near the front of a large file because every later boundary shifts.

Content-defined chunking (CDC) rediscovers boundaries based on nearby content, allowing later regions to match previous versions.

Revision 24 records explicit `[logical length, blob reference]` descriptions, so readers never need the
CDC algorithm. The optional native CDC helper is creation-time acceleration only.

**Rule:** chunk-boundary algorithms are encoder policy; stored chunk maps are reader semantics.

## Decision 14 — ZIP compatibility is an endpoint, not the canonical storage tax

v0.5 proved CMPCT could use ZIP method 93 and remain readable by modern Zstd-aware ZIP tooling. That experiment was valuable and remains relevant for compatibility.

But keeping ZIP’s physical layout as the canonical storage prevented deeper gains from content-addressed
deduplication, nested-container recipes, microblocks, sparse extents and transactional generations.

The project therefore moved to:

- native CMPCT canonical storage;
- import/export/compatibility views for ZIP and potentially other formats.

Fast ZIP export reuses exact Deflate streams when available, avoiding needless transcoding.

## Decision 15 — benchmark semantics must be explicit

Several early results changed interpretation once process startup, Python import cost, filesystem
metadata restoration, cache warmth, native-vs-Python codec overhead, or `fsync` durability were isolated.

Future benchmark records must state at minimum:

- source commit/revision;
- corpus construction/hash or generator version;
- archive settings;
- CPU/OS/filesystem;
- library versions;
- warm/cold cache policy;
- in-process vs process-start timing;
- metadata restoration semantics;
- integrity work performed;
- durability/fsync semantics;
- repetitions/statistic used.

## Decision 16 — near-equal information needs measured resemblance, not only exact CDC

v0.25 removed large classes of **exact** redundancy, yet shifted-version and boundary-churn attacks
showed that two objects can carry almost the same information without containing enough exact equal
chunks for ordinary CDC to exploit.

EntropyGraph II therefore adds bounded local sketches and LSH only as candidate discovery. Every
candidate base/target pair is then encoded into a concrete COPY/LITERAL delta, compressed, charged for
its metadata, and admitted only when the complete stored representation wins materially.

The fixed public evidence validates the mechanism where expected:

- shifted versions: **30,200,827 → 1,761,588 B (-94.17%)**;
- repeated boundary churn: **866,651 → 89,945 B (-89.62%)**.

False-neighbor and incompressible workloads do not receive a free pass; they fall back to the inherited
representation when the graph loses.

**Rule:** similarity can nominate work. It cannot prove correctness or compression value.

## Decision 17 — resemblance dependencies stay depth-1

Unlimited delta chains can save bytes but export hidden random-read latency, corruption fan-out,
recovery complexity and decoder-memory requirements.

v0.28 selects central bases by measured aggregate savings and forbids a selected base from itself being
a delta target. A logical node is therefore direct or depends on exactly one direct base plus one delta.

**Rule:** a byte win does not justify unbounded dependency depth. Deeper graphs need new evidence and a
new explicit contract rather than becoming the default because the encoder can construct them.

## Decision 18 — solid context is a budgeted resource, not a fixed virtue

A universal 512 KiB context ceiling left some resemblance locality on the table, but simply increasing
the window would repeat the old fixed-frame mistake in the other direction.

EntropyGraph II auditions **64/128/256/512 KiB, 1 MiB and 2 MiB** physical packs, measures final bytes,
and accounts for weighted decoded-bytes/logical-bytes read amplification. Wider context is accepted only
when it materially earns bytes and remains within **8x**. Otherwise the encoder keeps the 512 KiB plan.

**Rule:** context width is an optimization variable with an exported-read-cost budget, not a constant.

## Decision 19 — representation portfolios can enforce a no-size-regression frontier

A new research mechanism should not be forced into workloads merely to make the implementation visible.
EntropyGraph II builds both its graph candidate and the inherited v0.25 candidate and selects the smaller
complete artifact per workload.

Across the fixed 15-workload public suite this yields **3 improved / 0 regressed / 12 exact inherited
fallbacks**, for **137,557,457 B vs 166,816,028 B (-17.5394%)** overall.

This exports extra creation CPU, which remains visible. A future conservative cost model may skip obvious
losers, but prediction must not replace final byte measurement for candidates that are admitted.

**Rule:** fallback can preserve the Pareto frontier, but its audition tax must be measured rather than
pretended away.

## Decision 20 — fresh-process parallelism must earn startup cost separately

Deterministic parallel candidate encoding improved many in-process and large-workload creation timings,
but the first post-reconciliation v0.28 ABBA gate found one confirmed fresh-process regression:
media CLI creation measured **192.99 → 203.07 ms (+5.22%, +10.08 ms)** while the corresponding library
path moved by less than 1 ms.

The release candidate therefore keeps the in-process `Builder` parallel default but makes a fresh
`cmpct create` serial unless `--workers N` is explicitly supplied.

**Rule:** library throughput and process-start latency are separate products. Do not make every tiny CLI
invocation pay thread-pool setup because parallelism helps a large in-process benchmark.

## Rejected or superseded ideas

### Fixed 256 KiB framing for all files
Rejected because tiny already-open reads did unnecessary decompression. Replaced by adaptive file-aware framing/microblocks/chunk maps.

### Seekable TAR+Zstd as the final format
Rejected as canonical architecture. Kept as evidence that seekable Zstd itself works well.

### Always use FLAC for WAV
Rejected. Exact representation competition is better.

### Always virtualize nested archives
Rejected. Some nested archives are better treated as opaque/grouped exact bytes.

### Recompress already-compressed media anyway
Rejected. RAW/direct mmap storage can be smaller and much faster.

### Keep exact Deflate streams for every reproducible member
Superseded by policy that keeps them when they buy latency/compatibility value; cold streams can sometimes be regenerated from raw data + deterministic recipe.

### Store SHA-256 redundantly in every index layer
Rejected as needless random metadata overhead. Keep one authoritative content hash and reference it.

### Require libdeflate, native CDC or preflate to read canonical r24 archives
Rejected. Optional accelerators/research transforms must never become accidental canonical format dependencies.

### SHA-256 on every normal extraction
Rejected as unnecessary hot-path cost. Strong verification is explicit.

### Optimize the format around one private development corpus
Explicitly rejected. The universal/adversarial harness is mandatory for general policy changes.

### Whole-file MinHash + unbounded whole-file binary deltas
Rejected as the primary resemblance design. Large objects create base-memory debt and local insertions can destabilize whole-file similarity. Use bounded units and bounded source indexing.

### Unlimited delta chains
Rejected. They improve a scalar while exporting dependency/recovery/read debt. v0.28 caps graph depth at one.

### Trust similarity score as a compression decision
Rejected. Sketch collisions are expected. Concrete encoded bytes decide admission.

### Always use the largest available solid pack
Rejected. Wider context must win bytes and stay inside the read-amplification budget.

### Rerun a barely failed performance gate until it turns green
Rejected as process policy. Isolate the mechanism or improve measurement quality; do not use CI variance as a release strategy.

## Research directions still open

- productionize proven EntropyGraph-II representations one reader-visible semantic at a time;
- reduce portfolio audition cost with a conservative predictor that never overrides measured admission;
- independently specify/audit exact Deflate preprocessing before any canonical transform registry entry;
- vectorized/native entropy-coding research after structural redundancy is exhausted;
- authenticated encryption with modern KDF/AEAD and metadata authentication;
- production remote/object-store partial reads and verification;
- complete cross-platform deterministic encoding contract;
- representation-complete native memory-safe parser/encoder core;
- scalable streaming CDC/resemblance discovery;
- cross-archive optional content stores;
- richer platform metadata and ACL semantics;
- split-volume archives and non-seekable streaming creation;
- mount/file-manager integration;
- standardized codec/transform registry.

Any future experiment that contradicts a decision above is welcome **if it brings new measured evidence**.
The purpose of this log is to preserve reasoning, not freeze the project against better ideas.
