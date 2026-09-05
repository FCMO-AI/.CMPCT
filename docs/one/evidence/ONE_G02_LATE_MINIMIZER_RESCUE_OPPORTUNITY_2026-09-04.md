# ONE-G0.2 — late minimizer rescue opportunity falsifier

**Date:** 2026-09-04 America/Mexico_City  
**Experimental version:** `ONE-G0.2`  
**Result-bearing source:** `4498568e21908cf337d4625048743772566e52c5`  
**Workflow:** `33943844440`  
**Job:** `101246239490`  
**Artifact:** `9962688489`  
**Artifact digest:** `sha256:6ca856e27054b5da34ac17646e01f2bc68e4b19d1256854c394fc7112e414519`

## Mission lock

The full 4,096-position rolling minimizer preserves shift-invariant exact-reuse opportunity but exports material maintenance cost on ordinary random/already-compressed inputs. Sparse Gear is much cheaper, but deterministic long anchor starvation can make it blind to a useful shifted relation.

The tested rehabilitation is deliberately content-derived and untuned: keep the expensive minimizer cold until the sparse Gear stream has gone exactly `MINIMIZER_SPAN == 4096` eligible positions without an anchor, then cold-start minimizer rescue. The reader remains unchanged; all survivors still compile to generic exact-reuse Law.

**Hypothesis:** cold late activation preserves every full-minimizer opportunity uniquely absent from the fixed/sparse cheap observers while making minimizer maintenance sparse on ordinary negatives.

**Disproof:** any hard-rescue case loses full-minimizer opportunity. The 4,096-position threshold is frozen from the existing minimizer span and may not be moved after seeing this result.

## Exact result

The result-bearing workflow passed the complete `tests/one` semantic boundary and the falsifier.

Decision emitted by the immutable artifact:

`late_rescue_survives_hard_opportunity_falsifier`

`hard_rescue_loss_cases == []`.

The decisive hostile row was `starved_shifted_basis_8k_insert1`:

- input: **16,385 B**;
- fixed reuse opportunity: **0 B**;
- sparse Gear reuse opportunity: **0 B**;
- full minimizer reuse opportunity: **8,192 B**;
- cold late-rescue reuse opportunity: **8,192 B**;
- opportunity delta late vs full: **0 B**;
- rescue-active positions: **12,226 / 16,385 = 74.6170%**;
- emitted rescue minimizers: **5**;
- sparse anchors: **0**;
- exact verification reads: **128 B**;
- extension proof reads: **16,256 B**.

Thus the simple cold-start gate did not destroy the exact marginal relation that motivated minimizer retention.

## Negative-path activation

The gate also separated the two principal no-opportunity controls without workload labels:

| case | input | full-minimizer opportunity | late-rescue opportunity | rescue-active fraction | emitted rescue minimizers |
| --- | ---: | ---: | ---: | ---: | ---: |
| `random_1mib` | 1,048,576 B | 0 B | 0 B | **2.4141%** | 1 |
| `zlib_random_payload` | 1,048,902 B | 0 B | 0 B | **2.1696%** | 1 |
| `zeros_1mib` | 1,048,576 B | 0 B | 0 B | **0%** | 0 |

This is the mechanism-level headroom: expensive rolling-min maintenance need not run across roughly 97.6–97.8% of the two ordinary entropy-dense negative controls merely to preserve the currently observed starvation rescue.

## Other useful rows

The gate correctly stayed inactive on several short/friendly cases already covered by cheap observers. On the 1 MiB `repeat_basis_64k_1mib` row it activated for **15.0640%** of positions but did not create marginal opportunity beyond the cheap path. That is remaining false-positive compute and is part of the next timing/cost falsifier rather than being hidden.

The deterministic starved repeat without insertion activated for **74.6155%** of positions and still reconstructed the same **8,192 B** opportunity, but fixed aligned reuse already covered that row. This shows the gate is a starvation detector, not yet an optimal benefit predictor.

## Hostile review / claim boundary

This result proves **opportunity preservation**, not speed superiority. Rescue-active fraction is only a proxy for avoided minimizer work; sparse Gear scanning, gate bookkeeping, cold-start transitions, rescue state and exact proof traffic still cost CPU and memory. The next experiment must charge them directly in a repeated paired A/B against the full promoted minimizer path.

Only one current frozen row requires hard rescue beyond both cheap observers, so the structural-transfer evidence is promising but narrow. Do not generalize from this matrix to arbitrary shifted/versioned data without generator-distinct transfer.

No stored-byte, native throughput, product-speed, v0.29/v0.30 superiority, reader-format or release authority is created here.

## Decision

**Advance** the fixed-threshold late-rescue family to a paired elapsed/state/source-traffic falsifier. Do not tune the starvation threshold. Reject or rehabilitate the integration if its charged elapsed/state cost fails to materially preserve the theoretical avoided-work advantage.
