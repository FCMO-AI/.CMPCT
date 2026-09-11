# ONE-G0.2 — Overlap-safe no-alias relation dispatch advances

**Experimental line:** `ONE-G0.2`  
**Branch:** `research/cmpct1`  
**Status:** advance implementation rehabilitation; proven-disjoint fast path plus overlap-safe fallback  
**Result-bearing source:** `1bf115d50eff2d2275b08d4bdb0ddf6a0fa69bb9`

## Mission Lock

The preceding causal A/B identified conservative C alias analysis as the dominant residual in generic arbitrary-relation discovery. A blanket `restrict` contract was not admissible because legitimate arbitrary ONE source/target relations may overlap. This frozen Builder therefore productized the win with an overflow-safe dynamic dispatch:

- if source, target and result spans are all proven disjoint, execute the exact no-alias kernel;
- otherwise execute the existing overlap-safe generic direct kernel;
- charge the dispatch check inside measured runtime;
- preserve relation semantics and accounting exactly.

The frozen advance gate required on every disjoint 32/64 KiB row: exact result structs, fast-path selection, dispatch/direct <=0.95 and dispatch/compact-half <=1.05. Hostile same-pointer, forward-overlap and backward-overlap layouts had to select the fallback and exactly match the direct kernel. Thresholds were frozen before result and were not changed.

## Exact-head receipt

- workflow: `33963017403`
- job: `101298102958`
- artifact: `9968529997`
- artifact zip SHA-256: `65655d7c055e935d93487780f235a2ea1c353e6a800ba567fdb0e8706fb654b4`
- `tests/one`: **76 passed**
- decision: **`advance_overlap_safe_noalias_dispatch`**
- all result structs: exact

## Disjoint performance

| relation | case | dispatch/direct | speedup vs direct | dispatch/half |
|---:|---|---:|---:|---:|
| 32 KiB | shift +1 | 0.8784x | 12.16% | 0.9940x |
| 32 KiB | quarter-damaged +1 | 0.8732x | 12.68% | 0.9866x |
| 32 KiB | every96 positive | 0.8845x | 11.55% | 1.0021x |
| 32 KiB | every32 false control | 0.8808x | 11.92% | 1.0086x |
| 32 KiB | independent random | 0.8714x | 12.86% | 0.9841x |
| 64 KiB | shift +1 | 0.8759x | 12.41% | 0.9871x |
| 64 KiB | quarter-damaged +1 | 0.8736x | 12.64% | 0.9891x |
| 64 KiB | every96 positive | 0.8566x | 14.34% | 0.9648x |
| 64 KiB | every32 false control | 0.8673x | 13.27% | 0.9848x |
| 64 KiB | independent random | 0.8987x | 10.13% | 0.9765x |

The checked fast path therefore recovers **10.1-14.3%** versus the alias-conservative generic direct implementation while remaining approximately **0.965-1.009x** the compact half-layout control. The safety predicate itself is included in these measurements.

## Hostile overlap correctness

All frozen overlapping layouts selected the safe fallback (`dispatch_path=0`) and matched direct-kernel accounting exactly:

- identical source/target pointer;
- target starting one byte after source;
- source starting one byte after target.

No undefined-behavior shortcut is required to obtain the speed recovery.

## Interpretation

This materially rehabilitates the arbitrary-relation writer primitive: the prior transfer cost was exported implementation debt, not an inherent cost of ONE's generalized relation semantics. The mechanism is now at the point where another isolated micro-kernel optimization would be lower value than **integrated transfer** into the fused observation/discovery path. That transfer must charge nomination, disjointness proof, fallback incidence, total writer elapsed time, memory traffic/state and false-control work; isolated kernel parity is not a product creation-speed claim.

## Claim boundary

Writer-discovery implementation evidence only. No reader-visible ONE operation changed. No stored-byte result, product creation/decode throughput result, selective-access result, v0.29/v0.30 comparison or release authority changes.
