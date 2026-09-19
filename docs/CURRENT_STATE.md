# CMPCT current development state

This document is the **zero-chat-history handoff** for a new agent. Read it together with:

- `README.md` — project mission, current performance position and quick start;
- `AGENTS.md` — mandatory development, performance and versioning behavior;
- `docs/AGI_ENGINEERING_STANDARD.md` — mandatory quality ratchet, invention protocol, evidence hierarchy and adversarial completion standard;
- newest applicable note under `docs/releases/` — project-version milestone;
- `docs/PERFORMANCE_RELEASE_GATE.md` — candidate-vs-base no-regression contract;
- `docs/FORMAT.md` — current revision-24 on-disk contract;
- `docs/HISTORY.md` — surviving format/development history with private provenance generalized;
- `docs/ENTROPYGRAPH.md` — current research representation frontier;
- `docs/ENTROPYGRAPH_II_CAMPAIGN.md` — falsifiable v0.28 campaign design, gates and negative-evidence map;
- `docs/BENCHMARKS.md` and `benchmarks/history/` — benchmark semantics and durable public records;
- `docs/HARDENING.md` — hostile-parser and resource-boundary status;
- `docs/PORTABILITY.md` — ZIP-parity UX and first-class Android/desktop integration contract;
- `docs/NATIVE_CORE.md` — shared memory-safe reader/ABI capability and next representation gates;
- `docs/PUBLIC_SURFACE.md` — public disclosure boundary;
- `LICENSING.md` — non-final Apache-2.0 licensing proposal;
- `docs/ROADMAP.md` — work required before a defensible 1.0.

## Project objective

CMPCT is intended to become a **general-purpose lossless archive/container format and engine** for
arbitrary computer files and filesystems. The target is not merely “smaller ZIP.” The target is a
stronger default across size, creation/extraction speed, random access, integrity, recovery,
filesystem fidelity, crash-safe updates, remote-read potential, codec agility and ordinary end-user
portability.

The project is deliberately hostile to benchmark theater. Private corpora can be useful local
regression signals, but no private corpus may define public encoder policy or public claims. Public
evidence must be reproducible from public/deterministic workloads and must preserve losing cases.

## Canonical authority

Repository: `FCMO-AI/.CMPCT`

Branch: `main`

Current project version: **v0.28.0**

Current canonical executable format: **revision 24**

Project version and format revision are intentionally independent. v0.28.0 is the EntropyGraph II /
Resemblance Compiler **project/research milestone**: bounded resemblance discovery, measured depth-1
deltas, adaptive locality-bounded physical context, exact optional DEFLATE precompression research,
strict remote-range/fuzz/resource work and deterministic parallel-creation semantics are now durable
repository capabilities. The fixed public research portfolio stores **137,557,457 bytes** versus
**166,816,028 bytes** for inherited v0.25 across 15 workloads (**17.5394% smaller**), with **3 improved
and 0 regressed** because losing workloads retain the inherited artifact unchanged.

That does **not** make CMPNX8 canonical revision-24 grammar. Ordinary canonical Python/native archive
semantics remain r24; reader-visible graph promotion requires a future on-disk revision with independent
vectors, hostile parser/resource tests, recovery semantics, native parity and portability/export rules.

v0.27.0 introduced the mandatory AGI-grade engineering standard and material-PR evidence gate; v0.27.1
synchronized this zero-chat handoff with that contract. The v0.26 performance-release machinery remains
the executable no-regression foundation underneath v0.28.

`main` HEAD is the canonical implementation state. Everything created outside this repository is
experimental until reconciled into `main` with the required version, tests, benchmark record and
release documentation.

## v0.27+ engineering-quality contract

Every material task is governed by `docs/AGI_ENGINEERING_STANDARD.md`. “AGI-grade” is an engineering
quality shorthand, not a claim that a contributor, model or tool possesses AGI.

The repository-level quality ratchet requires future work to:

1. establish the observed problem/opportunity, direct baseline and invariants before implementation;
2. identify the dominant cost/failure mechanism and state a falsifiable hypothesis plus practical
   disproof test;
3. consider meaningfully different solution classes for non-trivial work instead of reflexively taking
   the first conventional implementation;
