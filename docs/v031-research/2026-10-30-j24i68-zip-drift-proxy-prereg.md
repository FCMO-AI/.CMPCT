# J24I68 — Prospective ZIP co-drift falsifier for source-identical r24 ABBA evidence
**Date:** 2026-10-30 UTC. **Status:** RESEARCH-ONLY preregistration, before J24I68 calculation/instrument. **Authority:** `FCMO-AI/.CMPCT main@80c358f8824ec1b20d349c92ed94c898090969b0`; v0.30.0/r24 published. No product or release mutation.

## Baseline / owner boundaries
The existing #835 and #837 GitHub Actions r24 A/B/B/A artifacts include source-identical baseline/candidate controls, some red and some green despite unchanged Builder/Reader/native source. The existing J24I65 detached audit authenticates eight provider ZIPs and calculates official regressions. The J24I53 #819 owner separately tested process-prefix cost; #835 owns the official performance workflow and evaluator. This experiment does **not** repeat #819 or change that gate, its thresholds, or source/evaluator semantics.

## One question / preregistered hypothesis
**Question:** Can same-corpus same-mode ZIP baseline→candidate timing drift be used as a *credible per-cell proxy* for the corresponding CMPCT drift in source-identical r24 A/A runs, thereby cheapening future attribution of false-positive release reds?

H1 (positive control-value): on **each** of the three predeclared source-identical hosted workflows, the sign of ZIP delta and CMPCT delta agrees in >=75% of cases where BOTH absolute changes exceed 1ms; within-run rank correlation across all 32 `(corpus, library|cli, create|extract)` paired deltas is >= +0.50. Do not pool differently hosted runs or pretend correlated cells are independent replicates.

H0/kill: any source-identical workflow fails **either** condition, or too few simultaneously >1ms pairs exist to identify a reliable relationship. Retire ZIP as a generic per-cell time-adjustment surrogate in this evidence family; it remains an independent execution/environment context sensor. No official red is waived.

## Frozen inputs / strongest control
Only existing original provider artifacts:
- #835 first failing ABBA: J24I65 bundle `cmpct_p835_firstfailure_12981944713.zip`;
- #835 second source-identical failing ABBA: `cmpct_source_identical_835_12986955317.zip`;
- #837 source-identical passing ABBA: `cmpct_source_identical_837_12988780098.zip`.

Do not regenerate benchmarks or reorder observations. For every 32-cell pair calculate per-side medians over the original A and B snapshots, then `delta_ms = 1000*(median(candidate-A,candidate-B)-median(base-A,base-B))`. ZIP and CMPCT are computed separately using unchanged source artifacts. Report the official >5% AND >3ms red count but do not substitute this research test for the official evaluator. Inspect per-A/per-B sign inversions separately as an anti-pooling stress test. Require all eight corpus names and all four A/B files, identical full logical corpus fingerprint within each run, exact CMPCT base/candidate archive-size parity and correct source identity from the existing provider evidence. Verify ZIP SHA from immutable provider/J24I65 manifest before scientific credit.

## Alternative explanations / loss criteria
A timing sign match can occur by chance or broad host drift without proving the same mechanism; rank correlation can be distorted by differing baseline timing scales or cross-cell dependence. ZIP and CMPCT do different work; cold/startup and cache/mode differences make per-cell extrapolation suspect. A null result only retires this narrow **diagnostic proxy**, not the ZIP competitor or official timing rule. Supplement with transparent within-run sign counts, raw four-observation effect samples, and leave-one-corpus-out checks. An inability to independently verify artifacts is infrastructure/evidence-debt, not a pass.

## Prospective decision
If H1 survives all three source-identical hosted runs and adversarial corrupted-report controls, recommend an **independent research-only** cross-engine drift instrument in future hosted comparisons, without denominator normalization or threshold adjustment. Otherwise publish a negative result linking raw provider ZIP/rows, advising future operators to diagnose CMPCT directly with fresh A/A control, source/bin custody and workload chronology rather than ZIP-drift subtraction. Never soften r24 release gates. The cheapest rung is original artifact analysis, not another expensive CI.

**Concurrency:** independent meta-measurement, not a duplicate Builder/Reader/ABI/recovery/packaging implementation; #835 and #819 maintain their owned mechanisms. No `docs/discovery/STATE.json` write (owned #574). **Disproof:** reproducibility/original SHA fails, source-identical basis false, or H1 thresholds fail. **Costs:** analysis CPU/RSS and evidence bytes only; no product performance credit.