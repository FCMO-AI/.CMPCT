# Promoted runtime whole-process-tree RSS companion v1 — result

Status: **COMPLETE / MEMORY SUPPORTED / TIMING INSTRUMENTATION CONFOUNDED / ZERO RELEASE CREDIT**

## Exact evidence

- source commit: `e7f8eaeb5df6f388217f4efd626501c710d73471`;
- workflow: `CMPCT v0.30 runtime promotion gate`;
- run: `33733682186`;
- substantive job: `100579219787` (`whole-tree-rss-companion`);
- artifact id: `9885110516`;
- artifact name: `v030-promoted-runtime-tree-rss`;
- artifact ZIP digest: `sha256:b0c9a7f69611bd5db28ac535cdf133fc375d4032213a884512d8ddc526f9fe16`;
- instrument schema: `cmpct-v030-release-performance-tree-rss-v1`;
- sampler: `benchmarks/v030_perf_worker_tree_rss.py`;
- release credit: **zero**.

The v1 receipt is immutable. It may not be edited, reinterpreted as the ordinary promoted-runtime authority, or made green by changing its post-result thresholds.

## What the receipt actually proved

The stronger sampler charged the worker plus live transitive descendants every 10 ms and retained the largest observed simultaneous process-tree VmRSS, with the worker's own `ru_maxrss` as a floor.

All three frozen promoted runtime targets plus the media companion remained below the inherited `<=1.25x` memory ceiling:

| workload | pack whole-tree RSS ratio | extract whole-tree RSS ratio | max |
|---|---:|---:|---:|
| Logs | 0.6240873x | 0.9217877x | 0.9217877x |
| Shifted | 0.9210590x | 0.9753086x | 0.9753086x |
| ML | 0.7445212x | 0.9657236x | 0.9657236x |
| media | 0.3009276x | 0.6809732x | 0.6809732x |

Global maxima:

- pack whole-tree RSS ratio: **0.9210589685x**;
- extract whole-tree RSS ratio: **0.9753086420x**;
- inherited memory ceiling: **1.25x**;
- exact target count/correctness/tree/strong-verification custody: **pass**.

This is decision-changing D5 evidence: the integrated PrefixGraph process child does not create a hidden whole-process-tree RSS regression on the measured promoted matrix.

## Why the workflow still failed

v1 collected RSS from a Python thread **inside the measured worker process**. The thread wakes every 10 ms, traverses `/proc`, parses process status and child lists, and therefore competes for the same Python GIL and CPU budget as CPU-heavy canonical pack work.

The receipt showed timing inflation concentrated in pack operations:

- Shifted create ratio: **1.2874814728x**;
- ML create ratio: **1.2837484231x**;
- Logs create ratio: **1.1440261407x**;
- media create ratio: **0.5276655973x**.

The independent promoted-product runtime authority, which uses the canonical worker without the in-process sampler, had already passed its frozen runtime matrix. The v1 companion was explicitly introduced as a zero-release-credit stronger **memory** companion, but its implementation inherited the base harness's timing decision and exited nonzero when sampler-contaminated wall ratios crossed that unrelated gate.

Therefore:

- the v1 timing miss is **not** evidence that the shipping product regressed to those ratios;
- the v1 RSS measurements remain useful scoped evidence;
- v1 may not be patched after result-bearing execution;
- a superseding instrument is required to separate the memory observation from the measured worker's GIL and from timing decision credit.

## Scoped negative constraint

Do not use an in-process Python sampling thread as a timing-comparable whole-tree RSS instrument for this CPU-heavy release matrix. Reopening that measurement design requires evidence that its timing perturbation is negligible under the same runtime regime.

## Terminal custody decision

**`TREE_RSS_V1_MEMORY_SUPPORTED_TIMING_INSTRUMENTATION_CONFOUNDED`**

The exact product runtime authority remains independently governed by `benchmarks/v030_release_performance_product.py`. The stronger memory question proceeds only through the frozen superseding v2 instrument.
