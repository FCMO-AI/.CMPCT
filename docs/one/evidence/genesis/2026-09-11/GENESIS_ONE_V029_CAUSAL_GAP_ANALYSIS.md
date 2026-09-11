# Genesis partial evidence — ONE-G0.2 vs frozen v0.29

**Date:** 2026-09-11
**Status:** partial Genesis evidence; **not** a final KEEP/PIVOT adjudication
**Authoritative raw artifact:** GitHub Actions run `34573437613`, artifact `10191000395`
**ONE candidate:** `38f17f4a45686a59a853bf62f0c840e228879e17` (ONE-G0.2)
**v0.29 comparator:** `02b8b27cb2d97af7c6e0797984a898e8fa8a8e5d`
**v0.30 comparator:** `f4b158a55a08b9b18b50e4e4abe4b9251048c772` — incomplete in this artifact; no v0.30 loss is inferred

## Mission-lock interpretation

This note extracts only deterministic facts already present in the raw Genesis artifact and asks the mechanism-level question required by the ONE research method: when a mature comparator wins, what predictive structure is it exploiting that ONE-G0.2 does not yet compile into Law + Surprise?

It does **not** alter the frozen candidate, workloads, comparators, scoring, or gate decision. It does not substitute for the full 15-workload v0.30 matrix.

## Exact matrix

| workload | ONE bytes | v0.29 bytes | ONE/v0.29 | v0.29 extra creation CPU | extra bytes eliminated per extra CPU | ONE creation speedup | ONE/v0.29 peak RSS |
|---|---:|---:|---:|---:|---:|---:|---:|
| `01_developer_repository` | 3,175,855 | 744,337 | 4.267x | 16.718 s | 145.4 kB/s | 68.4x | 0.432x |
| `02_office_workspace` | 16,408,441 | 5,954,026 | 2.756x | 24.758 s | 422.3 kB/s | 267.0x | 0.599x |
| `03_media_library` | 29,456,838 | 28,719,497 | 1.026x | 48.027 s | 15.4 kB/s | 328.2x | 0.596x |
| `04_analytics_and_database` | 31,920,630 | 6,135,172 | 5.203x | 209.567 s | 123.0 kB/s | 1382.2x | 0.726x |
| `05_logs_and_telemetry` | 17,354,869 | 3,550,609 | 4.888x | 121.930 s | 113.2 kB/s | 1292.9x | 0.602x |
| `06_incremental_backups` | 14,581,152 | 8,223,844 | 1.773x | 23.640 s | 268.9 kB/s | 123.1x | 0.613x |
| `07_incompressible_and_encrypted_like` | 10,930,856 | 10,193,958 | 1.072x | 17.127 s | 43.0 kB/s | 67.9x | 0.417x |
| `08_many_tiny_files` | 2,720,700 | 420,318 | 6.473x | 7.902 s | 291.1 kB/s | 9.2x | 0.738x |
| `09_ml_artifacts` | 18,553,871 | 13,836,439 | 1.341x | 50.793 s | 92.9 kB/s | 525.8x | 0.473x |
| `10_large_mixed_binary` | 34,254,292 | 12,593,372 | 2.720x | 27.684 s | 782.4 kB/s | 153.9x | 0.771x |
| `01_shifted_versions` | 34,233,736 | 1,723,056 | 19.868x | 104.808 s | 310.2 kB/s | 633.5x | 0.969x |
| `02_false_neighbors` | 40,667,358 | 34,698,771 | 1.172x | 54.333 s | 109.9 kB/s | 206.1x | 1.161x |
| `03_boundary_churn` | 9,954,062 | 79,876 | 124.619x | 74.823 s | 132.0 kB/s | 688.4x | 0.416x |
| `04_deflate_family` | 134,759 | 14,597 | 9.232x | 6.660 s | 18.0 kB/s | 217.6x | 0.814x |
| `05_incompressible` | 10,872,482 | 10,611,653 | 1.025x | 14.701 s | 17.7 kB/s | 172.1x | 0.624x |

Aggregate:

- ONE stored bytes: **275,219,901 B**
- v0.29 stored bytes: **137,499,525 B**
- deterministic ONE/v0.29 size ratio: **2.001608x**
- additional bytes eliminated by v0.29: **137,720,376 B**
- additional v0.29 creation CPU: **803.458 s**
- aggregate marginal information yield of that extra compute: **171.4 kB stored bytes eliminated per additional CPU-second**
- ONE creation CPU: **3.079 s** vs v0.29 **806.537 s**
- median per-workload ONE creation speedup: **217.6x**
- median ONE/v0.29 creation peak-RSS ratio: **0.613x**

ONE loses stored bytes on **15/15** workloads. The result is not threshold-sensitive.

## Causal decomposition of the density gap

The raw v0.29 product stats show that the gap is not one mechanism. Two different missing kinds of Law dominate:

