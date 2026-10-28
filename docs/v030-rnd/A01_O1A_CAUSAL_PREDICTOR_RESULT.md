# A01 O1a causal-predictor result

Status: **raw decision `PREDICTOR_FALSE_NEGATIVE`; post-run referee classification `INSTRUMENT_SPEC_CONTRADICTION`; no causal-predictor promotion**.

The raw result is preserved exactly. The predictor is **not** rescued or promoted. However, the raw decision cannot be cleanly interpreted as a scientific false negative because the frozen preregistration contains an internal contradiction exposed by the hostile two-cluster row.

## Immutable receipt

- source PR head used by merge test: `ac8c61feaaad49772b82ca554b8b46e277312acc`;
- merge-test SHA: `b2fde27c94e16bc997ec38c07e54b7cdcb80224a`;
- workflow run: `34973766226`;
- job: `104396210340`;
- artifact: `10398711838`, `v030-foundry-a01-research-b2fde27c94e16bc997ec38c07e54b7cdcb80224a`;
- artifact ZIP SHA-256: `9bbeb326eeefa7a5728db719f940508c42b2a7bc49f2fa35e0fcc8462f182a27`;
- O1a raw JSON SHA-256: `2fc109d20f8816dd31d2c4ef1e058767f2756f7b6b77dfb6c6b95cd144ea0335`;
- corpus fingerprint: `0f0fe29e5b409b9a804bc627b95c36762d2140e34f083528d3f0a4c96e01bcd2`;
- raw decision: **`PREDICTOR_FALSE_NEGATIVE`**;
- exact roundtrip: all six families.

The same run reproduced the accepted O0 receipt byte-for-byte at the JSON level: O0 result SHA-256 remained `c01647717574a2a9045d3c317b55a083a02708cbaa60198c79076a203f2f625b` and corpus fingerprint remained `2682a21c86bf9abfa7521075dd45b3afa17d7370a5c3b6848630bd4e40396ec0`.

## Direct measurements

| Family | Predictor advantage | Prediction | Best real | Best two real | Synthetic | Synthetic vs real | Frozen material flag |
|---|---:|---|---:|---:|---:|---:|---|
| independent bursts | 28.85% | LATENT | 178,836 B | 302,933 B | **159,787 B** | **-19,049 B / -10.65%** | true |
| independent scatter | 22.50% | LATENT | 192,209 B | 314,583 B | **168,932 B** | **-23,277 B / -12.11%** | true |
| shared correlated patch | 15.38% | LATENT | 157,746 B | 285,080 B | **147,970 B** | **-9,776 B / -6.20%** | true |
| near medoid | 0.00% | OBSERVED/MULTIMODAL | 167,328 B | 293,294 B | 164,914 B | -2,414 B / -1.44% | false |
| two cluster | 3.70% | OBSERVED/MULTIMODAL | 342,593 B | **302,143 B** | 336,541 B | -6,052 B / -1.77% vs real; **+34,398 B vs two-root** | true |
| independent random | 0.96% | OBSERVED/MULTIMODAL | 1,049,027 B | 1,049,046 B | 1,159,656 B | +110,629 B / +10.55% | false |

## What the data actually say

The sampled consensus-advantage statistic separated the intended unimodal latent families from both hostile random and the multimodal two-cluster family in the expected direction. It also correctly declined the near-medoid case under the frozen 8% threshold. That is interesting **research evidence**, but it is not promoted because the preregistered decision law fired.

The two-cluster row is the key: one synthetic root is 6,052 B smaller than the best *single* observed root, so the frozen `ACTUAL_LATENT_MATERIAL` flag becomes true. Yet the best two-observed-root control is 34,398 B smaller than the synthetic root, exactly matching the preregistered causal expectation that this family should be treated as multimodal/observed-root territory. The predictor returned `PREDICT_OBSERVED_OR_MULTIMODAL` — also the expected causal answer.

## Referee finding: preregistration contradiction

The frozen preregistration simultaneously required:

1. every family whose synthetic root beats `BEST_REAL_ROOT` by >=1% and >=4 KiB to be predicted `PREDICT_LATENT`; and
2. the `two_cluster` family to prefer `BEST_TWO_REAL_ROOTS` over `SYNTHETIC_ROOT` and be treated as multimodal.

Those conditions conflict whenever a two-cluster family lands in the perfectly plausible ordering:

`BEST_TWO_REAL_ROOTS < SYNTHETIC_ROOT < BEST_REAL_ROOT`.

That exact ordering occurred: 302,143 B < 336,541 B < 342,593 B.

Therefore the raw `PREDICTOR_FALSE_NEGATIVE` is preserved, but the run is **not accepted as evidence that the predictor missed latent-root opportunity**. The predictor actually rejected a case where the stronger multi-root control wins. The error is in the frozen outcome label/decision composition, not in reconstruction or byte accounting.

This classification is not a threshold rescue: no threshold, predictor output, family, byte result or raw decision is changed.

## Durable negative / narrowing

O1a still does **not** pass. A result-bearing experiment with an internally contradictory decision law cannot promote a causal predictor even if individual rows look favorable.

The next superseding freeze must define opportunity relative to the **strongest relevant ownership control**, not merely best single observed root. A clean label is likely to require synthetic root to beat both the best single-root and best multi-root observed representation by the materiality rule before calling the family latent-positive. Multimodal cases where two observed roots win must be explicit negatives.

That superseding test must use fresh generator-distinct families/seeds; the six O1a families are now evidence and cannot be reused as unseen validation.

## Strongest self-critique

The contradiction should have been caught before execution. The preregistration correctly described the two-cluster causal intent in prose but encoded `ACTUAL_LATENT_MATERIAL` against only `BEST_REAL_ROOT`, then universally quantified that label in the false-negative rule. This is exactly the kind of evaluator composition error CMPCT's anti-Goodhart doctrine is meant to expose.

The correct response is not to reinterpret the raw decision as success. It is to preserve the run, mark the instrument specification defective for causal adjudication, and make the next freeze stronger.