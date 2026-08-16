# Benchmark discipline and current checkpoints

CMPCT must be judged on heterogeneous workloads, not one showcase file. All headline comparisons
should state codec settings, filesystem/cache conditions, integrity semantics, durability semantics,
runtime/language, and whether a measurement includes process startup or filesystem metadata work.

## Durable benchmark policy

**Benchmark data is part of the project, not disposable scratch output.**

- Public/raw result records belong under `benchmarks/history/`.
- Benchmark harnesses belong under `benchmarks/`.
- Generated corpora may remain ignored when they are reproducible from code/seeds, but their generator/version must be recorded.
- Any public numeric core version or format change that cites a size/speed win must commit the machine-readable measurements used to justify it.
- A losing/adversarial result should be preserved when it changes design policy.
- Public-facing performance claims require controlled reruns; one-off development measurements are regression markers only.
- Private-corpus measurements may guide internal engineering, but their identity, raw input, artifact names and private provenance do not belong in the public benchmark archive.
- Research-frontier and canonical-parity records are different evidence classes; neither may be relabeled to fill a missing UI comparison.

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
- version-shift workloads for content-defined/resemblance chunking;
- near-duplicate shifted versions and repeated boundary churn;
- false-similarity-neighbor populations that attack candidate-search bounds;
- related DEFLATE container families and exact-transform round trips;
- corruption, truncated-tail and recovery workloads;
- cold and warm random-range reads;
- strict remote/range-backed access that can prove it did not silently fetch the whole archive.

## Minimum metadata for new benchmark records

When available, store:

- CMPCT commit SHA, project version and format revision;
- benchmark harness commit SHA;
- corpus generator/version, seed and/or content hashes for public/reproducible inputs;
- direct comparison base or inherited research baseline;
- CPU, RAM, storage, OS/kernel and filesystem;
- relevant codec/runtime/compiler versions;
- exact codec/archive settings;
- warm/cold cache state;
- process-start vs in-process timing;
- repetitions and statistic (median/mean/p95/etc.);
- integrity work included;
- metadata restoration semantics;
- durability/fsync semantics;
- dependency depth, decode-unit/read-amplification and memory ceilings for graph/solid representations;
- representation-selection/fallback policy;
- unavailable competitors and semantic mismatches;
- known losses or limitations.

## Public measured checkpoints

The public durable ZIP-parity records are development regression evidence, **not universal performance
guarantees**. The website reads these committed records directly and keeps library and CLI layers
separate.

Representative canonical synthetic/reproducible checkpoints include:

- tiny-file corpus: microblock packing reduced a 3,200-file corpus from roughly **674 KiB ZIP to ~179 KiB CMPCT** while preserving individual logical files;
- source/config corpus: roughly **13.7 KiB CMPCT vs ~140 KiB ZIP** in a shared-runner parity record;
- already-compressed media corpus: CMPCT stayed close to input/ZIP size while avoiding unnecessary recompression work;
- sparse corpus: CMPCT preserved logical holes and stored roughly **4.20 MiB** for a 128 MiB logical image in the parity corpus, rather than treating the entire logical zero range as ordinary payload;
- combined corpus: shared-runner records show CMPCT smaller than the Python Deflate-ZIP baseline and faster in several library create/extract paths;
- large-binary library extraction remains a known case where ZIP can still win; that loss is intentionally preserved as an engineering defect rather than hidden.

For exact values, environment and semantic caveats, use the JSON records in `benchmarks/history/`.

## v0.28 EntropyGraph II research checkpoint

`benchmarks/history/2026-08-16-entropygraph-v028.json` is the current research-frontier record. It
combines the original 10 neutral/hostile workloads with five resemblance-hostile attacks and treats
**inherited EntropyGraph v0.25** as the primary representation baseline.

Across all 15 fixed workloads:

- inherited v0.25: **166,816,028 B**;
- selected EntropyGraph II portfolio: **137,557,457 B**;
- change: **-17.5394%**;
- improved workloads: **3**;
- regressed workloads: **0**;
- exact inherited fallbacks: **12**;
- measured delta nodes: **233**;
- exact preflate wins: **25**.

The strongest causal wins are:

- shifted near-duplicate versions: **30,200,827 → 1,761,588 B (-94.17%)**;
- repeated one-byte boundary churn: **866,651 → 89,945 B (-89.62%)**;
- ML artifacts: **13,879,065 → 13,836,439 B (-0.31%)**.

The 12 unchanged workloads are not “ties by omission.” The portfolio actually emits the inherited v0.25
artifact when the new graph candidate loses. Creation CPU for auditioning both candidates remains
recorded as an exported cost.

The structural sweep uses two disjoint complete aggregate trees and records ZIP/Deflate-9, solid
tar+Zstd-19, 7z/LZMA2, ZPAQ m5, Borg and DwarFS when available. On the resemblance-hostile aggregate:
CMPCT stores **47,197,165 B**, tar+Zstd solid **47,065,652 B**, ZPAQ m5 **47,062,641 B**, 7z/LZMA2
**47,430,344 B**, Borg **76,460,621 B**, and ZIP/Deflate **76,690,799 B**. DwarFS was unavailable and
is explicitly recorded as unavailable.

These structural numbers are not canonical semantic-parity claims. Solid tools and CMPCT's bounded
reconstruction graph expose different random-member, dependency, authentication and recovery behavior.
The public site therefore labels the inherited frontier as the v0.28 primary comparator and keeps every
structural competitor under its real name.

## Failed v0.28 release-gate evidence is also evidence

The first post-reconciliation direct-base ABBA gate preserved exact archive sizes but rejected one
timing cell: media fresh-process CLI creation measured **192.99 → 203.07 ms (+5.22%, +10.08 ms)**.
Twenty timing cells improved in the same run, and the corresponding media library create path changed by
less than 1 ms. The result was not rerun until green.

The release candidate changed the default fresh-process CLI policy so `cmpct create` stays serial unless
`--workers N` is explicitly requested, while the in-process `Builder` retains deterministic parallel
creation. The fix must pass a new direct-base gate. This is the intended use of the benchmark: isolate an
exported cost and change the mechanism, not the acceptance threshold.

## Historical benchmark interpretation

Development work has used several benchmark layers:

1. codec-only/in-memory measurements;
2. already-open archive member reads;
3. open+read end-to-end operations;
4. full filesystem extraction;
5. process-start CLI timings;
6. native library read-through;
7. durability-equivalent mutation timings;
8. research structural-competitor aggregate trees;
9. selective-read decoded-byte/read-amplification accounting.

Do not compare numbers across those layers as if they measure the same operation. Durable public JSON
records must preserve the timing layer and semantic mismatch information needed to interpret results.

## Benchmark gate for merging encoder-policy changes

A threshold or representation-policy change should normally satisfy all of the following:

1. improve at least one reproducible target workload;
2. run at least one adversarial workload where it might lose;
3. preserve byte-exact round trip and random-access semantics;
4. avoid an unexplained creation/extraction regression;
5. preserve recovery/integrity/durability semantics;
6. expose dependency depth, decoded work and memory costs when the representation introduces them;
7. record the result under `benchmarks/history/` if it materially affects public project direction;
8. pass `tools/check_public_surface.py` before the benchmark record is treated as release-facing evidence.

Treat every historical number as a regression marker to reproduce under controlled CI, not marketing
copy. The universal and hostile harnesses exist to expose workloads where CMPCT loses and force the
format to improve or deliberately choose a simpler representation.
