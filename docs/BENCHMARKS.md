# Benchmark discipline and current checkpoints

CMPCT must be judged on heterogeneous workloads, not one showcase file. All headline comparisons
should state codec settings, filesystem/cache conditions, integrity semantics, durability semantics,
runtime/language, and whether a measurement includes process startup or filesystem metadata work.

## Durable benchmark policy

**Benchmark data is part of the project, not disposable scratch output.**

- Public/raw result records belong under `benchmarks/history/`.
- Benchmark harnesses belong under `benchmarks/`.
- Generated corpora may remain ignored when they are reproducible from code/seeds, but their generator/version must be recorded.
- Any public version or format change that cites a size/speed win should commit the machine-readable measurements used to justify it.
- A losing/adversarial result should be preserved when it changes design policy.
- Public-facing performance claims require controlled reruns; one-off development measurements are regression markers only.
- Private-corpus measurements may guide internal engineering, but their identity, raw input, artifact names and private provenance do not belong in the public benchmark archive.

The public benchmark record is preserved in `benchmarks/history/`, `docs/HISTORY.md`, and
`docs/RESEARCH_LOG.md`. Early private-development measurements that influenced design are generalized
in prose rather than published as private provenance.

## Required benchmark classes

- many tiny unique files and duplicates;
- source/config trees;
- already-compressed/random media;
- compressible and incompressible large binaries;
- duplicate files, hardlinks and symlinks;
- sparse VM/database-style images;
- nested archives with and without cross-container redundancy;
- version-shift workloads for content-defined chunking;
- corruption, truncated-tail and recovery workloads;
- cold and warm random-range reads;
- remote/range-backed access once implemented.

## Minimum metadata for new benchmark records

When available, store:

- CMPCT commit SHA and format revision;
- benchmark harness commit SHA;
- corpus generator/version, seed and/or content hashes for public/reproducible inputs;
- CPU, RAM, storage, OS/kernel and filesystem;
- relevant codec/runtime/compiler versions;
- exact codec/archive settings;
- warm/cold cache state;
- process-start vs in-process timing;
- repetitions and statistic (median/mean/p95/etc.);
- integrity work included;
- metadata restoration semantics;
- durability/fsync semantics;
- known mismatches or limitations.

## Public measured checkpoints

The current public durable ZIP-parity records are development regression evidence, **not universal
performance guarantees**. The website reads these committed records directly and keeps library and CLI
layers separate.

Representative public synthetic/reproducible checkpoints include:

- tiny-file corpus: microblock packing reduced a 3,200-file corpus from roughly **674 KiB ZIP to ~179 KiB CMPCT** while preserving individual logical files;
- source/config corpus: roughly **13.7 KiB CMPCT vs ~140 KiB ZIP** in the current shared-runner parity record;
- already-compressed media corpus: CMPCT stayed close to input/ZIP size while avoiding unnecessary recompression work;
- sparse corpus: CMPCT preserved logical holes and stored roughly **4.20 MiB** for a 128 MiB logical image in the current parity corpus, rather than treating the entire logical zero range as ordinary payload;
- combined corpus: current shared-runner records show CMPCT smaller than the Python Deflate-ZIP baseline and faster in several library create/extract paths;
- large-binary library extraction remains a known case where ZIP can still win; that loss is intentionally preserved as an engineering defect rather than hidden.

For exact values, environment and semantic caveats, use the JSON records in `benchmarks/history/`.

## Historical benchmark interpretation

Development work has used several benchmark layers:

1. codec-only/in-memory measurements;
2. already-open archive member reads;
3. open+read end-to-end operations;
4. full filesystem extraction;
5. process-start CLI timings;
6. native library read-through;
7. durability-equivalent mutation timings.

Do not compare numbers across those layers as if they measure the same operation. Durable public JSON
records must preserve the timing layer and semantic mismatch information needed to interpret results.

## Benchmark gate for merging encoder-policy changes

A threshold or representation-policy change should normally satisfy all of the following:

1. improve at least one reproducible target workload;
2. run at least one adversarial workload where it might lose;
3. preserve byte-exact round trip and random-access semantics;
4. avoid an unexplained creation/extraction regression;
5. preserve recovery/integrity/durability semantics;
6. record the result under `benchmarks/history/` if it materially affects public project direction;
7. pass `tools/check_public_surface.py` before the benchmark record is treated as release-facing evidence.

Treat every historical number as a regression marker to reproduce under controlled CI, not marketing
copy. The universal harness exists to expose workloads where CMPCT loses and force the format to
improve or deliberately choose a simpler representation.
