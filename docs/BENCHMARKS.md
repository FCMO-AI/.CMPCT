# Benchmark discipline and current checkpoints

CMPCT must be judged on heterogeneous workloads, not one showcase file. All headline comparisons
should state codec settings, filesystem/cache conditions, integrity semantics, durability semantics,
runtime/language, and whether a measurement includes process startup or filesystem metadata work.

## Durable benchmark policy

**Benchmark data is part of the project, not disposable scratch output.**

- Historical/raw result records belong under `benchmarks/history/`.
- Benchmark harnesses belong under `benchmarks/`.
- Generated corpora may remain ignored when they are reproducible from code/seeds, but their generator/version must be recorded.
- Any version or format change that cites a size/speed win should commit the machine-readable measurements used to justify it.
- A losing/adversarial result should be preserved when it changes design policy.
- Public-facing performance claims require controlled reruns; chat-local development measurements are regression markers only.

The complete surviving first development campaign is preserved in:

- `benchmarks/history/2026-08-13-development-campaign.json`
- `docs/HISTORY.md`
- `docs/RESEARCH_LOG.md`

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
- corpus generator/version, seed and/or content hashes;
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

## Measured development checkpoints

These are development measurements from the 2026-08-13 prototype campaign and are **not universal
performance guarantees**. Exact surviving figures are in the JSON historical record.

- Hermes aggregate: later native CMPCT revisions reached roughly half the size of the comparable ZIP
  while retaining all logical files and reconstructing the nested provenance archives exactly.
- Hermes full extraction: an optimized prototype reached about **27.8 ms vs ~42.9 ms ZIP** in the
  same repeated local test.
- Hermes creation: optimized CMPCT reached roughly **153 ms vs ~183 ms** for the controlled ZIP build.
- Large nested-file range read: a fresh-open 4 KiB slice late in a ~2 MiB nested source archive was
  measured around **0.49 ms vs ~5.21 ms** for the ZIP path in one checkpoint.
- Tiny-file corpus: microblock packing reduced a 3,200-file corpus from roughly **674 KiB ZIP to ~177
  KiB CMPCT** and cut all-file read time from roughly **32 ms to ~2.5 ms**.
- Source/config corpus: one campaign produced **~13.3 KiB CMPCT vs ~140 KiB ZIP** while remaining
  faster to read; later scanner optimization also moved creation ahead of ZIP on that corpus.
- Sparse corpus: a 256 MiB logical image with ~2 MiB allocated data produced **~2.00 MiB CMPCT vs
  ~2.25 MiB ZIP**, while CMPCT recreated a sparse file rather than materializing 256 MiB of zeros.
- Synthetic 16 MiB file + hardlink + symlink: CMPCT preserved link semantics and used **~16.78 MB vs
  ~50.35 MB** in a Python ZIP comparison that materialized link targets; a 4 KiB late range read was
  **~0.0043 ms vs ~22.9 ms**.
- Hostile already-compressed media corpus: the adaptive prototype reached **4,224,967 B CMPCT vs
  4,230,623 B ZIP** and created the archive in roughly **29 ms vs ~87 ms**.
- Twelve nested ZIPs: treating the exact archive bytes as an indexed Zstd group reached **796,725 B
  vs 808,393 B** for the normal outer ZIP, showing that nested virtualization should be adaptive.

## Historical benchmark interpretation

The early campaign deliberately mixed several benchmark layers:

1. codec-only/in-memory measurements;
2. already-open archive member reads;
3. open+read end-to-end operations;
4. full filesystem extraction;
5. process-start CLI timings;
6. native library read-through;
7. durability-equivalent mutation timings.

Do not compare numbers across those layers as if they measure the same operation. The historical JSON preserves the semantic labels where they survived.

## Benchmark gate for merging encoder-policy changes

A threshold or representation-policy change should normally satisfy all of the following:

1. improve at least one reproducible target workload;
2. run at least one adversarial workload where it might lose;
3. preserve byte-exact round trip and random-access semantics;
4. avoid an unexplained creation/extraction regression;
5. preserve recovery/integrity/durability semantics;
6. record the result under `benchmarks/history/` if it materially affects project direction.

Treat every historical number as a regression marker to reproduce under controlled CI, not marketing
copy. The universal harness exists to expose workloads where CMPCT loses and force the format to
improve or deliberately choose a simpler representation.
