# ONE-G0.2 — Arbitrary-relation address rebasing: partial win, insufficient rehabilitation

**Experimental line:** `ONE-G0.2`  
**Branch:** `research/cmpct1`  
**Status:** immutable causal negative / pointer rebasing retained as useful implementation fact but retired as sufficient rehabilitation  
**Result-bearing source:** `c9cccfadbda57bf330fc28682e7c81fc36f2cf47`

## Exact-head receipts

### Rebased arbitrary-relation transfer

- workflow: `33961845219`
- job: `101294966416`
- artifact: `9968191417`
- artifact zip SHA-256: `c27b19d982ff08b740598c7c73f61cd29b6efaab544ac4a1a5bab9ede3d2768c`
- `tests/one`: **76 passed**
- decision: `retire_rebased_arbitrary_relation_transfer`

### Direct old-vs-rebased addressing A/B

- workflow: `33961845310`
- job: `101294965417`
- artifact: `9968185322`
- artifact zip SHA-256: `a63a1c58db8153dc7c50387e1e13977fd3c61165aa10b0a1375f0993eaa32a73`
- `tests/one`: **76 passed**
- decision: `address_rebasing_not_sufficient_cost_owner`

## What rebasing fixed

The first arbitrary-offset kernel had transferred admission semantics exactly but cost roughly 1.16–1.28x the compact half-layout control on 32/64 KiB relations. The Builder validated carrier bounds once, rebased source/target pointers once, and kept hot coordinates relation-local.

A paired A/B on **identical carrier bytes** proves that this was a real cost owner rather than benchmark noise. Full result structs remained exact. Representative rebasing speedups versus the old arbitrary kernel were:

- 32 KiB clean +1: **10.18–10.60%**;
- 32 KiB every96 positive: **10.20–10.95%**;
- 32 KiB every32 false control: **10.69–10.97%**;
- 64 KiB clean +1: **12.37–12.59%**;
- 64 KiB quarter-damaged +1: **11.16–12.17%**;
- 64 KiB every96 positive: **12.82–13.05%**;
- 64 KiB every32 false control: **12.36–13.29%**;
- 64 KiB independent random: **10.47–10.88%**.

The frozen causal gate nevertheless required >=8% speedup on **every** row. It failed because some 32 KiB rows were below that bound, including quarter-damaged placement 0 (**6.73%**) and random placements 0/1 (**7.67% / 7.82%**). Hence pointer rebasing is material but not a complete causal explanation.

## Why the absolute transfer still failed

Even after rebasing, every result/proof signature still matched the compact half-layout control, but the frozen <=1.10x absolute cost ceiling was not met on the 32/64 KiB grid.

Representative rebased / compact-half ratios:

- 32 KiB clean +1: **1.145–1.149x**;
- 32 KiB quarter-damaged +1: **1.156–1.164x**;
- 32 KiB random: **1.214–1.222x**;
- 64 KiB clean +1: **1.117–1.139x**;
- 64 KiB quarter-damaged +1: **1.121–1.144x**;
- 64 KiB every32 false: **1.114–1.138x**;
- 64 KiB random: **1.116–1.130x**.

One 32 KiB every96 timing sample was an obvious large outlier at 1.647x on one placement, but the experiment does not discard it after result; the frozen all-row gate remains failed regardless.

## Causal interpretation

Two statements survive simultaneously:

1. **Absolute offsets in hot loops were real compute debt.** Removing them often recovered about a tenth of elapsed time.
2. **They were not the full residual.** The arbitrary relation path remains measurably more expensive than the compact half-layout path after semantic code shape is substantially aligned.

The remaining hypotheses must therefore be separated experimentally rather than blended into another optimization patch:

- per-call carrier bounds / richer ABI overhead;
- physical source/target stream placement and cache/TLB/prefetch behavior;
- compiler code-generation differences between the compact half-layout and generic relation APIs;
- measurement effects specific to very small microsecond-scale kernels.

Two superseding frozen diagnostics were opened:

- a direct-pointer A/B removes carrier bounds/offset arguments while touching the **same physical relation bytes**;
- a spatial-locality A/B keeps the direct-pointer function fixed and compares adjacent versus widely separated copies of the **same relation** inside one carrier.

These diagnostics may attribute the residual. They may not change proof semantics, coverage stride, displacement set, corpus classification, or the already-failed 1.10x transfer gate.

## Claim boundary

Writer-discovery compute attribution only. No ONE representation, reader-visible operation, stored-byte result, product-speed claim, v0.29/v0.30 comparison, or release authority changes.
