# J24B03-M2 — held-out upper-cardinality full Reader session: material direct guard debt

**Date:** 2026-10-27 UTC. **Status:** `MATERIAL_DIRECT_SESSION_DEBT`, evidence confirmed by independent referee; not a product release/merge permission.

## Immutable question and source

The preregistration [J24B03-M2](2026-10-27-j24b03-m2-upper-scale-prereg.md) was committed at `2b15bd4fe05161aa1820dcfaf17adafdaeb39c5c` **before** its instrument (`f61fa1be879a2a5c3d55fad3c3ed748e5e46d518`), independent referee, or hosted result. It reused the original J24B03-M numerical veto **unchanged**, applied prospectively to valid higher-cardinality N=131,072 / 262,144 plus N=1 control. Original J24B03-M non-veto at 65,536 remains true within its own preregistered regime and is **not rewritten**.

- Genuine source-exact `main@80c358f8824ec1b20d349c92ed94c898090969b0` vs #609 Reader blob `33deb74e196f7e40aa8351b6ec426a24255d5eec` and validator blob `74a907253c8e9719ec972aa7a8d7bae9d7a27124`.
- Result-bearing `HEAD=64b61fc6cfa145ea0c2629b723489bec450b02f8`; hosted [GitHub Actions run #40589345207](https://github.com/FCMO-AI/.CMPCT/actions/runs/40589345207) **SUCCESS**, original [artifact #12773935848](https://github.com/FCMO-AI/.CMPCT/actions/runs/40589345207/artifacts/12773935848), original ZIP SHA-256 `b2b70fa0c6cc577af264656264056cfab54900f1975bfc192885ec4eb68aeac1`. The original artifact contains actual 1 / 131,072 / 262,144 signed r24 wire images, 36 fresh-process rows, reader/validator source SHA-256, independent referee and checksum receipts.
- The independent stdlib referee reports `PASS`, 36/36 subprocess observations, all 3 deliberately falsified receipts rejected, exact archive/source and order custody. Local second-root audit re-opened the downloaded artifact and recomputed raw medians and threshold, confirming the 131,072 decision.

## Direct measured medians — source-identical inputs

All measurements are from one hosted Ubuntu 24.04 / Python 3.11 environment; normal subprocess startup excluded, all Reader open/read/close costs included. Each arm uses 6 ABBA observations per N; error diagnostics and physical archive bytes charged. Every logical file is queried, output length/checksum verified. One RAW 128-byte physical owner is referenced by N distinct valid direct file rows.

| Metric | N=131,072 baseline | N=131,072 guarded | N=262,144 baseline | N=262,144 guarded |
|---|---:|---:|---:|---:|
| Cold Reader open wall | 220.082 ms | 221.031 ms | 463.894 ms | 463.254 ms |
| Selective reads wall | 155.274 ms | 193.411 ms | 316.901 ms | 388.758 ms |
| Full session wall | 374.442 ms | **414.479 ms** | 779.770 ms | **850.417 ms** |
| Full session CPU | 374.408 ms | **414.419 ms** | 779.689 ms | **850.345 ms** |
| Strict preflight wall | 431.301 ms | 428.508 ms | 902.694 ms | 907.225 ms |
| Peak session VmHWM | 77,246 KiB | 77,286 KiB | 131,026 KiB | 130,970 KiB |

**N=131,072:** full session wall **+40.037 ms / 1.10693×**, CPU **+40.011 ms / 1.10686×**, and no material RSS increase. This meets the *conjunction* of both >=1.10× ratios and both >=25 ms additions — **the preregistered material-session veto fires**.

**N=262,144:** session wall **+70.647 ms / 1.09060×**, CPU **+70.655 ms / 1.09062×**. Its larger absolute penalty **does not** fire the same veto because both ratios are below the frozen 1.10× boundary. The result is not recast as a pass or failure by tweaking the test; it is a scoped measurement and a larger absolute burden. Neither profile fires the independent preflight or RSS veto.

**Final decision:** `MATERIAL_DIRECT_SESSION_DEBT` (driven by 131,072); `MATERIAL_DIRECT_PREFLIGHT_DEBT` did not fire. The original M decision `NO_PREREGISTERED_MACRO_DEBT_SIGNAL` at 65,536 is retained, and historical J24B03-H falsified prediction remains red.

## Interpretation, strongest negative and counterfactual

The guard is materially necessary: original J24B03-A/H2 source-exact three-platform tests show the released Reader can return physically displaced/wrong RAW bytes when index and BHDR contradict. Removing or weakening the per-read physical guard to win the timing court is prohibited.

The increase scales with the number of selected reads, rather than archive bytes or cold-open alone: +38.137 ms in the 131k selective phase; +71.856 ms at 262k. The reopened N=262k observation additionally falsifies a naive *linear proportional full-session ratio* extrapolation: index-open costs dominate enough that 1.10× does not hold, despite absolute guard cost growing. The unmodified original J24B03-M near-veto at 65k was an early prospectively observable discriminator for this larger-scale failure; it justified expanding cardinality instead of threshold farming.

Potential rehabilitations to test independently: an authenticated per-physical-owner **bounded** read-layout proof cached under the already pinned descriptor, or a different ownership boundary that amortizes physical BHDR work without losing strict size/CRC/format failure semantics. **Neither is authorized by these measurements**; mutable same-inode source (#531) and alias/collision/hardlink semantics must be confronted before caching any physical claim. Precomputing whole index on open is not a free win: it exports CPU/RSS and may amplify #569's measured chunk-open 27–28× debt.

This is one synthetic but legal high-dedup direct RAW regime, not a general-purpose archive throughput or ZIP/Zstd competitor benchmark, not Windows/macOS latency evidence, not extract/write/recovery evidence, and not a new format or release. Engineering safety acceptance remains confirmed; **promotion economics now have a positive veto**. Before merge/composition, repair or explicitly keep #609 as an unmerged research seed while #569's primary owner pursues a stronger architecture. No other owner branch, benchmark evaluator or discovery state was modified.


## Subsequent exact-final-HEAD replication — contradictory terminal, preserve both (2026-10-27 UTC)

**Critical later result:** after the first source-identical result, GitHub independently ran this *unchanged* M2 instrument and product sources on final documentation HEAD `f571454c5ca3f2751440afc0bcaa7296fa0b4dfe` ([Actions #40590362310](https://github.com/FCMO-AI/.CMPCT/actions/runs/40590362310), **SUCCESS**, [original artifact #12773867222](https://github.com/FCMO-AI/.CMPCT/actions/runs/40590362310/artifacts/12773867222), ZIP SHA-256 `498647a60d1df3ec9287f4daa0e647ce62e5302214f151fd1099e3a185665419`). Downloaded original ZIP was re-opened, SHA-256 matched, and its independent referee reports `PASS`, 36 source-identical processes, three forged receipts rejected. **This replication's preregistered decision is `NO_PREREGISTERED_MACRO_DEBT_SIGNAL`, contradicting the earlier source-exact run's `MATERIAL_DIRECT_SESSION_DEBT`. Do not promote the first run's veto as replicated fact.**

| Profile | First run full session baseline → guarded; relative | Final-head replication full session relative and absolute penalty | Frozen conjunctive veto |
|---|---|---|---|
| 131,072 | 374.442 → 414.479 ms, 1.10693× (+40.037ms) | **1.09084× (+34.697ms wall; +34.693ms CPU)** | First run YES; replication **NO** (relative <1.10×) |
| 262,144 | 779.770 → 850.417 ms, 1.09060× (+70.647ms) | **1.09257× (+73.473ms wall; +73.438ms CPU)** | Both NO (relative <1.10×) |

Both runs agree on the *material absolute* per-call accumulation: approximately +35–40ms at 131k and +70–73ms at 262k. Both independently audited, same sources, same input semantics, different timing observations. The original M2 exact preregistration is **not** changed; neither terminal is overwritten. Correct current science classification is **`M2_MATERIAL_ABSOLUTE_TAX_CONFIRMED__PREREG_VETO_NOT_STABLE_ACROSS_RUNS`** (descriptive reconciliation, not a retroactive evaluator verdict). The first-run measured veto still happened; the second did not. This distinction is decision-changing: do not claim a reproducible ≥10% full-session wall/CPU regression, and do not assert complete release parity either. The guard is visibly expensive for legal highly deduplicated archives, yet margin sensitivity/noise requires independent-host replication and stronger whole-product economics before readiness decisions.

No Reader/validator/frozen-test source, original result, prior threshold, format, or release gate changed. Both original artifacts are durable. Prefer next highest-value product work (#569's order-of-magnitude chunk open debt) over additional threshold gardening; if rehabilitation is pursued, test a bounded physical-owner proof on immutable/descriptor-pinned sources without exporting uncharged initialization/RSS costs or violating mutable-source safety.