4. prefer mechanism-level/Pareto improvements and independent evidence over threshold tuning or prose;
5. preserve losing workloads, ambiguous results and rejected experiments that carry future information;
6. perform adversarial self-review across pathological inputs, resource bounds, integrity, recovery,
   locality, filesystem semantics and portability where relevant;
7. account for hidden exported costs such as peak memory, bytes decoded, dependency depth, temporary
   materialization and reader complexity;
8. expose the completion dossier in the PR so a skeptical reviewer can falsify the claimed mechanism.

`.github/workflows/engineering-evidence.yml` and `tools/check_pr_evidence.py` enforce the structural part
of that contract for material PRs. They deliberately do not assign a synthetic “genius score”; technical
quality remains grounded in tests, independent oracles, benchmark evidence and expert-level causal
reasoning. Changes to workflow/policy surfaces are themselves material under version discipline so the
quality gates cannot be silently weakened through a supposedly “docs-only” or CI-only change.

## v0.26+ performance-release contract

Performance is a merge requirement rather than optional telemetry.

Every numeric core release must:

1. advance `pyproject.toml` and add `docs/releases/vX.Y.0.md` under the current scarce-version policy;
2. run the candidate benchmark harness against the direct base and candidate engines;
3. generate **one corpus tree** and make both engines consume that exact tree on the same runner;
4. fingerprint the corpus and record process/cache/integrity semantics;
5. reject any deterministic CMPCT archive-size increase on the release parity corpus;
6. reject create/extract slowdowns that clear both sides of the documented same-runner noise envelope;
7. commit the accepted candidate result under `benchmarks/history/` before merge;
8. keep every losing/adversarial workload visible.

`tools/check_performance_regression.py` applies the direct comparison. `.github/workflows/zip-parity.yml`
owns the release benchmark topology. `docs/PERFORMANCE_RELEASE_GATE.md` is the normative policy.

A crucial v0.26 hardening lesson is already encoded in the tooling: the old universal generator used
independent random bytes and current ZIP timestamps, so two unchanged engines could receive different
input and appear to regress or improve by a few bytes. The corpus generator is now deterministic, and
the release gate additionally generates the tree once, freezes controllable metadata and reuses it for
both engines. **Do not loosen the zero-byte size rule to accommodate a bad benchmark substrate. Fix the
substrate instead.**

v0.28 added a second concrete lesson. Its first reconciled ABBA run found one fresh-process regression:
media CLI creation measured **192.99 → 203.07 ms (+5.22%, +10.08 ms)** while the underlying library path
moved by less than 1 ms and twenty other timing cells improved. The release candidate did not rerun until
lucky; it removed the exported thread-pool startup from the default CLI path. In-process `Builder` keeps
parallel creation by default, while fresh `cmpct create` stays serial unless `--workers N` is requested.
The failed run remains evidence and the fix must pass a fresh direct-base gate.

## Public website state

`site/` is the public human/agent front door and is deliberately performance-first. The experience is
designed so the first screen creates impact, the second proves the performance claim, and the rest
explains the engineering and qualifications.

The generated site includes:

- a live research-frontier headline sourced from committed benchmark history;
- benchmark-declared comparisons rather than one hard-wired competitor label;
- a workload-level win/fallback/loss matrix and explicit frontier defects;
- an information-graph explanation of the EntropyGraph direction;
- a strict canonical-vs-research boundary;
- canonical ZIP parity with separate library and fresh-process CLI layers;
- the current no-regression release law;
- Browser Lab local archive creation and header inspection;
- a project-version trajectory.

`site/build_site.py` builds the canonical data package and `site/frontier_v028_adapter.py` normalizes the
new v0.28 research schema after build without renaming structural competitors. `frontier-v028.js`
changes labels only when that explicit schema is present. For v0.28 the primary research comparator is
**inherited EntropyGraph v0.25**, while ZIP/Deflate, 7z/LZMA2, solid tar/Zstd, ZPAQ and Borg are displayed
from the structural sweep under their real names. Large performance percentages are not hand-maintained
in HTML.

