# ONE-G0.2 tombstone-free exact local-index A/B — terminal result

Date: 2026-09-06
Experimental line: ONE-G0.2

## Exact CI receipt

- frozen authority: `docs/one/evidence/ONE_G02_LOCAL_INDEX_BACKSHIFT_EXACT_PREREG_2026-09-06.md`
- exact source: `f5d2c4e5186f8ca9b882eafdd379ae3eb275d7dc`
- workflow run: `34010841450`
- job: `101426268997` (`exact-local-index-backshift`)
- conclusion: **success**
- semantic/hostile ONE suite: **93 passed**
- artifact: `9982406490`
- artifact ZIP SHA-256: `937ff6810e0e61cb5ff5f47fd6ecc116da36e59881f0f156f8bb62207b7aebfb`
- frozen harness decision: **`hold_local_index_backshift`**

## Result

Backward-shift deletion completely removed the catastrophic historical-deletion debt of the tombstone/rebuild design and preserved exact local-ring decisions on every measured row and on the independently constructed low-bucket collision stream.

Key aggregate facts:

- `semantic_ok = true`;
- candidate bucket probes / baseline scalar key comparisons: **0.127772x**;
- fixed state ratio: **2.333333x** (`3,584 B` vs `1,536 B`);
- worst ordinary measured row: **0.939402x** candidate/baseline;
- total backward-shift moves across final ordinary rows: **217,091**.

Size-median candidate/baseline elapsed ratios:

- 4 KiB relation: **0.700582x**;
- 8 KiB: **0.698335x**;
- 16 KiB: **0.718770x**;
- 64 KiB: **0.893016x**;
- 256 KiB: **0.932260x**.

Thus the candidate passes the probe, state, semantic and no-row-regression gates, and beats the scalar ring substantially through 64 KiB, but **fails the preregistered <=0.90x mature-size rule at 256 KiB**. The gate is not weakened after seeing the result.

The hostile same-bucket stream remained exact but is intentionally ugly: **53,568 candidate bucket probes vs 18,400 baseline comparisons**, maximum probe 65, and 16,128 backward shifts. This demonstrates that open addressing has a real collision-sensitive control envelope even after tombstones are eliminated.

## Causal interpretation

This result cleanly separates two effects:

1. Historical tombstone accumulation was the cause of the previous locator's 1.7x–3.4x mature slowdown. Removing tombstones turns that failure into a broad real speedup.
2. The remaining hash/mix/probe/deletion machinery still exports enough per-event cost that the gain decays on long streams, reaching only about 6.8% at the 256 KiB size median. The adversarial same-bucket stream also shows that exact open addressing retains irregular worst-case work.

Therefore backward-shift hashing is useful causal evidence but **not promoted** as the local lookup baseline.

## Scoped negative / reopening law

Do not add a size dispatcher merely to use this candidate on the rows where it wins. That would encode the current benchmark crossover instead of solving the carrying-cost mechanism.

Per the frozen preregistration, the next allowed family is a more regular accelerator of the authoritative ring: a compact fingerprint/SIMD-like rejection surface that makes ordinary misses cheap without hash-table insertion/deletion maintenance. Full 64-bit equality remains sole hit authority.

## Claim boundary

This is an isolated native local-index A/B. No ONE reader operation, Law, wire byte, format, density claim or v0.29/v0.30 comparison changes.
