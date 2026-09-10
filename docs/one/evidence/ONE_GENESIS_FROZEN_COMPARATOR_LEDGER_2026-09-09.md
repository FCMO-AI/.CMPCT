# ONE Genesis frozen comparator evidence ledger — 2026-09-09

Status: **PRE-GATE EVIDENCE AUTHORITY / NO GENESIS SCORING EXECUTED**  
Experimental state: `ONE-G0.2`  
Primary branch: `research/cmpct1`  
Purpose: make the 2026-09-11 Genesis comparison unable to weaken, conflate, or cherry-pick the inherited CMPCT frontier.

## Mission Lock / Referee

### Question

What exact historical evidence must the Genesis gate preserve when deciding whether CMPCT1 / ONE has a materially stronger path than frozen v0.29 and the deferred v0.30 frontier?

### Hard constraints

- Frozen v0.29 authority remains `02b8b27cb2d97af7c6e0797984a898e8fa8a8e5d`.
- Frozen v0.30 authority remains `f4b158a55a08b9b18b50e4e4abe4b9251048c772`.
- The 15-workload gate must use the already-certified identical corpus substrate and same semantics.
- Shipping/canonical product state, accepted research frontier, and mechanism-oracle evidence are different authority classes and MUST NOT be conflated.
- A historical mechanism result is not permission to construct a post-hoc best-per-row oracle portfolio that never existed.
- A historical negative is not permission to compare ONE only against a weak v0.30 state when a stronger already-developed mechanism result is reproducible fairly.
- No Genesis candidate/comparator encoding or scoring is performed by this ledger.

### Falsification condition

This ledger is invalid if any quoted byte/runtime fact cannot be recovered from the named record at the frozen v0.30 tree, if it labels research syntax as shipping/canonical authority, or if it silently omits a known stronger reproducible historical comparator relevant to the final decision.

## Authority classes

The gate must keep three distinct facts visible.

### A. v0.29 canonical shipping/product baseline

`benchmarks/history/2026-09-02-v029-shipping-vs-frontier.json` records canonical revision-24 shipping against the accepted v0.29 research frontier on identical per-row trees. It is explicitly a storage comparison between different CMPCT authority levels, not an interoperability-equivalence claim.

This record is important because the shipping writer is not the strongest v0.29 density comparator. Examples from its fixed matrix include:

- `01_developer_repository`: shipping `858,023 B`, research frontier `746,627 B` (`12.9829%` smaller frontier);
- `02_office_workspace`: `15,445,186 B -> 5,954,026 B` (`61.4506%` smaller);
- `04_analytics_and_database`: `10,392,442 B -> 6,135,172 B` (`40.9651%` smaller);
- `05_logs_and_telemetry`: `5,260,129 B -> 3,550,609 B` (`32.4996%` smaller);
- `08_many_tiny_files`: `617,923 B -> 420,318 B` (`31.9789%` smaller);
- `01_shifted_versions`: `30,275,311 B -> 1,723,056 B` (`94.3087%` smaller).

The accepted v0.29 research frontier also loses to canonical shipping on at least some rows, including the recorded media and incremental-backup rows. Those losses remain evidence and cannot be averaged away.

**Gate implication:** do not let a ONE win against only canonical r24 masquerade as a win over the strongest v0.29 research representation. Conversely, do not borrow non-canonical v0.29 research semantics as if they were already shipping product guarantees.

## B. deferred v0.30 canonical/generalization state

Exact record:

`benchmarks/history/2026-09-02-v030-canonical-generalization-red-e75f.json`

Historical source: `e75f3d3e2d7a774836c35c0dd50cc130a07a02c6`  
Historical workflow run: `33578285446`  
Historical job: `100086983938`  
Artifact digest: `sha256:17a46e41c92b5bb04dbf4580414e70476585b4df9a65f130972229bd9572a0da`

Recorded decision: **`FAILED_ALL15_GENERALIZATION_GATE`**.

Across all 15 rows:

- accepted-v0.29 research frontier: `137,499,525 B`;
- v0.30 candidate: `150,060,401 B`;
- delta: **`+12,560,876 B`**;
- `9` improved, `6` regressed;
- no release credit.

The failure was highly concentrated but still per-row blocking: Office and Analytics contributed about `96.75%` of total regression mass. The exact record also preserves smaller regressions in Deflate-family, incompressible and tiny-file controls.

**Gate implication:** v0.30 cannot be narrated as a broad 15-workload density win. But this RED integration also cannot erase narrower v0.30 mechanisms that legitimately beat the accepted v0.29 frontier.

## C. deferred v0.30 runtime/product state

Exact record:

`benchmarks/history/2026-09-02-v030-canonical-runtime-red-e75f.json`

Historical source: `e75f3d3e2d7a774836c35c0dd50cc130a07a02c6`  
Historical workflow run: `33578285446`  
Historical job: `100086984016`  
Artifact digest: `sha256:0e87b7668d8fe12c469e9bc72e267472d74d71929967da312796a3c06cedf518`

Recorded decision: **`FAILED_RELEASE_RUNTIME_GATE`**.

Frozen totals:

- median create ratio vs accepted v0.29: **`1.270137x`**;
- worst workload create ratio: **`1.485127x`**;
- median extract ratio: **`1.455366x`**;
- worst workload extract ratio: **`2.626761x`**;
- maximum peak-RSS ratio: **`3.392828x`**.

All five release-runtime gates recorded in that artifact failed.