The Pages workflow rejects a site whose project version, release note, benchmark frontier, canonical
parity evidence, JavaScript or Browser Lab compatibility do not agree. It additionally asserts that the
v0.28 frontier carries the EntropyGraph-II render contract, zero recorded size regressions and the
correct inherited comparator. Canonical `main` publishes automatically after those gates pass.

## EntropyGraph research frontier

v0.25 introduced the public neutral/hostile reconstruction-graph frontier: exact compressed-stream
federation, directional inverse views, exact object interning, implicit micro-pack indexing, bounded
context, hot/cold stream roots, authenticated metadata and operational recovery. Its durable record
remains `benchmarks/history/2026-08-16-entropygraph-v025.json`.

v0.28 builds on that model with **bounded resemblance reuse** rather than pretending near-equal objects
are unrelated. Current research mechanisms now include:

- deterministic bounded FastCDC-style units;
- bounded multi-band similarity candidate generation;
- measured COPY/LITERAL deltas whose compressed+metadata cost must beat direct storage;
- central-base selection with maximum dependency depth **1**;
- similarity-ordered root packing auditioned from **64 KiB through 2 MiB**;
- <=**8x weighted read amplification** for admitted pack plans;
- optional exact preflate transformation through a pinned memory-safe bridge;
- explicit physical decode-unit and decoder-memory ceilings;
- Merkle-authenticated physical payload leaves plus logical SHA-256/CRC checks;
- authenticated primary/tail metadata recovery;
- strict remote range sources that cannot silently fetch entire archives;
- a measured portfolio that emits inherited v0.25 unchanged when resemblance loses.

The durable v0.28 record is `benchmarks/history/2026-08-16-entropygraph-v028.json`. Across its fixed 15
workloads the portfolio is **17.5394% smaller than inherited v0.25**, with the major mechanism wins on
shifted versions (**-94.17%**) and repeated boundary churn (**-89.62%**). Twelve workloads deliberately
fall back unchanged. On the resemblance-hostile structural aggregate CMPCT stores **47,197,165 B**, in
the same size class as tar+Zstd-19 solid (**47,065,652 B**), ZPAQ m5 (**47,062,641 B**) and 7z/LZMA2
(**47,430,344 B**) while retaining a different bounded locality/recovery contract. These remain
**research-frontier results, not canonical r24 interoperability claims**.

Promotion into the canonical format must happen one representation at a time with independent golden
vectors, hostile parser/resource tests, bounded selective-read accounting, recovery semantics, ZIP
compatibility/export semantics and native-core parity.

## Current implementation architecture

`src/cmpct/codec.py`
: Canonical representation primitives, Zstd/Deflate/FLAC handling, content-defined chunking interface,
  exact nested-ZIP reconstruction helpers and integrity primitives.

`src/cmpct/builder.py`
: Filesystem scan, candidate/representation selection, deduplication, dictionaries/microblocks,
  sparse/link handling, reproducible build policy and deterministic parallel physical construction.

`src/cmpct/reader.py`
: Archive parsing, index recovery, logical reads, range reads, extraction, verification and salvage.

`src/cmpct/transactions.py`
: Append generations, mutation journal, rename/delete/update behavior, checkpoints and commit-footer
  semantics.

`src/cmpct/cli.py`
: User-facing create/info/list/read/range/extract/verify/export/recovery operations. Fresh-process create
  is serial by default after the v0.28 startup-regression finding; `--workers N` explicitly enables
  deterministic parallel candidate encoding.

`src/cmpct/resemblance.py`
: Reusable deterministic bounded chunking, similarity sketches/LSH, rolling COPY/LITERAL deltas,
  bounded delta decoding, central-base selection and similarity ordering used by EntropyGraph II.

`experiments/entropygraph_v025.py`
: Historical executable research-only CMPNX5 reader/writer and exact per-workload fallback for v0.28.

`experiments/entropygraph_v028.py`
: EntropyGraph II CMPNX8 research writer/reader with measured resemblance edges, adaptive physical
  packing, Merkle-authenticated records, preflate transform audition and exact inherited fallback.

`experiments/entropygraph_v028_strict.py`
: Strict-locality research engine that enforces the campaign's independent-read floor and <=8x bounded
  amplification contract.

