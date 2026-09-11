# ONE-G0.2 — Direct-pointer relation A/B: carrier ABI is not the dominant residual

**Experimental line:** `ONE-G0.2`  
**Branch:** `research/cmpct1`  
**Status:** immutable causal negative / direct-pointer simplification retained as useful implementation evidence, retired as dominant residual explanation  
**Result-bearing source:** `2610b072acc2e90d16ececc2cc36b60e8848c2cc`

## Mission Lock

The already-failed arbitrary-relation transfer retained a measurable cost gap after pointer rebasing. This frozen discriminator removed carrier bounds and offset arguments while keeping the same relation bytes, proof semantics, coverage stride, displacement set and result structure. The preregistered causal gate required direct-pointer addressing to be at least **5% faster on every 32/64 KiB row**. Failure retires carrier/offset ABI overhead as the dominant remaining owner rather than tuning the threshold after result.

## Exact-head receipt

- workflow: `33962010444`
- job: `101295401899`
- artifact: `9968228221`
- artifact zip SHA-256: `88cb7246a0406157c11db41b37fb57a09befe47b203030dce4ae02af72e47c37`
- `tests/one`: **76 passed**
- decision: `carrier_api_not_dominant_residual_owner`
- all reported result structs: exact

## Result

The direct-pointer form is generally faster, so carrier/offset ABI work is real debt, but it does not satisfy the frozen all-row causal gate.

Representative direct-pointer speedups versus the rebased carrier API:

- 32 KiB clean +1: **6.94–9.10%**
- 32 KiB quarter-damaged +1: **7.66–8.76%**
- 32 KiB every96 positive: **8.28–9.21%**
- 32 KiB every32 false control: **6.35–8.45%**
- 32 KiB independent random: **8.32–8.98%**
- 64 KiB clean +1: **5.08–6.24%**
- 64 KiB quarter-damaged +1: **5.46–6.17%**
- 64 KiB every96 positive: **5.03–6.09%**
- 64 KiB every32 false control: **4.73–5.58%**
- 64 KiB independent random: **3.68–4.03%**

The decisive misses are therefore not marginal bookkeeping: the 64 KiB independent-random rows are consistently below 5%, and one 64 KiB every32 placement is also below 5%.

## Causal interpretation

Removing the carrier API recovers additional writer compute after address rebasing, especially at 32 KiB, but the residual gap cannot be attributed mainly to bounds/offset arguments. The effect also weakens with larger relations, which is more consistent with a fixed per-call/API component being amortized than with it owning the remaining per-byte gap.

The already-frozen physical spatial-locality A/B is the next discriminator. It keeps the direct-pointer function fixed and compares identical relation bytes stored adjacently versus hundreds of KiB apart. If far placement is not >=5% slower on every frozen row, physical separation is also retired as the dominant residual and the campaign should inspect compact-half versus generic-direct code generation / benchmark ABI rather than blend more optimizations into the failed transfer.

## Claim boundary

Writer-side causal compute attribution only. No ONE representation, reader-visible operation, stored-byte result, product-speed claim, v0.29/v0.30 comparison or release authority changes.
