# .CMPCT

**Canonical repository for the CMPCT general-purpose archive/container project.**

CMPCT is an experimental lossless archive system designed around a simple goal: make the default
technical choice better than legacy ZIP across size, speed, random access, fidelity, integrity,
recovery, updates, and modern storage semantics—without optimizing for one application or corpus.

> Status: **project v0.25.0 / pre-1.0 / format under active development.** `main` is the canonical
> source of truth. The current executable reference implementation still writes format revision
> **24**. v0.25.0 publishes the EntropyGraph research milestone without pretending its research-only
> `CMPNX5` grammar is already a canonical revision-25 archive.

> Licensing status: **Apache-2.0 is proposed, not yet adopted.** See `LICENSING.md` and
> `LICENSE-APACHE-2.0-PROPOSED.txt`. The proposal must not be interpreted as a finalized public grant.

## What CMPCT is trying to do

CMPCT is not "Zstd with a new extension". It is a content-aware archive layer that can choose the
best exact representation for each object while preserving a single filesystem-like interface.
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

Project v0.25.0 additionally publishes an **experimental EntropyGraph engine** that explores global
compressed-stream federation, reversible representation inversion, exact object interning, compact
micro-pack indexing, bounded adaptive context, hot/cold stream roots, and operational tail-metadata
recovery. Those ideas are real executable research, but they remain gated from the canonical reader
until they pass format integration, conformance, hardening, and portability requirements.

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
2. `AGENTS.md` — mandatory development and versioning rules;
3. `docs/CURRENT_STATE.md` — zero-chat-history handoff and immediate frontier;
4. newest applicable note under `docs/releases/` — project-version milestone;
5. `docs/FORMAT.md` — current revision-24 on-disk contract;
6. `docs/HISTORY.md` — surviving format/prototype history with private provenance generalized;
7. `docs/RESEARCH_LOG.md` and `docs/ENTROPYGRAPH.md` — experimental conclusions and frontier;
8. `docs/BENCHMARKS.md` — benchmark semantics and merge discipline;
9. `benchmarks/history/` — machine-readable public benchmark measurements;
10. `docs/PUBLIC_SURFACE.md` — public-repository/site disclosure boundary;
11. `docs/ROADMAP.md` — work remaining before 1.0.

A new agent should not need private chat, private corpora, or unrelated project context to continue
development safely.

## Repository map

- `src/cmpct/` — canonical revision-24 reference implementation.
- `experiments/entropygraph_v025.py` — executable v0.25 research engine; not canonical archive grammar.
- `benchmarks/neutral_hostile_corpus_v1.py` — deterministic-per-workload heterogeneous hostile corpus generator.
- `benchmarks/history/` — durable public machine-readable benchmark records, including v0.25 EntropyGraph evidence.
- `docs/releases/` — one release note per material project version.
- `native/cmpct_cdc.c` — optional native content-defined chunking accelerator.
- `docs/CURRENT_STATE.md` — current handoff/frontier for a zero-context developer or agent.
- `docs/FORMAT.md` — current on-disk contract and invariants.
- `docs/HISTORY.md` — format and design lineage through the canonical revision-24 baseline.
- `docs/ENTROPYGRAPH.md` — v0.25 generalized research results and integration boundary.
- `docs/RESEARCH_LOG.md` — design decisions, failed ideas and experimental conclusions.
- `docs/PRINCIPLES.md` — rules that prevent corpus-specific overfitting.
- `docs/BENCHMARKS.md` — benchmark discipline and interpreted checkpoints.
- `docs/PUBLIC_SURFACE.md` — what may and may not enter the public-facing repository/site surface.
- `docs/ROADMAP.md` — blockers between the prototype and a defensible 1.0.
- `tests/` — format and round-trip regression tests.

## Version discipline

Every **material merged CMPCT milestone gets a new project version**. Project version and on-disk format
revision are deliberately separate: research, encoder policy, benchmark frontier, hardening or platform
integration can justify a new project version without changing archive grammar. Reader-visible storage
semantics require an on-disk format revision bump as well.

CI checks material paths and rejects a merge that reuses the previous project version or lacks the
matching `docs/releases/vX.Y.Z.md` note. This keeps substantive work visible to humans and agents instead
of leaving it stranded in chat, scratch artifacts, or unversioned commits.

## Development history and benchmark provenance

The project began as a sequence of Seekable-Zstd, indexed-Zstd, adaptive-framing and ZIP-family
experiments before becoming the native content-aware CMPCT format. The technical history is preserved,
but private corpus identities, private artifact names and unrelated project provenance are intentionally
not part of the public project record.

Public benchmark history must be independently reproducible or generated from deliberately public,
synthetic inputs. Private development corpora may still be useful local regression signals, but their
names, hashes, paths, contents, and artifact provenance are not public evidence.

Historical benchmark data is **not** automatically a public performance claim. CI and release notes
should preserve losing workloads and the exact semantics of each comparison rather than rewriting the
record around whichever result looks best.

## Public-surface rule

CMPCT must stand on its own. The repository and website must not require or expose unrelated internal
projects, private customer data, private corpora, personal information, chat transcripts, credentials,
private artifact names, or private-system links. See `docs/PUBLIC_SURFACE.md` for the enforceable rule.

## Canonicality

This repository supersedes chat-local CMPCT prototypes and benchmark scripts. New format changes,
benchmarks, experiments and design decisions must land here as a versioned project milestone.
Experimental code must be clearly labeled and cannot claim canonical format support until it is wired
into the reference reader/writer and conformance surface.

## License

Apache License 2.0 is the **current proposed license**, not the final adopted license. The repository
contains the unmodified proposed license text in `LICENSE-APACHE-2.0-PROPOSED.txt` plus an explicit
adoption checklist in `LICENSING.md`. Until that process is completed, do not represent CMPCT as
finally released under Apache-2.0.
