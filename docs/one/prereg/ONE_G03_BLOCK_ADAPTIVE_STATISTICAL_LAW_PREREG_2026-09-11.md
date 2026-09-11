# ONE-G0.3 block-adaptive Statistical-Law diagnostic — preregistration

**Date:** 2026-09-11
**Status:** frozen diagnostic design; no product/candidate promotion authority
**Parent evidence:** `docs/one/evidence/ONE_G03_STATISTICAL_LAW_OPPORTUNITY_RESULT_2026-09-11.md`

## Mission Lock / Referee

The first G0.3 information-opportunity diagnostic found large empirical previous-byte predictability on the exact Genesis trees while incompressible controls stayed negative. That result used final workload counts, so it does not establish that ONE can realize the information in one pass without storing a large learned model or destroying selective access.

This experiment asks the narrower causal question: **does most of the signal survive under a reader-mirrorable online model whose dependency radius is bounded independently of workload size?**

### Falsifiable hypothesis

A fixed **64 KiB block-reset adaptive H1 Law** with a symmetric Krichevsky-Trofimov prior (`alpha=0.5`) should retain material predictive value on at least two of the three preregistered statistical target workloads while refusing incompressible controls.

The model is generic and data-independent:

- file boundaries reset state;
- every 64 KiB source block resets state again;
- the first byte of each non-empty block is charged at 8 bits;
- subsequent bytes use previous-byte context with an adaptive 256-way KT distribution;
- encoder and reader update exactly the same counts after each symbol;
- no learned count table is persisted;
- charge **8 B per non-empty block** as conservative coder/framing allowance in addition to ideal KT codelength;
- block size, prior and charge are frozen before observing this result.

For the diagnostic, exact KT prequential codelength may be computed from per-block transition counts using the Dirichlet-multinomial identity. This is mathematically the same probability assigned by sequential KT updates; it does not permit a final-count model unavailable to the reader.

### Why this shape

It obeys the speed/efficiency law more closely than a two-pass static model: source observation can be fused with encoding and does not require rereading the input. Resetting every 64 KiB gives a bounded restart cone for future selective coding. It does **not** yet include a physical block-offset index, complete ONE wire framing, authenticated checkpoints or a real entropy coder, so it remains opportunity evidence only.

## Frozen advancement gate

`ADVANCE_BLOCK_ADAPTIVE_STATISTICAL_LAW` only if all are true:

1. the exact 15 frozen Genesis input identities are reproduced;
2. measured source bytes equal frozen logical regular-file bytes on all rows;
3. observation/source passes are exactly one;
4. at least **2/3** target rows (`04_analytics_and_database`, `05_logs_and_telemetry`, `10_large_mixed_binary`) have modeled ratio **<= 0.75x** after the frozen 8 B/block framing charge;
5. at least one target retains **>= 5 MiB** modeled saving;
6. both incompressible controls have modeled ratio **>= 0.98x**;
7. model state is bounded by one 256x256 transition table plus row totals/counters and does not scale with input size;
8. no stored learned model bytes, comparison scoring or winner selection occurs.

Otherwise preserve `HOLD_BLOCK_ADAPTIVE_STATISTICAL_LAW`.

## Hostile-review conditions

- Already-compressed/media/tiny rows are not allowed to disappear from the matrix; negative ratios are valuable selector evidence.
- A green information ratio is not a product size result. Arithmetic/range coder implementation, block framing, authenticated block offsets, complete wire bytes, decode throughput, memory traffic and selective-read amplification remain unpaid debt.
- Do not tune block size after seeing this result. Any later block-size study must be a separate preregistered structural experiment.
- The earlier v0.29 comparator rows are quarantined for final Genesis adjudication after the historical source-seal defect. This experiment depends only on independently regenerated frozen workload identities and the G0.3 predictor result, not on those comparator bytes.

## Required follow-up after a green result

Implement a generic bounded Statistical Law + Surprise prototype with real coding and explicit 64 KiB Crystallization/indexing, then compare complete authenticated wire against ordinary Surprise on the same exact inputs. Reader discovery remains forbidden.
