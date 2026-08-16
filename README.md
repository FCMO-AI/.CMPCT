# .CMPCT

**Canonical repository for the CMPCT general-purpose archive/container project.**

CMPCT is an experimental lossless archive system built around a demanding goal: make the default
archive choice better than legacy ZIP across **size, speed, random access, fidelity, integrity,
recovery, updates and modern storage semantics**—without winning one metric by quietly sacrificing the
others.

> Status: **core project v0.27.1 / surface 0.27.a / pre-1.0 / format under active development.** `main`
> is the canonical source of truth. The executable reference implementation still writes format
> revision **24**. Surface revisions describe site/docs/repository presentation and do not consume a
> numeric core release number.

> Licensing status: **Apache-2.0 is proposed, not yet adopted.** See `LICENSING.md` and
> `LICENSE-APACHE-2.0-PROPOSED.txt`. The proposal must not be interpreted as a finalized public grant.

## The performance position

CMPCT is not "Zstd with a new extension" and it is not satisfied by being smaller on one hand-picked
directory. Numeric core release candidates are benchmarked against their direct base before release.

The release rule is deliberately asymmetric because size and timing have different measurement physics:

- **archive size:** identical input + encoder semantics must never get larger; release gate tolerance is **0 bytes**;
- **create/extract speed:** base and candidate run on the same runner with repeated medians; a confirmed
  slowdown outside the documented relative+absolute noise envelope blocks release;
- **benchmark evidence:** every numeric core release must commit a fresh public benchmark record rather
  than leave the new result only in CI output;
- **corpora:** losing/adversarial workloads stay visible. A benchmark is not improved by deleting the
  case that disproves the headline.

See `docs/PERFORMANCE_RELEASE_GATE.md` for the normative release policy.

The broader v0.25 EntropyGraph neutral/hostile checkpoint remains the current research frontier: on its
fixed 10-workload synthetic suite, the experimental candidate recorded **16.46% smaller aggregate
storage than ZIP/Zstd-93**, **18.88% smaller than ZIP/Deflate-9**, and **6.91% smaller than a monolithic
solid tar+Zstd-19 diagnostic**, while retaining the workloads where it lost. Those are research-engine
results, not a claim that the canonical revision-24 reader already implements every EntropyGraph storage
semantic.

## What CMPCT can do today

Current canonical prototype capabilities include:

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
- on-demand export to ordinary Deflate ZIP for legacy compatibility.

The EntropyGraph research engine additionally explores global compressed-stream federation, reversible
representation inversion, exact object interning, compact micro-pack indexing, bounded adaptive
context, hot/cold stream roots and operational tail-metadata recovery. Those mechanisms remain gated
from the canonical reader until they pass format integration, conformance, hardening and portability
requirements.

The important rule is **content-driven selection, not extension-driven folklore**. If a specialized
representation is slower or larger for the actual bytes, CMPCT should not use it.

## Quick start

```bash
python -m pip install -e .
python -m cmpct create ./folder archive.cmpct
python -m cmpct info archive.cmpct
python -m cmpct list archive.cmpct
python -m cmpct verify archive.cmpct
python -m cmpct extract archive.cmpct ./restored
python -m cmpct range archive.cmpct path/to/huge.bin 1048576 4096 -o slice.bin
python -m cmpct export-zip archive.cmpct legacy.zip
```

For the optional native content-defined chunker on Linux:

```bash
cc -O3 -shared -fPIC native/cmpct_cdc.c -o src/cmpct/libcmpct_cdc.so
```

The reader does **not** depend on that helper. It accelerates boundary selection while creating an
archive; chunk boundaries are explicitly recorded on disk.

## New-agent reading order

A coding/research agent with no previous CMPCT context should read, in order:

1. `README.md` — mission and project shape;
2. `AGENTS.md` — mandatory development, benchmark and versioning rules;
3. `docs/CURRENT_STATE.md` — zero-chat-history handoff and immediate frontier;
4. newest applicable note under `docs/releases/` — latest numeric core milestone;
5. `docs/PERFORMANCE_RELEASE_GATE.md` — no-regression core-release contract;
6. `docs/FORMAT.md` — current revision-24 on-disk contract;
7. `docs/HISTORY.md` — surviving format/prototype history with private provenance generalized;
8. `docs/RESEARCH_LOG.md` and `docs/ENTROPYGRAPH.md` — experimental conclusions and frontier;
9. `docs/BENCHMARKS.md` — benchmark semantics and interpretation discipline;
10. `benchmarks/history/` — durable public machine-readable benchmark measurements;
11. `docs/PUBLIC_SURFACE.md` — public-repository/site disclosure boundary;
12. `docs/ROADMAP.md` — work remaining before 1.0.

