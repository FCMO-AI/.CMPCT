# CMPCT1 / ONE Genesis gate — execution and adjudication contract

Date frozen: **2026-09-10**  
Applies at/after: first qualifying activation on **2026-09-11 America/Mexico_City**  
Current experimental lineage: **ONE-G0.2**  
Status: **preregistered procedure; no gate scoring performed by this document**

## 1. Mission lock

The September 11 Genesis decision asks one empirical question:

> Does the best frozen CMPCT1 / ONE state demonstrate a materially stronger path than both frozen v0.29 and the strongest already-developed deferred-v0.30 frontier, under the same logical inputs and without exporting cost into creation, read/access behavior, memory, integrity, recovery, portability, or reader complexity?

This contract removes adjudication freedom before results are observed. It does not encode or score the 15 gate workloads before the allowed date.

## 2. Immutable authorities

Frozen comparators from `docs/CMPCT1_GENESIS.md`:

- v0.29: `02b8b27cb2d97af7c6e0797984a898e8fa8a8e5d`
- deferred v0.30 integration: `f4b158a55a08b9b18b50e4e4abe4b9251048c772`

Shared input substrate:

- exactly **15 workloads**;
- **10** from `neutral_hostile_v1`;
- **5** from `resemblance_hostile_v1`;
- current accepted neutral generation authority: `neutral-hostile-repair-v6`;
- each workload must match the file count, logical byte count, and `tree_sha256` already accepted by the readiness authority;
- no input may be removed, regenerated under a different semantic identity, or replaced after observing a contender result.

Pre-gate readiness has separately proven these identities without encoding/scoring. The actual gate must re-check them before measurements.

The CMPCT1 candidate SHA is **not** frozen by this preregistration because Genesis explicitly grants research through September 10. At the first qualifying September 11 activation, the runner must bind the then-best admissible `research/cmpct1` SHA **before any gate contender is executed** and record that SHA in the result. No candidate patch may occur between observing gate output and adjudicating that run. A later repaired candidate requires a fresh, explicitly identified gate run and cannot overwrite the first result.

## 3. Same-input / same-semantics rule

The candidate harness owns comparison semantics for all contenders as required by `docs/PERFORMANCE_RELEASE_GATE.md`. Historical result files may identify authorities and frontier hypotheses, but independently running each historical harness and comparing those numbers is not a valid same-runner gate.

For every workload and contender, the measured artifact must reproduce the same logical filesystem/object universe. At minimum preserve all semantics exposed by the portable corpus and relevant CMPCT contract:

- exact regular-file bytes;
- path identity and normalization;
- directory/file distinction;
- duplicate/hardlink/symlink semantics where represented by the workload;
- sparse semantics where represented;
- nested-container bytes exactly;
- integrity/authentication requirements;
- bounded resource behavior;
- selective member/range access where the workload exposes it;
- recovery/portability requirements that are applicable to the contender.

A smaller artifact obtained by dropping a semantic obligation is invalid evidence, not a size win.

## 4. No hidden side state

`stored_bytes` means every persistent byte required to reproduce the contender's promised semantics from the archived state under the gate contract.

A contender may not omit from accounting an external dictionary, model, previous version, lookup table, index, cache, crystal, proof object, manifest, or metadata object that is required but not independently assumed by the same workload contract.

Where a workload legitimately models an already-existing authenticated prior generation, both candidate and comparator may consume that prior state under the same declared lifecycle semantics. Cold establishment and warm incremental ingest must be reported separately rather than silently mixing one contender's cold cost with another contender's warm cost.

## 5. Measurement layers

Do not collapse unlike operations into one speed number. Preserve the benchmark layers required by `docs/BENCHMARKS.md`.

For every contender/workload where meaningful, record:

### 5.1 Creation

- archive/program bytes;
- process boundary (`library/in-process` versus `fresh-process CLI`) if both are measured;
- CPU time;
- wall time;
- peak RSS/temporary memory;
- all mandatory discovery, exact proof, Program construction/validation, canonical emission, hashing/integrity generation, and required placement work inside the declared creation boundary;
- warm incremental state, if used, explicitly identified and charged according to Section 4.

### 5.2 Whole-object read/extract

