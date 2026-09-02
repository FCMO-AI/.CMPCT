# r25 candidate-phase RSS ownership result

Status: **accepted diagnostic causal evidence / Forge-Custody / no release credit**.

This record preserves the first substantive result from the exact candidate-family RSS ownership oracle after the product-phase experiment ruled out canonical profile/manifest capture alone as the dominant owner of the current r25 peak-memory regression.

It does **not** change selector behavior, candidate admission, archive grammar, integrity, recovery, locality/decode-unit limits, benchmark thresholds, or release state.

## Authority

- exact source: `c2bbfdce215113790124c01fb96f69bf09b8962e`;
- workflow: `.github/workflows/v030-r25-candidate-phase-rss.yml`;
- workflow run: `33589815780`;
- substantive job: `100121374612` (`candidate-phase-rss`);
- artifact id: `9831560776`;
- artifact: `v030-r25-candidate-phase-rss-c2bbfdce215113790124c01fb96f69bf09b8962e`;
- artifact digest: `sha256:809845f1a769664cdb4d60294db4ce270a27d338cb691c1f613811c0246a111a`;
- schema: `cmpct-v030-r25-candidate-phase-rss-v1`;
- experiment valid: `true`;
- worker failures: `0`;
- release credit: `false`.

The substantive measurement step completed successfully. A green classifier alone would not have been evidence; this receipt is bound to the completed fresh-process measurement job and uploaded artifact above.

## Frozen measurement boundary

The oracle measures each candidate family in its own fresh process after importing all compared candidate surfaces before the baseline RSS snapshot. Strong verification remains mandatory but occurs outside the candidate pack timer. Total fresh-process peak RSS is the release-boundary ownership signal; baseline-subtracted `ru_maxrss` is diagnostic only because a high-water mark is not an additive allocation counter.

Two execution orders are used to reduce order artifacts:

1. `shipping -> g04 -> prefixgraph`;
2. `prefixgraph -> g04 -> shipping`.

Candidate bytes are never added together or credited simultaneously. Structural PrefixGraph ineligibility is not reclassified as a failure.

## Result

### Shifted versions

`resemblance_hostile_v1 / 01_shifted_versions`

| Arm | Median total peak RSS | Median diagnostic incremental RSS | Median wall time | Complete bytes |
|---|---:|---:|---:|---:|
| shipping r25 | **399,008 KiB** | 276,004 KiB | 58.334 s | 1,700,601 B |
| isolated G0-G4 | **149,068 KiB** | 26,064 KiB | 107.969 s | 1,723,056 B |
| isolated PrefixGraph | **430,496 KiB** | 307,492 KiB | 5.578 s | 1,700,242 B |

Ratios versus shipping total fresh-process peak RSS:

- G0-G4: **0.37360x**;
- PrefixGraph: **1.07892x**.

The two PrefixGraph repetitions were 430,476 and 430,516 KiB total peak RSS. The two shipping repetitions were 400,536 and 397,480 KiB.

**Causal interpretation:** PrefixGraph candidate construction is sufficient by itself to reproduce—and slightly exceed—the shifted-version shipping peak-memory problem. G0-G4 is not the dominant shifted RSS owner in this tested regime. The next shifted-memory intervention should therefore target PrefixGraph construction ownership rather than profile capture, G0-G4, or the release RSS threshold.

This does not prove every byte of shipping RSS is PrefixGraph-owned. It proves the isolated PrefixGraph path already reaches a higher total fresh-process peak than shipping while preserving the same research-tree identity and exact strong verification.

### ML artifacts

`neutral_hostile_v1 / 09_ml_artifacts`

| Arm | Median total peak RSS | Median diagnostic incremental RSS | Median wall time | Complete bytes |
|---|---:|---:|---:|---:|
| shipping r25 | **181,370 KiB** | 58,366 KiB | 36.894 s | 13,674,822 B |
| isolated G0-G4 | **154,944 KiB** | 31,940 KiB | 73.678 s | 13,674,596 B |
| isolated PrefixGraph | structurally ineligible | — | — | — |

G0-G4 is **0.85430x** the shipping total peak and **0.54724x** the diagnostic incremental high-water delta.

**Causal interpretation:** isolated G0-G4 construction does not reproduce the full ML shipping peak. PrefixGraph is structurally ineligible, so the remaining ML excess lies in product composition/lifetime/other r25 work rather than in PrefixGraph construction. This result does not identify that remaining owner by itself.

## Scoped negative constraints

1. **Shifted:** do not spend another Forge cycle treating G0-G4 as the primary shifted RSS owner unless new evidence contradicts this exact fresh-process result. PrefixGraph alone is already sufficient to exceed shipping peak RSS.
2. **ML:** do not claim the isolated G0-G4 candidate alone explains the shipping memory debt. It accounts for materially less total peak RSS than shipping and PrefixGraph is ineligible.
3. Do not infer additive allocation ownership from baseline-subtracted `ru_maxrss`; the artifact explicitly marks that field diagnostic only.
4. Do not use this result for release credit. The frozen `runtime-memory-selective` receipt remains governed by `docs/V030_RELEASE_LOCK.json` and the authoritative full-product runtime/memory/selective-read evidence.

## Strongest surviving self-critique

PrefixGraph's isolated high-water measurement establishes ownership at the candidate-family boundary, not the exact allocation mechanism inside PrefixGraph. The current implementation combines raw source retention, direct-payload caching, per-anchor raw-content Zstd dictionaries/compressors, complete candidate serialization, and bounded concurrent anchor auditions. A lower-level intervention should distinguish those owners rather than merely assume the worker count is causal because concurrency is visible in the code.

Likewise, ML still needs another causal layer. The gap between isolated G0-G4 and shipping may come from product integration, overlapping retained state, canonical wrapping, r24/r25 tournament state, or another phase. This result alone cannot choose among them.

## Forge decision

**Shifted:** advance one causal layer into PrefixGraph memory ownership while preserving its exact candidate bytes, anchor set, complete-artifact tournament, locality contract and proven size gain. Prefer a lowest-sufficient R1/R2 systems intervention if the allocator/lifetime owner is demonstrated; do not change the representation merely to reduce RSS.

**ML:** preserve the unresolved integration/lifetime debt and use a separate causal instrument; do not reuse the shifted PrefixGraph fix as an explanation because PrefixGraph is not eligible on ML.

## Reopening predicates

Reconsider the shifted G0-G4 ownership conclusion only if a new exact-source fresh-process experiment shows G0-G4 total peak RSS approaching/exceeding the shipping peak under equivalent semantics, or if a PrefixGraph-internal ablation demonstrates that the apparent PrefixGraph peak is an instrument artifact.

Reconsider the ML conclusion only with an instrument that isolates the missing product-composition/lifetime phase and materially closes the ~26 MiB total-peak gap between isolated G0-G4 and shipping.