A new agent should not need private chat, private corpora, or unrelated project context to continue
development safely.

## Repository map

- `src/cmpct/` — canonical revision-24 reference implementation.
- `experiments/entropygraph_v025.py` — executable EntropyGraph research engine; not canonical archive grammar.
- `benchmarks/universal_bench.py` — deterministic heterogeneous canonical benchmark corpus generator.
- `benchmarks/zip_parity_bench.py` — fair CMPCT/ZIP parity harness and shared-corpus release-gate harness.
- `benchmarks/neutral_hostile_corpus_v1.py` — broader deterministic-per-workload hostile corpus generator.
- `benchmarks/history/` — durable public machine-readable benchmark records.
- `tools/check_performance_regression.py` — direct-base release regression checker.
- `tools/check_version_discipline.py` — core-vs-surface version discipline gate.
- `SURFACE_REVISION` — alphabetic presentation/process revision (`x.x.a`, `x.x.b`, …).
- `docs/PERFORMANCE_RELEASE_GATE.md` — normative performance release policy.
- `docs/releases/` — one release note per numeric core release.
- `site/` — performance-first website and local Browser Lab.
- `native/cmpct_cdc.c` — optional native content-defined chunking accelerator.
- `native/cmpct-core/` — shared memory-safe read-only core and C ABI.
- `docs/CURRENT_STATE.md` — current handoff/frontier for a zero-context developer or agent.
- `docs/FORMAT.md` — current on-disk contract and invariants.
- `docs/HISTORY.md` — format and design lineage through the canonical revision-24 baseline.
- `docs/ENTROPYGRAPH.md` — generalized research results and integration boundary.
- `docs/RESEARCH_LOG.md` — design decisions, failed ideas and experimental conclusions.
- `docs/PRINCIPLES.md` — rules that prevent corpus-specific overfitting.
- `docs/BENCHMARKS.md` — benchmark discipline and interpreted checkpoints.
- `docs/PUBLIC_SURFACE.md` — what may and may not enter the public-facing repository/site surface.
- `docs/ROADMAP.md` — blockers between the prototype and a defensible 1.0.
- `tests/` — format and round-trip regression tests.

## Website

The site is designed to **create impact first, prove the claim second, and earn trust after that**.
Its headline performance numbers, competitor ladder, workload matrix, losses and core-release state are
generated from committed benchmark history rather than hand-maintained marketing percentages.

It deliberately separates:

- **research frontier** — the strongest currently verified experimental representation results;
- **canonical parity** — the executable revision-24 reader/writer compared against ZIP at equivalent
  library and fresh-process CLI boundaries;
- **surface revision** — the current site/docs/repository presentation milestone, which has no authority
  over archive semantics or benchmark truth.

The site may be visually and rhetorically aggressive. It may not blur those boundaries or invent a win.
Canonical `main` publishes through the Pages workflow only after public-surface, data-coherence,
surface-revision, JavaScript and Browser Lab compatibility checks pass.

## Version discipline

CMPCT no longer treats the numeric project version as a commit counter.

There are three different version axes:

1. **Numeric core project version (`MAJOR.MINOR.PATCH`)** — reserved for a material improvement to CMPCT
   itself: archive/engine capability, compression or speed, reliability, recovery,
   portability/interoperability, or another product-level gain. After the historical v0.27.1 checkpoint,
   normal core advancement moves the `MAJOR.MINOR` line and uses `PATCH=0` for packaging compatibility.
2. **Surface revision (`MAJOR.MINOR.LETTER`)** — site animation/design, documentation cleanup, repository
   presentation, workflow ergonomics and similar non-format work. The current surface milestone is
   `0.27.a`. It does not change `pyproject.toml` and does not require a synthetic benchmark record.
3. **On-disk format revision** — changes only when readers need new archive grammar/storage semantics.

A core release can improve encoder policy, speed, reliability or interoperability without changing the
on-disk revision, but it must still earn its numeric number with durable evidence. Conversely, a site or
repo beautification pass can be useful and substantial without pretending CMPCT itself became a new
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
