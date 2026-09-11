# ONE-G0.2 segmented minimizer rehabilitation evidence — 2026-09-04

Status: frozen Builder result preserved; candidate retired, mechanism signal retained.

## Mission lock

Hypothesis: replacing per-position monotonic-deque maintenance with the frozen four-block segmented rightmost-minimum maintenance can preserve the exact `cmpct-gear-v1` 64-byte recurrence and 4096-state rightmost-minimum selector while materially reducing large-input encoder-discovery cost without exporting unacceptable boundary, hostile-case, or state debt.

Disproof rule is the immutable interpretation in `benchmarks/one/one_g02_minimizer_segmented_ab.py`. This record does not alter that grammar or any threshold.

## Exact evidence

- source: `ec3dcf570b1425f3588e34d00c1561d6916c1318`
- workflow run: `33934765773`
- result-bearing job: `101220894342`
- artifact: `9959914095`
- artifact SHA-256: `3cfe359239b8218eaf1d1b5e2d393526e0f92d02f03fd673139419bcef648ee7`
- ONE semantic/hostile suite: substantive job completed successfully before the result-bearing microbench steps.

## Result

Exact selector semantics survived: all frozen rows matched the independent Python rightmost-minimum trace.

The candidate nevertheless fails its preregistration because the two shortest boundary rows regress beyond the 5% ceiling:

- below enablement boundary: segmented / masked elapsed ratio `1.2768918657` (~+27.7%) — FAIL;
- at enablement boundary: `1.1812505179` (~+18.1%) — FAIL.

The mechanism has substantial retained headroom elsewhere:

- large-input geometric-mean elapsed ratio: `0.5638404064` (~1.77x faster than masked deque) — PASS;
- no frozen large row exceeded the `0.75` ratio ceiling — PASS;
- 16,385-byte shifted-starvation hostile ratio: `0.6358955872` (~1.57x faster) — PASS;
- reserved-state ratio: `0.7591688852` — PASS.

Frozen terminal decision: `retire_candidate_preserve_block_rehabilitation`.

## Residual compute debt

`one_g02_minimizer_segmented_residual.py` measured the same compiled segmented maintenance against the Gear-only recurrence floor on 1 MiB regimes:

| regime | segmented ns/B | segmented throughput | Gear-only ns/B | Gear-only throughput | elapsed ratio |
| --- | ---: | ---: | ---: | ---: | ---: |
| random | 4.8486 | 206.25 MiB/s | 0.5613 | 1781.48 MiB/s | 8.6389x |
| zeros | 4.6942 | 213.03 MiB/s | 0.5453 | 1834.46 MiB/s | 8.6080x |
| periodic257 | 4.7110 | 212.27 MiB/s | 0.5550 | 1801.82 MiB/s | 8.4885x |

Geometric residual ratio: ~`8.5778x` Gear-only. This remains discovery-microkernel evidence only; it is not a product-speed, stored-byte, reader, v0.29, or deferred-v0.30 claim.

## Causal interpretation

The rejected result falsifies **uniform use** of the four-block segmented maintenance across the full admissible size range. It does not falsify the maintenance principle: the sign reversal between boundary and mature inputs, plus lower retained state, is evidence of an amortizable fixed/setup component rather than a large-input regression.

The next permitted question is therefore narrower: map the exact crossover without a promotion rule, then preregister at most one same-semantics maintenance policy from mechanism-derived evidence. Any superseding policy must preserve Gear identity, 4096-state rightmost-minimum semantics, exact anchor trace, one source pass, bounded state, and generic ONE reuse-Law emission. It may not hide a second reader-visible codec/mechanism.