- CPU and wall time;
- exact bytes returned/restored;
- peak temporary memory when available;
- integrity verification included or explicitly separated in the same way for all contenders;
- fresh-open and already-open layers not compared as if equivalent.

### 5.3 Selective access

For deterministic requested members/ranges, record at minimum:

- requested logical bytes;
- physical archive/source bytes touched/read;
- decoded/reconstructed bytes;
- authentication/proof bytes touched;
- reconstruction work or an exact operation-count proxy where available;
- temporary memory;
- open/preflight cost separately from repeated-read cost where the design has reusable validated authority;
- failure blast radius / dependency cone relevant to the request.

No contender may materialize a whole root/archive and call only the returned slice 'selective'.

### 5.4 Reader/implementation burden

Record whether a candidate result requires:

- new reader-visible opcodes/mechanisms;
- discovery at read time;
- optional/native-only semantics without a portable reference path;
- increased graph/dependency limits;
- hidden fallback codecs;
- capability differences that alter the product contract.

ONE may choose among cheaper internal execution backends for the same validated Law; that is not a representation win or loss by itself. Reader-visible semantic complexity is.

## 6. Size adjudication

Archive/stored size is deterministic and receives **zero-byte regression tolerance** at a promotable boundary, consistent with `docs/PERFORMANCE_RELEASE_GATE.md`.

For the 15-workload matrix report, each CMPCT1 row is classified relative to each frozen comparator independently:

- `SIZE_WIN`: candidate stored bytes < comparator;
- `SIZE_EQUAL`: exactly equal;
- `SIZE_LOSS`: candidate stored bytes > comparator.

Aggregate bytes must be shown, but aggregate savings may not erase a losing workload. A dramatic new representation may remain research-frontier evidence with explicit debt, but a loss is still a loss.

## 7. Timing adjudication

For same-runner repeated medians, a slowdown is a confirmed timing regression only when it exceeds **both**:

- **5% relative**, and
- **3 ms absolute**.

Anything inside either side of that envelope is `TIMING_AMBIGUOUS`, not a win and not a confirmed regression. This is a confidence rule, not a slowdown budget.

The gate must record repetitions/statistic and runner/environment identity. If scheduling noise is plainly unstable, increase measurement quality/repetitions rather than moving thresholds.

## 8. Resource and access adjudication

There is no aggregate percentage that can buy away a violation of a hard semantic/resource invariant.

The following are veto-class failures when the comparator satisfies the corresponding contract:

- incorrect reconstruction;
- integrity/authentication weakening;
- recovery requirement weakening;
- unsafe/unbounded resource behavior;
- hidden whole-root work for a selective request;
- portability loss without a separately demonstrated dominating product-level Pareto contract;
- reader discovery;
- hidden required side state;
- corpus/semantic mismatch.

Memory, touched bytes, reconstruction work, and reader complexity otherwise remain explicit Pareto dimensions and must be reported even where no universal single scalar threshold exists.

## 9. Workload-level verdict vocabulary

Do not reduce the matrix to one aggregate ratio. Each workload receives an evidence tuple against v0.29 and v0.30 containing size, creation, read/extract, selective-access/resource and semantic status.

Allowed high-level row summaries:

- `WIN`: no hard-veto failure or deterministic size loss, with a material measured advantage in at least one important dimension and no confirmed unexplained regression in another;
- `FALLBACK/EQUAL`: semantically equivalent and essentially preserves the comparator frontier, including exact reuse of an admissible existing representation where the ONE compiler legitimately chooses not to pursue a worse Law;
- `DEBT`: a reproducible high-upside ONE advantage exists but a size/timing/resource/access dimension remains worse; preserve under breakthrough-rehabilitation law, not as a clean gate win;
- `LOSS`: candidate is materially worse without a stronger preserved breakthrough case that justifies explicit rehabilitation debt;
- `INVALID`: same-input/same-semantics/resource evidence is not comparable.

The machine-readable record must retain raw metrics; these labels are derived summaries, not substitutes for measurements.

## 10. v0.30 frontier fairness

The frozen v0.30 integration SHA is the executable comparator authority, but Genesis also requires comparison against the **strongest already-developed v0.30 evidence/line**.

