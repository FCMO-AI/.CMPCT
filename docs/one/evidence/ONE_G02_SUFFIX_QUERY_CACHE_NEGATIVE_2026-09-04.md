# ONE-G0.2 — Suffix query cache negative: 99% fewer loads, slower elapsed

**Branch:** `research/cmpct1`  
**Exact result-bearing source:** `7b014c81f16808d6aa6ccc6f3976f3893a0390ee`  
**Workflow run:** `33942770144`  
**Result-bearing job:** `101243240135`  
**Artifact:** `9962364559`  
**Artifact ZIP SHA-256:** `0d36f0c3e433b5d35efed5990efb2cdbdc8cd4b6fab3cf6ea5cc18ed61589fd6`  
**Experimental version:** `ONE-G0.2`

## Frozen hypothesis

The promoted offset-only query path performs a suffix-offset lookup plus a retained-state indirect load for essentially every eligible query window. Because the suffix start advances monotonically within each block, a cached suffix candidate can be refreshed only when the start passes the cached rightmost argmin. The preregistered hypothesis was that this tiny event gate would remove most actual indirect loads without reproducing the control debt seen in the broader event-driven maintenance experiment.

The candidate explicitly charges **24 B** of cache state. Promotion required exact oracle equality, unchanged suffix construction/lifecycle, zero source rescans, state <=1.001x baseline, candidate suffix-value loads <=0.05x baseline on selected rows, 17 warm-started A-B-B-A rounds, every selected median <=1.03x, every large p90 <=1.05x and cross-large median <=0.95x. A large median >=1.05x triggers rejection for control debt.

## Result

**Frozen decision: `reject_suffix_query_cache_for_control_debt`.**

All **50 ONE tests passed** before the experiment. Exact Python anchor traces, final Gear state, considered positions, suffix-build lifecycle and derived-state-read count remained unchanged. Source rescans remained zero.

The load-reduction mechanism worked far beyond its frozen prerequisite:

- random 1 MiB: **1,043,398 -> 7,565 loads**, ratio **0.007250x**;
- zlib-random ~1 MiB: **1,043,723 -> 7,682**, ratio **0.007360x**;
- exact pair: **1,043,398 -> 7,552**, ratio **0.007238x**;
- shifted pair: **1,043,399 -> 7,557**, ratio **0.007243x**;
- repeated basis: **1,043,398 -> 6,811**, ratio **0.006528x**;
- hostile 16,385 B: **12,215 -> 106**, ratio **0.008678x**.

That is roughly a **99.1%–99.35% reduction** in the targeted indirect-load count. Enabled modeled state rose only from **41,056 B to 41,080 B** (`1.000585x`), exactly the charged cache debt.

Elapsed moved the wrong way:

- cross-large median candidate/baseline: **1.069687x** — about **6.97% slower**;
- random 1 MiB median **1.032389x**, p90 **1.086476x**;
- zlib-random median **1.069687x**, p90 **1.104184x**;
- exact pair median **1.072173x**, p90 **1.083528x**;
- shifted pair median **1.070889x**, p90 **1.081201x**;
- repeated basis median **1.058980x**, p90 **1.072373x**;
- hostile 16,385 B median **1.056634x**, p90 **1.072942x**.

Multiple large medians exceeded the frozen 1.05x rejection boundary.

## Causal interpretation / retirement

This is a strong negative, not an ambiguous microbenchmark. On this selector and hosted `-O3` regime, **removing >99% of regular suffix indirect loads by inserting per-window cache/event control makes the kernel materially slower**. The baseline direct indexed loads are sufficiently cache-friendly/cheap that branch/control/dependency overhead dominates their removal.

This independently reinforces the earlier event-driven dense negative: low event counts are not a performance objective when achieving them replaces regular bulk work with control-heavy state machines.

**Retire the query-cache/event-gate family under this regime.** Do not reopen it merely with a different refresh threshold, cache-hit percentage or smaller counter. Reopening requires a causally different machine-level technique that removes the regular loads without a per-window branch/dependency chain (for example demonstrated vector/load fusion or compiler-visible straight-line transformation), plus static or hardware-counter evidence supporting that cause.

The result also changes research priority: further local attempts to reduce suffix/query operation counts are now lower-value than measuring whether the existing 8 KiB-dispatched minimizer produces enough additional reusable structure per unit compute to justify its charged cost in the fused ONE observer.

No implementation is promoted and no reader, Law, wire, stored-byte, product-speed, comparator or release authority is created.
