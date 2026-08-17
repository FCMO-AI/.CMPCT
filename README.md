# .CMPCT

**Canonical repository for the CMPCT general-purpose archive/container project.**

CMPCT is an experimental lossless archive system built around a demanding goal: make the default
archive choice better than legacy ZIP across **size, speed, random access, fidelity, integrity,
recovery, updates and modern storage semantics**—without winning one metric by quietly sacrificing the
others.

> Status: **core project v0.28.0 / surface 0.28.c / pre-1.0 / format under active development.** `main`
> is the canonical source of truth. The executable reference implementation still writes format
> revision **24**. Surface revisions describe site/docs/repository presentation and do not consume a
> numeric core release number.

> v0.28.0 is the **EntropyGraph II / Resemblance Compiler research milestone**. Its CMPNX8 research
> grammar is not being smuggled under revision-24 magic; canonical reader/writer semantics remain r24
> until graph representations independently earn a future format revision.

> Licensing status: **Apache-2.0 is proposed, not yet adopted.** See `LICENSING.md` and
> `LICENSE-APACHE-2.0-PROPOSED.txt`. The proposal must not be interpreted as a finalized public grant.

## The performance position

CMPCT is not "Zstd with a new extension" and it is not satisfied by being smaller on one hand-picked
directory. Numeric core release candidates are benchmarked against their direct base before release.

The release rule is deliberately asymmetric because size and timing have different measurement physics:

- **archive size:** identical input + encoder semantics must never get larger at release promotion; gate tolerance is **0 bytes**;
- **create/extract speed:** base and candidate run on the same runner with repeated medians; a confirmed
  slowdown outside the documented relative+absolute noise envelope blocks promotion;
- **benchmark evidence:** every numeric core release must commit a fresh public benchmark record rather
  than leave the new result only in CI output;
- **corpora:** losing/adversarial workloads stay visible. A benchmark is not improved by deleting the
  case that disproves the headline.

That strict final floor is **not an exploration ban**. A reproducible mechanism-level breakthrough may
be preserved as research even when it temporarily regresses another performance dimension. The project
then opens explicit regression debt and works to retain the breakthrough while restoring the damaged
metric before promotion. The preferred sequence is adaptive portfolio/fallback selection, isolate the
exported cost, change the representation boundary, then counter-invent against the new bottleneck.
Correctness, byte-exact losslessness, authentication, hostile-input safety and truthful benchmark
semantics are never borrowable metrics.

See `docs/PERFORMANCE_RELEASE_GATE.md` for the normative release policy and
`docs/BREAKTHROUGH_REHABILITATION.md` for the exploration-to-promotion protocol.

### v0.28 research frontier

The fixed v0.28 neutral + resemblance-hostile portfolio contains **15 deterministic workloads**. The
inherited v0.25 EntropyGraph engine stores **166,816,028 bytes**; EntropyGraph II stores
**137,557,457 bytes**, **17.5394% smaller**, with **3 workloads improved and 0 regressed**. The other
**12/15 workloads are exact inherited fallbacks** rather than losses hidden inside an average.

The mechanism-level wins are concentrated where resemblance reuse predicts them:

- shifted near-duplicate versions: **30,200,827 → 1,761,588 bytes (-94.17%)**;
- repeated boundary churn: **866,651 → 89,945 bytes (-89.62%)**;
- ML artifacts: **13,879,065 → 13,836,439 bytes (-0.31%)**.

On the resemblance-hostile structural aggregate the selected CMPCT candidate stores **47,197,165 B**,
in the same size class as solid tar+Zstd-19 (**47,065,652 B**), ZPAQ method 5 (**47,062,641 B**) and
7z/LZMA2 (**47,430,344 B**), while ZIP/Deflate-9 stores **76,690,799 B**. These are structural size
comparisons, **not semantic-parity claims**: solid archives export different selective-read and recovery
costs. DwarFS was unavailable on the evidence runner and remains recorded as unavailable.

The public category frontier is deliberately harder than a ZIP-only boast. Fresh same-lifetime v0.28
measurements archive every workload independently with CMPCT, solid tar+Zstd-19 and ZIP/Deflate-9. Across
those 15 rows CMPCT stores **137,555,039 B** versus **143,861,222 B** for solid Zstd-19 and
**188,084,175 B** for ZIP/Deflate-9: **4.3835% smaller than solid Zstd-19** and **26.8652% smaller than
ZIP/Deflate-9** in the independent-workload aggregate. CMPCT wins **7/15** categories against solid
Zstd and loses **8/15**; the losing rows remain public. Notable Zstd wins include office workspace
(**28.37% smaller**), analytics/database (**34.38%**), logs/telemetry (**18.42%**) and many tiny files
(**5.94%**). The hardest recorded Zstd loss is boundary churn, where CMPCT is **23.07% larger**.

