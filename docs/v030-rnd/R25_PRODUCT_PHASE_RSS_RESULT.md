# r25 product-phase RSS causal result

Status: **DURABLE DIAGNOSTIC EVIDENCE / NO RELEASE CREDIT**

This record preserves the exact-head result of the v0.30 product-phase RSS oracle. It is a scoped Forge causal constraint, not a benchmark-release receipt, representation win, Foundry thesis, or permission to weaken the RSS gate.

## Provenance

- authoritative branch: `agent/v030-authoritative-integration`
- source head: `86d6407816a71eb35df288b9b0bb91ce10f73f08`
- workflow: `CMPCT v0.30 r25 product-phase RSS oracle`
- workflow run: `33587322779`
- artifact: `v030-product-phase-rss-86d6407816a71eb35df288b9b0bb91ce10f73f08`
- artifact id: `9830647880`
- schema: `cmpct-v030-product-phase-rss-v1`
- rounds: 2, with forward/reverse arm order
- each arm: fresh Python process after importing the same promoted product/base modules
- source identity: each target is regenerated from the accepted repaired-source corpus and checked against its accepted historical tree hash before measurement
- correctness: r24 and full-product archives are strongly verified against the source tree after the RSS snapshot

`ru_maxrss` is a process high-water mark, not an additive allocation counter. The decisive ownership comparison is therefore total operation peak RSS. Baseline-subtracted values are retained only as diagnostics, exactly as the frozen instrument specifies.

## Exact result

| target | r24 peak KiB | profile-capture peak KiB | full r25 peak KiB | full/r24 peak | full minus max isolated KiB |
|---|---:|---:|---:|---:|---:|
| `resemblance_hostile_v1/01_shifted_versions` | 283,634 | 123,384 | 399,494 | **1.408484x** | **115,860** |
| `neutral_hostile_v1/05_logs_and_telemetry` | 123,384 | 123,384 | 166,360 | **1.348311x** | **42,976** |
| `neutral_hostile_v1/09_ml_artifacts` | 131,280 | 123,384 | 198,874 | **1.514884x** | **67,594** |

Median profile-capture incremental peak RSS was **0 KiB on all three targets**. Its median wall time was only 34.42 ms on shifted versions, 17.92 ms on logs, and 17.51 ms on ML. By contrast, the complete r25 product is the first measured arm in this decomposition that owns the material RSS increase.

The archive artifacts and semantic verification were deterministic across both repetitions. This experiment intentionally changed no selector, scheduling, grammar, integrity rule, locality/decode-unit budget, archive bytes, RSS threshold, or publication rule.

## Causal interpretation

### Scoped negative constraint

For this exact release-product implementation and these three frozen targets, **canonical profile/manifest capture alone is not the dominant cause of the r25 peak-RSS regression**. Retuning or rewriting profile capture without new causal evidence is therefore not a justified Forge intervention for the observed RSS red.

This does **not** prove that profile-related state can never contribute indirectly once candidate construction starts. The oracle isolates capture only. The excess appears when the complete product build executes, so the next causal question is which candidate-construction family owns that increase.

### Reopening predicate

Reopen profile-capture RSS as a primary hypothesis only if one of the following becomes true:

1. profile/manifest capture semantics or implementation materially change;
2. a new phase-isolated measurement shows profile capture itself raises total fresh-process peak RSS materially above the matched import baseline; or
3. independent heap/ownership evidence shows memory retained by capture is later amplified by candidate construction and removing that retained state materially lowers complete-product peak RSS without losing the representation gain.

Runner noise or a different baseline-subtraction narrative is not a reopening predicate.

## Next decisive experiment

Run `benchmarks/v030_r25_candidate_phase_rss_oracle.py` on the authoritative line. It isolates, in fresh processes, the genuine r24 build, the shipping candidate, the G0-G4 candidate, and the combined geometry tournament on shifted versions and ML artifacts. That result should identify or falsify the candidate family responsible for the excess peak before any Builder change is made.

If candidate isolation still cannot account for the complete-product peak, escalate one causal layer to overlap/lifetime ownership rather than tuning RSS thresholds or representation gains away.
