# ONE-G0.2 — starvation-gated minimizer paired timing

**Date:** 2026-09-04 America/Mexico_City  
**Experimental version:** `ONE-G0.2`  
**Result-bearing source:** `ff06f9e908e5f9dd57b6c2813a879e42a5d01a24`  
**Workflow:** `33943929056`  
**Job:** `101246460961`  
**Artifact:** `9962721689`  
**Artifact digest:** `sha256:a759d2336b83d7a928cbc01ffc37bd17b321c4577e3f9d7caadff8f132b523d5`

## Question

The preceding opportunity falsifier showed that a cold minimizer activated only after a frozen 4,096-position sparse-anchor starvation gap retains the current hard-rescue relation. This paired A/B charges actual hosted reference execution against the full always-maintained minimizer.

The corpus and gate threshold were frozen before timing. Nine rounds alternate A/B order. Garbage collection is disabled during each timed call. Every row retains raw samples in the immutable artifact.

**Hypothesis:** sparse-anchor starvation gating materially lowers elapsed discovery cost on entropy-dense no-opportunity controls while preserving the hard-rescue relation.

**Disproof:** any hard-rescue opportunity loss or absence of a material elapsed advantage on the random/compressed controls rejects performance advancement of this integration shape.

## Result

Decision: `advance_late_rescue_compute_rehabilitation`.

No hard-rescue opportunity loss occurred. Median of the two principal negative-control elapsed ratios was **0.450582x** full minimizer.

| case | full median | gated median | gated/full | opportunity full -> gated | rescue-active fraction |
| --- | ---: | ---: | ---: | ---: | ---: |
| random 1 MiB | 708.543 ms | 315.943 ms | **0.445905x** | 0 -> 0 B | 2.4141% |
| zlib-random payload | 691.006 ms | 314.586 ms | **0.455258x** | 0 -> 0 B | 2.1696% |
| repeated 64 KiB basis, 1 MiB | 686.718 ms | 360.984 ms | **0.525665x** | 983,040 -> 983,040 B | 15.0640% |
| shifted 512 KiB pair + 1 B | 689.905 ms | 309.446 ms | **0.448534x** | 524,288 -> 524,288 B | 1.3742% |
| starved shifted 8 KiB basis + 1 B | 10.455 ms | 9.091 ms | **0.869520x** | 8,192 -> 8,192 B | 74.6170% |

The random row improved by about **55.41%**, the zlib-random row by **54.47%**, and the ordinary shifted-version row by **55.15%** in this hosted Python implementation. Even the intentionally worst starvation row, where rescue is active for almost three quarters of the input, improved by about **13.05%** while retaining all 8,192 B of unique opportunity.

## Causal interpretation

The result is consistent with the intended mechanism rather than a threshold trick. Sparse Gear and a cheap gap counter remain active; the dense rolling-min state is built only after observed anchor starvation. On ordinary entropy-dense controls, that state exists for only about 2.2–2.4% of input positions, and paired elapsed falls by more than half. The reader is unaffected: the encoder still emits only generic exact-reuse Law after byte proof.

The repeated-64-KiB row is an important criticism rather than a hidden loss. The gate activates for **15.06%** of positions even though cheap observers already have the complete 983,040 B relationship. Yet total elapsed still falls to 0.526x full minimizer. This means the current gate is useful but is a starvation detector, not an optimal benefit predictor.

## Hostile review / claim boundary

This is hosted Python causal evidence only. It does not establish native throughput, product creation speed, stored-byte benefit, memory-bandwidth behavior, selective-read benefit, v0.29/v0.30 superiority or release authority.

The current frozen matrix contains only one row where the full minimizer is strictly necessary beyond both fixed and sparse observers. That makes transfer the strongest surviving objection. A mechanism that only rescues one constructed seed is not enough to justify permanent compute or implementation surface.

The next decisive experiment is therefore generator-distinct starvation transfer with the same 4,096-position gate. It must select hostile inputs by the pre-existing starvation property, not by whether the gated algorithm wins, and it must preserve losses without retuning the gate.

## Decision

**Advance the starvation-gated minimizer family as a compute-rehabilitation candidate, not yet as the normal fused-observer baseline.** Preserve the full minimizer as the opportunity oracle while generator-distinct transfer and broader opportunity-value accounting remain open.
