# ONE-G0.2 exact local-index hash A/B — terminal result

Date: 2026-09-06
Experimental line: ONE-G0.2
Activation T0: `2026-09-06T04:07:17Z`
Authority: `research/cmpct1`

## Frozen authorities

- preregistration: `docs/one/evidence/ONE_G02_LOCAL_INDEX_HASH_EXACT_PREREG_2026-09-06.md`
- hostile amendment: `docs/one/evidence/ONE_G02_LOCAL_INDEX_HASH_EXACT_HOSTILE_AMENDMENT_2026-09-06.md`
- exact source: `0cb00d4e23cc9d831d28258a745e3a44666608c9`
- workflow run: `34008825904`
- job: `101420881402` (`exact-local-index-hash`)
- artifact: `9981831540`
- artifact ZIP SHA-256: `eb7a014065988a97bff4f285ba063412a8ee074a67c5d99ea4bd5f0818bb7a49`
- semantic/hostile ONE suite: **93 passed**

## Result

The saturation-repaired 128-bucket open-address locator preserved exact local-ring semantics, but failed the frozen performance/work gates decisively.

Exact summary emitted by the result-bearing harness:

- `semantic_ok = true`;
- decision emitted by the frozen harness: `hold_exact_local_index_hash`;
- aggregate candidate probes / baseline key comparisons: **1.047093x**, versus the preregistered requirement `<= 0.30x`;
- maximum state ratio: **2.333333x** (within the `<=2.5x` state gate);
- total charged candidate rebuilds across final rows: **610**;
- worst row elapsed ratio: **3.438718x**.

Size-median candidate/baseline elapsed ratios were:

- 4 KiB relation: **0.840312x**;
- 8 KiB relation: **1.016863x**;
- 16 KiB relation: **1.724327x**;
- 64 KiB relation: **2.271484x**;
- 256 KiB relation: **2.269985x**.

The independently constructed low-bucket collision stream also remained semantically exact but exposed the same control-cost problem: **45,760 candidate probes vs 18,400 baseline comparisons**, with maximum probe length 65.

## Causal interpretation

The small-size win confirms the original attribution was not imaginary: replacing a linear 64-entry search can reduce work while the locator still contains abundant never-used buckets. The design fails as the stream ages because deletion leaves tombstones. Misses and removals increasingly traverse long clusters; full-saturation repair then rebuilds the table, but that repair occurs only after the accumulated control cost has already become large. At mature sizes the locator spends roughly as many or more bucket probes as the linear ring while also paying hashing, irregular branches, tombstone handling, removals and rebuilds.

Therefore the useful hypothesis is narrower than “hash the local ring.” The rejected shape is specifically:

> **linear-probed open addressing + tombstone deletion + saturation-triggered rebuild**.

Do not rehabilitate this result by tuning a tombstone percentage, size threshold or rebuild cadence. Those would move the crossover rather than remove the mechanism that caused it.

## Next falsifiable hypothesis

A causally different exact locator can remove tombstone accumulation **by construction**: preserve the same 128-bucket/64-live-entry map, but use backward-shift deletion so every lookup retains a valid empty sentinel and no rebuild policy exists.

That candidate must keep the same exact ring semantics and the same frozen work/elapsed/state gates. If it still fails, the project should stop elaborating open-address locators and move to a more regular approach such as SIMD/fingerprint filtering of the authoritative ring.

## Claim boundary

This is native causal evidence for the isolated local lookup policy only. It changes no ONE reader operation, Law, wire byte or format. It does not establish total fused-observer speed, writer speed, density or comparator superiority.