The durable records are `benchmarks/history/2026-08-16-entropygraph-v028.json` for release/structural
evidence and `benchmarks/history/2026-08-17-entropygraph-v028-category.json` for exact-tree category
evidence. Historical v0.25 evidence remains preserved rather than rewritten.

## What CMPCT can do today

Current canonical revision-24 prototype capabilities include:

- content-addressed deduplication;
- adaptive Zstandard and raw storage;
- Zstd dictionaries and micro-solid packs for forests of tiny files;
- content-defined chunking for large evolving files;
- fast byte-range reads and parallel chunk decode;
- hardlink, symlink and sparse-file preservation;
- UID/GID and extended-attribute metadata capture where available;
- nested ZIP/WHL virtualization when exact regeneration is profitable;
- lossless PCM-WAV transformation where it actually wins;
- raw Deflate reuse for fast legacy ZIP export;
- CRC32 hot-path corruption checks plus SHA-256 strong verification;
- redundant head/tail indexes and self-describing blob records for salvage;
- transactional append journal for update/delete/rename operations;
- on-demand export to ordinary Deflate ZIP for legacy compatibility;
- opt-in reproducible creation and deterministic parallel candidate encoding.

The EntropyGraph II research engine additionally explores:

- bounded FastCDC-style resemblance units;
- bounded multi-band similarity candidate search;
- measured depth-1 COPY/LITERAL deltas;
- adaptive similarity-ordered physical context from 64 KiB through 2 MiB under <=8x weighted read
  amplification;
- exact optional DEFLATE precompression through a pinned memory-safe bridge;
- Merkle-authenticated physical records and authenticated tail recovery;
- strict remote range sources that cannot silently fetch entire archives;
- inherited-v0.25 portfolio fallback whenever the graph candidate is larger.

Those mechanisms remain gated from the canonical reader until they pass format integration,
conformance, hardening, native parity and portability requirements.

The important rule is **content-driven selection, not extension-driven folklore**. If a specialized
representation is slower or larger for the actual bytes, CMPCT should not use it in the promoted
configuration. During research, a dramatic mechanism may remain preserved with explicit regression debt
while its losing region is rehabilitated rather than reflexively deleting the discovery.

## Quick start

```bash
python -m pip install -e .
python -m cmpct create ./folder archive.cmpct
python -m cmpct create ./folder reproducible.cmpct --reproducible
python -m cmpct create ./large-folder parallel.cmpct --workers 8
python -m cmpct info archive.cmpct
python -m cmpct list archive.cmpct
python -m cmpct verify archive.cmpct
python -m cmpct extract archive.cmpct ./restored
python -m cmpct range archive.cmpct path/to/huge.bin 1048576 4096 -o slice.bin
python -m cmpct export-zip archive.cmpct legacy.zip
```

Fresh-process CLI creation is intentionally serial unless `--workers N` is supplied. The v0.28 release
gate found that thread-pool startup could cost a small media tree ~10 ms while its library work barely
changed. The in-process `Builder` API keeps deterministic parallel creation by default, where callers can
amortize setup and large workloads showed material gains.

For the optional native content-defined chunker on Linux:

```bash
cc -O3 -shared -fPIC native/cmpct_cdc.c -o src/cmpct/libcmpct_cdc.so
```

The reader does **not** depend on that helper. It accelerates boundary selection while creating an
archive; chunk boundaries are explicitly recorded on disk.

## New-agent reading order

A coding/research agent with no previous CMPCT context should read, in order:

1. `docs/AGI_ENGINEERING_STANDARD.md` — quality ratchet, falsifiability and evidence hierarchy;
2. `README.md` — mission and project shape;
3. `AGENTS.md` — mandatory development, benchmark and versioning rules;
4. `docs/CURRENT_STATE.md` — zero-chat-history handoff and immediate frontier;
5. newest applicable note under `docs/releases/` — latest numeric core milestone;
6. `docs/PERFORMANCE_RELEASE_GATE.md` — no-regression core-release promotion contract;
7. `docs/BREAKTHROUGH_REHABILITATION.md` — how to preserve a high-upside research seed and pay its regression debt before promotion;
8. `docs/FORMAT.md` — current revision-24 on-disk contract;
9. `docs/HISTORY.md` — surviving format/prototype history with private provenance generalized;
10. `docs/ENTROPYGRAPH.md` and `docs/ENTROPYGRAPH_II_CAMPAIGN.md` — current research frontier and gates;
11. `docs/HARDENING.md` — hostile parser/resource state;
12. `docs/PORTABILITY.md` and `docs/NATIVE_CORE.md` — product integration and shared reader-core state;
13. `docs/RESEARCH_LOG.md` — failed ideas and experimental conclusions;
14. `docs/BENCHMARKS.md` and `benchmarks/history/` — benchmark semantics and durable public records;
15. `docs/PUBLIC_SURFACE.md` — public-repository/site disclosure boundary;
16. `docs/ROADMAP.md` — work remaining before 1.0.

A new agent should not need private chat, private corpora, or unrelated project context to continue
development safely.

## Repository map

- `src/cmpct/` — canonical revision-24 reference implementation.
- `src/cmpct/resemblance.py` — reusable bounded similarity/delta primitives used by EntropyGraph II.
- `experiments/entropygraph_v025.py` — historical CMPNX5 engine and v0.28 exact fallback.
- `experiments/entropygraph_v028.py` — EntropyGraph II CMPNX8 research engine.
- `experiments/entropygraph_v028_strict.py` — strict-locality EntropyGraph II portfolio.
- `experiments/entropygraph_v028_remote.py` — strict range-source research reader.
- `benchmarks/universal_bench.py` — deterministic heterogeneous canonical benchmark corpus generator.
- `benchmarks/zip_parity_bench.py` — fair CMPCT/ZIP parity and shared-corpus release-gate harness.
- `benchmarks/neutral_hostile_corpus_v1.py` — deterministic neutral/hostile research suite.
- `benchmarks/resemblance_hostile_corpus_v1.py` — shifted-version/false-neighbor/boundary-churn attack suite.
- `benchmarks/history/` — durable public machine-readable benchmark records.
- `fuzz/` — malformed canonical/graph/delta resource and parser attacks.
- `tools/check_performance_regression.py` — direct-base release regression checker.
- `tools/check_version_discipline.py` — core-vs-surface version discipline gate.
- `tools/check_pr_evidence.py` — material-PR evidence-dossier gate.
- `SURFACE_REVISION` — alphabetic presentation/process revision (`x.x.a`, `x.x.b`, …).
- `docs/PERFORMANCE_RELEASE_GATE.md` — normative performance release policy.
- `docs/BREAKTHROUGH_REHABILITATION.md` — normative exploration/regression-debt rehabilitation policy.
- `docs/releases/` — one release note per numeric core release.
- `site/` — performance-first website, evidence adapters and local Browser Lab.
- `native/cmpct_cdc.c` — optional native content-defined chunking accelerator.
- `native/preflate-bridge/` — optional pinned exact-DEFLATE research transform bridge.
- `native/cmpct-core/` — shared memory-safe read-only core and C ABI.
- `docs/CURRENT_STATE.md` — current handoff/frontier for a zero-context developer or agent.
- `docs/FORMAT.md` — current on-disk contract and invariants.
- `docs/HISTORY.md` — format and design lineage through the canonical revision-24 baseline.
- `docs/ENTROPYGRAPH.md` — current generalized research results and integration boundary.
- `docs/ENTROPYGRAPH_II_CAMPAIGN.md` — v0.28 falsifiable design/evidence map.
- `docs/RESEARCH_LOG.md` — design decisions, failed ideas and experimental conclusions.
- `docs/PRINCIPLES.md` — rules that prevent corpus-specific overfitting.
- `docs/BENCHMARKS.md` — benchmark discipline and interpreted checkpoints.
- `docs/PUBLIC_SURFACE.md` — what may and may not enter the public-facing repository/site surface.
- `docs/ROADMAP.md` — blockers between the prototype and a defensible 1.0.
- `tests/` — format, round-trip, resemblance, strict-locality and reproducibility regression tests.

## Website

The site is designed to **create impact first, prove the claim second, and earn trust after that**.
Its headline performance numbers, competitor ladder, category frontier, losses and core-release state are
generated from committed benchmark history rather than hand-maintained marketing percentages.

For v0.28 the public surface deliberately gives four benchmark views different jobs:

- **whole-suite research arena** — current CMPCT versus matched external archive tools. ZIP/Deflate is the familiar headline comparator and solid Zstd-19 is prominently shown beside it as the serious compression-size baseline;
- **category frontier** — every exact workload is independently compared against solid Zstd-19, with ZIP/Deflate retained as secondary context. Green and red cells both remain visible;
- **canonical ZIP execution parity** — the executable revision-24 reader/writer compared against ZIP at equivalent library and fresh-process CLI archive-size/create/extract boundaries;
- **release delta** — current research candidate versus its inherited direct base, kept as causal release evidence rather than overwriting the competitive category view.

Whole-suite and independent-workload totals are intentionally not mixed: aggregation changes physical
context and deduplication opportunity. Fresh category evidence also records its own exact tree identity
because some generated office/media producer metadata can vary across separate runs. The category
baseline therefore measures CMPCT and Zstd/ZIP during the same workload lifetime instead of pretending
a later regeneration is byte-identical.

The site may be visually and rhetorically aggressive. It may not blur those boundaries or invent a win.
Canonical `main` publishes through the Pages workflow only after public-surface, data-coherence,
surface-revision, JavaScript and Browser Lab compatibility checks pass.

## Version discipline

CMPCT does not treat the numeric project version as a commit counter.

There are three different version axes:

1. **Numeric core project version (`MAJOR.MINOR.PATCH`)** — reserved for a material improvement to CMPCT
   itself: archive/engine capability, compression or speed, reliability, recovery,
   portability/interoperability, or another product-level gain. After the historical v0.27.1 checkpoint,
   normal core advancement moves the `MAJOR.MINOR` line and uses `PATCH=0` for packaging compatibility.
2. **Surface revision (`MAJOR.MINOR.LETTER`)** — site animation/design, documentation cleanup, repository
   presentation, workflow ergonomics and similar non-format work. The current surface milestone is
   `0.28.c`. It does not independently change `pyproject.toml` and does not require a synthetic benchmark
   record.
3. **On-disk format revision** — changes only when readers need new archive grammar/storage semantics.

A core release can improve encoder policy, speed, reliability or interoperability without changing the
on-disk revision, but it must still earn its numeric number with durable evidence. A research milestone
can likewise advance the project line while keeping experimental bytes explicitly non-canonical. A site
or repo beautification pass can be useful and substantial without pretending CMPCT itself became a new
format release.

CI rejects numeric bumps that do not touch archive/engine paths, requires matching release and benchmark
evidence for numeric core releases, validates the alphabetic surface line, and keeps those concerns
separate from the performance regression gate.

## Development history and benchmark provenance

The project began as a sequence of Seekable-Zstd, indexed-Zstd, adaptive-framing and ZIP-family
experiments before becoming the native content-aware CMPCT format. The technical history is preserved,
but private corpus identities, private artifact names and unrelated project provenance are intentionally
not part of the public project record.

Public benchmark history must be independently reproducible or generated from deliberately public,
synthetic inputs. Private development corpora may still be useful local regression signals, but their
names, hashes, paths, contents and artifact provenance are not public evidence.

Historical benchmark data is **not** automatically a universal performance guarantee. The project
records environment, process boundaries and semantic mismatches, and preserves losing workloads rather
than rewriting the record around whichever result looks best.

## Public-surface rule

CMPCT must stand on its own. The repository and website must not require or expose unrelated internal
projects, private customer data, private corpora, personal information, chat transcripts, credentials,
private artifact names or private-system links. See `docs/PUBLIC_SURFACE.md` for the enforceable rule.

## Canonicality

This repository supersedes chat-local CMPCT prototypes and benchmark scripts. New format changes,
benchmarks, experiments, site changes and design decisions must land here, but they do not all receive
the same kind of version marker. Material archive/engine progress earns a numeric core release; site,
documentation and repository presentation use `SURFACE_REVISION`; research may remain explicitly
experimental until it is promoted. Experimental code cannot claim canonical format support until it is
wired into the reference reader/writer and conformance surface.

## License

Apache License 2.0 is the **current proposed license**, not the final adopted license. The repository
contains the unmodified proposed license text in `LICENSE-APACHE-2.0-PROPOSED.txt` plus an explicit
adoption checklist in `LICENSING.md`. Until that process is completed, do not represent CMPCT as
finally released under Apache-2.0.

Footnote: historical release notes and benchmark records are not rewritten to fit the new policy. The
scarce-version rule applies prospectively so the repository preserves an honest audit trail.