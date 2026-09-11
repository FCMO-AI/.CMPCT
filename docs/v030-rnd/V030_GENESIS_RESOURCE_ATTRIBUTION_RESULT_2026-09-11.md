# v0.30 Genesis resource attribution result — 2026-09-11

Status: **accepted diagnostic evidence; zero release credit; frozen gate verdict unchanged**.

This result separates two resource-accounting effects that the source-sealed Genesis worker could not distinguish:

1. Linux `ru_maxrss` lifetime high-water inherited before the frozen v0.30 product is imported;
2. CPU consumed by bounded descendant processes that `time.process_time()` in the Genesis parent does not charge.

The frozen contender remains `f4b158a55a08b9b18b50e4e4abe4b9251048c772`. No contender, format, selector, threshold, workload, or ONE evidence changed.

## Hosted receipts

- RSS attribution: run `34653349975`, job `103440281966`, exact-head `e8f3a15d67a69f922231517c57fce047bf7763bf`, **SUCCESS**.
- child-CPU attribution: run `34653583877`, job `103441025398`, exact-head `fbd069c26cac6fe0be9e70d17b30d66a38ee8fdc`, **SUCCESS**.

Both diagnostics execute the unchanged frozen v0.30 source through a detached worktree, verify all loaded `cmpct` modules resolve inside that checkout, generate benchmark inputs outside the measured child, and carry no release credit.

## RSS: Genesis high-water is already present at process start

Genesis reported `511,176,704 B` creation peak RSS for frozen v0.30 on every one of its 15 workloads. The attribution probe measured Analytics and DEFLATE-family as controls:

| workload | current RSS at process start | current RSS after product import | current RSS after build | `ru_maxrss` at process start | `ru_maxrss` after build |
|---|---:|---:|---:|---:|---:|
| Analytics | 14,532,608 B | 32,030,720 B | 175,734,784 B | 485,011,456 B | 485,011,456 B |
| DEFLATE-family | 14,397,440 B | 30,699,520 B | 36,974,592 B | 485,011,456 B | 485,011,456 B |

The lifetime high-water is therefore already about `462.5 MiB` **before** product import and does not rise during either build. It is `94.88%` of the historical Genesis `511,176,704 B` signal before any v0.30 work begins.

This falsifies the interpretation that the nearly constant Genesis `~487.5 MiB` value is workload-specific codec state. The likely mechanism is inherited high-water across the fork/exec path used to launch the worker after a much heavier parent process generated/loaded the corpus. `ru_maxrss` remains useful as a process lifetime statistic, but that specific Genesis measurement does not causally attribute build memory.

The current resident-memory endpoints are informative but are **not peak measurements during construction**. Analytics ends the build around `167.6 MiB` current RSS and DEFLATE-family around `35.3 MiB`; neither number should be promoted as the true operation peak without sampling the live process tree. The existing v0.30 runtime authority already owns a zero-credit 10 ms whole-process-tree sampler; future source-sealed historical attribution should use the same class of measurement rather than lifetime high-water alone.

## CPU: parent `process_time()` materially undercharges v0.30 descendants

The source-sealed child-CPU companion measures `RUSAGE_SELF` and `RUSAGE_CHILDREN` around the unchanged frozen build in a fresh child.

| workload | frozen v0.30 wall | parent/self CPU | reaped child CPU | total process-tree CPU | source-sealed v0.29 CPU | v0.29 wall |
|---|---:|---:|---:|---:|---:|---:|
| Analytics | 109.6490 s | 1.3905 s | 261.5150 s | **262.9055 s** | 209.7236 s | 209.7459 s |
| DEFLATE-family | 1.5358 s | 0.4455 s | 1.7310 s | **2.1764 s** | 6.6890 s | 6.6896 s |

The two controls show opposite economics:

- **Analytics:** v0.30 finishes substantially sooner in elapsed time because it parallelizes, but consumes about `25.36%` more total CPU than v0.29 (`262.91 / 209.72`). This is a real compute-efficiency debt even though latency is better.
- **DEFLATE-family:** v0.30 improves both elapsed latency and total CPU materially.

Therefore the Genesis aggregate `33.0603 s` creation CPU for v0.30 remains a correct parent-process measurement, but it must not be described as total compute. The frozen matrix aggregate elapsed creation wall remains about `347.28 s` versus `806.62 s` for v0.29, so the near-term line still has a real latency advantage. Compute-efficiency now requires explicit process-tree CPU attribution on material expensive paths.

## Consequence for R4 / Analytics

Analytics is simultaneously:

- the second-largest frozen density deficit versus v0.29;
- the largest block of expensive r25 audition work that ultimately loses publication to r24;
- a case where v0.30 lowers elapsed time through parallelism but spends more total CPU than v0.29.

That strengthens, rather than weakens, the current sparse-R4 objective. A useful Analytics mechanism must not merely make the stored bytes smaller. It should either:

1. turn existing expensive work into a publishing representation with materially better information yield; or
2. supply a cheap gate that avoids most of the expensive audition when the opportunity cannot win.

The correct optimization metric is now explicitly **authenticated bytes eliminated per process-tree CPU second / elapsed second / memory traffic**, not parent-process CPU alone.

## Claim boundary

These diagnostics do not alter the ONE Genesis decision. The decisive gate result remains authenticated stored bytes: ONE-G0.2 lost to both mature comparators on all 15 workloads, so v0.30 remains the primary near-term line and ONE remains preserved as secondary research evidence.

They do alter future reporting discipline:

- never use Genesis v0.30 parent CPU as total compute;
- never use the historical uniform `ru_maxrss` as workload-attributed build memory;
- charge descendant CPU where v0.30 uses process parallelism;
- use sampled current process-tree RSS for operation memory;
- keep elapsed wall, total CPU and memory as separate axes rather than collapsing them into one speed claim.
