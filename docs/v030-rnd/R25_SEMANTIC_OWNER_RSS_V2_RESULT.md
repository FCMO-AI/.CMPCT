# r25 exact semantic-owner RSS v2 result

Status: **accepted diagnostic causal evidence / Forge-Custody / no release credit**.

This record preserves the superseding candidate-family RSS result after v1 was found to compare shipping against the wrong isolated PrefixGraph implementation. V2 invokes and asserts the exact private canonical semantic owners used by shipping before measurement.

It changes no selector, admission policy, candidate scheduling, archive grammar, integrity, recovery, locality/decode-unit bound, benchmark threshold, or release state.

## Authority

- exact source: `60543bcbb1779ecbfe1e1807b725709f8ec3d57e`;
- workflow: `.github/workflows/v030-r25-semantic-owner-rss-v2.yml`;
- workflow run: `33593983348`;
- substantive job: `100133653322` (`semantic-owner-rss-v2`);
- artifact id: `9832934858`;
- artifact: `v030-r25-semantic-owner-rss-v2-60543bcbb1779ecbfe1e1807b725709f8ec3d57e`;
- artifact digest: `sha256:48503c074a73d81b68595b23040152383f82c541685cde86609b1d28f1188d6e`;
- schema: `cmpct-v030-r25-semantic-owner-rss-v2`;
- experiment valid: `true`;
- worker failures: `0`;
- release credit: `false`.

The substantive fresh-process measurement completed successfully. The exact-owner ratchet passed and the artifact was uploaded. A classifier-only success is not part of this authority.

## Exact semantic-owner proof

Every eligible worker receipt asserted:

- `canonical.RC.PG is PROFILE_ISOLATION.PG`;
- `canonical.RC.G04 is PROFILE_ISOLATION.SHARED`;
- `canonical.RC.READER is PROFILE_ISOLATION.POLICY`;
- PrefixGraph module: `experiments._v030_canonical_prefixgraph`;
- G0-G4 module: `experiments._v030_canonical_shared_portfolio`;
- reader/policy module: `experiments._v030_canonical_release_reader_policy`.

Each candidate ran in its own fresh process. Strong verification remained mandatory and outside the candidate pack timer. Total fresh-process peak RSS is the causal ownership boundary; baseline-subtracted `ru_maxrss` remains diagnostic only.

## Result

### Shifted versions

`resemblance_hostile_v1 / 01_shifted_versions`

| Exact arm | Median total peak RSS | Median diagnostic incremental RSS | Median wall time | Complete bytes |
|---|---:|---:|---:|---:|
| shipping r25 product | **400,000 KiB** | 275,836 KiB | 60.273 s | 1,700,604 B |
| exact canonical G0-G4 | **180,654 KiB** | 56,490 KiB | 55.257 s | 1,723,056 B |
| exact canonical PrefixGraph | **200,670 KiB** | 76,506 KiB | 10.209 s | 1,700,242 B |

Ratios versus shipping total fresh-process peak RSS:

- G0-G4: **0.451635x**;
- PrefixGraph: **0.501675x**.

Repetition peaks:

- shipping: 399,780 / 400,220 KiB;
- G0-G4: 170,624 / 190,684 KiB;
- PrefixGraph: 200,800 / 200,540 KiB.

The shipping selector chose `prefixgraph` in both repetitions. Exact isolated PrefixGraph produced 1,700,242 B while the complete shipping product was 1,700,604 B; the shipping artifact therefore carries product framing/accounting beyond the isolated research candidate, as expected.

**Decision-changing causal result:** neither exact candidate family alone reproduces the ~400 MiB shipping peak. The exact PrefixGraph semantic owner peaks at only about half of shipping, and exact G0-G4 lower still. V1's 430,496 KiB PrefixGraph result was caused by measuring the parallel research wrapper rather than the exact canonical semantic owner and must not be used for shipping attribution.

The next shifted-memory hypothesis moves one level upward: **cross-candidate/product lifetime overlap**. Shipping's product construction owns a peak substantially above either exact candidate in isolation. The next diagnostic must distinguish concurrent candidate overlap from other product-level retention while preserving exact candidate bytes and the selected shipping artifact.

### ML artifacts

`neutral_hostile_v1 / 09_ml_artifacts`

| Exact arm | Median total peak RSS | Median diagnostic incremental RSS | Median wall time | Complete bytes |
|---|---:|---:|---:|---:|
| shipping r25 product | **190,376 KiB** | 66,212 KiB | 38.080 s | 13,674,821 B |
| exact canonical G0-G4 | **124,164 KiB** | 0 KiB | 37.454 s | 13,674,596 B |
| exact canonical PrefixGraph | structurally ineligible (`file-size-ceiling`) | — | — | — |

G0-G4 is **0.652204x** the shipping total fresh-process peak. PrefixGraph is not a candidate on this workload.

**Causal result:** isolated exact G0-G4 also does not reproduce ML shipping peak memory. Because PrefixGraph is structurally ineligible, ML's remaining ~66 MiB shipping-vs-isolated total-peak gap belongs to product composition/lifetime/other r25 work, not PrefixGraph.

## Scoped negative constraints

1. Do not treat exact PrefixGraph internals as the primary shifted RSS owner merely because PrefixGraph is the selected representation. V2 falsifies that family-level attribution under equivalent exact semantic ownership.
2. Do not treat exact G0-G4 alone as the primary shifted or ML RSS owner under this tested fresh-process regime.
3. Do not resurrect v1's parallel-wrapper PrefixGraph peak as shipping evidence; v2 exists specifically because that implementation identity was wrong.
4. Do not infer additive allocation ownership from baseline-subtracted `ru_maxrss`.
5. Do not use this evidence for release credit. Full-product runtime/memory/selective-read authority remains governed by `docs/V030_RELEASE_LOCK.json`.

## Strongest surviving self-critique

The v2 result identifies the unresolved ownership boundary as product composition/lifetime, but it does not yet prove **concurrency** is the cause. Shipping may retain common source/profile/tournament state, temporary candidate outputs, verification structures, canonical wrapping state, or multiple candidate lifetimes simultaneously. The release-candidate implementation currently has an overlapping candidate-build path when PrefixGraph is eligible, making concurrency a strong low-level hypothesis, but code visibility is not causal proof.

A correct next experiment must therefore compare exact shipping-equivalent candidate composition under concurrent versus serialized scheduling while proving selected bytes/tree remain identical. It should not change the production scheduler first and then infer causality from an improved number.

## Forge decision

**Advance from candidate-family attribution to product-composition lifetime attribution.**

For shifted versions, run an exact semantic-owner concurrency/lifetime A/B in fresh processes:

- arm A: inherited shipping-equivalent concurrent candidate construction;
- arm B: the same exact candidates serialized, with identical admission/selection/verification and exact selected output bytes/tree required;
- charge total fresh-process peak RSS and wall time;
- no selector/admission/grammar/locality/recovery change;
- no release credit.

If serialization materially collapses the shipping RSS peak while preserving identical selected bytes/tree, concurrency/lifetime overlap becomes an R1/R2 systems intervention candidate. If not, preserve the negative result and isolate the next product-level retained-state boundary instead of modifying the representations.

For ML, where PrefixGraph is ineligible, use a separate product-composition/lifetime causal lane; a shifted concurrency result must not be generalized to ML without evidence.
