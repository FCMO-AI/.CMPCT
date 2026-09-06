# ONE-G0.2 fused native nomination carrying cost — terminal result

Date: 2026-09-06
Experimental line: `ONE-G0.2`
Authoritative branch: `research/cmpct1`

## Mission Lock

Test whether the exact one-pass fused native nominator is economically better in elapsed time than the exact same nomination semantics implemented as selector + intermediate anchor trace + second native event-consumer pass. Keep selector-only as an explicit carrying-cost reference.

Frozen authority: `docs/one/evidence/ONE_G02_FUSED_NATIVE_NOMINATION_CARRYING_COST_PREREG_2026-09-06.md`.

## Exact CI receipt

- branch head under test: `ca2a34df33a35346c7e130b2a12defb8c1c97f37`
- result artifact name binds PR merge/source SHA: `f3114df75fef0d149daad32e074e143cc6f93201`
- workflow run: `34003649997`
- job: `101406839346` (`fused-native-nomination-carrying-cost`)
- workflow conclusion: **success**
- semantic/hostile ONE suite: **93 passed**
- artifact: `9980253533`
- artifact ZIP SHA-256: `205f97f7734e9d0eb530fc16541576adfd538092abcd89e72d405c4c86e38557`
- semantic mismatches: `[]`
- decision: **`hold_fused_nomination_state_rehabilitation`**

## Result

The one-pass fused path is consistently faster than the exact two-stage native baseline, but narrowly misses the preregistered `<=0.90x` median bar required for immediate advancement.

Across the frozen 36-row mature envelope (64 and 256 KiB relation sizes × seeds 7/29/53 × six case families):

- median fused / two-stage: **0.906228629x** (~9.38% lower elapsed);
- worst fused / two-stage row: **0.953395348x**;
- worst negative-control fused / two-stage row: **0.952208789x**;
- median fused / selector-only: **1.319874639x** (~31.99% carrying premium over the selector without nomination semantics);
- fixed research event-index reservation: **198,144 B**.

Size split:

- 64 KiB relation rows: median fused/two-stage **0.881356023x**; median fused/selector-only **1.252647546x**;
- 256 KiB relation rows: median fused/two-stage **0.938195808x**; median fused/selector-only **1.388114500x**.

Case medians fused/two-stage:

- independent random: **0.895493964x**;
- fragmented every 96: **0.902647943x**;
- fragmented every 32: **0.904848920x**;
- shift +1: **0.909128813x**;
- hostile fixed bands: **0.916028656x**;
- quarter damage: **0.922736320x**.

The fastest observed row was 64 KiB `fragmented_every32`, seed 7 at **0.866599420x**. The slowest relative row was 256 KiB `damage_quarter`, seed 29 at **0.953395348x**. No row regressed against the exact two-stage baseline.

## Causal interpretation

Fusion is doing real work: removing the redundant second sequential scan and intermediate trace improves every frozen row. The fact that the gain shrinks from a 64 KiB median of ~11.86% to a 256 KiB median of ~6.18% while selector premium grows indicates that the in-loop nomination/index/proof work increasingly dominates as inputs mature.

Therefore the next owner is not the eliminated scan. It is nomination carrying cost itself: fixed oversized index state, linear first-witness lookup over that state, exact witness/proof traffic, and irregular control in the minimizer hot loop.

## Hostile Reviewer

This is **not** a promotion. The result deliberately misses the preregistered `<=0.90x` median advancement bar, and fused nomination is still ~31.99% slower than selector-only. The fixed prototype also reserves 198,144 B although the terminal semantic envelope observed at most 64 local + 272 global live entries (8,064 B at the current 24-byte research entry layout).

A 9.38% win over an intentionally two-pass same-semantics baseline does not prove that always-hot nomination is worthwhile in the final writer. It only proves that, if this nomination policy is carried, fusion is the better execution shape.

## Decision / next falsifier

**HOLD and rehabilitate the obvious state/index debt.** Execute the already-frozen bounded demand-grown index experiment without lowering the 8,192-entry hard cap. Preserve exact nomination semantics and report actual reserved capacity/bytes. Then rerun this exact paired timing boundary with allocation/growth cost included.

If state rehabilitation materially lowers resident memory and improves or preserves elapsed economics, continue toward integrated discovery + safe-relation dispatch. If carrying premium remains large or worsens despite fixing the obvious cache/state debt, shift from always-hot nomination toward sparse/opportunity-gated nomination rather than micro-tuning the same hot loop.
