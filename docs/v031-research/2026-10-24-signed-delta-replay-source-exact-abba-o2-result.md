# O2 result — source-exact signed delta replay ABBA (2026-10-24)

**Status: DECISIVE FOCUSED PRODUCT PERFORMANCE CANDIDATE; NOT A RELEASE CLAIM.** This document records the result **after** the immutable O2 preregistration. Never alter the original preregistration, frozen O0 benchmark, source comparator or acceptance gates to reinterpret this result.

## Actual authority and result identity

- Research PR: [#347](https://github.com/FCMO-AI/.CMPCT/pull/347), stacked on O1 implementation [#346](https://github.com/FCMO-AI/.CMPCT/pull/346).
- Successful GitHub Actions source-exact run: [40088624307](https://github.com/FCMO-AI/.CMPCT/actions/runs/40088624307), exact workflow HEAD `72fd5e627b6b8930f95dab49b992359ec1c0f801`.
- Immutable historical full `validation.py` blob: `51c2849061f99a4afeddb7666956b24566ce7de0` at `4545d7d5b2a0b712b4b00f5a9c291d4a3a9e169b`. SHA-256 `0c77dceeac0ae518b2e72f3dad8925c03225e8cb7b81b3f799a3f0c8de41e0eb`.
- O1 candidate source commit: `fb887d8610dced551acf5a84778ba539d08dac59`, `validation.py` blob `58a71ae97837d7158a6a853653ef58818d0b1ee8`. SHA-256 `5a2d0af48a8af212e98c95fc2e5010a01cdc91879f29c8c167c6d0cb8f501dff`.
- Source dependency parity: `codec.py` and `path_policy.py` bytes identical for historical and candidate source commits; the court checks these facts and checks the live candidate file against the pinned commit.
- Raw artifact [#12557973325](https://github.com/FCMO-AI/.CMPCT/actions/runs/40088624307/artifacts/12557973325) ZIP SHA-256 `37526ab54525dde86eaa22b507d28046401801eb895a7f4bdc7397c9212985bd`; JSON receipt SHA-256 `9d119716f634fd2cb972e9f2f66dc11663faa675e08945b2e46c1eedde8ba506`.

## Whole historical validator versus installed candidate

Both modules executed the **same physical signed revision-24 archive bytes**, not separately generated corpus files. Repeated calls alternated A/B/B/A and B/A/A/B on one Ubuntu Python 3.11 runner. Each arm ran 14 wall/CPU samples after warmup, while checkpoint controls had identical final logical indexes. Builder, process startup and import costs were outside the timed boundary. 12 independent O1 randomized/hostile regression tests also passed.

| Signed rename operations | Historical full preflight median (ms) | O1 full preflight median (ms) | Same-runner speedup | Historical replay CPU (ms, full preflight) | O1 CPU (ms, full preflight) |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 128 | 0.782877 | 0.4769995 | **1.64×** | 0.782256 | 0.472777 |
| 512 | 7.2173345 | 1.835162 | **3.93×** | 7.216704 | 1.8343815 |
| 2,048 | 94.921964 | 7.201383 | **13.18×** | 94.923932 | 7.2002475 |
| 4,096 | 369.101145 | 14.6557855 | **25.18×** | 369.084664 | 14.6545695 |

At 4,096 operations the complete signed delta archive was **12,046 bytes** for both sources; the structurally same-final signed checkpoint was **4,601 bytes**. Historical and candidate checkpoint preflight medians were **9.6954845 ms** and **9.413957 ms**, respectively; checkpoint differences are not a separate confirmed improvement. The whole source-authentic preflight answer, authenticated bytes, file count, delta depth and exact Reader sample contents agreed.

## Strong negative: exported allocation cost

`tracemalloc` ran in a **separate, untimed pass** to avoid distorting the speed benchmark. It counts traced peak Python allocations, **not process peak RSS**, native allocations or complete system cost.

| Operations | Historical traced peak | Indexed traced peak | Exported allocation |
| ---: | ---: | ---: | ---: |
| 128 | 97,971 B | 122,315 B | **+24,344 B (+24.85%)** |
| 512 | 305,097 B | 423,657 B | **+118,560 B (+38.86%)** |
| 2,048 | 1,182,681 B | 1,679,392 B | **+496,711 B (+42.00%)** |
| 4,096 | 2,345,893 B | 3,349,237 B | **+1,003,344 B (+42.77%)** |

The heap-per-path positional index removes quadratic scans but exports linear temporary memory. The full parser permits substantially more than 4,096 files, so memory/RSS is a genuine remaining product decision, not a rounding artifact. The observed linear trend alone does not justify extrapolating a hard upper bound without measuring peak process RSS and GC behavior.

## Decision / PARETOBONK

**O1 CPU-amplification mitigation survives its source-exact same-machine falsifier**, with a genuine 25.18× full-preflight median improvement on the 4,096-operation research input and no observed semantic mismatch. **It is not yet a Pareto-dominant full product win:** transient Python allocations increased materially, the recovery/multi-generation/OS frontier remains incompletely tested, and the official release benchmark comparison has not earned promotion credit.

Simpler controls rejected: a plain dict cannot preserve first-occurrence and transient duplicates; reducing limits changes accepted history; a checkpoint-only comparison does not measure historical replay CPU. A bounded next experiment may measure independent per-process peak RSS and compare a compressed/sparse ownership index that preserves all historical semantics without one heap object per unique name. Do not garden the existing 8-op/64-file threshold or declare memory free. PR #342 owns independent hardlink graph memoization in the same `validation.py`; exact combined-source semantic and performance verification is required before integration.

Counterfactual: direct comparison of historical `_apply_delta` loop and candidate index predicts the CPU asymptotics cheaply; a prospective allocation probe would have exposed the memory cost **before** attributing the full speedup to a robust product Pareto win. This is a transferable instrumentation lesson, not grounds to amend the Discovery Engine based on one case. No release, merge or numeric version promotion is authorized.
