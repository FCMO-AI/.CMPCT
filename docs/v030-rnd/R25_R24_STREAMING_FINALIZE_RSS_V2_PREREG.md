# r24 streaming-finalize RSS v2 preregistration

Status: **FROZEN BEFORE RESULT / SUPERSEDING DIAGNOSTIC / NO RELEASE CREDIT**

## Why v2 exists

The existing `benchmarks/v030_r24_streaming_finalize_rss_oracle.py` contains an embedded, older `StreamingFinalizeBuilder`. The productization implementation that the workflow separately regression-tests is `experiments/entropygraph_v030_r24_streaming_finalize.StreamingFinalizeBuilder`; it releases raw/Deflate candidate buffers inside the encoder worker and uses `MAX_IN_FLIGHT_FACTOR = 1`, while the embedded v1 oracle implementation releases those buffers only after ordered consumption and uses a factor of 2.

A v1 receipt therefore answers a legacy-prototype question. It must be preserved if it executes, but it may not be interpreted as evidence for the reusable productization implementation. V2 changes no observed threshold after a result; it freezes the semantic-owner repair before execution.

The operation-scoped r24 worker-policy repair also changed the canonical Shifted r24 byte/policy regime after historical streaming work. V2 must run on the current repaired semantics.

## Frozen question

Does the **reusable current streaming-finalize semantic owner**, substituted only for the genuine-r24 floor inside the promoted r25 product, materially reduce peak RSS while preserving exact r24 and final-product bytes and avoiding material wall-time regression?

## Frozen arms and corpus

Two fresh-process arms, AB/BA ordered for two repetitions, on exactly:

- `resemblance_hostile_v1/01_shifted_versions`
- `neutral_hostile_v1/09_ml_artifacts`

Arms:

1. `shipping`: inherited genuine-r24 construction.
2. `streaming`: the exact class object `experiments.entropygraph_v030_r24_streaming_finalize.StreamingFinalizeBuilder` under the same current release-owned r24 policy.

Both `r24` and complete `full` product operations are measured. Strong tree verification is mandatory.

## Immutable identity and accounting law

For every target, repetition and operation, shipping and streaming must have identical:

- complete archive byte count;
- physical SHA-256;
- verified logical tree SHA-256.

The semantic-owner ratchet must prove the v2 worker uses the reusable module class and records its module SHA-256 plus `SPOOL_MEMORY_BYTES = 1 MiB` and `MAX_IN_FLIGHT_FACTOR = 1`.

`ru_maxrss` fresh-process operation high-water is the diagnostic metric, with baseline-subtracted values retained only as in the predecessor instrument. No selector, archive grammar, integrity/recovery rule, locality/decode-unit bound, corpus identity, r24 policy, benchmark threshold or release state changes.

## Frozen decision bands

Promotion signal requires all of the following, unchanged from v1:

- exact archive/tree identity for every arm;
- no target complete-product wall ratio above **1.05x**;
- Shifted complete-product streaming/shipping incremental peak RSS ratio <= **0.75x**;
- Shifted r24-only streaming/shipping incremental peak RSS ratio <= **0.50x**.

Failure of any condition means **no promotion signal**. A loss is preserved as scoped negative evidence for this exact reusable implementation; thresholds, corpus, order or interpretation may not be changed after observation.

## Claim boundary

This is Forge causal/productization evidence only. A positive result authorizes evaluating the reusable streaming finalizer as an R1/R2 rehabilitation candidate and re-earning full runtime, correctness, native/platform and release authority. It does not itself grant release credit or permission to weaken the existing <=1.25x release RSS gate.

V1 and any result it produces remain immutable provenance and may not be silently relabeled as v2 evidence.
