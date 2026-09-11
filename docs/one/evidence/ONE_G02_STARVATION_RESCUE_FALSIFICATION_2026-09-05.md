# ONE-G0.2 — Starvation-rescue falsification and residual-owner narrowing

**Evidence source:** `892858871717e0dae590134ce7c2b24e57a6cd0f`  
**Branch:** `research/cmpct1`  
**Experimental version:** `ONE-G0.2`  
**Authority:** encoder-discovery research evidence only. This document grants no reader/wire, stored-byte, product-speed, comparator, release, or v0.29/v0.30 superiority authority.

## Mission lock

Test whether rolling-minimum compute can be made sparse enough to retain its unique shift/starvation opportunity while materially reducing encoder cost, without changing the ONE reader ontology or the exact rightmost-minimum semantics used by the current discovery candidate.

Three independently result-bearing exact-head experiments close two tempting escape routes and narrow the remaining causal owner:

1. sparse-anchor starvation as a cheap activation signal;
2. cold/late minimizer rescue after that signal fires;
3. halving suffix-derived state reads inside the promoted selector path.

All three preserve the ONE reader boundary. All exact-head workflows reran `tests/one`: **50 passed**.

## Referee hypotheses and disproofs

### H1 — sparse-anchor starvation can gate expensive minimizer work cheaply

Frozen hypothesis from `one_g02_starvation_byte_history_native_ab`: the byte-history near-miss is mainly interpreter/control overhead, so a compiled starvation gate should materially beat the promoted tail-return selector baseline on both 1 MiB entropy-dense controls while preserving gated recurrence semantics.

Frozen disproof: native recurrence mismatch, or median gate/baseline `>= 0.90` on either entropy-dense 1 MiB control.

### H2 — once starvation is visible, a cold late-rescue minimizer preserves the full-minimizer marginal opportunity

Frozen transfer disproof: any hard-rescue transfer row loses full-minimizer opportunity. Zero hard-rescue rows would be inconclusive rather than a win.

### H3 — redundant suffix-derived reads are a material owner of the remaining promoted-selector runtime

Frozen rolling-min fusion promotion boundary: cross-large median candidate/baseline `<= 0.97`, derived-state-read ratio `<= 0.55`, large p90 `<= 1.05`, selected-case median `<= 1.03`. Rejection required a large median `>= 1.05`.

## Result A — starvation is observable, but not selective enough to justify the proposed gate

Exact-head workflow `33944834503`, job `101248937513`, artifact `9963012658` (`sha256:e07dfae6c4e6bb62c5c2a4a740ebff4117e98370561e0ddde12152343f2dfd65`).

The 4,096-position sparse-anchor-gap signal does identify the known shifted-starvation adversary strongly: `12,227 / 16,322` considered positions are active (**74.91%**) and the full minimizer owns **8,192 B** of marginal reuse opportunity there.

But the same signal also activates on ordinary negative controls: random 1 MiB spends **25,314 positions / 2.414%** active and zlib-random spends **22,757 / 2.170%** active. Repeated 64 KiB bases spend **157,958 / 15.065%** active despite having zero minimizer marginal opportunity over the cheap selector. Thus a gap signal is informative, but it does not by itself identify where expensive rescue has positive marginal information yield.

## Result B — compiled starvation gating is slower and materially larger in state

Exact-head workflow `33944834699`, job `101248936508`, artifact `9962996442` (`sha256:5b7823b3a137ae1f38baf858de2dc01fdafb3b2501dabc56ffa2b1535aba5cbd`). Trace equality held on every row.

The candidate reserved **71,680 B** versus **41,056 B** for the promoted baseline: **+30,624 B / +74.59%** retained state.

Median candidate/baseline elapsed ratios:

- random 1 MiB: **1.053261** — 5.33% slower;
- zlib-random 1 MiB: **1.070877** — 7.09% slower;
- repeated 64 KiB basis 1 MiB: **1.060176** — 6.02% slower;
- shifted 512 KiB + 1 insertion: **0.987956** — only 1.20% faster;
- starved seed-10 shifted 8 KiB + 1: **3.765841** — 276.58% slower.

Both entropy-dense controls violate the preregistered `<0.90` requirement by a wide margin. The interpreter-overhead rehabilitation hypothesis is therefore falsified.

**Decision:** `reject_compiled_starvation_gate_as_compute_rehabilitation`.

## Result C — cold late rescue destroys the opportunity it was meant to preserve

Exact-head workflow `33944834569`, job `101248937361`, artifact `9962991438` (`sha256:4937389beb5d01a0704ba58699e5e1ac6489a45867036ea646354e22f7bc9274`).

