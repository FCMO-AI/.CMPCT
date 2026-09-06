# ONE-G0.2 compact fingerprint ring-view A/B — terminal result

Date: 2026-09-06
Experimental line: ONE-G0.2

## Exact CI receipt

- preregistration: `docs/one/evidence/ONE_G02_LOCAL_INDEX_FINGERPRINT_VIEW_PREREG_2026-09-06.md`
- hostile amendment: `docs/one/evidence/ONE_G02_LOCAL_INDEX_FINGERPRINT_VIEW_HOSTILE_AMENDMENT_2026-09-06.md`
- exact source: `64d2a596fdda8b2250949dd2ed2a7f438a31ad90`
- workflow run: `34011110481`
- job: `101427162919` (`compact-fingerprint-ring-view`)
- conclusion: **success**
- semantic/hostile ONE suite: **93 passed**
- artifact: `9982540204`
- artifact ZIP SHA-256: `916f4e6b56329128cb095ea07532eb19b4829586fa4ba060270e2e43f9486bb6`
- frozen decision: **`advance_local_index_fingerprint_view`**

## Result

The duplicated 8-bit fingerprint view preserved every authoritative local-ring decision while removing nearly all ordinary full-key comparisons and remaining cheap across the complete frozen size ladder.

Aggregate facts:

- `semantic_ok = true`;
- candidate full-key checks / baseline scalar full-key comparisons: **0.0039503989x**;
- fixed state ratio: **1.083333x** (`1,664 B` vs `1,536 B`);
- worst ordinary measured row: **0.860584x**;
- no ordinary row regressed.

Size-median candidate/baseline elapsed ratios:

- 4 KiB relation: **0.838414x**;
- 8 KiB: **0.815066x**;
- 16 KiB: **0.768663x**;
- 64 KiB: **0.766898x**;
- 256 KiB: **0.757139x**.

The mature-size medians therefore improve by roughly **23.1%–24.3%** while preserving the same Gear scan and lookup cadence.

## True hit-rich hostile amendment

Hostile review correctly observed before result authority that the byte-generated case named `cyclic_local_hits` did not actually create repeated accumulated Gear-state keys. The repaired source added a native key stream with 64 distinct warm keys followed by **4,096 guaranteed hits**.

Result:

- baseline hits = candidate hits = **4,096**;
- baseline full-key checks: **135,136**;
- candidate full-key checks: **4,096**;
- baseline elapsed: **128,554 ns** median;
- candidate elapsed: **30,775 ns** median;
- candidate/baseline: **0.239396x**;
- exact prior-position decision checksum and live-entry parity preserved.

Thus the accelerator is not merely a miss optimization; it also accelerates genuine local hits strongly when fingerprints are selective.

## Same-fingerprint hostile case

All keys in the hostile key stream deliberately shared the same 8-bit fingerprint. The candidate degraded exactly to full authoritative checking rather than producing false authority:

- baseline full-key checks: **18,400**;
- candidate full-key checks: **18,400**;
- exact hit count, decision checksum and live-entry parity preserved.

This establishes the intended worst collision shape: the fingerprint view can lose its filtering advantage, but it does not amplify full-key work beyond the underlying ring or create false hits.

## Causal interpretation

The local-ring owner did not need a second search data structure. The expensive common case was repeatedly asking 64 full-width keys whether they matched. A 128-byte mirrored rejection surface makes that question a dense byte-search operation and reserves full 64-bit equality for the rare fingerprint matches. Eviction remains the existing authoritative-ring update plus two byte stores.

Compared with the preceding experiments:

- tombstone/rebuild hashing failed because historical deletion control overwhelmed lookup savings;
- backward-shift hashing proved those tombstones were causal, but residual hashing/deletion machinery diluted the mature gain;
- the fingerprint view removes both maintenance families and produces a larger, stable speedup with only **128 B** extra fixed state.

## Decision and next gate

**ADVANCE `compact fingerprint ring view` to fused native nomination-consumer integration.**

This is not yet the promoted fused-observer baseline. The next A/B must integrate the view into the real native nomination consumer, preserve nomination/output semantics exactly, charge observation + minimizer + local/global nomination bookkeeping together, and demonstrate that the isolated ~23–24% mature local-lookup improvement remains material end-to-end.

No size dispatch is authorized or needed by this result.

## Claim boundary

This is native isolated local-lookup evidence only. No ONE reader operation, Law, canonical wire byte, format, density, selective-access, integrity, v0.29 or deferred-v0.30 authority changes.
