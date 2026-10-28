# J24I03 — #699/#704 binary-create attribution: two narrow nulls and a prefix-conditioned null

**2026-10-28 UTC / decision-complete research, NOT a product gate, no merge or release.** Source ownership: draft [PR #711](https://github.com/FCMO-AI/.CMPCT/pull/711) stacked on #704. Published CMPCT remains v0.30.0/revision-24 at `main@80c358f8824ec1b20d349c92ed94c898090969b0`. This report links source-exact original evidence instead of replicating broader project state.

## Mission question and current decision

**Question:** Is the **real, repeated** official parity release failure for `binary/library/create_s_median` in composed candidate #704 a reproducible direct candidate/Builder slowdown, or evidence of benchmark runner, Python import/process state, or earlier workload chronology?

**Decision:** **`RELEASE_VETO_PRESERVED; ISOLATED_BUILDER_SIGNAL_NOT_REPRODUCED_TWICE; PREFIX_CONDITIONED_SIGNAL_NOT_REPRODUCED_ON_ONE_HOST`.** Nothing in these narrower research tests legitimately turns either original full parity red green. It is not yet possible to assign the >17% regression causally to the Reader constructor, to Builder, or to infrastructure. More near-identical single-workload microbenchmarks are low expected-value; move to a materially different **full-run measurement/provenance frame**, and otherwise prioritize existing independent P0 correctness work.

## Exact source and original product evidence

- **Base #699:** `4de43609046ceaba93902e6680af3b4059aee49f`.
- **Candidate #704:** `293aa161a4a13b4c1f4fd0f5089aa62e4dbeedef`.
- **Original full official comparator:** [Actions #40768077184](https://github.com/FCMO-AI/.CMPCT/actions/runs/40768077184), two substantive attempts on **the same candidate/base source and complete immutable input tree SHA `b0cc877945eb66602e9ac5e3d7626d3935462aed616ac6011de1afd57858688f`** (7,713 files/303,738,466 logical bytes).
- First full ABBA: **139.4093305 → 171.2223795 ms**, +31.813049ms/+22.8199%. Second full ABBA: **168.996 → 199.053 ms**, +30.056ms/+17.79%. Both violate 5%-AND-3ms hard gate and are **genuine product promotion blockers**.
- All 32 CMPCT/ZIP source-equal archive-size comparisons per attempt agree. Third-root auditor recalculated 64 base/candidate timing medians per attempt. Both executions make binary/library/CMPCT a singular ~30ms outlier versus **binary/CLI CMPCT (+1.785/+1.066ms)** and **binary/library/ZIP (−0.695/−3.563ms)**. Full-matrix issue remains unexplained.
- Exact Git comparison confirms the only changed product function from #699 to #704 is `src/cmpct/reader.py::CMPCT.__init__`. Timed `Builder(src).build(out)` does not invoke that constructor; the original benchmark module does import Reader.

## First scientific rung — source-locked warmed A/A and A/B

**Preregistered before source edits:** `eb524766fc9cd74e438e907f44e30772bbb63f8b`. The instrument `benchmarks/v031_j24i03_binary_create_aa_ab.py` loads the exact base/candidate Builder trees in separately warmed processes. It uses 8 groups each for A/A sham and A/B (7 timing observations per group; 16 processes/112 timings per execution), records independent wall/CPU/RSS, input SHA and complete deterministic archive SHA.

Hosted **[Actions #40782479556 attempt 1](https://github.com/FCMO-AI/.CMPCT/actions/runs/40782479556/attempts/1)**, original artifact `12857788040`, SHA-256 `395c8fb85564461f8e6fdc0040d93038c9fe7a6133239de098297353c42e89a5`:
- A/A: 195.7862845 vs 196.831437ms, **+0.534%/+1.045ms** wall; CPU delta +0.375ms.
- A/B: 195.713637 vs 194.773362ms, **−0.480%/−0.940ms** wall; CPU delta −2.789ms.

Same exact source, independent hosted **[attempt 2](https://github.com/FCMO-AI/.CMPCT/actions/runs/40782479556/attempts/2)**, original artifact `12858485285`, SHA-256 `20f303c60f7e6ffb82885064af2fdf200e3e96baf09d25e623b9f3f1aa2427bf`:
- A/A: 184.971552 vs 186.282211ms, **+0.709%/+1.311ms** wall; CPU delta +1.574ms.
- A/B: 186.786395 vs 186.163193ms, **−0.334%/−0.623ms** wall; CPU delta −6.275ms.

Both CI attempts **SUCCESS**; third-root JSON auditor independently recomputed raw medians and rejected **7/7 tampered receipts in each attempt**. Neither A/B passes frozen >5% AND >3ms both wall and CPU; all 8 A/B matched temporal pairs fail the strong positive-consistency requirement across the two trials.

**Strongest adversarial limitation discovered after measurement:** This original instrument imports `cmpct.builder` but **does not import `cmpct.reader`**. Static source inspection of package initializer and encoder modules confirms no Reader import in that path. This trial tests **unconditional direct Builder cost under narrower module imports**, not Reader module import-time effects or full-parity process state. It must not be treated as a complete falsifier of the official code delta.

## Second scientific rung — unchanged official helper under preceding-workload prefix

**Separately preregistered AFTER first rung evidence but BEFORE prefix code:** `036825277e32a8375fc4b1822adf48c52023c063`. `research/v031_j24i03_prefix_conditioned_court.py` imports the genuine `benchmarks/zip_parity_bench.py` helper, hence Reader, and executes exact same helper's first four rows `tiny→source→media→binary`, both library/CLI, with 3 repeats per timed operation. A/A and A/B chronological cases each have 4 independent process records; all eight input+layer output CMPCT archive SHA identities are pairwise unchanged.

The first hosted [run #40783050035](https://github.com/FCMO-AI/.CMPCT/actions/runs/40783050035) **FAILED BEFORE producing a receipt** on a measurement typo `ru_max` vs `ru_maxrss`, with unrelated unnecessary large artifact. Fixed **only** that RSS receipt name and temporary output placement (original error remains preserved); no mechanism, comparator, source or threshold changed.

**Actual first result-bearing run:** [Actions #40783322571](https://github.com/FCMO-AI/.CMPCT/actions/runs/40783322571), exact instrument HEAD `0c37c37ad1c2feaa07ac29ea10f63d9e7a0d683c`, **SUCCESS**, artifact `12858640979`, ZIP SHA-256 `8bcc364bace6b93d148ada4ef5c2214d79dad955bdc75657b1cd749b3f4a95db`, raw JSON SHA-256 `78170390e33b9b860ea786d09a01225ad4a753ad6598d3b43d8e00078c808718`.

| Chronological court | Base binary/library/create | Other | Delta wall | Prospective gate-scale |
|---|---:|---:|---:|---|
| A/A sham, base vs base | 208.071100 ms | 206.265975 ms | **−1.805125ms / −0.868%** | No |
| A/B, base vs #704 | 207.136784 ms | 207.543937 ms | **+0.407153ms / +0.197%** | **No** |

Independent third-root referee audited **8 hosted process records, all 4 rows × 2 layers, 8 complete archive identities** and independently recalculated both court medians and flags; **8/8 forged/altered receipts rejected**. No full product timing win or broad portability is credited.

**Important remaining limits:** This court measures 3 rather than the official 7 repetitions; it retains per-operation *three-sample medians*, not original raw three timing samples. It does not run the complete eight-corpus parity matrix, does not call `universal.logical_bytes` in the same outer-loop context, and uses another hosted runner. The A/A and A/B source comparisons are within one Ubuntu runner execution, not independent cross-host replication. Thus it rules out a large candidate penalty **under this bounded prefix** and unchanged helper, not under the identical full official execution context.

## Controls, alternative explanations, negative discipline

1. Candidate and base output archives have unchanged full physical SHA in all held-out prefix records; mixed archive identity cannot explain the nulls.
2. Source-mode differences: direct Builder benchmark vs actual Reader-imported parity helper are separated, not silently pooled.
3. Different entire-run sequencing, native allocator/cache state, process startup/imports, scheduling/provider contention, timestamped shared external corpus creation and **release job-specific** environment may still matter.
4. Real official negative remains **twice**; no positive research microbench redeems it or authorizes merge/release.
5. First prefix infrastructure failure is an instrument defect, not a product failure, not included in measured results.

## Frame review and next zero-history executable target

This is already a **three-fork mechanistic sequence** (one original official failure replicated; isolated warm baseline null ×2; real Reader-imported prefix null ×1). Stop narrow import/List/Builder time-variant gardening and choose a **different frame**: full-run provider/execution-custody A/A comparator (identical engine labeled both sides) with CPU scheduling/thermal/affinity/load observability and exact historical full-matrix inputs, coordinated with [#238](https://github.com/FCMO-AI/.CMPCT/pull/238), whose historical A/A owner works a different exact source pair. Only if a newly preregistered, affordable, independent observation can change which engineer has to act should this lane consume new CI budget. Meanwhile P0 correctness owners of extraction quota, path safety, physical Deflate, ZIP publication and Reader resource custody remain higher-leverage release blockers.

**Counterfactual lesson:** Compare the real module-import graph and source boundary before granting an isolated component A/B credit to falsify a whole-script regression. This is supported as a local methodological repair; there is **insufficient repeated cross-family evidence** to modify normative Discovery Engine policy or `docs/discovery/STATE.json`, which has separate ownership under #574.

**No product edits, no baseline/threshold/evaluator changes, no force-push, no merge, no release.** This report supersedes any earlier summary suggesting the isolated A/B alone disproved the official slowdown.
