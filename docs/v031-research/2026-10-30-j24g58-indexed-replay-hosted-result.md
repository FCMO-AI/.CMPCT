# J24G58 — authenticated large signed-journal replay index results (research, not release)

**Observed source HEAD:** `9582a4f0639427440c5f8542871793487123a338` on isolated PR #797, stacked on #795 `1935c14c76f1bb39fd218d73cdbee93d3c2b76a1`. Source preregistration `e344fb7a5de25d8fb98bb9f47f5edc945db70945` predates implementation. Frozen parent's actual journal helper Git blob: `03743ca2a06c022c2ec64243a90fe373cf91e899`. Candidate helper blob at first implementation: `ba5ac2d01be9757651576a6fb5d640c4d212a62a` (unchanged through this tested HEAD).

## Original negative and instrument correction

The initial dedicated hosted court [#40989981913](https://github.com/FCMO-AI/.CMPCT/actions/runs/40989981913) executed 10/10 reference/hostile differential tests successfully but ended FAILURE: ABBA instrument had a Python `SyntaxError` in the constructed `owner_overrides` comprehension before any measurements. Artifact [#12948931839](https://github.com/FCMO-AI/.CMPCT/actions/runs/40989981913/artifacts/12948931839) preserves that red. Commit `cb7b7584ba59939f34e54ca96daac3ad50920fab` fixed the instrument without changing the candidate helper; rerun [#40990255024](https://github.com/FCMO-AI/.CMPCT/actions/runs/40990255024) passed 10/10 and yielded source-bound numbers. This was a scientific-instrument defect, not a measured engine result; the failed run is not relabeled.

## Exact-head source-bound evidence

**Hosted [J24G58 run #40990488670](https://github.com/FCMO-AI/.CMPCT/actions/runs/40990488670)** completed SUCCESS at exact code HEAD `9582a4f0639427440c5f8542871793487123a338`. Original artifact [#12949311104](https://github.com/FCMO-AI/.CMPCT/actions/runs/40990488670/artifacts/12949311104), with `head.txt`, original JUnit/log and JSON ABBA receipt. CI verified checkout/prereg ancestry, exact frozen reference Git blob, installed candidate bytes equal checked-out source and native package build. The two new **authentic physical r24** Builder→committed-generation Reader/preflight cases (128 operations on 128 real files, all renames and delete/reinsert) passed, with exact full-index equality to source-pinned original replay, 128 verified members and sampled byte-by-byte reads. Alongside randomized, metadata, collision and invalid-op checks: **12/12 pytest pass**.

### Instrument-only ABBA (not a product benchmark)

Same installed package, same complete operation inputs, exact historical helper source, Python 3.11 on Ubuntu 24.04. For every case five alternating ABBA/BAAB blocks (20 timed mutation executions) follow untimed equality checks. The timer wraps **only** the replay function; copy, import, index decode, filesystem, SHA verification, Builder, extraction and process startup are outside its boundary. Raw per-observation wall and process-CPU values are in `evidence/j24g58-abba.json`, SHA-256 `f8076793ea83643c51384ae6fd870e5f5f0c3d077eec65cbfc4239e06b1dc872`.

| Renames / initial rows | Exact parent median wall | Candidate median wall | Median A/B ratio | Peak traced Python allocated bytes A/B |
| --- | ---: | ---: | ---: | ---: |
| 64 | 0.106 ms | 0.081 ms | 1.307× | 22,216 / 29,040 |
| 512 | 2.777 ms | 0.546 ms | 5.085× | 157,224 / 207,456 |
| 2,048 | 38.938 ms | 2.438 ms | 15.970× | 646,164 / 855,712 |
| 4,096 | 174.235 ms | 5.238 ms | **33.266×** | 1,285,680 / 1,970,576 |

**Loss / exported cost:** At 4,096 rows, the fast execution allocated **684,896 additional traced Python bytes**, ~53% more than the parent during the separate allocation probe; it is not process VmHWM/RSS and excludes package/OS memory. The index uses extra memory O(rows) and must justify carrying cost. Row shape is a synthetic helper input; the separate 128-file physical archive court establishes correctness, not its performance. Source-only historical #344/#346/#358 speedups are different generations and are not relabeled as current numbers. Repeating the earlier 10-test head gave 4096 rows 201.741ms vs 6.726ms (29.992×) under a slightly different code/evidence HEAD; both measurements remain source-scoped.

## Falsifiers and remaining gates

The fast path is limited to unique-name, noncolliding, ≥64-row/≥16-operation sequences after a full name-graph dry-run. Unusual/collision and max-file-overflow sequences stay on the unchanged original loop. Unknown or malformed operations are rejected before both paths, signed xattrs/owner metadata rekey stays untouched. The 1800-seed reference sweep plus physical 128-file tests passed, **not** a proof over arbitrary hostile archives.

Still owed: realistic signed 2k–4k generation Reader cold-open/CPU/RSS/verify costs; large-index filesystem xattrs and owner restoration on Linux/macOS; 64-generation checkpoint; same-UID publication/adversarial recovery; full version/release ABI/size/performance/portability courts and artifact-level detached hostile auditor. Inherited #795 general suite failed five historical controls on its own HEAD; that history cannot be waived. The official CMPCT r24/ZIP job may finish administratively SUCCESS with substantive performance skipped. There is no new 0.x release, product merge or 1.0 competitor comparison.

## Causal decision

A bounded dictionary/tombstone executor can eliminate a large fraction of repeated name-scan work in a compatible signed-journal state *without changing physical archive semantics* in the two accepted hosted cases. It cannot earn product promotion from a helper ABBA because the true archive reading hot path, CPU/RSS and recovery are not priced. The 4k peak allocation delta is an explicit regression-debt candidate. Next operator should either run one real 4k authenticated signed archive cold-open ABBA with sampled RSS and exact source, or reject the mechanism on whole-product economics. Do not add threshold gardening or alter release gates.

**Concurrency:** #789 and #795 retain shared replay/grammar implementation ownership; #346/#358 are historical mechanism donors; #775 owns different rekey cost; #574 owns stale discovery cache. No shared owner or STATE mutation; merge prohibited pending integration review.
