# Benchmark discipline and current checkpoints

CMPCT must be judged on heterogeneous workloads, not one showcase file. All headline comparisons
should state codec settings, filesystem/cache conditions, integrity semantics, durability semantics,
runtime/language, and whether a measurement includes process startup or filesystem metadata work.

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

## Measured development checkpoints

These are development measurements from the 2026-08-13 prototype campaign and are **not universal
performance guarantees**:

- Hermes aggregate: later native CMPCT revisions reached roughly half the size of the comparable ZIP
  while retaining all logical files and reconstructing the nested provenance archives exactly.
- Hermes full extraction: an optimized prototype reached about 27.8 ms versus ~42.9 ms for ZIP in the
  same repeated local test.
- Hermes creation: optimized CMPCT reached roughly 153 ms versus ~183 ms for the controlled ZIP build.
- Large nested-file range read: a fresh-open 4 KiB slice late in a ~2 MiB nested source archive was
  measured around 0.49 ms versus ~5.21 ms for the ZIP path.
- Tiny-file corpus: microblock packing reduced a 3,200-file corpus from roughly 674 KB ZIP to ~177 KB
  CMPCT and cut all-file read time from roughly 32 ms to ~2.5 ms in that prototype test.
- Source/config corpus: one campaign produced ~13.3 KB CMPCT versus ~140 KB ZIP while remaining faster
  to read; later scanner optimization also moved creation ahead of ZIP on that corpus.
- Sparse corpus: a 256 MiB logical image with ~2 MiB allocated data produced ~2.00 MiB CMPCT versus
  ~2.25 MiB ZIP, while CMPCT recreated a sparse file rather than materializing 256 MiB of zeros.
- Synthetic 16 MiB file + hardlink + symlink: CMPCT preserved link semantics and used ~16.78 MB versus
  ~50.35 MB in a Python ZIP comparison that materialized link targets; a 4 KiB late range read was
  ~0.004 ms versus ~22.9 ms.

Treat every number above as a regression marker to reproduce under controlled CI, not marketing copy.
The universal harness exists to expose workloads where CMPCT loses and force the format to improve or
deliberately choose a simpler representation.
