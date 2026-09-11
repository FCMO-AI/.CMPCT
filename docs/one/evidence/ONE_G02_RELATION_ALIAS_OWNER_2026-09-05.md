# ONE-G0.2 — Alias-analysis A/B: dominant generic-relation compute owner identified

**Experimental line:** `ONE-G0.2`  
**Branch:** `research/cmpct1`  
**Status:** advance causal finding; no-alias code shape is proven headroom, blanket `restrict` remains unsafe until overlap is handled explicitly  
**Result-bearing source:** `6559b5d38ae6256f91f543fc7a51c2d378a802d6`

## Mission Lock

Native-internal timing had already retired Python/ctypes as the dominant residual while proving a real compiled-C gap between the direct generic-relation kernel and the compact half-layout control. The next frozen hypothesis was that conservative alias analysis owns that gap because the generic interface exposes two source pointers plus a written result object.

The A/B changed only the compile-time non-alias contract on benchmark inputs that are physically disjoint by construction. Promotion required, on **every** frozen 32/64 KiB row:

1. exact result structs;
2. `restrict / direct <= 0.95` (>=5% recovery); and
3. `restrict / compact-half <= 1.05`.

Thresholds were frozen before result.

## Exact-head receipt

- workflow: `33962880057`
- job: `101297733090`
- artifact: `9968497857`
- artifact zip SHA-256: `4516de60f084f136edfd37ba3f7d7fc3978f4813baa95160410e68de01ea25c9`
- `tests/one`: **76 passed**
- decision: **`alias_analysis_is_dominant_residual_owner`**
- all result structs: exact

## Result

The hypothesis passed every row by a wide margin.

| relation | case | restrict/direct | speedup vs direct | restrict/half |
|---:|---|---:|---:|---:|
| 32 KiB | shift +1 | 0.8484x | 15.16% | 0.8849x |
| 32 KiB | quarter-damaged +1 | 0.8583x | 14.17% | 0.8878x |
| 32 KiB | every96 positive | 0.8252x | 17.48% | 0.9356x |
| 32 KiB | every32 false control | 0.8543x | 14.57% | 0.8941x |
| 32 KiB | independent random | 0.8819x | 11.81% | 0.8876x |
| 64 KiB | shift +1 | 0.8350x | 16.50% | 0.8981x |
| 64 KiB | quarter-damaged +1 | 0.8629x | 13.71% | 0.8820x |
| 64 KiB | every96 positive | 0.8498x | 15.02% | 0.8908x |
| 64 KiB | every32 false control | 0.8487x | 15.13% | 0.8971x |
| 64 KiB | independent random | 0.9224x | 7.76% | 0.9272x |

The no-alias generic relation kernel is not merely inside the old <=1.10x transfer ceiling; it is **6.4-11.8% faster than the compact-half control** on all frozen rows in this native paired instrument.

## Causal interpretation

The old generic-relation penalty was not an inherent cost of representing arbitrary ONE relations. It was largely compiler conservatism caused by a weaker pointer contract. This is exactly the kind of exported implementation debt Breakthrough Rehabilitation asks us to attack rather than tuning away the generalized mechanism.

## Hard correctness boundary

This result is **not permission to apply `restrict` universally**. The arbitrary ONE relation ontology may validly describe source/target ranges that overlap. Passing overlapping ranges to a C function whose corresponding pointer accesses violate `restrict` association rules would invoke undefined behavior and is unacceptable.

The production-shaped continuation is therefore a **proven-disjoint fast path** plus the existing overlap-safe generic fallback. The admission check must include source/target range non-overlap and result-storage non-overlap, be overflow-safe, and preserve exact fallback behavior for hostile overlapping layouts. Its own runtime cost must be charged.

## Claim boundary

Writer-discovery compute headroom only. No reader-visible ONE operation changed; no stored bytes, creation-product runtime, decode runtime, access amplification, v0.29/v0.30 comparison or release authority changed.
