# ONE-G0.2 — native epoch-min result

**Status:** native seed passes; advances to broad structural opportunity transfer  
**Exact source:** `f959e2fcda9402494d054b7f3408c0d384099ff8`  
**Workflow:** `33947084166`  
**Job:** `101255037119`  
**Artifact:** `9963667199`  
**Artifact digest:** `sha256:07cea042641b5de44c6e28db916475eeccb75c69332c23a2392b60fa4836e592`  
**Experiment:** `ONE-G0.2`

## Referee freeze

The scalar epoch-min semantic seed had preserved all 35 hard shifted/starvation transfer rows. The native gate then required exact epoch recurrence, <=0.10x promoted selector state, <=1.10x promoted on the hard 8,193-byte row, <=0.80x promoted on every 1 MiB control, and retirement if any large row exceeded 0.90x. No semantic constant could move after result-bearing execution.

## Result

Artifact decision: `advance_epoch_min_to_broad_opportunity_transfer`.

Native/Python epoch traces, final Gear state and accounting matched exactly on every tested row. Modeled reserved state is **2,088 B**, or **0.050857x / 5.09%** of the promoted selector's 41,056 B.

| Case | Epoch / promoted | Promoted median | Epoch median | Pulses |
|---|---:|---:|---:|---:|
| random 1 MiB | **0.533596x** | 5.058 ms | 2.697 ms | 38 |
| zlib-random 1 MiB | **0.532275x** | 5.067 ms | 2.694 ms | 38 |
| repeated 64 KiB basis 1 MiB | **0.520017x** | 5.092 ms | 2.659 ms | 64 |
| shifted 512 KiB +1 | **0.457200x** | 5.055 ms | 2.314 ms | 26 |
| hard starved seed10 +1, 8,193 B | **0.719123x** | 28.993 us | 20.882 us | 2 |

Thus the scalar seed is 46.6-54.3% faster on the large controls and **28.1% faster** on the formerly pathological hard 8 KiB transfer case. This closes both exported implementation debts of the predecessor rescue family: compact exact rescue reserved 47,104 B and was 2.965x promoted on the hard row; full edge replay reduced state to 6,144 B but remained 1.886x promoted there.

## Causal interpretation

For the tested shifted/starvation family, exact sliding-window minimum maintenance is unnecessary discovery work. A single rightmost minimum over successive starvation epochs retains the useful relation while removing both sliding-queue state and historical replay.

This is a mechanism-level simplification, not threshold tuning. It preserves the same fused Gear signal and existing 4,096 starvation/span boundary but changes what historical statistic is retained by the encoder discovery path.

## Hostile review / claim boundary

The native result is not sufficient for promotion. Epoch-min deliberately nominates a different candidate subset from the mature sliding minimizer. The remaining risk is now structural coverage / Addressable Opportunity Mass: a dramatically cheaper selector is worthless if it loses the mature minimizer's rare but high-value shifted/versioned opportunities.

This evidence grants no reader/wire, stored-byte, product-speed, v0.29/v0.30 comparator, release, access, integrity, recovery or portability authority. The promoted tail-return selector remains authoritative pending broad opportunity transfer.

## Next decisive test

Run the frozen epoch-min transfer on the pre-existing mature-minimizer marginal-yield corpus. Every row where the mature minimizer contributes positive marginal opportunity beyond the fixed observer must be preserved individually; aggregate extra opportunity cannot hide a lost required row. If that passes, expand to an unfiltered shifted/versioned structural-transfer cohort before considering selector promotion.
