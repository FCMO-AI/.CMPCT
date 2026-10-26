# O188b — post-result hostile order/phase controls (prospective addendum)

Date: 2026-10-26 UTC. **Recorded after O188 original outcomes, BEFORE these new independent hostile controls execute.** Not a retroactive addition to original O188 prospective trace set. Exact branch source at addendum start: O188 result `e2d6d40d8561119b44c9a66e26f4efd14c498a78`. Baseline owners, release and physical format unchanged.

## New decision-changing question
Does the guarded 48/16 policy have a broadly useful adaptive property or is the O188 gain merely an accident of repeated forward access order? A stronger LRU control must win when working set fits, and no plausible universal claim should be inferred from one adversarial forward scan.

## Frozen independent adversarial controls / predictions
- **H1 Reverse:** 96 distinct 1MiB keys forward exactly once, then the SAME objects read in reverse order exactly once. Prediction: ordinary 64MiB LRU now gets **64 second-pass hits** (the 64 objects retained from the end of pass1); both 64MiB fixed-pin and guarded can also get hits. This narrows O175's unqualified "96 objects cause all warm misses" reading to *direction-dependent* thrash.
- **H2 Fit-phase migration:** warm initial 96 one-MiB A-keys in two ascending passes, then switch permanently to **48 disjoint 1MiB B-keys for five passes**. Prediction: LRU adapts after the first B pass (>=48 hits in B2); fixed pin remains stale (B2=0); guarded spends additional B-phase misses until its no-protected-hit reset and is strictly worse than LRU on an early B pass. If guarded immediately matches LRU, its adaptive phase-shift debt is smaller than hypothesized.
- **H3 Same-fit:** 64 keys each 1MiB over four full passes. Prediction: LRU wins every warm access; guarded and fixed-pin should match on this benign control. If guard loses here, reject its simple correctness thesis.

No algorithm may see phase labels, future requests or key identity patterns beyond stable equality and byte sizes. The capacity remains 64MiB and entry cap 32768. Evaluate all three actual methods from O188 `research/o188_cache_admission_oracle.py` unchanged and include no-cache negative control. Use the same schema, output all phases, assert capacity and exact hit accounting, retain raw results. The upper bound 64 second-pass reverse hits is mathematical for this uniform case.

## Kill/narrow law
If H2 shows guarded loses substantial repeated reads versus LRU before relearning a 48MiB fitted B working set, **do not recommend direct guarded Reader implementation** merely from O188 forward scan; require a genuinely improved admission/eviction architecture or prove the tradeoff acceptable with source-authenticated physical Reader measurements. H1 reverse control should bound any categorical LRU scan-thrash story. Neither control earns product/RSS/CPU credit. No threshold or evaluator changes after outcomes.
