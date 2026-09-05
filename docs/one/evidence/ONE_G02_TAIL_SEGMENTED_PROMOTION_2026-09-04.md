# ONE-G0.2 — Tail-aware segmented minimizer promotion receipt

**Status:** exact-head result-bearing evidence  
**Source:** `c40fdb518ba256a44fe0fdbf986e8bdcde0f900a`  
**Workflow:** `33938347273`  
**Job:** `101230624486` (`semantic-evidence`)  
**Artifact:** `9960981282`, `one-genesis-c40fdb518ba256a44fe0fdbf986e8bdcde0f900a`  
**Artifact digest:** `sha256:5add89250184eadb1ead3e62a9a598025709c195088e9b7a3f4043e4ef193bb6`  
**Instrument:** `benchmarks/one/one_g02_minimizer_tail_promotion_ab.py`  
**Schema:** `cmpct-one-g02-minimizer-tail-promotion-ab-v1`

## Mission Lock

The earlier four-segment prefix/suffix maintenance candidate was correctly rejected because its just-enabled 4,160-byte case violated the frozen no-regression law. A later causal A/B established that provably dead EOF suffix construction materially owned that boundary debt. This superseding experiment therefore changed only that causally identified maintenance debt and re-applied the original promotion bar; it did not relax selector semantics, Gear identity, proof semantics, reader representation, or benchmark cases.

Frozen promotion law before result-bearing execution:

- exact emitted anchor-position trace, final Gear state and considered-position count equal the independent Python oracle on every case;
- tail-aware median <= `0.70 * masked` on every large case (at least 30% faster);
- tail-aware median <= `1.10 * masked` on every tested case;
- modeled reserved discovery state including the shared Gear table <= `0.85 * masked`;
- zero source-byte rescans.

Any violation rejected promotion. No threshold was mutable after execution.

## Exact result

`decision = promote_tail_aware_segmented_maintenance`

All 50 ONE semantic/hostile tests passed before the benchmark. Every benchmark row matched the independent oracle trace exactly and performed zero source-byte rescans.

| Case | masked deque | tail segmented | tail / masked | modeled state |
| --- | ---: | ---: | ---: | ---: |
| below enablement 4,159 B | 5.198 us | 5.268 us | **1.0135x** | 0 B |
| at enablement 4,160 B | 12.198 us | 11.467 us | **0.9401x** | 51,296 B |
| random 1 MiB | 8.746 ms | 4.749 ms | **0.5430x** | 51,296 B |
| zlib-random ~1 MiB | 8.876 ms | 4.787 ms | **0.5393x** | 51,296 B |
| exact pair 512 KiB + 512 KiB | 8.859 ms | 4.757 ms | **0.5370x** | 51,296 B |
| shifted pair +1 B insertion | 8.698 ms | 4.759 ms | **0.5472x** | 51,296 B |
| repeated 64 KiB basis, 1 MiB | 8.377 ms | 4.736 ms | **0.5654x** | 51,296 B |
| shifted-starvation hostile 16,385 B | 71.648 us | 66.380 us | **0.9265x** | 51,296 B |

Masked-deque modeled state is 67,584 B. The tail-aware candidate is therefore **0.7590x / 75.90%** of masked state whenever enabled, comfortably inside the frozen 85% ceiling.

The 4,160-byte row built only the one suffix block that can ever be queried and skipped three provably dead suffix blocks. Large rows likewise skipped the three dead EOF suffix blocks while preserving exact traces.

## Interpretation

This result rehabilitates **one encoder-side implementation of the same single rolling-minimum nomination law**. It does not create a second reader mechanism: surviving nominations still compile to generic exact reuse Laws in ONE. The reader performs no discovery.

The important causal chain is preserved rather than rewritten:

1. the original block candidate exposed a large mature-input gain but lost at startup and was rejected;
2. four-way segmentation reduced state and preserved the mature gain but still failed its frozen startup rule;
3. the tail A/B demonstrated that provably dead EOF suffix construction materially owned the just-enabled debt;
4. the causally repaired implementation then passed the original all-case speed/state law without threshold relaxation.

That is sufficient to promote tail-aware segmented maintenance as the current **encoder-discovery maintenance baseline** for the rightmost-minimum selector.

## Non-claims and surviving debt

This is not a stored-byte, wire, reader, product-speed, v0.29, v0.30 or full CMPCT1 superiority claim. The full Genesis comparator gate remains due on/after 2026-09-11.

The surviving compute debt is still material. This selector remains a multi-millisecond-per-MiB discovery microkernel before exact proof, Law selection, emission, wire cost, or reader work. The prior same-family residual probe showed dense segmented maintenance far above the Gear-only recurrence, so promotion against masked deque is not permission to stop optimizing marginal information yield.

The next causal target is derived suffix traffic. Dense segmented maintenance materializes one suffix-minimum entry per derived state even though the suffix-minimum function changes only at strict record minima. A separately preregistered record-minimum/change-point A/B may test whether preserving only those change points removes material write traffic while retaining exact semantics and bounded worst-case state. That follow-up must earn its own result; it is not implied by this receipt.
