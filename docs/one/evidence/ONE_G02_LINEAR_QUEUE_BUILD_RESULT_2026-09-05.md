# ONE-G0.2 — Linear activation-time queue construction result

**Exact source:** `6372700db47d672207b00fb903c420e095207485`  
**Branch:** `research/cmpct1`  
**Experimental version:** `ONE-G0.2`  
**Workflow:** `33945774199`  
**Result-bearing job:** `101251461190`  
**Artifact:** `9963284615`  
**Artifact ZIP SHA-256:** `5e2a138606df154e4c81926353592070951f1305ab550c6e3e721ba2a2827da5`  
**Authority:** encoder-discovery A/B only. No stored-byte, reader, product-speed, v0.29/v0.30 comparator, or release authority.

## Referee freeze

Prior exact-head decomposition isolated activation-time monotonic-queue construction as the primary ordinary-path exported cost of the bounded byte-history rescue: +21.1/+21.4% over replay-only on the two entropy controls, versus +7.1/+7.3% for later maintenance.

During activation build, queue `head == 0` and no expiry can occur. Therefore the queue cannot wrap while the historical 4,096-position window is being materialized. The Builder replaced generic ring modulo addressing only during that construction phase with a linear rightmost-min monotonic-stack build. Normal ring expiry/update semantics remain in force after activation.

Frozen promotion required:

- exact trace and accounting equality on every row;
- candidate/generic median `<= 0.95` on both entropy-dense ~1 MiB controls;
- no tested-case median `> 1.05`;
- identical reserved state.

Before the A/B, exact-head `tests/one` reran: **50 passed**.

## Result

Decision: **`advance_linear_queue_build_for_integration_review`**.

| case | linear / generic elapsed | p90 | speed change | state |
|---|---:|---:|---:|---:|
| random 1 MiB | **0.900870x** | 0.903085x | **−9.91%** | 71,680 B = 71,680 B |
| zlib-random ~1 MiB | **0.899256x** | 0.903072x | **−10.07%** | 71,680 B = 71,680 B |
| repeated 64 KiB basis 1 MiB | **0.814263x** | 0.873665x | **−18.57%** | 71,680 B = 71,680 B |
| shifted 512 KiB pair +1 | **0.922514x** | 0.925592x | **−7.75%** | 71,680 B = 71,680 B |
| random 4,160 B boundary | **1.004842x** | 1.009129x | +0.48% | 71,680 B = 71,680 B |
| hard starved 8,193 B | **0.833090x** | 0.966524x | **−16.69%** | 71,680 B = 71,680 B |

Every row had exact nomination-trace and accounting equality. Replayed-history byte counts were unchanged: 77,824 B on each entropy control, 131,072 B repeated, 49,152 B shifted and 4,096 B on the hard-rescue case. Peak queue entry counts were also unchanged (15–22 on active large/hard cases).

## Causal interpretation

This result validates the preceding cost-owner chain rather than merely finding a lucky local optimization. The queue construction phase was identified first; only then was its unnecessary modulo-ring organization removed. The ~10% entropy-control gain is materially larger than the earlier ring-address micro-optimization on the always-on selector, because this edit attacks a phase where all 4,096 historical entries are constructed at once and where wrap semantics are provably absent.

The result does **not** make the full deferred-rescue path product-ready. It still reserves 71,680 B in the current instrument versus 41,056 B for the promoted tail-return selector, and the full rescue still carries replay and post-activation queue-maintenance cost. The 4,160-byte boundary remains a reason to retain the existing size dispatch; no lowering of that boundary is authorized.

## Hostile review

Strongest surviving criticism: the candidate removes address arithmetic but leaves a 4,096-entry queue allocation even though observed peak live queue counts in this corpus are only 15–22. The low observed occupancy is suggestive but cannot justify capping capacity: an adversarial monotone signal can require far more live entries. State reduction therefore needs a proof-equivalent representation, not an empirical queue-size cap.

A safe next Builder is to preserve full 4,096 capacity while compacting queue position metadata. Because a live entry can be at most 4,095 positions old, an exact modulo position with a modulus larger than twice the maximum age can disambiguate expiry without storing a 64-bit absolute position. A `uint16_t` modulo-8192 position therefore has enough information for exact age/expiry within a 4,096-span queue. If validated against exact traces, this would reduce queue entry storage from 16 B to 10 B conceptually (or two structure-of-array fields: 8 B values + 2 B positions), cutting modeled queue storage from 65,536 B to 40,960 B before history/Gear state. Any implementation must charge alignment and actual allocation bytes rather than claiming the conceptual figure.

The next experiment must preregister exact expiry/tie equivalence, actual reserved-state accounting, elapsed behavior and hostile monotone/duplicate-value cases. State compaction alone is not promotion; it must preserve or improve elapsed compute as well.
