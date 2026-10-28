# J24G13 — traced vs untraced ancestry CPU/RSS: **prior valid-chain CPU debt materially overstated by instrumentation**

Date: 2026-10-28 UTC. [Scientific PR #674](https://github.com/FCMO-AI/.CMPCT/pull/674), independent measurement child of [#671](https://github.com/FCMO-AI/.CMPCT/pull/671). Preregistered **before instrument** at `7b3aeab46c99a87c75c4fa8886f72fe1702ed6a1`. Original source parent `2a56e83a55bdd60a0b9de86e7d09bec2ca4d664d`, exact installed Reader Git blob `f13c5492f5acfa1cfcfec97cdbe0da71e41e327b`, no product source changes.

## First hosted answer and provenance

[Actions #40687049749](https://github.com/FCMO-AI/.CMPCT/actions/runs/40687049749), **SUCCESS** at exact test/head source `610f56d2ef824464b3142dfebc885504b6f500c1`, Ubuntu 24.04 / CPython 3.11. Artifact ID `12815402174`, SHA-256 `80e284e345ecd9487fa1b9c9dd07c41f96a65fa8301b30387195c54751872128` (GitHub artifact reported digest). All case samples use source-locked installed Reader and the same physical archive checksum across eager and guarded models, tested in fresh child processes with tracer **off** versus tracer **on** in predetermined interleaved order. Four independent observations per arm/mode for all non-malformed cases; one malformed-negative observation per arm/mode. CPU and wall include Reader open, complete read, two range reads and verify, not Python process startup or source/digest receipt computation.

### Median genuine process CPU, no `tracemalloc` within the timed operation

| Identical physical case | Eager | Guarded parse/discard | Guarded/eager | Peak RSS eager → guarded |
|---|---:|---:|---:|---:|
| Real Writer rename | 0.367 ms | 0.385 ms | 1.048x (+4.8%) | 31,880 → 31,880 KiB |
| 512 valid chained deltas | 15.041 ms | 16.851 ms | **1.120x (+12.0%)** | 33,288 → 33,288 KiB |
| 4,096 linked invalid SHA-authentic deltas | 89.114 ms | 59.403 ms | **0.667x (-33.3%)** | **62,550 → 44,400 KiB** |
| 4,096 independent invalid SHA-authentic deltas | 50.092 ms | 56.271 ms | **1.123x (+12.3%)** | 48,580 → 48,580 KiB |

### Matched median CPU when the tracer is on

| Physical case | Eager tracer ON | Guarded tracer ON | Guarded/eager tracer ON |
|---|---:|---:|---:|
| Writer rename | 0.746 ms | 0.796 ms | 1.067x |
| 512 valid deltas | 176.714 ms | 232.555 ms | **1.316x (+31.6%)** |
| 4,096 linked invalid deltas | 1,065.055 ms | 941.171 ms | **0.884x (-11.6%)** |
| 4,096 independent invalid deltas | 814.711 ms | 928.714 ms | 1.140x (+14.0%) |

The **same code and matched cases** therefore show a 1.120x rather than 1.316x valid-512 CPU ratio when running without allocation tracing. Eager valid-512 itself took 15.041 ms untraced versus 176.714 ms traced; this is not an estimate of normal CMPCT product slowdown, but a strong indication that tracing dominates the prior CPU observation. In the linked invalid case, the actual untraced resident peak reduces **29.0%**, not the 64.8% reduction seen with traced eager's 126,224 KiB RSS versus guarded's 44,400 KiB. The 88% Python traced-object peak reduction reported by J24G12 remains a true property *under that tracer*, but cannot be extrapolated as an 88% reduction in uninstrumented process RSS.

The malformed signed MessagePack negative gate was preserved: both the original eager and research guarded model rejected it, rather than silently selecting an older valid checkpoint. All normal cases preserved selected footer, delta depth, full member bytes, read_range boundaries and verify.

## Independent referee

The stdlib-only `research/j24g13_independent_receipt_audit.py` imports no CMPCT code. On first exact source/head: **866 deterministic receipt/source/raw checks**, **six fabricated receipt changes rejected** (false CPU row, fabricated median, hidden malformed failure, false Reader source, fake release, tracer-contaminated untraced row). It independently recomputed medians and ratios from recorded raw rows, checked same-archive SHA between arms, actual Git blobs and the no-release flags.

This audit is a second root for **receipt arithmetic and custody**, **not** independently reconstructed `.cmpct` physical bytes, repeat hosts, full released product or a proof of source mutation safety.

## Scientific decision

**DECISION CHANGED:** the exact original J24G12 valid-chain +30–34% CPU finding was **confounded by enabled tracemalloc** and cannot be claimed as untraced production CPU cost. The corresponding direct-hosted untraced research result is +12.0% valid-512 and +12.3% flat-invalid CPU. This is below the preregistered +25% valid-CPU kill boundary, but **still a measurable loss**, not a Pareto-dominating product replacement.

The guarded model has credible **29% lower untraced total process peak RSS** on the 4,096 chained orphan scenario and **33% faster untraced recovery CPU** in that same case. On a normal 512-valid chain, untraced RSS was equal at the measured process peak, despite lower traced Python live allocations. Thus guarding every ancestry object is not a general resource bound and is not yet fit for merging.

## Strongest negatives, alternative explanations and missing work

- The new matched no-tracer ratios are based on four independent fresh children per cell on **one Ubuntu host**, not a cross-platform product distribution. Linux `ru_maxrss` reports **total peak process RSS**, not incremental heap of one Reader; allocator baseline and loaded libraries can mask lower intermediate allocations.
- The old J24G12 instrument also monkeypatched decode/MessagePack call counters, whereas J24G13 does not monkeypatch the timed path. **Only the paired tracer ON/OFF result within J24G13** identifies the tracer confound. Never naively subtract CPU from the two different historical instruments.
- The trial's SHA-authentic orphan tails stress failure behavior; they do not establish natural prevalence, whole-archive create/extract time, real-world cold startup or exported disk/temp-memory costs. The actual set/trail still scales with ancestry length. Malicious unbounded inputs remain unproven safe.
- No concurrent on-disk same-inode mutation was performed; #654 risk remains. Multi-host (Windows, macOS), released-v0.30 competitor, native ABI and exact full performance/evidence gates remain **unmeasured**.
- The first hosted material-PR Engineering Evidence job **failed for missing PR dossier sections**, not for an observed Reader failure. The PR body was then replaced with the complete mandated dossier before the next commit; this is evidence-gate repair, not a changed evaluator.

## Counterfactual and next executable target

A prospective tracer OFF/ON matched court alongside J24G12 would have avoided interpreting the +34% valid CPU observation as production economics. Retain this **local** methodological lesson: when evaluating allocation-heavy architectures, measure CPU untraced and RSS externally, and reserve tracemalloc for heap attribution in separate or matched runs. **Do not change general discovery policy on this one episode**.

The next product-grade fork is a small **adaptive ownership** mechanism with deterministic generic memory budget and exact fallback: preserve one-pass eager records for provably shallow legitimate generations, free/defer long uncertain ancestry without changing signed malformed errors, and explicitly account for source revalidation, CPU, peak total RSS, temporary I/O and all prior release baselines. Check independent current ownership before writing code. If this mechanism cannot beat the eager control across real workloads, retire the always-guarded branch and switch to another measured product bottleneck.

**No merge, no release, no format/version change, no product-source edit, no exact released Reader speed claim.** Final HEAD and exact-head CI after writing this result are independently inspected and must not be inferred from first-hosted run `610f56d2`.
