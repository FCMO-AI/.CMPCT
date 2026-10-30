# J24I54 — READ-only versus real Builder prefix: two physical hosted attempts

**As of:** 2026-10-30 UTC. **Disposition: INTERMEDIATE / NOT REPLICATED AT PREREGISTERED READ THRESHOLD.** Source exact `f051992580a7252a6b55a881fbbd4697d4a64cbc`, preregistration `a9ab3d0255434d3da95a1303cfdf9acf1762eb6e` before instrument `ddbe2c9892715a650c617eca94d06d561da043c5`. This is **O1-style causal research**, not candidate shipping evidence, a benchmark-gate override, or proof of an implementation regression.

## Question and inherited controls

PR [#819](https://github.com/FCMO-AI/.CMPCT/pull/819) independently reproduced a ~7.85–8.64% wall and ~6.20–6.53% process-CPU increase on binary creation after the real `tiny→source→media` Builder prefix, without changing source. PR [#816](https://github.com/FCMO-AI/.CMPCT/pull/816) separately falsified an intrinsic Zstd codec slowdown in a lower-rung A/B. PR [#807](https://github.com/FCMO-AI/.CMPCT/pull/807) still has **two binding official release-gate FAILs** on binary/library/create, +16.18% and +14.55%. No new experiment relabels those failures.

Preregistered fork: is a READ-only traversal of the *same* earlier input trees (with no compression/output) **sufficient** to create a >5% AND >3ms wall+CPU penalty in the later full Builder, relative to FRESH, with same-source BUILD as positive control and FRESH/FRESH label sham as noise control? There are 18 real child processes and 54 timed complete Builder calls per independent hosted attempt; both experimental groups reverse chronological order, with one identical binary warmup in each child. Every within-attempt binary archive SHA, source/native origin, output size and unchanged input-tree fingerprint are checked.

## Provider attempts and material evidence

Both attempts of [GitHub Actions run #41035843713](https://github.com/FCMO-AI/.CMPCT/actions/runs/41035843713) completed **SUCCESS** on the **same original source SHA**. This means the court/invariants ran successfully; it does **not** mean both attempts supported the original scientific hypothesis.

- **Attempt 1**: [physical ZIP artifact #12968750031](https://github.com/FCMO-AI/.CMPCT/actions/runs/41035843713/artifacts/12968750031), 17,570,515 B, ZIP SHA-256 `5735b9d7f074f79321660ae12a507192a65e24e72666b63986b52745a18a1d44`.
- **Attempt 2** (independent provider rerun of the same job and source): [physical ZIP artifact #12968397468](https://github.com/FCMO-AI/.CMPCT/actions/runs/41035843713/artifacts/12968397468), 17,570,458 B, ZIP SHA-256 `df29423439ed29e85dc09fe567b8c4c153dccd3f11e22b002fa156643ca48f98`.

The raw JSON receipts were independently recalculated using a separate Python auditor (no project imports). All 54 observations, grouped contrasts, sham medians, native module SHA and physical file sums were checked for **each** attempt. A separate stdlib+libzstd+MessagePack third-root physical referee independently checked header/footer, both matching compressed indices, authenticated index SHA, and **all 123 CMA4 physical records** per ZIP, requiring exact decoded CRC32/SHA-256 on 64 RAW and 59 Zstd blobs. Two exact valid archive files were retained. No decoder or evaluator weakening.

### Direct observed full-Builder medians

All values are median in-process full-Builder wall or CPU, ms, excluding child startup and output SHA evidence capture; CPU can exceed wall due to native concurrent work.

| Trial | Metric | FRESH | READ | BUILD | READ/FRESH | BUILD/FRESH |
|---|---|---:|---:|---:|---:|---:|
| Attempt 1 | wall | 153.585 | 164.610 | 167.080 | **+7.179% / +11.025ms** | +8.787% / +13.495ms |
| Attempt 1 | CPU | 200.029 | 210.340 | 213.094 | **+5.155% / +10.311ms** | +6.532% / +13.065ms |
| Attempt 2 | wall | 153.450 | 160.138 | 163.377 | **+4.359% / +6.688ms** | +6.470% / +9.928ms |
| Attempt 2 | CPU | 198.252 | 204.976 | 208.255 | **+3.391% / +6.723ms** | +5.046% / +10.003ms |

**A/A shams:** attempt 1 wall **+0.010%**, CPU **−0.538%**; attempt 2 wall **+0.858%**, CPU **+0.728%**. Both independently reversed experiment groups retained positive signs on READ and BUILD, but group-level effect sizes differ: in attempt 1, group 0 READ CPU +2.30% vs group 1 +6.68%; in attempt 2, group 0 READ CPU +1.46% vs group 1 +4.61%. This matters for overconfident causal interpretation.

**Prospective decision:** attempt 1 earned `READ_HISTORY_SUFFICIENT_IN_COURT` by the preregistered test, but READ process CPU exceeded 5% by only 0.155 percentage points. **Attempt 2 produced `INTERMEDIATE_AMBIGUOUS`, not a replication of the threshold-level READ sufficiency claim.** BUILD remains material by both preregistered aggregate CPU+wall criteria in both attempts. Accordingly the combined finding is *directionally repeatable READ-associated slowdown that did not replicate its preregistered materiality threshold*. Do not promote the first trial alone; do not rewrite the +5%/+3ms boundary. Nothing establishes that prior file reads cause the original candidate-vs-base official gate red.

### Physical identity across attempts

The two retained original archives both contain **16,793,243 B**, but their **complete SHA-256s differ**:
- Attempt 1: `6bccb1684c69eb03e2688506b00d9d3149ba9173107201734da937f532674f3e`.
- Attempt 2: `a67d5f3c88f27b316d5a31b602b5503f502f8cf0c353a943e88563c0be152272`.

The separately decoded indices differ **only in file rows 0 and 1 at index field 3 (original nanosecond mtime)**. The entire 16,790,693-B encoded physical payload section is byte-identical across runs, SHA-256 `0edfbe167875b075d922cbd8e9ce5b2e0a6b6cac3461926f870975cdb1193342`. Both native module SHA values are identically `591495782dc316e820216a1b7f3806aa33361c25dfed816682cda0fd2d8d2a33`. Normalizing only these two *analysis-copy* timestamp fields yields identical decoded indices. **The inputs are exactly identical within each attempt, but cross-attempt source-tree fingerprints and physical CMPCT archive SHA are not identical.** No original source metadata was modified post-result to rescue a hypothesis.

## Falsification and limitations

- **Supported:** Builder-history BUILD adds a reproducible conditional burden; READ-only history also trends slower but fails preregistered READ threshold in the independent replay. The original strong sufficiency claim is **narrowed to an individual attempt** rather than asserted as a general replicated phenomenon.
- **Unresolved:** which of file cache, allocation, CPU power/scheduling, interpreter state, kernel page faults, worker/thread effects, or other process state explains the shift; whether archive-generation sequencing explains the official #807 base/candidate asymmetry; other OS/inputs; full product creation/extraction economics.
- **Not evidence:** no new physical bytes saved, faster published code, stronger reader semantic coverage, no release approval. Historical #807 release parity FAILs remain binding.
- **Concurrency:** current J24I54 branch changes only a new research instrument/workflow/docs; product owners #807/#816 and #819 untouched, no shared `docs/discovery/STATE.json` update (#574 ownership). No discovery policy self-modification earned.

## Cheapest next unclaimed decision

**Stop threshold gardening or repeated same-host source-identical READ microvariants.** The two attempts already show that READ-only input history is *not reliably sufficient* to satisfy the strong preregistered explanation. Next measure a **materially different frame**: one paired exact-source, official-semantics A/A release-harness chronology crossover (both engines identical bits) that controls full workload order and process startup. This distinguishes mere test execution order/host-state variability from actual candidate implementation change. Separately, if relevant, profile only the dominant full Builder phases `scan → micro-pack → deflate reuse → dictionary → ordered encode → index/materialization`, alongside major page-fault counters, without modifying or softening official release timing windows. Choose whichever cheaper observable changes the #807 promotion diagnosis. Preserve all contradictory raw evidence.

## Counterfactual discovery lesson

The independent rerun was decisive: it downgraded an initially positive threshold-level READ-sufficiency result to *directional but ambiguous*. A preregistered stronger repeated-run requirement would have avoided overpromotion even earlier. That is a scoped evidence-quality lesson, not repeat evidence sufficient to alter the global discovery policy.
