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

Current project version: **v0.27.1**

Current canonical executable format: **revision 24**

Project version and format revision are intentionally independent. v0.27.0 introduced the mandatory
AGI-grade engineering standard and material-PR evidence gate while preserving revision-24 archive
semantics. v0.27.1 synchronizes this zero-chat handoff with that new canonical engineering contract.
The v0.26 performance-release machinery remains the executable no-regression foundation, and
EntropyGraph remains a research engine rather than a canonical revision-25 claim.

`main` HEAD is the canonical implementation state. Everything created outside this repository is
experimental until reconciled into `main` with the required version, tests, benchmark record and
release documentation.

## v0.27 engineering-quality contract

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

## v0.26 performance-release contract

Performance is now a merge requirement rather than optional telemetry.

Every material project version must:

1. advance `pyproject.toml` and add `docs/releases/vX.Y.Z.md`;
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

## Public website state

`site/` is the public human/agent front door and is now deliberately performance-first. The experience
is designed so the first screen creates impact, the second proves the performance claim, and the rest
explains the engineering and qualifications.

The generated site includes:

- a live research-frontier headline sourced from committed benchmark history;
- aggregate comparisons against ZIP/Zstd, ZIP/Deflate and a solid tar/Zstd diagnostic;
- a workload-level win/loss matrix and explicit frontier defects;
- an information-graph explanation of the EntropyGraph direction;
- a strict canonical-vs-research boundary;
- canonical ZIP parity with separate library and fresh-process CLI layers;
- the current no-regression release law;
- Browser Lab local archive creation and header inspection;
- a project-version trajectory.

`site/build_site.py` reads repository state and normalizes both canonical parity records and the
EntropyGraph research-frontier schema. Large performance percentages are not hand-maintained in HTML.
The Pages workflow rejects a site whose project version, release note, benchmark frontier, canonical
parity evidence, JavaScript or Browser Lab compatibility do not agree. Canonical `main` is configured
to publish automatically after those gates pass.

## EntropyGraph research frontier

The v0.25 milestone introduced a public neutral/hostile suite and an executable research engine under
`experiments/entropygraph_v025.py`. It treats the archive as an authenticated reconstruction graph in
which the encoder can choose which exact reversible representations become physical roots.

Current research mechanisms include:

- global exact compressed-stream federation across related ZIP-like containers;
- entropy-oriented representation inversion;
- exact object interning across aliases/snapshots;
- generic exact inverse edges for required gzip/xz/zstd/bzip2 sidecars;
- compact implicit micro-pack indexing;
- adaptive same-family context audition capped at 512 KiB physical decode units;
- hot/cold stream-root layout to protect latency-sensitive inverse views;
- authenticated head/tail metadata recovery exercised by the research reader;
- explicit strong verification of physical packs plus canonical logical tree root.

The durable v0.25 frontier record is
`benchmarks/history/2026-08-16-entropygraph-v025.json`. On that 10-workload synthetic suite, the
research candidate recorded 16.46% smaller aggregate storage than ZIP/Zstd-93, 18.88% smaller than
ZIP/Deflate-9, and 6.91% smaller than the solid tar/Zstd-19 diagnostic, while preserving the workloads
where it lost. These are **research-frontier results, not canonical r24 interoperability claims**.

Promotion into the canonical format must happen one representation at a time with independent golden
vectors, hostile parser/resource tests, bounded selective-read accounting, recovery semantics, ZIP
compatibility/export semantics and native-core parity.

## Current implementation architecture

`src/cmpct/codec.py`
: Canonical representation primitives, Zstd/Deflate/FLAC handling, content-defined chunking interface,
  exact nested-ZIP reconstruction helpers and integrity primitives.

`src/cmpct/builder.py`
: Filesystem scan, candidate/representation selection, deduplication, dictionaries/microblocks,
  sparse/link handling and physical archive construction.

`src/cmpct/reader.py`
: Archive parsing, index recovery, logical reads, range reads, extraction, verification and salvage.

`src/cmpct/transactions.py`
: Append generations, mutation journal, rename/delete/update behavior, checkpoints and commit-footer
  semantics.

`src/cmpct/cli.py`
: User-facing create/info/list/read/range/extract/verify/export/recovery operations.

`experiments/entropygraph_v025.py`
: Executable research-only CMPNX5 reader/writer used to test representation-graph mechanisms before
  they are admitted to canonical grammar.

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

`native/cmpct_cdc.c`
: Optional creation-time content-defined chunk boundary accelerator. The reader does not depend on it.

`native/cmpct-core/`
: Memory-safe Rust read-only core and C ABI. It authenticates/decodes the r24 primary index, applies the
  shared lexical path policy, bounds base blobs, and covers direct RAW, bounded direct
  Zstd/WAV-FLAC/raw-Deflate/Zstd-dictionary, fixed/CDC maps, sparse extents, checked `S_PACK` slices,
  and selected virtual-ZIP projection paths. The detailed representation/conformance matrix and open
  gaps live in `docs/NATIVE_CORE.md`; do not duplicate or fork those semantics here.

