# v0.30 exact strict external ledger — `1ea5128f`

This file preserves one completed, source-bound external-competitor receipt so future convergence work does not
confuse historical aggregate shorthand with an exact per-row result. It is **historical evidence only**: later
release-critical fingerprints must regenerate authority and this file grants no current-head release credit.

## Custody

- Exact candidate head: `1ea5128f4f705733002c277bb028243875c571bb`
- GitHub Actions run: `33496102115` (`CMPCT v0.30 canonical r25 authority`)
- Substantive job: `canonical-external-frontier`
- Artifact ID: `9797145429`
- Artifact name: `v030-canonical-external-1ea5128f4f705733002c277bb028243875c571bb`
- Artifact ZIP SHA-256: `e325823e29111aad5c6ce381c8c20886bd37d1294178d48f639326c16dfc8b53`
- Engine: `experiments/entropygraph_v030_release_product.py`
- Release facade: `cmpct-v030-release-product-v1`

The artifact completed all fifteen ordinary CMPCT/ZIP/solid-Zstd comparisons and independently verified source
semantics. The strict release contract treats equality as failure.

## Exact scoreboard

- Strictly smaller than ordinary ZIP/Deflate: **15/15**
- Strictly smaller than solid Zstd-19: **7/15**
- Strictly faster to create than ordinary ZIP/Deflate: **5/15**
- Strictly faster to create than solid Zstd-19: **5/15**
- Strict joint win — smaller **and** faster than both ZIP and Zstd-19: **5/15**

The five exact joint wins are:

| Workload | CMPCT bytes | Zstd-19 bytes | CMPCT create s | Zstd-19 create s |
| --- | ---: | ---: | ---: | ---: |
| `03_media_library` | 27,448,307 | 28,716,013 | 0.412 | 5.468 |
| `05_logs_and_telemetry` | 3,550,294 | 4,358,684 | 0.547 | 8.483 |
| `10_large_mixed_binary` | 12,590,162 | 12,591,881 | 0.162 | 1.970 |
| `02_false_neighbors` | 34,643,102 | 34,660,112 | 0.643 | 7.356 |
| `05_incompressible` (resemblance-hostile) | 10,609,137 | 10,616,616 | 0.205 | 1.982 |

Two additional rows beat Zstd-19 on bytes but **not** on creation time, so they are not strict joint wins:

| Workload | CMPCT bytes | Zstd-19 bytes | CMPCT create s | Zstd-19 create s |
| --- | ---: | ---: | ---: | ---: |
| `06_incremental_backups` | 8,081,635 | 8,384,906 | 29.000 | 1.805 |
| `09_ml_artifacts` | 13,674,830 | 13,704,258 | 40.834 | 4.603 |

The eight Zstd-size reds at this fingerprint are:

| Workload | CMPCT − Zstd-19 bytes | CMPCT create s | Zstd-19 create s |
| --- | ---: | ---: | ---: |
| `01_shifted_versions` | +5,857 | 65.836 | 0.842 |
| `03_boundary_churn` | +2,658 | 59.609 | 0.289 |
| `04_deflate_family` | +3,358 | 5.819 | 0.076 |
| `07_incompressible_and_encrypted_like` | +7,201 | 25.085 | 2.160 |
| `01_developer_repository` | +116,494 | 11.827 | 0.890 |
| `08_many_tiny_files` | +219,461 | 6.260 | 0.981 |
| `04_analytics_and_database` | +1,054,896 | 126.496 | 13.407 |
| `02_office_workspace` | +7,132,357 | 42.941 | 1.397 |

## Interpretation boundary

This receipt settles the earlier custody ambiguity around the shorthand `5/15`: at this exact fingerprint,
**5/15 is a real strict joint size+creation score**, while **7/15** is the corresponding Zstd-size-only score.
Neither number may be silently projected onto a later head.

The ledger also separates two Forge problems that aggregate reporting hides. Incremental backups and ML already
have byte wins and therefore primarily export creation/runtime debt. The other eight rows still have a byte gap;
several of the small-gap resemblance rows are representation/search reds, while Office and Analytics additionally
show very large complete-product/front-door costs. Those distinctions should govern the next exact diagnostics
rather than treating every red as the same optimization problem.
