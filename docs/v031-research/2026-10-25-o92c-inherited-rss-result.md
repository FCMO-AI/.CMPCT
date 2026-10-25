# O92c — Hosted Linux parent → subprocess RSS high-water inheritance: confirmed

Date: 2026-10-25 UTC

## Prospective hypothesis and source custody

The [O92c prospective preregistration](2026-10-25-o92c-inherited-rss-prereg.md) was committed at `b0de6e842643782854e6180f8260fc5efc68684c` **before** the instrument `170f48e4218a6f614139a3896ded3d8ed769af64` and workflow `523487f90fcc9d3596b7bf6d01628e09ba9f7b8e`. No CMPCT product/format/benchmark/evaluator changed.

**Genuine hosted Ubuntu Actions [#40211292193](https://github.com/FCMO-AI/.CMPCT/actions/runs/40211292193) SUCCESS** at exact research HEAD `523487f90fcc9d3596b7bf6d01628e09ba9f7b8e`. Four executed child Python processes, zero failures/skips. Raw original [artifact #12606081578](https://github.com/FCMO-AI/.CMPCT/actions/runs/40211292193/artifacts/12606081578), artifact digest `sha256:7d7a74c94a96535e925b6524e586ca9acfea3319f912348ae33b2d6d1ad3dada`. Python 3.11.17, Linux GitHub Ubuntu 24.04.

## Direct unambiguous result (KiB)

| Process checkpoint | `resource.ru_maxrss` | Independent Linux `VmHWM` | Current `VmRSS` |
| --- | ---: | ---: | ---: |
| **Clean child** before parent allocation | **12,268** | **12,272** | 12,272 |
| Parent after touching 192 MiB (192 MiB extra) | 209,012 | 209,016 | 209,016 |
| Parent after freeing allocation | 209,012 | 209,012 | 12,404 |
| **Child #1 after parent peak** | **209,012** | **12,296** | 12,296 |
| **Child #2 after parent peak** | **209,012** | **12,400** | 12,400 |
| **Child #3 after parent peak** | **209,012** | **12,396** | 12,396 |

The child Python process **inherits its parent's `ru_maxrss` high-water number** despite its independent `/proc/self/status VmHWM` showing only ~12 MiB actual child high-water. This persisted in all three child repetitions. It is a **real hosted instrument primitive** in the exact Linux subprocess-execution context.

**DECISION: CONFIRMED_INHERITED_ACCOUNTING**. It confirms the likely cause of O92's apparent ~300 MiB *pre-Builder* baseline on a child of the same parent which generates 3 × 65 MiB inflated fixture members. It does **not** prove a specific original O88 child's actual physical memory; that requires measuring the two authentic CMPCT engines with independent child `VmHWM` at matched sources.

## Consequence for existing product evidence

- O88 #447's **complete archive bytes, CPU and exact read/verify/extract observations remain valid** and unaffected by this finding.
- O88's `resource.ru_maxrss` after subprocess creation **must no longer be treated as exact peak physical memory of an independent CMPCT engine**, because the witness can inherit parent fixture-generation peaks. Any previously reported ~300 MiB comparison is an untrusted memory-attribution claim pending independent child `VmHWM` comparison.
- O92's 300,348 KiB "before Builder" is **not proof that CMPCT imported ~300 MiB**. O92b separately showed clean imports ~23 MiB. The cross-experiment pattern plus this hosted primitive strongly support inherited accounting. The ~4,368 KiB O63 minus O86 *above inherited floor* is real recorded increment in ru_maxrss but may underestimate allocations under a high inherited floor; do not interpret it as a true Builder peak-memory delta.
- `ru_maxrss` per se is not bogus: it truthfully reflects this Linux accounting API's value. The error is interpreting it as an isolated child peak under parent-spawn conditions.

## Self-critique / negative / exact scope

This is a Linux OS/Python-process metric falsifier, **not a new product regression or an archival throughput experiment**. Synthetic parent memory materialization ensures the effect can be seen but is not the CMPCT workload itself; O88-source child VmHWM has not yet been measured. The test uses one hosted kernel/runtime and three repeated children, not all OS variants. No changes to Linux, Python, CMPCT, or the original instruments; no release credit.

## Cheapest executable continuation / counterfactual

The efficient prospective test was to log **both** `ru_maxrss` and `/proc/self/status:VmHWM` at the start of each child benchmark run. Its absence led to two avoidable interpretive hypotheses about Builder vs Reader. The transferable scientific lesson is to treat resource **measurement provenance** as carefully as Git source provenance: a fresh exec may not mean a fresh `ru_maxrss` history on Linux.

Next implement an **independent new (never edited-in-place O88) genuine original O63-versus-O86 same-fixture research court** that measures child `VmHWM` immediately before and after Builder and after Reader, plus actual current `VmRSS`, with strict identical file hashes, installed source identities, raw repeated observations and no memory-efficiency claim without those measurements. That is a distinct scientific-fidelity prerequisite, not license to optimize codecs, adjust gates or raise VZIP budgets.

No discovery-policy edit is justified by only one platform primitive even when exact result is replicated.
