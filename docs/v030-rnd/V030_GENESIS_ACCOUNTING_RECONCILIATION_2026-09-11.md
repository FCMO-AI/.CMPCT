# v0.30 post-Genesis accounting reconciliation — 2026-09-11

Status: **evidence correction / interpretation hardening; gate verdict unchanged**.

This note reconciles three accounting ambiguities found while reactivating v0.30 after the ONE Genesis gate. It does **not** rewrite the frozen contenders, the source-sealed artifacts, or the `REACTIVATE_V030_NEAR_TERM` decision.

## Authorities inspected

- failed combined Genesis run `34573437613`, artifact `10191000395` (`cmpct1` + frozen v0.29 raw rows);
- source-sealed v0.30 recovery run `34594599804`, job `103251512822`, artifact `10263288496`;
- frozen ONE/v0.29/v0.30 identities recorded by `docs/one/evidence/ONE_GENESIS_GATE_RESULT_2026-09-11.md`;
- frozen historical worker `benchmarks/one/one_genesis_historical_product_worker.py`;
- accepted v0.29 reconstruction in `benchmarks/v030_release_generalization.py` and historical v0.28/repair-v6 evidence.

The accepted whole-matrix stored-byte totals remain:

| contender | authenticated stored bytes |
|---|---:|
| ONE-G0.2 | 275,219,901 |
| v0.29 | 137,499,525 |
| frozen v0.30 | 150,055,575 |

No size result or gate verdict changes.

## 1. Analytics accepted-v0.29 floor is 6,135,172 B

The source-sealed v0.29 raw receipt in artifact `10191000395` reports `6,135,172 B` for `neutral_hostile_v1/04_analytics_and_database`. This is also the inherited v0.28 row reconstructed by current `benchmarks/v030_release_generalization.py`; Analytics is not one of the two accepted v0.29 winner overrides.

A different number, `6,135,344 B`, appears inside frozen-v0.30 product stats. It is the frozen v0.30 line's embedded historical/r25 candidate value, not the final source-sealed accepted-v0.29 comparator row. Those values differ by 172 B.

Consequence: post-Genesis R4 work must beat **6,135,172 B** on the same repaired Analytics input if it claims a strict stored-byte win over accepted v0.29. The integrated R4 recovery lane therefore binds to the source-sealed 15-row map whose sum is exactly `137,499,525 B`.

This correction makes the research bar slightly harder; no threshold is weakened.

## 2. Genesis `creation.cpu_s` for v0.30 is parent CPU, not total process-tree CPU

The Genesis historical worker measures phase CPU with `time.process_time()`. Frozen v0.30 may run bounded child processes during expensive r25/G0-G4 auditions. `process_time()` does not charge CPU consumed by those descendants.

Source-sealed aggregate medians across the 15 rows are:

| contender | sum creation parent CPU (s) | sum creation wall (s) |
|---|---:|---:|
| ONE-G0.2 | 3.079128646 | 3.079434412 |
| v0.29 | 806.536861374 | 806.620606210 |
| frozen v0.30 | 33.060306044 | 347.276693688 |

Thus the previously quoted `33.06 s vs 806.54 s` remains a correct statement about **parent-process CPU as measured by Genesis**, but it is not a valid statement of total compute consumed by v0.30.

The clearest row is Analytics:

- frozen v0.30 parent CPU: `1.654130263 s`;
- frozen v0.30 elapsed wall: `130.678255425 s`;
- frozen v0.30 product-reported portfolio create time: about `130.57 s` in the same source-sealed sample;
- v0.29 parent CPU: `209.723601091 s`;
- v0.29 elapsed wall: `209.745858378 s`.

Across all 15 workloads frozen v0.30 still beats v0.29 in elapsed creation wall on **12/15** rows, and aggregate elapsed wall is about **2.32x lower** (`806.62 / 347.28`). The three elapsed-wall losses are Office, Incremental Backups, and Incompressible/Encrypted-like.

So there is still a real speed advantage, but its magnitude is much smaller than the parent-CPU ratio suggests. Total process-tree CPU is now an explicit missing measurement, not assumed to equal either parent CPU or wall.

A source-sealed diagnostic, `benchmarks/v030_genesis_child_cpu_attribution.py`, was added to measure self CPU plus reaped-child CPU around the unchanged frozen-v0.30 build. It carries zero release credit.

## 3. The 511,176,704 B Genesis v0.30 RSS signal is not workload-attributed

Every frozen-v0.30 Genesis row reports exactly `511,176,704 B` creation peak RSS, including workloads ranging from tiny DEFLATE-family inputs to Analytics and Media. The historical worker:

1. loads the complete frozen product surface;
2. then starts the operation timer;
3. reports `resource.getrusage(RUSAGE_SELF).ru_maxrss`, which is a lifetime high-water mark.

Therefore the Genesis value cannot by itself distinguish product-import/runtime baseline from memory added by a particular build. It should not be described as per-workload codec state.

Current v0.30 release infrastructure already contains a stronger zero-credit whole-process-tree RSS companion that samples the process tree while retaining the parent `ru_maxrss` floor. The new `benchmarks/v030_genesis_rss_attribution.py` addresses a different question: it source-seals the frozen Genesis contender and records process-start, post-product-import, and post-build RSS separately on Analytics and DEFLATE-family controls.

Until that receipt lands, the correct statement is: **Genesis observed a ~487.5 MiB parent-process lifetime RSS high-water for frozen v0.30, but the metric is not yet causally attributed to import/runtime versus build state.**

## Gate consequence

None. The ONE-week decision remains `REACTIVATE_V030_NEAR_TERM` because the decisive density result is unchanged: ONE-G0.2 lost authenticated stored bytes to both mature comparators on all 15 workloads. ONE also retains its very large elapsed creation advantage: its aggregate creation wall is about `3.079 s`, and it beats both mature comparators on elapsed creation wall in all 15 rows.

What changes is the optimization target for reactivated v0.30:

- use **stored bytes + elapsed wall + properly charged process-tree CPU + operation-attributed RSS**, not parent CPU alone;
- preserve v0.30's real elapsed advantage over v0.29 while recovering density;
- treat child-process compute and fixed import/runtime memory as costs, not gifts;
- do not tune product thresholds in response to this accounting correction.

## Next evidence

1. adjudicate the exact 15-workload integrated R4 tabular-owner falsifier against the corrected `6,135,172 B` Analytics floor;
2. adjudicate the frozen-v0.30 import-vs-build RSS attribution receipt;
3. adjudicate self+child CPU attribution on the same frozen contender;
4. if R4 survives density/integrity, require repeated timing and actual file-backed selective I/O before any productization claim.
