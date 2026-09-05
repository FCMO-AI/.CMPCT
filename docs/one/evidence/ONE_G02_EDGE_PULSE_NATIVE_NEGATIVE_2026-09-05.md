# ONE-G0.2 — native edge-pulse full-replay negative

**Status:** native full-replay edge-pulse scheduling shape retired  
**Exact source:** `6eef08f26a589afd6e0a6a459f2fdc47f03fd1c9`  
**Workflow:** `33946672711`  
**Job:** `101253917158`  
**Artifact:** `9963542123`  
**Artifact digest:** `sha256:8e530f3151e4abee21abe54d14c99b0628e8faa2dedbab6ff411849c56d30896`  
**Experiment:** `ONE-G0.2`

## Referee freeze

The semantic edge-pulse seed preserved 35/35 generator-distinct hard opportunities using two bounded replays. Native promotion was deliberately stricter: exact pulse recurrence, state <=0.20x promoted, material large-path speed, and closure of the localized 8,193-byte debt to <=1.20x promoted and <=0.65x complete compact rescue.

## Result

Artifact decision: `retire_native_edge_pulse_scheduling_shape`.

Exact native/Python pulse recurrence equality held on every row. Reserved state fell to **6,144 B**, only **0.149649x / 14.96%** of the promoted 41,056-byte selector state and 13.04% of the complete compact rescue's 47,104 B.

Large-input medians were strong:

| Case | Edge / promoted | Edge / compact | Pulses | Replayed bytes |
|---|---:|---:|---:|---:|
| random 1 MiB | **0.912129x** | 0.880537x | 38 | 155,648 |
| zlib-random 1 MiB | **0.911854x** | 0.876243x | 38 | 155,648 |
| repeated 64 KiB basis 1 MiB | **0.970360x** | 1.075654x | 64 | 262,144 |
| shifted 512 KiB +1 | **0.883081x** | 0.900840x | 24 | 98,304 |

So event-edge replay can be both much smaller in state and materially faster than the promoted continuous selector on large ordinary/shifted controls.

The decisive hard row failed the frozen closure gate:

- input: **8,193 B**;
- pulses: **2**;
- replayed history: **8,192 B**;
- edge/promoted median: **1.885985x** (required <=1.20x);
- edge/compact median: **0.737425x** (required <=0.65x).

Although this improves sharply over the complete compact rescue's earlier 2.965x promoted ratio, it remains an unacceptable small-input creation-cost debt under the frozen gate.

## Scoped negative constraint

**Retire full-span replay at each edge as the small-case scheduling shape.** Do not reopen it by moving the 4,096 starvation/span constants or by relaxing the small-row gate.

The result does **not** retire historical edge querying itself. It localizes the remaining bill to reconstructing all 4,096 Gear states per edge. The accepted reopening direction is a continuously maintained bounded sufficient statistic that answers the same exact rightmost-min query without full-span replay, with its always-on update cost and retained state charged.

A natural next Builder follows the existing ONE semantics rather than introducing a tuned parameter: use the already-canonical `WINDOW == 64` as a block granularity. Maintain rightmost minima for completed 64-position blocks plus enough boundary history/checkpoints to resolve the two partial blocks of an arbitrary 4,096-position query exactly. An edge query then inspects ~63 block summaries plus at most two 64-position boundaries instead of replaying all 4,096 positions.

## Claim boundary

This is native encoder-discovery negative evidence only. It creates no stored-byte, reader, product, comparator, release, access, recovery, integrity or portability authority. The earlier 35/35 semantic transfer remains valid evidence that edge queries can preserve the tested hard opportunity; only this full-replay implementation shape is retired.
