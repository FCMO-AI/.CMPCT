# .CMPCT

**Canonical repository for the CMPCT general-purpose archive/container project.**

CMPCT is an experimental lossless archive system designed around a simple goal: make the default
technical choice better than legacy ZIP across size, speed, random access, fidelity, integrity,
recovery, updates, and modern storage semantics—without optimizing for one application or corpus.

> Status: **pre-1.0 / format under active development.** `main` is the canonical source of truth.
> The current executable prototype writes format revision **24**. No stability promise is made yet
> for pre-1.0 archives; reproducibility and backward compatibility become mandatory at 1.0.

## What CMPCT is trying to do

CMPCT is not "Zstd with a new extension". It is a content-aware archive layer that can choose the
best exact representation for each object while preserving a single filesystem-like interface.
Current prototype capabilities include:

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
2. `AGENTS.md` — mandatory development rules;
3. `docs/CURRENT_STATE.md` — zero-chat-history handoff and immediate frontier;
4. `docs/FORMAT.md` — current revision-24 on-disk contract;
5. `docs/HISTORY.md` — complete surviving version/prototype history;
6. `docs/RESEARCH_LOG.md` — experimental conclusions and rejected/superseded ideas;
7. `docs/BENCHMARKS.md` — benchmark semantics and merge discipline;
8. `benchmarks/history/` — machine-readable historical measurements;
9. `docs/ROADMAP.md` — work remaining before 1.0.

A new agent should not need the original ChatGPT conversation to continue development safely.

## Repository map

- `src/cmpct/` — working v0.24 reference implementation and executable format documentation.
- `native/cmpct_cdc.c` — optional native content-defined chunking accelerator.
- `docs/CURRENT_STATE.md` — current handoff/frontier for a zero-context developer or agent.
- `docs/FORMAT.md` — current on-disk contract and invariants.
- `docs/HISTORY.md` — version history from precursor experiments through the canonical v0.24 baseline.
- `docs/RESEARCH_LOG.md` — design decisions, failed ideas and experimental conclusions.
- `docs/PRINCIPLES.md` — rules that prevent corpus-specific or Hermes-specific overfitting.
- `docs/BENCHMARKS.md` — benchmark discipline and interpreted checkpoints.
- `benchmarks/history/` — durable machine-readable benchmark records.
- `docs/ROADMAP.md` — blockers between the prototype and a defensible 1.0.
- `benchmarks/universal_bench.py` — heterogeneous corpus benchmark generator/harness.
- `tests/` — format and round-trip regression tests.

## Development history and benchmark provenance

The project began as a sequence of Seekable-Zstd, indexed-Zstd, adaptive-framing and ZIP-family
experiments before becoming the native content-aware CMPCT format. That history is preserved rather
than rewritten into a clean fictional narrative.

- `docs/HISTORY.md` accounts for every revision range through v0.24 and explicitly marks intermediate
  revisions for which no independent release note survives.
- `docs/RESEARCH_LOG.md` records why major architectural choices were accepted or rejected.
- `benchmarks/history/2026-08-13-development-campaign.json` preserves the complete surviving numeric
  benchmark record from the original campaign in machine-readable form.

Historical benchmark data is **not** automatically a public performance claim. Future CI should
reproduce it under controlled hardware/software and append new result records rather than overwriting history.

## Canonicality

This repository supersedes chat-local CMPCT prototypes and benchmark scripts. New format changes,
benchmarks, experiments and design decisions should land here and be tied to a format revision or an
explicit experimental feature flag.

Any material version/format change should update the format spec, history/current-state documents,
relevant tests/conformance vectors and durable benchmark records in the same development cycle.

## License

No public/open-source license has been granted yet. Treat this private repository as FCMO-AI
internal work until a license is deliberately selected.