`experiments/entropygraph_v028_remote.py`
: Strict byte-range source/reader work that refuses silent whole-archive fallback.

`benchmarks/universal_bench.py`
: Deterministic heterogeneous canonical corpus generator. Random-looking bytes use a fixed benchmark
  PRNG rather than `os.urandom`, and nested ZIP members have fixed timestamps.

`benchmarks/zip_parity_bench.py`
: Fair CMPCT-vs-ZIP harness with separate library/CLI timing. It can consume an externally supplied
  immutable corpus so the release workflow can drive base and candidate engines through the same
  harness and exact input tree.

`benchmarks/neutral_hostile_corpus_v1.py`
: Broader deterministic-per-workload suite covering developer, office, media, analytics/database,
  logs, backups, incompressible, tiny-file, ML and large-binary workloads.

`benchmarks/resemblance_hostile_corpus_v1.py`
: Five deterministic attacks targeting shifted versions, false similarity neighbors, boundary churn,
  related DEFLATE containers and incompressible controls.

`native/cmpct_cdc.c`
: Optional creation-time content-defined chunk boundary accelerator. The reader does not depend on it.

`native/preflate-bridge/`
: Pinned memory-safe optional research bridge for exact DEFLATE precompression/reconstruction. It is not
  a canonical r24 reader dependency.

`native/cmpct-core/`
: Memory-safe Rust read-only core and C ABI. It authenticates/decodes the r24 primary index, applies the
  shared lexical path policy, bounds base blobs, and covers direct RAW, bounded direct
  Zstd/WAV-FLAC/raw-Deflate/Zstd-dictionary, fixed/CDC maps, sparse extents, checked `S_PACK` slices,
  and selected virtual-ZIP projection paths. The detailed representation/conformance matrix and open
  gaps live in `docs/NATIVE_CORE.md`; do not duplicate or fork those semantics here.

`site/`
: Performance-command-center website, generated project/benchmark data, evidence-schema adapters and
  local Browser Lab.

## Current canonical format capabilities

Revision 24 supports or prototypes:

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
- ZIP export, including reuse of stored Deflate streams where possible.

Treat these as **reference behavior**, not yet as a frozen 1.0 interoperability standard.
EntropyGraph-II CMPNX8 semantics are intentionally **not** included in this r24 capability list.

## Provisional v0.30 r25 filesystem-control integration

On `agent/v030-authoritative-integration`, the canonical r25 writer/reader admits the compact implicit-v4
filesystem control through the shared content-agnostic admission seam. The decisive exact-head A/B that
authorized landing reduced the developer-repository complete r25 artifact from **909,369 B to 844,116 B**
(**65,253 B saved**) while preserving exact user-tree semantics, strong verification and **1.0x** control-read
amplification. The explicit filesystem-v1 encoding remains the mandatory fallback on ties or any failed semantic
proof.

This is a D5 productization step, not release authority. Recovery/malformed-control parity, shared native parsing,
Android/platform parity, genuine r24 product-floor selection, exact all-workload competitor authority and the
strict release lock still must pass on one exact candidate before v0.30 can ship.

## Design invariants

1. **Byte-exact losslessness.** Extraction reproduces file bytes exactly unless a caller explicitly requests different semantics.
2. **Reader simplicity over encoder heuristics.** Archives record enough information that readers do not reproduce old encoder decisions.
3. **Content-driven representation.** Extensions are hints, never codec commands.
4. **Graceful incompressible case.** Already-compressed/encrypted/random data should approach input size + small metadata.
5. **Independent access.** Ratio gains must not silently create unbounded decode units.
6. **Filesystem fidelity.** Links, sparse holes and metadata are semantics, not baggage.
7. **Crash safety.** Incomplete mutation tails must not destroy the last committed generation.
8. **Recovery as a format property.** Critical metadata uses redundancy/scannability rather than one irreplaceable directory.
9. **Codec agility.** Zstd is a general codec, not the definition of CMPCT.
10. **No corpus overfitting.** Threshold changes need adversarial evidence and preserve losses.
11. **ZIP parity is a floor.** A reproducible ZIP advantage remains an engineering defect until explained or removed.
12. **Portability is product behavior.** A superior archive that ordinary devices cannot open is not yet a viable default.
13. **Public CMPCT stands alone.** Unrelated private provenance never enters release-facing surfaces.
14. **Core versions are scarce claims.** Numeric releases require a material product/engine improvement; presentation/process work uses `SURFACE_REVISION`.
15. **Numeric releases are benchmarked.** Every core version receives a direct-base benchmark and durable public record.
16. **No silent performance regression.** Identical-input archive-size growth is zero-tolerance; confirmed same-runner slowdowns block release.
17. **Evidence drives the website.** Public headline numbers are generated from committed records, not static copy.
18. **Quality ratchet is mandatory.** Material work must expose its baseline, causal hypothesis, disproof surface, negative evidence and relevant hidden costs; green tests alone are not completion.
19. **Research grammar is not canonical by implication.** A project-version milestone does not authorize older readers to interpret new experimental bytes.