### 1. Statistical/local Surprise modelling is a first-order missing Law family

Several of the largest gaps occur where v0.29 does **not** select Mosaic and reports little or no cross-object relation use. In particular:

- `04_analytics_and_database`: v0.29 eliminates **25.79 MB** beyond ONE.
- `05_logs_and_telemetry`: v0.29 eliminates **13.80 MB** beyond ONE.
- `10_large_mixed_binary`: v0.29 eliminates **21.66 MB** beyond ONE.

Those three rows alone account for **61.25 MB (44.5%)** of the total ONE→v0.29 gap. This is evidence that ONE cannot close Genesis merely by widening file-to-file resemblance search. The Canon already permits statistical symbol prediction as generic Law and Surprise consumed under an explicit probability model; G0.2 simply does not implement that part of the ontology yet.

### 2. Non-adjacent/range relation discovery is the other first-order gap

- `01_shifted_versions`: v0.29 eliminates **32.51 MB** beyond ONE.
- `03_boundary_churn`: v0.29 eliminates **9.87 MB** beyond ONE.
- `06_incremental_backups`: v0.29 eliminates **6.36 MB** beyond ONE.

These three contribute **48.74 MB (35.4%)** of the gap. The v0.29 stats expose exact-chunk aliases/residual relation packing on backups and explicit Mosaic selection on shifted/boundary workloads. The ONE response should be compiler-side candidate discovery for reusable source ranges / shifts / multi-parent relations, then compilation into the stable algebra—not reader-visible Mosaic opcodes.

### 3. Metadata/Crystallization overhead is a distinct tiny-file failure

`08_many_tiny_files` is **6.473x** v0.29 (2,720,700 B vs 420,318 B). Existing ONE raw stats attribute much of total expansion to authenticated-manifest representation. This is not a reason to weaken authentication; it is evidence that integrity Crystallization needs a more compact physical representation and amortized indexing for small roots.

## Marginal-information-yield ordering

The mature comparator also gives a useful upper-bound proxy for where additional encoder work is economically plausible. Ranking the observed v0.29 extra stored-byte elimination by additional creation CPU:

- `10_large_mixed_binary`: **782.4 kB/CPU-s** (21.66 MB for 27.68 s extra)
- `02_office_workspace`: **422.3 kB/CPU-s** (10.45 MB for 24.76 s extra)
- `01_shifted_versions`: **310.2 kB/CPU-s** (32.51 MB for 104.81 s extra)
- `08_many_tiny_files`: **291.1 kB/CPU-s** (2.30 MB for 7.90 s extra)
- `06_incremental_backups`: **268.9 kB/CPU-s** (6.36 MB for 23.64 s extra)
- `01_developer_repository`: **145.4 kB/CPU-s** (2.43 MB for 16.72 s extra)
- `03_boundary_churn`: **132.0 kB/CPU-s** (9.87 MB for 74.82 s extra)
- `04_analytics_and_database`: **123.0 kB/CPU-s** (25.79 MB for 209.57 s extra)

This is not a proposed ONE implementation cost. It is a causal prioritization signal: generic mechanisms that can recover large fractions of these gains at a small fraction of v0.29's search cost should be tested before expensive low-yield synthesis.

## Falsifiable post-gate hypotheses

These are research hypotheses only; they do not modify the frozen Genesis candidate:

1. **Statistical-Law hypothesis:** a small, bounded generic predictor + explicit Surprise probability model can recover a material share of the analytics/logs/mixed-binary gap without introducing a legacy codec registry. Disproof: complete authenticated wire does not materially improve, or reader/creation/resource burden leaves the Pareto frontier.
2. **Range-Law hypothesis:** one fused rolling observation pass plus a bounded non-adjacent candidate index can nominate shift/range/multi-parent relations that recover a material share of shifted/boundary/backups while keeping exact proof opportunity-gated. Disproof: survivor rate or exact-proof traffic destroys marginal information yield.
3. **Compact-Crystallization hypothesis:** authenticated small-root metadata can be represented substantially more compactly without weakening independent verification, selective reads, recovery, or failure isolation. Disproof: metadata savings move work/amplification into the reader or enlarge blast radius beyond the frozen product contract.

## Hostile-review boundary

- The apparent ONE whole-read advantage is **not** used here: the historical worker times `strong_verify()` plus `extract()`, so read semantics require an independent fairness audit before supporting a supersession claim.
- v0.30 remains incomplete in the authoritative partial gate artifact. Two source-sealed diagnostic rows subsequently completed before a Python `soundfile` dependency failure on media; that failure is harness/environment evidence, not comparator evidence.
- Final `KEEP_CMPCT1` / `REACTIVATE_V030_NEAR_TERM` adjudication remains blocked on the complete frozen v0.30 15-row matrix and the preregistered gate rules.
