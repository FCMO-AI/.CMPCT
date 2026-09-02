# r25 dual-candidate process-isolation RSS result

Status: **accepted Forge R2 causal evidence / scoped negative after a material PrefixGraph lifetime win / no release credit**

This record preserves the result-bearing execution of the frozen experiment in
`docs/v030-rnd/R25_DUAL_CANDIDATE_PROCESS_ISOLATION_RSS_PREREG.md`. The preregistration,
worker, oracle and workflow are immutable after this result-bearing execution.

## Authority

- authoritative branch: `agent/v030-authoritative-integration`
- exact source head: `769cb54e47de454af9c5e6cf57c6d0e495878048`
- workflow: `CMPCT v0.30 dual-candidate process-isolation RSS A/B`
- workflow run: `33614037325`
- substantive job: `100195637104` (`dual-candidate-process-isolation-rss`)
- artifact: `v030-r25-dual-candidate-process-isolation-rss-769cb54e47de454af9c5e6cf57c6d0e495878048`
- artifact id: `9840339395`
- artifact ZIP SHA-256: `78e4091e50297bd9c55056f614ad8333319f09132d4c58208e3428bad39ade9a`
- schema: `cmpct-v030-r25-dual-candidate-process-isolation-rss-v1`
- experiment valid: **true**
- release credit: **false**

The exact-head job executed the substantive fresh-process A/B, passed the frozen identity/charging
ratchet, passed `tools/check_ci_topology.py`, and uploaded the exact JSON receipt. This is not a
classifier-only success.

## Exact result

Frozen target: `resemblance_hostile_v1 / 01_shifted_versions`.

| arm | median whole-process-tree peak RSS | median parent `ru_maxrss` | median wall time | median samples |
|---|---:|---:|---:|---:|
| PrefixGraph isolated, G0–G4 in parent | **289,488 KiB** | 289,100 KiB | **62.4479 s** | 5,803 |
| PrefixGraph isolated, then G0–G4 isolated | **289,450 KiB** | 288,948 KiB | **64.8377 s** | 6,330.5 |

Frozen derived quantities:

- incremental whole-tree peak reduction: **0.0131266%**;
- absolute median peak reduction: **38 KiB**;
- wall-time ratio: **1.038269x** (**+3.8269%**);
- maximum process count at the sampled global peak: **1** in both arms;
- frozen decision: **`G04_PROCESS_LIFETIME_RETIRED_AS_PRIMARY`**.

Every row retained the same selected representation, complete archive bytes and SHA-256, strongly
verified canonical filesystem tree, format revision, and exact r24/r25 complete-product prices.
The PrefixGraph child exited before G0–G4 in both arms; the dual arm additionally routed exact canonical
G0–G4 through one disposable child and observed its exit before selection. No representation, selector,
grammar, locality/decode-unit rule, integrity/recovery condition, comparator, threshold, or production
source changed.

## Causal interpretation

The accepted predecessor remains a material positive: disposing PrefixGraph's process lifetime before
later work reduced honest whole-process-tree peak RSS from **400,958 KiB to 289,300 KiB (-27.8478%)**,
while exporting **+17.98% create-time debt**.

This experiment tests whether the remaining ~289 MiB is substantially the same kind of process-lifetime
debt in G0–G4. It is not. Adding an equivalent lifetime boundary around exact G0–G4 changes median peak
by only **38 KiB**, far below the frozen 10% retirement boundary, while making the operation slower.

The fact that the sampled global high-water occurs with only one process alive is also informative:
after PrefixGraph's proven lifetime reset, the residual peak is a **parent/product-process high-water**.
It must not be attributed to a live child merely because candidate construction previously used one.

## Scoped negative constraint

For this exact repaired Shifted target and accepted PrefixGraph-isolated topology:

1. do not add another subprocess boundary around G0–G4 as the primary RSS repair;
2. do not infer that every candidate benefits from process isolation merely because PrefixGraph does;
3. do not spend further Forge cycles proliferating process boundaries without a new phase/ownership
   result that reopens the question;
4. retain the PrefixGraph process-lifetime intervention as a reproducible rehabilitation seed, but do
   not promote it while its large create-time and portability debt remains unpaid.

## Reopening predicate

Reopen G0–G4 process isolation only if G0–G4 semantics/lifetime materially change, or a new exact
phase/heap attribution proves a G0–G4-owned allocation class large enough to explain the residual peak
and shows that a changed process boundary can actually avoid that class. Runner noise or a few MiB of
ordinary variation is not a reopening predicate.

## Forge decision and next decisive action

**Stop process-boundary proliferation and localize the residual parent high-water by exact product
phase.**

The next diagnostic should preserve the accepted PrefixGraph-isolated/G0–G4-parent architecture and
sample whole-process-tree live RSS while tagging exact parent phases: profile preparation, r24 build,
r25 build, G0–G4 build, publication, and the complete build's mandatory final verification. The global
peak's active phase signature becomes the next ownership coordinate.

A phase label is not itself a causal win. It only authorizes a narrower A/B on the phase that actually
owns the high-water. If no phase localizes consistently, move to allocation/heap ownership rather than
another scheduler permutation.