## What is not yet production-grade or 1.0-ready

Major open areas include:

- normative byte-level format specification and complete index schema;
- complete conformance/golden archives and stable cross-version vectors;
- representation-complete parser fuzzing/property coverage and strict resource/bounds limits;
- deterministic archive mode as a fully specified user-facing canonical contract across platforms;
- formal codec/transform registry and capability negotiation;
- authenticated encryption and key derivation;
- complete ACL/Windows/macOS metadata/path normalization rules;
- split-volume and streaming/non-seekable creation;
- production remote HTTP/object-store range access with partial verification;
- representation-complete native reading, streaming/extraction and committed-generation recovery;
- scalable CDC without whole-file memory loading;
- robust Android/Linux/Windows/Apple archive browsing/file-manager integrations defined by `docs/PORTABILITY.md`;
- deliberate canonical promotion or rejection of EntropyGraph-II storage semantics after conformance/security/native integration;
- controlled-hardware benchmark infrastructure that can tighten timing envelopes and run the broader hostile suite continuously;
- formal adoption or rejection of the proposed Apache-2.0 license after provenance review.

## Benchmark interpretation

The benchmark system has three different roles and they must not be blurred:

1. **Release regression gate** — direct base vs candidate, one identical corpus, same runner; blocks backward movement.
2. **Canonical parity** — current executable CMPCT vs ZIP at explicit library and CLI boundaries.
3. **Research frontier** — broader EntropyGraph comparisons against the inherited research frontier and structural archive competitors under explicit semantic qualifications.

Current policy:

- commit exact harness/version and accepted public result;
- fingerprint the release corpus and preserve comparison base;
- record durability/metadata/cache/process/integrity semantics;
- preserve losing cases;
- never compare a richer operation to a weaker competitor operation without saying so;
- never compare fresh-process CMPCT to in-process ZIP as one timing layer;
- never use private corpus identity as public proof;
- never treat CI runner noise as either a win or a regression without the documented confidence rule;
- never rename one competitor to satisfy a stale visualization schema.

## Immediate high-value development missions

### Mission 1 — conformance and hostile-parser foundation

Finish independent golden archives and hostile parser/property tests across every canonical storage
kind, path/resource boundary, journal generation, recovery path and virtual reconstruction mode. Extend
the new fuzz foundation until all canonical r24 representations and future promoted graph primitives have
independent malformed-input coverage.

### Mission 2 — performance frontier under the release gate

Use the direct-base gate as the floor, then extend controlled benchmark infrastructure so the
neutral/resemblance-hostile suites run routinely. Tighten timing confidence as measurement quality
improves. Every stable competitor advantage is a prioritized defect. Do not buy aggregate wins by
deleting a losing workload or weakening selective-access semantics.

### Mission 3 — deterministic mode and normative schema

Turn the working r24 specification into a byte-level interoperable contract: canonical integer
encodings, ordering, path normalization, endianness, bounds, index schemas and deterministic creation.
The v0.28 reproducible mode is useful implementation evidence, not yet the complete cross-platform
normative contract.

### Mission 4 — native core

Continue representation-by-representation parity in `native/cmpct-core/` using Python as the executable
specification/cross-check oracle. Complete virtual-ZIP modes, independent pack conformance, sequential
streams, extraction, structural preflight and committed-generation recovery without forking semantics.

