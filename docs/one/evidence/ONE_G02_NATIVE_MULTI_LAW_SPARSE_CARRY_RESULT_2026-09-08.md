# ONE-G0.2 sparse native multi-Law carrying cost — exact result

**Date:** 2026-09-08  
**Decision:** `HOLD_NATIVE_MULTI_LAW_SPARSE_CARRY`  
**Admissible source:** `72854ebc77dc97f9762a9e823bb524d3e7b0d7b5`  
**Workflow run:** `34298376955`  
**Job:** `102299835204`  
**Artifact:** `10084049934`  
**Artifact digest:** `sha256:1b2c6b482db8901876feeaba7705abda4ad2aeae57b386be4a80af022553bdc7`

## Result

The stride-16 rehabilitation preserved the promoted fused-gate semantics, including six generator-distinct 1 MiB transfer positives, but did not rehabilitate carrying cost.

Across all 30 frozen rows:

- semantic decisions equal the independent full Python oracle on every row;
- common run/reuse state equals the native baseline on every row;
- source scan remains exactly `1.0x` input;
- median candidate/baseline wall ratio: **1.515289x**;
- median candidate/baseline CPU ratio: **1.514758x**.

Across the 1 MiB rows:

- median wall ratio: **1.551746x**;
- median CPU ratio: **1.550924x**;
- worst wall ratio: **1.715767x**;
- worst CPU ratio: **1.715719x**.

Representative 1 MiB rows:

| family | candidate / baseline wall | candidate MiB/s |
|---|---:|---:|
| long_runs | 1.4195x | 253.2 |
| exact_repeat | 1.5521x | 344.3 |
| add8_ramp | 1.7158x | 371.9 |
| xor_chain | 1.7152x | 373.6 |
| mixed_structured | 1.5096x | 313.8 |
| random | 1.2765x | 210.9 |
| compressed_like | 1.2735x | 211.0 |
| false_pattern | 1.2609x | 213.9 |

Transfer rows remained semantically green: all three independent add8 ramps retained add8 nomination and all three independent XOR chains retained XOR nomination. Their wall ratios ranged from roughly **1.55–1.71x**, so the failure cannot be blamed on the original synthetic seeds alone.

## Causal interpretation

Fixed-stride sampling is insufficient. Relative to the full per-byte carrying experiment (`HOLD_NATIVE_MULTI_LAW_CARRY`, median ~1.599x), stride-16 sampling improves the median only to ~1.515x. Most of the unwanted marginal cost therefore survives even after removing 15/16 relation histogram updates.

That strongly argues against continuing a stride-tuning sequence. Do **not** try stride 32/64 after seeing this result merely to cross a threshold. The next relation-discovery experiment must change the causal mechanism: e.g. trigger relation statistics only inside blocks nominated by substantially cheaper structural evidence, or compute relation summaries with a genuinely vectorized/bulk pass whose memory traffic and CPU are charged explicitly.

The full run/reuse observer remains useful and the promoted Python multi-Law substrate remains evidence that add8/XOR cues can be selective. What failed is carrying those cues continuously in this scalar per-position native loop.

## Pre-result invalidation retained

Source `6212fa48dea72373551bddb7252d1905d157aa94` remains inadmissible. Its original source-to-source transformation was a no-op against the formatted parent C source and would have benchmarked the full-signal candidate under a sparse label. The repaired descendant hard-failed unless the sparse transform was present before compiling and timing. No scientific threshold, matrix row, sample stride, or interpretation rule changed during that repair.

## Stop condition

Stop fixed-stride relation-statistic micro-tuning. Preserve this negative and move to opportunity-triggered or bulk/vectorized relation evidence under a new preregistration. Exact downstream Law proof remains mandatory; nomination is never semantic authority.
