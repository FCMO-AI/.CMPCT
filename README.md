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

## Repository map

- `src/cmpct/` — working v0.24 reference implementation and executable format documentation.
- `native/cmpct_cdc.c` — optional native content-defined chunking accelerator.
- `docs/FORMAT.md` — current on-disk contract and invariants.
- `docs/PRINCIPLES.md` — rules that prevent corpus-specific or Hermes-specific overfitting.
- `docs/BENCHMARKS.md` — benchmark discipline and current measured checkpoints.
- `docs/ROADMAP.md` — blockers between the prototype and a defensible 1.0.
- `benchmarks/universal_bench.py` — heterogeneous corpus benchmark.
- `tests/` — format and round-trip regression tests.

## Canonicality

This repository supersedes chat-local CMPCT prototypes and benchmark scripts. New format changes,
benchmarks, experiments and design decisions should land here and be tied to a format revision or an
explicit experimental feature flag.

## License

No public/open-source license has been granted yet. Treat this private repository as FCMO-AI
internal work until a license is deliberately selected.