Transfer selected the first 12 independently generated 4,096-byte bases in seeds `[0,4095]` with zero qualifying sparse Gear anchors, then tested insertion lengths 1, 8 and 31. There were **35 hard-rescue rows**. The late-rescue candidate lost the full-minimizer opportunity in **all 35 / 35**.

Typical hard-rescue rows had **4,096 B** of full-minimizer reuse opportunity, **0 B** from late rescue, and **0 emitted rescue minimizers**. The active fraction was already about **49.2–49.4%**, so this is not a tiny-duty-cycle corner where activation merely arrived a few instructions too late.

**Decision:** `reject_late_rescue_transfer`.

**Causal interpretation:** the information needed to nominate the useful rightmost minimum is historical. Starting exact minimizer state only after observing starvation discards precisely the preceding window state required to recover the shift-stable candidate. A cold rescue cannot reconstruct that lost state without replay, additional history, or an equivalent continuously maintained summary; each would export the supposedly avoided compute/memory cost elsewhere.

## Result D — halving suffix-derived reads does not materially reduce elapsed time

Exact-head workflow `33944834658`, job `101248937635`, artifact `9963020033` (`sha256:03b3a1079ded8815556141bc8c71bd9e4751583c1600d4031f6069cbcf92d5bf`).

The rolling suffix-min candidate reduces derived-state reads on the large path from roughly **2.088–2.090 million** to **1.044–1.046 million** per ~1 MiB input: ratio **0.500244**, while preserving **41,056 B** reserved state and zero source-byte rescans.

Yet cross-large median elapsed is **0.996057x** the baseline — only about **0.39% faster**, far short of the frozen `<=0.97` promotion threshold. Representative medians:

- random 1 MiB: `0.992086x`;
- zlib-random 1 MiB: `0.997099x`;
- exact 512 KiB pair: `0.996057x`;
- shifted pair +1: `1.004779x`;
- repeated 64 KiB basis 1 MiB: `0.994404x`.

The hostile shifted-starvation row improved to `0.981540x`, but the 4,160-byte enablement boundary regressed to `1.064439x`.

**Decision:** `offset_rollmin_inconclusive`; do not promote.

**Causal interpretation:** retained-state load count is not the dominant residual owner. A 49.98% reduction in those reads produced only ~0.39% cross-large elapsed benefit. The remaining cost is therefore more likely in the serial arithmetic/control dependency chain that constructs and consumes exact rightmost-minimum state, not raw suffix memory traffic by itself.

## Hostile-review synthesis

The three tempting local stories are now ruled out in the tested regimes:

1. **"Run the minimizer only when sparse Gear starves."** Rejected: the gate itself is slower than the promoted baseline on entropy-dense controls and carries 74.59% more state.
2. **"Start the minimizer late once starvation is known."** Rejected: 35/35 independently generated hard-rescue rows lose the full-minimizer opportunity.
3. **"The remaining cost is mostly redundant suffix loads."** Unsupported: halving those reads buys only ~0.39% cross-large median elapsed.

This strengthens, rather than weakens, the earlier co-dominant suffix+selection diagnosis: the next Builder should target the **serial dependency structure** shared by suffix construction and exact rightmost-minimum selection, not threshold tuning, ring micro-optimizations, cold rescue, or another state-read-only edit.

## Next decisive Builder hypothesis

Test a **hierarchical/block summary of the same exact rightmost-minimum recurrence** that is maintained during the fused Gear observation pass and allows selection to resolve from a small fixed hierarchy rather than a byte-position serial walk.

Required invariants:

- exact emitted rightmost-minimum trace equality against the independent oracle;
- unchanged inherited Gear identity and 4,096-position semantics;
- no source-byte rescan and no reader-side discovery;
- preserve the promoted 8 KiB dispatch boundary unless separately superseded by evidence;
- explicitly charge all block-summary state and memory traffic;
- include random, zlib-random, repeated, shifted, the 4,160-byte boundary, and starvation-hostile cases;
- preregister a material elapsed threshold before result-bearing execution; do not promote a read-count win without elapsed/compute benefit.

**Disproof direction:** if a fixed hierarchy preserves the exact trace but cannot materially reduce cross-large elapsed without >5% hostile/boundary regression or material state growth, retire hierarchical summary as a primary owner attack and move to a different recurrence organization rather than increasing hierarchy depth until green.

## Reopening predicates

- Starvation gating may reopen only if a new causal signal predicts **marginal Law opportunity**, not merely sparse-anchor gaps, and its always-on observation cost is included.
- Late rescue may reopen only with a continuously maintained sufficient statistic or bounded replay whose total compute/state/read cost is charged and whose transfer preserves full-minimizer opportunity.
- Derived-state-load optimization may reopen only as part of a broader recurrence/layout change that demonstrates material elapsed gain; isolated load-count reductions are no longer enough.