Important mechanism-level rows remain visible:

- shifted versions selected PrefixGraph at `1,700,603 B` vs `1,723,056 B` accepted-v0.29, but median create ratio was `1.270137x` and maximum pack RSS `3.392828x`;
- logs-inverse reached an extreme median create ratio of `0.009044x`, but extraction was `1.455366x` and max RSS `1.444203x`;
- ML G04-overlay saved bytes (`13,674,821 B` vs `13,836,439 B`) but create/extract/RSS were `1.485127x / 2.626761x / 1.691243x`.

**Gate implication:** v0.30 contains real structural ideas and even dramatic stage-specific speed results, but the frozen product envelope exported substantial runtime/RSS debt. ONE must not be compared only on bytes, and v0.30 must not receive credit for a density mechanism while its measured product costs disappear.

## D. strongest independently frozen early v0.30 PrefixGraph mechanism oracle recovered

Exact record:

`benchmarks/history/2026-08-17-v030-prefixgraph-oracle-v1.json`

Claim boundary in the record: **orthogonal two-workload mechanism oracle; canonical r24 unchanged**.

Against the accepted v0.29 Mosaic research comparator:

| workload | accepted v0.29 | PrefixGraph | saving | recorded PrefixGraph create | recorded v0.29 create |
| --- | ---: | ---: | ---: | ---: | ---: |
| shifted versions | 1,723,056 B | 1,700,242 B | 22,814 B | 9.2412 s | 84.8752 s |
| boundary churn | 79,876 B | 75,480 B | 4,396 B | 3.1908 s | 60.8162 s |
| **total** | **1,802,932 B** | **1,775,722 B** | **27,210 B** | — | — |

Both rows improved, max dependency depth remained `1`, and the mechanism gate passed.

This is evidence that v0.30 learned additional structure beyond the already-strong v0.29 Mosaic frontier. It is **not** evidence that PrefixGraph was a broad 15-workload or shipping win.

## E. v0.30 parameter/RSS negative evidence must remain attached to PrefixGraph

Exact record:

`benchmarks/history/2026-08-30-v030-prefixgraph-window-frontier-negative.json`

The attempt to reduce Shifted PrefixGraph RSS by shrinking the Zstd window was falsified as a material fix:

- window-log 22/21 preserved exact bytes but reduced RSS by less than `1%`;
- window-log 20 caused a `8.334945x` byte ratio, `1.597282x` wall ratio and `2.083197x` RSS ratio.

The durable conclusion is that ordinary parameter tuning was terminal for that blocker; the remaining issue was ownership/lifetime of concurrently materialized anchor-audition work.

**Gate implication:** do not compare ONE against an imaginary low-memory PrefixGraph obtained by assuming an unproven parameter tweak.

## Admissibility rules for the 2026-09-11 decision

1. **The primary 15-row comparison remains same-input/same-semantics against the frozen executable authorities.** It is not replaced by this historical ledger.
2. **Historical research-frontier evidence is attached as a second axis.** It answers whether ONE has a credible path to supersede the strongest already-developed structure, not whether a non-canonical artifact already satisfied all product requirements.
3. **No best-per-row hindsight oracle.** A historical mechanism may be credited on rows where it had frozen evidence; it may not be recombined after the fact with unrelated historical candidates unless such a portfolio/selector itself existed and had bounded measured cost.
4. **Every historical win carries its measured debt.** Creation CPU, extraction, RSS, locality, integrity, recovery and reader/format status travel with the byte result.
5. **Every historical loss remains visible.** Aggregate improvement cannot delete a row.
6. **ONE receives the same treatment.** Mechanism microbenchmarks remain supporting evidence until the 15-workload candidate passes the frozen execution contract.

## Hostile review

### Strongest risk of understating v0.30

The frozen tree contains a large research history beyond the four records summarized here. A later pre-pivot v0.30 mechanism may contain a stronger legitimate result than the early PrefixGraph oracle. Therefore this ledger does **not** declare `2026-08-17-v030-prefixgraph-oracle-v1.json` to be the globally strongest v0.30 result merely because it is the strongest exact positive authority recovered in this pass.

Before final gate adjudication, the runner/reviewer MUST scan the remaining pre-pivot v0.30 evidence records and either:

- identify a stronger admissible result and append it to the ledger; or
- record that no stronger same-semantics reproducible authority was found.

This prevents an incomplete historical audit from becoming a conveniently weak comparator.

### Strongest risk of overstating v0.30

Conversely, combining all historical positive mechanism rows into an oracle selector would manufacture a system that was never built and would hide selection/search carrying cost. The gate must refuse that construction.

## Current conclusion

The frozen evidence already establishes a demanding but coherent comparator shape:

- v0.29 had a powerful accepted research frontier, including very large resemblance wins;
- v0.30 discovered additional useful structure beyond that frontier on specific workloads;
- the broad canonical/generalized v0.30 integration remained RED in both bytes and runtime/resource behavior;
- v0.30's useful principles therefore deserve to be beaten or absorbed by ONE, while its exported product debt does not deserve to disappear.

No CMPCT1 win/loss claim is made here. The Genesis gate remains reserved for the first qualifying activation on 2026-09-11 America/Mexico_City.

## Next decisive action

Complete the frozen-tree scan for any later/stronger admissible v0.30 mechanism evidence, then bind the resulting ledger paths/digests into the Genesis gate artifact validator so a final report cannot silently omit either the broad RED state or a stronger historical frontier result.