### Mission 5 — productionize EntropyGraph II without random-access regression

Do **not** move CMPNX8 wholesale under r24. Promote proven graph mechanisms one reader-visible storage
semantic at a time: exact/resemblance node descriptions, bounded depth-1 deltas, physical authentication,
preflate transform contracts and adaptive pack metadata each need precise bytes, independent vectors,
hostile dependency/resource tests, recovery, ZIP/export behavior and native parity before the relevant
format-revision bump.

### Mission 6 — reduce portfolio tax and erase practical ZIP advantages

Build a conservative cost model that can skip obvious losing EntropyGraph auditions without replacing
final byte measurement for admitted candidates. In parallel, prioritize encoder/extractor/native startup
hotspots where fair parity still favors ZIP while continuing Android/Linux/Windows/Apple integration
from `docs/PORTABILITY.md`. Platform claims require real conformance on the platform/emulator.

### Mission 7 — public-release readiness

Keep disclosure, engineering-evidence, version, performance, site and native gates green; maintain the
performance site as a self-contained front door; finish third-party provenance review; and resolve the
license proposal before 1.0/public release claims.

## Historical traps

Do not reintroduce these without new evidence:

- fixed 256 KiB frames for every file;
- TAR as canonical internal storage;
- forcing every file through Zstd;
- always using FLAC for WAV/PCM;
- always virtualizing nested archives;
- duplicating SHA-256 in multiple indexes;
- mandatory native helpers;
- SHA-256 on every ordinary read;
- ZIP physical layout as permanent canonical overhead;
- benchmark optimizations that help one private corpus only;
- a permanent hidden ZIP shadow for file-manager recognition;
- global stream federation as one giant decode unit;
- exact recompression recipes without replay-latency accounting;
- unlimited or delta-on-delta resemblance chains;
- treating similarity score as proof that a representation is smaller or correct;
- always widening solid context because a larger window exists;
- default fresh-process thread-pool startup when the workload cannot amortize it;
- separately regenerated base/candidate benchmark corpora;
- `os.urandom()` or wall-clock timestamps in a corpus expected to support byte-level regression claims;
- weakening a failed performance gate rather than fixing the engine or measurement substrate;
- relabeling a structural competitor to fit a hard-wired website schema.

## Project-version, surface-revision and format-revision rules

CMPCT has three independent axes:

1. **Numeric core project version (`MAJOR.MINOR.PATCH`)** — a scarce product-progress claim. Under the
   current policy, normal releases advance `MAJOR.MINOR` with `PATCH=0`. A numeric release requires a
   material format/engine capability, compression/speed gain, reliability/recovery improvement,
   portability/interoperability gain or similarly meaningful product behavior; it adds a release note,
   passes the direct-base performance gate and commits fresh durable public benchmark evidence.
2. **Surface revision (`MAJOR.MINOR.LETTER`)** — presentation/process identity in `SURFACE_REVISION`.
   Website polish, documentation cleanup, repository presentation and workflow ergonomics advance this
   track without consuming a numeric core version or manufacturing a benchmark record.
3. **On-disk format revision** — advances only when a reader must understand a new field, record,
   storage description, codec or reconstruction semantic to read newly created canonical archives.

Encoder or reliability changes can earn a numeric release while retaining r24 if reader grammar is
unchanged. Research code may also exist without being canonical grammar. A project release that records
a research frontier does not authorize an on-disk revision claim by implication.

Any format bump must additionally update:

- `docs/FORMAT.md`;
- `docs/HISTORY.md`;
- this file;
- conformance vectors/tests;
- benchmark evidence;
- browser-writer revision gate when enabled;
- native/platform compatibility gates that consume the grammar.

## Definition of a good next agent

A good next agent should be comfortable saying **“this change loses on workload X, so it does not
merge yet.”** It should also be willing to change the model of a problem before lowering the standard
of proof, as required by `docs/AGI_ENGINEERING_STANDARD.md`. CMPCT’s goal is not to accumulate clever
codecs or prettier charts. It is to become the strongest boring default: small, fast,
random-accessible, faithful, recoverable, secure, portable, independently implementable and ordinary
to open on the devices people use.
