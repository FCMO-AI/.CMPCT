# r25 generic discovery-source R3 Builder result

Status: **ACCEPTED FOR FORGE PRODUCTIZATION / ZERO RELEASE CREDIT BY ITSELF**

Frozen preregistration: `docs/v030-rnd/R25_DISCOVERY_SOURCE_GENERIC_R3_BUILDER_PREREG.md`  
Instrument: `benchmarks/v030_discovery_r3_product_ab.py`  
Workflow run: `33816700715`  
Job: `100850323670`  
Source commit: `f8a76ebcf2ad6f92e795cc1568887e3c7a7975fa`  
Artifact: `v030-discovery-r3-product-ab-f8a76ebcf2ad6f92e795cc1568887e3c7a7975fa` / ID `9918364981`  
Artifact ZIP SHA-256: `0c425d7cc2b50ec580f864c2ee2f48dcce9f390c30c9d5fb7c330f2f8cb55c1c`

## Frozen question

Can the child-scoped discovery neutralization be promoted generically in the canonical shared portfolio without workload-name routing, while preserving exact bytes, selection, locality and runtime non-regression?

## Accepted result

The frozen Builder decision law returned:

**`PROMOTE_R3_PRODUCT_NEUTRALIZATION`**

Product A/B totals:

- workloads: **15 / 15**;
- byte-identical rows: **15 / 15**;
- runtime targets: **3 / 3**;
- material runtime regressions: **0**;
- runtime regression rows: **none**;
- maximum selected-member read amplification: **7.684560232628689x**, within the frozen <=8x limit.

The three preregistered runtime targets were:

| Target | Baseline wall median | Candidate wall median | Delta | Ratio | Material regression? |
|---|---:|---:|---:|---:|---|
| `neutral_hostile_v1/05_logs_and_telemetry` | 93.796135454 s | 94.411500504 s | +0.615365050 s | 1.006560665x | no |
| `neutral_hostile_v1/09_ml_artifacts` | 52.803891836 s | 49.575938378 s | -3.227953458 s | 0.938869024x | no |
| `resemblance_hostile_v1/01_shifted_versions` | 56.817210451 s | 47.701592140 s | -9.115618311 s | 0.839562375x | no |

The attempt-5 child medians moved in the same qualitative direction on the two material speed wins:

- ML: 28.517880315 s -> 26.574027484 s, ratio **0.931837401x**;
- Shifted: 50.685542032 s -> 39.440707595 s, ratio **0.778145128x**.

Logs was effectively flat at the child boundary: 63.151850728 s -> 63.282953389 s, ratio **1.002075991x**.

## Decision and scope

The generic neutralization clears its frozen R3 Builder gate. This authorizes productization of the generic child-scoped intervention without workload-name routing. It does **not** grant v0.30 release authority, does not substitute for fresh-process release-performance evidence, and does not relax any complete-product, competitor, recovery, native, platform or strict-lock requirement.

The strongest surviving self-critique is timing scope: this A/B uses the preregistered same-runner/same-process measurement boundary rather than fresh-process release timing. Its legitimate conclusion is therefore causal/productization authorization and demonstrated absence of a material regression under the frozen Builder law, not a standalone global speed headline.

## Custody note: workflow topology failure

The result-bearing experiment and frozen decision-law assertion completed successfully before a later workflow-hygiene step failed because `.github/workflows/v030-discovery-r3-product-ab.yml` invoked nonexistent `tools/ci_topology_selfcheck.py`. The exact receipt was still uploaded successfully. This infrastructure failure does not alter the scientific/productization verdict above, but the workflow must not be represented as globally green and the missing topology guard must be repaired separately before treating the workflow surface as healthy.

## Forge transition

1. Preserve this receipt unchanged as the accepted R3 Builder result.
2. Productize the generic neutralization at the lowest sufficient intervention level, preserving exact output identity and implicit-v4's proven product bytes.
3. Re-run the exact affected correctness/runtime/locality/product authority on the resulting fingerprint.
4. Treat any later exact-head regression as productization debt; do not rewrite this frozen result or weaken its timing/identity law.
