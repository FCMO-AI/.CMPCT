<div align="center">
  <a href="https://fcmo-ai.github.io/.CMPCT/">
    <img src=".github/assets/repository-hero.svg" width="100%" alt="CMPCT — Archive formats made peace with compromise. CMPCT did not.">
  </a>

  <br>

  **A general-purpose lossless archive/container project engineered to push stored bytes, selective access, integrity, recovery and portability forward together.**

  <br>

  [![CI topology](https://github.com/FCMO-AI/.CMPCT/actions/workflows/ci-topology.yml/badge.svg)](https://github.com/FCMO-AI/.CMPCT/actions/workflows/ci-topology.yml)
  [![Fuzz](https://github.com/FCMO-AI/.CMPCT/actions/workflows/fuzz.yml/badge.svg)](https://github.com/FCMO-AI/.CMPCT/actions/workflows/fuzz.yml)
  [![Engineering evidence](https://github.com/FCMO-AI/.CMPCT/actions/workflows/engineering-evidence.yml/badge.svg)](https://github.com/FCMO-AI/.CMPCT/actions/workflows/engineering-evidence.yml)

  **[Website](https://fcmo-ai.github.io/.CMPCT/)** · **[Browser Lab](https://fcmo-ai.github.io/.CMPCT/#lab)** · **[Benchmarks](docs/BENCHMARKS.md)** · **[Format](docs/FORMAT.md)** · **[Roadmap](docs/ROADMAP.md)** · **[Agent entrypoint](docs/CURRENT_STATE.md)**

  <sub>core v0.29.0 · canonical format r24 · surface 0.29.i · pre-1.0</sub>
</div>

---

> **Performance is the release contract.** Research may discover an uncomfortable tradeoff. A promoted release does not get to hide one: deterministic archive-size regression has **0-byte tolerance**, confirmed speed regression outside the documented same-runner noise envelope blocks promotion, and losing workloads remain public evidence.

## Why CMPCT exists

| | CMPCT is trying to make this better |
|---|---|
| **Stored bytes** | Use exact identity, content-aware representations and bounded relationship reuse instead of treating every file as an unrelated byte stream. |
| **Selective access** | Read the requested object or range without turning the entire archive into one mandatory decompression event. |
| **Integrity + recovery** | Keep checks, redundant metadata and salvage paths as executable reader behavior rather than disaster-recovery prose. |
| **Filesystem fidelity** | Preserve links, sparse files, metadata and update semantics expected from a modern general-purpose container. |
| **Interoperability** | Keep a canonical reader/writer contract, ZIP export, native-core work and portability gates separate from experimental research grammar. |
| **Evidence quality** | Derive public claims from committed reproducible records, preserve losses and reject benchmark theater. |

CMPCT is not “Zstd with a new extension” and it is not satisfied by winning one hand-picked directory. The target is a stronger default archive across **size, speed, random access, fidelity, integrity, recovery, updates and modern storage semantics** without quietly exporting the cost somewhere else.

## Latest verified frontier

**Project v0.29.0 — Mosaic / Residual Program Packing** advances the verified research engine while the shipping canonical format remains **revision 24**.

| v0.29 research evidence | Result |
|---|---:|
| Portable inherited-frontier portfolio | **137,501,815 B** |
| Direct v0.28 base | 137,550,416 B |
| Exact saving | **48,601 B (0.035333%)** |
| Portable workloads | **15** |
| Improved / regressed | **2 / 0** |
| Exact v0.28 fallbacks | **13 / 15** |
| Hostile mechanism suites | **4.407362% smaller**, 9 improved / 0 regressed across 18 workloads |
| Fixed hostile scheduler | **182.454 s → 97.944 s median (-46.318%)**, byte-identical selected archive |

On the deterministic 724-file / 93,526,384-byte resemblance-hostile aggregate, accepted attempt #5 stores **47,147,764 B**. On that same tree, ZPAQ method 5 stores 47,062,639 B, solid tar+Zstd-19 stores 47,065,652 B, 7z/LZMA2 stores 47,430,343 B, Borg stores 76,461,311 B and ZIP/Deflate-9 stores 76,690,799 B.

These rows are **matched stored-byte comparisons, not semantic-parity claims**. Solid archives, backup repositories and CMPCT expose different selective-read, update, integrity and recovery tradeoffs. The durable release record is [`docs/releases/v0.29.0.md`](docs/releases/v0.29.0.md); machine-readable evidence lives under [`benchmarks/history/`](benchmarks/history/).

### Shipping vs frontier

| Authority | Current state | Meaning |
|---|---|---|
| **Canonical reader/writer** | **format r24** | What `python -m cmpct create` writes and canonical readers must understand. |
| **Research frontier** | **CMPNX11 / v0.29.0** | Experimental Mosaic + Residual Program Packing engine; not canonical r24 syntax. |
| **Public surface** | **0.29.i** | Repository/site/docs presentation only; it does not alter archive semantics or consume a core version. |
| **License** | **Apache-2.0 proposed** | Proposal only. It is not yet the finalized public grant. |

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

The v0.29 research line additionally explores and measures:

- bounded FastCDC-style resemblance units and multi-band similarity search;
- measured depth-1 COPY/LITERAL deltas;
- bounded multi-root Mosaic placement;
- Residual Program Packing for groups of related delta recipes;
- exact v0.28 portfolio fallback whenever the new representation does not win;
- locality/resource ceilings for selected physical plans;
- exact optional DEFLATE precompression through a pinned memory-safe bridge;
- Merkle-authenticated physical records and authenticated tail recovery;
- strict remote range sources that cannot silently fetch entire archives;
- byte-identical parallel portfolio scheduling for the accepted v0.29 research engine.

Those research mechanisms remain gated from the canonical reader until they independently pass format integration, conformance, hardening, native parity, recovery and portability requirements.

The important rule is **content-driven selection, not extension-driven folklore**. If a specialized representation is slower or larger for the actual bytes, CMPCT should not use it.

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

Fresh-process canonical CLI creation is intentionally serial unless `--workers N` is supplied. The v0.28 release gate found that thread-pool startup could cost a small media tree about 10 ms while its library work barely changed. The in-process `Builder` API keeps deterministic parallel creation by default, where callers can amortize setup and large workloads showed material gains.

For the optional native content-defined chunker on Linux:

```bash
cc -O3 -shared -fPIC native/cmpct_cdc.c -o src/cmpct/libcmpct_cdc.so
```

The reader does **not** depend on that helper. It accelerates boundary selection while creating an archive; chunk boundaries are explicitly recorded on disk.

## The performance position

Numeric core release candidates are benchmarked against their direct base before release. The release rule is deliberately asymmetric because size and timing have different measurement physics:

- **archive size:** identical input + encoder semantics must never get larger; release gate tolerance is **0 bytes**;
- **create/extract speed:** base and candidate run on the same runner with repeated medians; a confirmed slowdown outside the documented relative+absolute noise envelope blocks release;
- **benchmark evidence:** every numeric core release must commit a fresh public benchmark record rather than leave the new result only in CI output;
- **corpora:** losing/adversarial workloads stay visible. A benchmark is not improved by deleting the case that disproves the headline.

See [`docs/PERFORMANCE_RELEASE_GATE.md`](docs/PERFORMANCE_RELEASE_GATE.md) for the normative release policy and [`docs/BREAKTHROUGH_REHABILITATION.md`](docs/BREAKTHROUGH_REHABILITATION.md) for how high-upside research is preserved while regression debt is paid before promotion.

## New-agent reading order

A coding/research agent with no previous CMPCT context should read, in order:

1. `docs/AGI_ENGINEERING_STANDARD.md` — quality ratchet, falsifiability and evidence hierarchy;
2. `README.md` — mission and project shape;
3. `AGENTS.md` — mandatory development, benchmark and versioning rules;
4. `docs/CURRENT_STATE.md` — zero-chat-history handoff and immediate frontier;
5. newest applicable note under `docs/releases/` — latest numeric core milestone;
6. `docs/PERFORMANCE_RELEASE_GATE.md` — no-regression core-release contract;
7. `docs/BREAKTHROUGH_REHABILITATION.md` — breakthrough preservation and regression-debt protocol;
8. `docs/FORMAT.md` — current revision-24 on-disk contract;
9. `docs/HISTORY.md` — surviving format/prototype history with private provenance generalized;
10. `docs/ENTROPYGRAPH.md`, `docs/ENTROPYGRAPH_II_CAMPAIGN.md` and `docs/MOSAIC_V029_CAMPAIGN.md` — research lineage and current frontier;
11. `docs/HARDENING.md` — hostile parser/resource state;
12. `docs/PORTABILITY.md` and `docs/NATIVE_CORE.md` — product integration and shared reader-core state;
13. `docs/RESEARCH_LOG.md` — failed ideas and experimental conclusions;
14. `docs/BENCHMARKS.md` and `benchmarks/history/` — benchmark semantics and durable public records;
15. `docs/PUBLIC_SURFACE.md` — public-repository/site disclosure boundary;
16. `docs/ROADMAP.md` — work remaining before 1.0.

A new agent should not need private chat, private corpora or unrelated project context to continue development safely.

## Repository map

- `src/cmpct/` — canonical revision-24 reference implementation.
- `src/cmpct/resemblance.py` — reusable bounded similarity/delta primitives.
- `experiments/entropygraph_v025.py` — historical CMPNX5 engine and inherited fallback lineage.
- `experiments/entropygraph_v028.py` — EntropyGraph II CMPNX8 research engine.
- `experiments/entropygraph_v029_release.py` — stable accepted v0.29 research entrypoint and byte-identical scheduler surface.
- `benchmarks/universal_bench.py` — deterministic heterogeneous canonical benchmark corpus generator.
- `benchmarks/zip_parity_bench.py` — fair CMPCT/ZIP parity and shared-corpus release-gate harness.
- `benchmarks/neutral_hostile_corpus_v1.py` — deterministic neutral/hostile research suite.
- `benchmarks/resemblance_hostile_corpus_v1.py` — shifted-version/false-neighbor/boundary-churn attack suite.
- `benchmarks/mosaic_v029_generalization_bench.py` — portable v0.29 generalization gate.
- `benchmarks/mosaic_v029_structural_competitors.py` — matched hostile cross-format structural comparison.
- `benchmarks/history/` — durable public machine-readable benchmark records.
- `fuzz/` — malformed canonical/graph/delta resource and parser attacks.
- `tools/check_performance_regression.py` — direct-base release regression checker.
- `tools/check_version_discipline.py` — core-vs-surface version discipline gate.
- `tools/check_pr_evidence.py` — material-PR evidence-dossier gate.
- `SURFACE_REVISION` — alphabetic presentation/process revision (`x.x.a`, `x.x.b`, …).
- `docs/PERFORMANCE_RELEASE_GATE.md` — normative performance release policy.
- `docs/releases/` — one release note per numeric core release.
- `site/` — performance-first website, evidence adapters and local Browser Lab.
- `native/cmpct_cdc.c` — optional native content-defined chunking accelerator.
- `native/preflate-bridge/` — optional pinned exact-DEFLATE research transform bridge.
- `native/cmpct-core/` — shared memory-safe read-only core and C ABI.
- `docs/CURRENT_STATE.md` — current handoff/frontier for a zero-context developer or agent.
- `docs/FORMAT.md` — current on-disk contract and invariants.
- `docs/HISTORY.md` — format and design lineage through the canonical revision-24 baseline.
- `docs/ENTROPYGRAPH.md` — generalized graph-representation research and integration boundary.
- `docs/ENTROPYGRAPH_II_CAMPAIGN.md` — v0.28 falsifiable design/evidence map.
- `docs/MOSAIC_V029_CAMPAIGN.md` — v0.29 Mosaic campaign and falsifiable mechanism gates.
- `docs/RESEARCH_LOG.md` — design decisions, failed ideas and experimental conclusions.
- `docs/PRINCIPLES.md` — rules that prevent corpus-specific overfitting.
- `docs/BENCHMARKS.md` — benchmark discipline and interpreted checkpoints.
- `docs/PUBLIC_SURFACE.md` — what may and may not enter the public-facing repository/site surface.
- `docs/ROADMAP.md` — blockers between the prototype and a defensible 1.0.
- `tests/` — format, round-trip, resemblance, strict-locality and reproducibility regression tests.

## Website

The live site is designed to **create impact first, prove the claim second, and earn trust after that**. Its headline performance numbers, competitor ladder, workload matrix, losses and core-release state are generated from committed benchmark history rather than hand-maintained marketing percentages.

For v0.29 the public adapter exposes the accepted Mosaic / Residual Program Packing frontier while keeping ZIP/Deflate, 7z/LZMA2, solid tar/Zstd, ZPAQ and Borg under their actual names. A stale UI schema is not allowed to rename one competitor into another merely to keep an old hero label filled in.

The site deliberately separates:

- **research frontier** — the strongest currently verified experimental representation results;
- **canonical parity** — the executable revision-24 reader/writer compared against ZIP at equivalent library and fresh-process CLI boundaries;
- **surface revision** — the current site/docs/repository presentation milestone, which has no authority over archive semantics or benchmark truth.

The site may be visually and rhetorically aggressive. It may not blur those boundaries or invent a win. Canonical `main` publishes through the Pages workflow only after public-surface, data-coherence, surface-revision, JavaScript and Browser Lab compatibility checks pass.

**Open it:** https://fcmo-ai.github.io/.CMPCT/

## Version discipline

CMPCT does not treat the numeric project version as a commit counter. There are three different version axes:

1. **Numeric core project version (`MAJOR.MINOR.PATCH`)** — reserved for a material improvement to CMPCT itself: archive/engine capability, compression or speed, reliability, recovery, portability/interoperability, or another product-level gain. After the historical v0.27.1 checkpoint, normal core advancement moves the `MAJOR.MINOR` line and uses `PATCH=0` for packaging compatibility.
2. **Surface revision (`MAJOR.MINOR.LETTER`)** — site animation/design, documentation cleanup, repository presentation, workflow ergonomics and similar non-format work. The current surface milestone is **`0.29.i`**. It does not independently change `pyproject.toml` and does not require a synthetic benchmark record.
3. **On-disk format revision** — changes only when readers need new archive grammar/storage semantics. The canonical executable format remains **r24**.

A core release can improve encoder policy, speed, reliability or interoperability without changing the on-disk revision, but it must still earn its numeric number with durable evidence. A research milestone can likewise advance the project line while keeping experimental bytes explicitly non-canonical. A site or repository beautification pass can be useful and substantial without pretending CMPCT itself became a new format release.

CI rejects numeric bumps that do not touch archive/engine paths, requires matching release and benchmark evidence for numeric core releases, validates the alphabetic surface line, and keeps those concerns separate from the performance regression gate.

## Development history and benchmark provenance

The project began as a sequence of Seekable-Zstd, indexed-Zstd, adaptive-framing and ZIP-family experiments before becoming the native content-aware CMPCT format. The technical history is preserved, but private corpus identities, private artifact names and unrelated project provenance are intentionally not part of the public project record.

Public benchmark history must be independently reproducible or generated from deliberately public, synthetic inputs. Private development corpora may still be useful local regression signals, but their names, hashes, paths, contents and artifact provenance are not public evidence.

Historical benchmark data is **not** automatically a universal performance guarantee. The project records environment, process boundaries and semantic mismatches, and preserves losing workloads rather than rewriting the record around whichever result looks best.

## Public-surface rule

CMPCT must stand on its own. The repository and website must not require or expose unrelated internal projects, private customer data, private corpora, personal information, chat transcripts, credentials, private artifact names or private-system links. See `docs/PUBLIC_SURFACE.md` for the enforceable rule.

## Canonicality

This repository supersedes chat-local CMPCT prototypes and benchmark scripts. New format changes, benchmarks, experiments, site changes and design decisions must land here, but they do not all receive the same kind of version marker. Material archive/engine progress earns a numeric core release; site, documentation and repository presentation use `SURFACE_REVISION`; research may remain explicitly experimental until it is promoted. Experimental code cannot claim canonical format support until it is wired into the reference reader/writer and conformance surface.

## License

Apache License 2.0 is the **current proposed license**, not the final adopted license. The repository contains the unmodified proposed license text in `LICENSE-APACHE-2.0-PROPOSED.txt` plus an explicit adoption checklist in `LICENSING.md`. Until that process is completed, do not represent CMPCT as finally released under Apache-2.0.

Footnote: the repository hero is deliberately evergreen and contains no benchmark percentages or release numbers; evidence-bearing values remain text sourced from the current release record, where they can be reviewed and updated without turning artwork into stale benchmark authority. Historical release notes and benchmark records are not rewritten to fit the new policy. The scarce-version rule applies prospectively so the repository preserves an honest audit trail.