`site/`
: Performance-command-center website, generated project/benchmark data and local Browser Lab.

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
14. **Material work is versioned.** Every substantive merged milestone advances project version.
15. **Material work is benchmarked.** Every substantive version receives a direct-base benchmark and durable public record.
16. **No silent performance regression.** Identical-input archive-size growth is zero-tolerance; confirmed same-runner slowdowns block release.
17. **Evidence drives the website.** Public headline numbers are generated from committed records, not static copy.
18. **Quality ratchet is mandatory.** Material work must expose its baseline, causal hypothesis, disproof surface, negative evidence and relevant hidden costs; green tests alone are not completion.

## What is not yet production-grade or 1.0-ready

Major open areas include:

- normative byte-level format specification and complete index schema;
- complete conformance/golden archives and stable cross-version vectors;
- parser fuzzing/property testing and strict resource/bounds limits;
- deterministic archive mode as a user-facing canonical option;
- formal codec/transform registry and capability negotiation;
- authenticated encryption and key derivation;
- complete ACL/Windows/macOS metadata/path normalization rules;
- split-volume and streaming/non-seekable creation;
- remote HTTP/object-store range access with partial verification;
- representation-complete native reading, streaming/extraction and committed-generation recovery;
- scalable CDC without whole-file memory loading;
- robust Android/Linux/Windows/Apple archive browsing/file-manager integrations defined by `docs/PORTABILITY.md`;
- deliberate promotion or rejection of EntropyGraph storage semantics after canonical conformance/security integration;
- controlled-hardware benchmark infrastructure that can tighten timing envelopes and run the broader hostile suite continuously;
- formal adoption or rejection of the proposed Apache-2.0 license after provenance review.

## Benchmark interpretation

The benchmark system has three different roles and they must not be blurred:

1. **Release regression gate** — direct base vs candidate, one identical corpus, same runner; blocks backward movement.
2. **Canonical parity** — current executable CMPCT vs ZIP at explicit library and CLI boundaries.
3. **Research frontier** — broader EntropyGraph comparisons, including ZIP/Zstd and whole-solid diagnostics.

Current policy:

- commit exact harness/version and accepted public result;
- fingerprint the release corpus and preserve comparison base;
- record durability/metadata/cache/process/integrity semantics;
- preserve losing cases;
- never compare a richer operation to a weaker competitor operation without saying so;
- never compare fresh-process CMPCT to in-process ZIP as one timing layer;
- never use private corpus identity as public proof;
- never treat CI runner noise as either a win or a regression without the documented confidence rule.

## Immediate high-value development missions

### Mission 1 — conformance and hostile-parser foundation

Finish independent golden archives and hostile parser/property tests across every canonical storage
kind, path/resource boundary, journal generation, recovery path and virtual reconstruction mode.

### Mission 2 — performance frontier under the new release gate

Use the v0.26 direct-base gate as the floor, then extend controlled benchmark infrastructure so the
neutral/hostile suite also runs routinely. Tighten timing confidence as measurement quality improves.
Every stable competitor advantage is a prioritized defect. Do not buy aggregate wins by deleting a
losing workload or weakening selective-access semantics.

### Mission 3 — deterministic mode and normative schema

Turn the working r24 specification into a byte-level interoperable contract: canonical integer
encodings, ordering, path normalization, endianness, bounds, index schemas and deterministic creation.

### Mission 4 — native core

Continue representation-by-representation parity in `native/cmpct-core/` using Python as the executable
specification/cross-check oracle. Complete virtual-ZIP modes, independent pack conformance, sequential
streams, extraction, structural preflight and committed-generation recovery without forking semantics.

### Mission 5 — integrate EntropyGraph without random-access regression

Formalize the reconstruction DAG and dependency/resource bounds, then promote exact object interning,
compact micro-indexing, global virtual-container federation and inverse views one storage description at
a time. Every promoted edge needs independent conformance, hostile dependency tests, bounded read cost,
recovery and native parity before a format-revision bump.

### Mission 6 — erase practical ZIP advantages and ship first-class archive UX

Prioritize encoder/extractor/native startup hotspots where fair parity still favors ZIP while continuing
Android/Linux/Windows/Apple integration from `docs/PORTABILITY.md`. Platform claims require real
conformance on the platform/emulator.

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
- separately regenerated base/candidate benchmark corpora;
- `os.urandom()` or wall-clock timestamps in a corpus expected to support byte-level regression claims;
- weakening a failed performance gate rather than fixing the engine or measurement substrate.

## Project-version and format-revision rules

Every material merged milestone advances project version, adds `docs/releases/vX.Y.Z.md`, passes the
release performance gate and commits a fresh public benchmark record for that version.

Bump the on-disk revision only when a reader must understand a new field, record, storage description,
codec or reconstruction semantic to read newly created canonical archives. Encoder, research, site,
benchmark, engineering-policy or release-tooling changes can keep r24 while still requiring a new
project version.

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