Therefore the final adjudication must report two separate things:

1. the exact same-runner 15-workload result against frozen v0.30 integration; and
2. an explicit frontier ledger of reproducible pre-pivot v0.30 wins/debts relevant to structures ONE claims to supersede.

Do not pretend v0.30 had no frontier merely because its broad frozen integration matrix was red. Conversely, do not transplant a favorable v0.30 microbenchmark into the 15-workload aggregate as though it had passed broader semantics/cost gates. Existing frontier strengths and their exported creation/access/resource costs must travel together.

## 11. Genesis campaign decision

There is deliberately **no post-result numeric vote-count threshold invented here**. `docs/CMPCT1_GENESIS.md` supplies the decision law: keep CMPCT1 primary only if the full evidence demonstrates a **materially stronger path and credible ability to supersede both** frozen v0.29 and the deferred-v0.30 frontier.

Interpret that phrase conservatively:

A case to keep ONE primary should require, together:

- at least one substantial, reproducible system-level advantage that is not merely a hand-picked microbenchmark;
- no manufactured win through weakened semantics or hidden side costs;
- the 15-workload matrix showing that losses are absent or isolated rehabilitation debt rather than broad regression;
- creation/access/resource evidence showing that ONE's density gains do not simply export cost elsewhere;
- credible generalization from the small ONE algebra, rather than a growing reader-visible mechanism zoo;
- an evidence-backed route to absorb remaining v0.29/v0.30 structural strengths.

If those conditions are not supported after the week, v0.30 returns as the primary near-term line and ONE evidence is preserved. Ambiguity must not be resolved in ONE's favor merely because Genesis is strategically appealing.

## 12. Frozen report schema requirements

The final retained gate record must include at least:

- result schema/version;
- exact CMPCT1 candidate SHA;
- exact v0.29/v0.30 SHAs;
- readiness/substrate authority hashes;
- all 15 workload identities/fingerprints;
- runner OS/CPU/environment/runtime/compiler/codec versions available to the harness;
- repetitions/statistics and process/cache semantics;
- per-workload stored bytes for every contender;
- creation CPU/wall and peak RSS where measurable;
- read/extract CPU/wall/throughput where measurable;
- selective requested/touched/decoded/authentication bytes and reconstruction work where applicable;
- semantic/integrity/recovery/portability qualifications;
- workload-level raw comparison tuples and derived verdicts;
- aggregates without dropping losses;
- unavailable measurement cells as explicit `unavailable`, never zero;
- strongest v0.30 frontier ledger with exact evidence references;
- strongest ONE negative result/debt;
- final decision and rationale;
- exact-source artifact digest and durable committed result path.

## 13. Execution order on September 11

1. Re-read Canon, Grid, CURRENT_STATE, Genesis and engineering/evidence authorities.
2. Resolve and freeze the candidate SHA before contender execution.
3. Re-run non-scoring 15/15 substrate and comparator-identity readiness.
4. Record environment/toolchain versions.
5. Run inherited semantic/hostile suites needed to establish candidate validity.
6. Execute each contender against the same generated workload tree and measurement boundaries.
7. Run selective/resource/integrity probes without weakening unsupported cells into zeros.
8. Persist raw machine-readable outputs before interpretation.
9. Derive the 15-row matrix and aggregates from raw results.
10. Attach the pre-existing v0.30 frontier ledger and ONE negative-debt ledger.
11. Apply hostile review and `docs/CMPCT1_GENESIS.md` decision law.
12. Commit the result and evidence receipt; do not rewrite a negative first run.

## 14. Prohibited rehabilitation after observing gate output

The first qualifying result is evidence. After seeing it, do not:

- change thresholds;
- remove workloads;
- change fingerprints;
- alter comparator settings;
- switch cold/warm boundaries selectively;
- stop charging integrity/proof work;
- rename missing metrics as wins;
- learn workload-name/size thresholds from the gate and rerun as though preregistered;
- overwrite the first result.

A discovered harness defect may be repaired only when the repair strengthens or preserves the previously frozen contract and the invalid run remains durable. A scientific candidate rehabilitation must be a new explicitly preregistered experiment/run.
