# J24I69 — Within-arm temporal placebo on three source-identical r24/ZIP ABBA artifacts

**Classification:** POST-HOC RESEARCH / evidence interpretation only. Zero compression, product, runtime, format, ABI, release or comparator credit. This is **not** a prospectively blinded study: a small exploratory preview predated [the bounded analysis plan](2026-10-30-j24i69-source-identical-intra-arm-analysis-plan.md). No statistical significance claim.

## Scientific question and baseline

The [J24I68 #865](https://github.com/FCMO-AI/.CMPCT/pull/865) prospective source-identical experiment falsified ZIP temporal co-drift as a reliable surrogate for CMPCT drift. A more causally proximal existing control is to compare **each source arm against itself** between the A and B portions of exactly the same hosted A/B/B/A gate. Because the product/benchmark source is held identical within an arm, a material change cannot be attributed to a source edit between that arm's two sweeps. It may still reflect real process state, scheduling, cache, host history or measurement conditions.

This analysis uses the exact **three** already-published original provider ZIPs:
- #835 first: Actions artifact `12981944713`, SHA-256 `cf20ded12b7e5b6348a9fc272cadc7565dc4e76982e1760fce674b1b2e7e1598`
- #835 second: `12986955317`, SHA-256 `aedd2d6150746f5c6bcef4b0e8a41af5ed5f5c9f9fbb0c3ba78b54da59bbd1ee`
- #837: `12988780098`, SHA-256 `1d43e55fb359db5ec779607d9da25508efe61bbaa6d5ba5c5665d8819999490b`

GitHub source comparisons [#865](https://github.com/FCMO-AI/.CMPCT/pull/865) already established zero product/benchmark source mutations between candidate and base for these attempts. Original corpus fingerprint in each: `b0cc877945eb66602e9ac5e3d7626d3935462aed616ac6011de1afd57858688f`, 7,713 files / 303,738,466 logical bytes. Every original archive-size entry was identical across all four sweeps of each trial. **Archive sizes alone do not prove full physical archive-byte identity**; no claim is made beyond the available receipts.

## Method, boundaries and complete denominator

The [detached stdlib referee](../../research/j24i69_withinarm_referee.py) requires original provider ZIP SHA-256, source HEAD, frozen corpus, schema, seven-repetition medians, eight corpora, two modes, two engines, two operations, positive finite times and identical reported stored bytes. It reads `base-a.json`, `base-b.json`, `candidate-a.json`, `candidate-b.json`, computes late-minus-early effects **within the exact same source arm**, and uses a descriptive **magnitude crossing** only if `abs(delta)>3ms AND abs(delta/early)>5%`. This is NOT an approval or veto threshold. Official base-vs-candidate positive gate reds are recomputed separately, using the unchanged >5% AND >3ms policy.

Across three original hosted runs there are **384 within-arm effects**: 3 × 2 arms × 2 engines × 8 corpora × 2 modes × 2 operations, split into 192 CMPCT and 192 ZIP. There are 96 original CMPCT base-vs-candidate cells. The four values for each cell are **four sweep medians**, each median summarizing seven internal repetitions; the 28 raw individual timings per cell were not retained in these ZIP summaries.

## Historical result — original provider arithmetic

| Hosted attempt | CMPCT within-arm magnitude crossings (of 64) | ZIP within-arm crossings (of 64) | Official CMPCT positive reds (of 32) |
|---|---:|---:|---:|
| #835 first | **5** (base 4, candidate 1) | 6 (base 5, candidate 1) | **2** |
| #835 second | **14** (base 7, candidate 7) | 1 (base 1, candidate 0) | **5** |
| #837 | **0** | 0 | **0** |
| **Total** | **19/192** | **7/192** | **7/96** |

The original two #835 attempts reported **the same named CPU model** (AMD EPYC 9V45), yet the temporal-placebo counts differed 5 versus 14 for CMPCT and 6 versus 1 for ZIP. This disproves treating CPU model identity or ZIP drift as a sufficient causal diagnosis. Source identity within the hosted experiments is stronger than cross-run conjectures.

## Most important negative: do NOT promote placebo into a release veto/waiver

The within-arm flag is not a reliable automatic explanation for official reds:

| Original trial | Official red plus any same-cell CMPCT within-arm crossing | Official red with both within-arm comparisons *below* magnitude envelope | Flagged cell without official red |
|---|---:|---:|---:|
| #835 first | 1 | **1** | 4 |
| #835 second | 5 | 0 | 7 |
| #837 | 0 | 0 | 0 |
| **Total** | 6 | **1** | **11** |

**Counterexample:** the #835 first `nested/cli/create` official base/candidate effect was **71.894428ms → 79.528258ms (+7.633830ms / +10.618%)**, while individual source-arm sweeps were **base 71.062111 → 72.726745ms** and **candidate 79.001216 → 80.055300ms**; **neither same-arm difference crossed the 5% AND 3ms envelope**. Thus even where the same-source temporal-placebo control is quiet, an official source-identical red can persist.

Conversely, #835 second contained 7 non-red CMPCT cells with a same-arm crossing. Neither a positive nor negative within-arm placebo is sufficient to classify official pairwise effects as engine regressions or host noise. **All seven historical official failures remain FAILURES under their original evaluator**. A passing #837 does not retroactively erase either #835 failing run.

### Stronger negative: even two independently red A/B blocks do not identify a source regression

The same original source comparison shows **4 of the 7 official red cells** also breach the numerical positive threshold *independently in both matching A and B blocks* (1/2 first #835, 3/5 second #835). The clearest counterexample is the same `nested/cli/create` case: the A-block pair differs by **+7.939105ms / +11.172%** and the B-block pair by **+7.328555ms / +10.077%**, despite zero product/benchmark source changes. Thus merely requiring an official red to reproduce in both A/B blocks cannot prove a causal source regression either. This **does not erase the release veto**; it narrows what block-to-block repeatability can justify. Worktree path, binary execution identity and environment/candidate label remain possible unisolated causes. No prospective causal randomization was performed.

## What this establishes and does not establish

**Measured/recomputed:** at least 19 of 192 same-source CMPCT within-arm effects in the three fixed original trials exceeded the *magnitude* of the official numerical timing envelope, without any source modification between the two sweeps of the same arm. This narrows the claim that one within-run observed temporal effect can be read as a purely source-causal effect. It provides a useful cheapest diagnostic before costly new candidate implementation.

**Not measured:** individual seven timings, CPU frequency, affinity, process lifetime effects, scheduler contention, page cache, RSS, native ELF actually mapped during timed calls, full per-invocation archive SHA, or independent physical archives. The evidence has three correlated trials, not 384 independent host experiments. This is not proof of the mechanism causing the seven actual historical reds. A/B/B/A order cannot by itself establish whether an effect is true treatment or time without further assumptions and measurements.

## Method validation and adversarial checks

The reusable referee has 15 independent synthetic fixture tests covering positive admission, strict digest/source/corpus/schema validation, mismatched archive sizes, non-finite/nonpositive/string time, duplicate ZIP names, omitted sweeps and directional non-equivalence of magnitude flags and release red. All 15 passed locally. The original full artifact calculation passed and output all 384 effects plus 96 official effects. A new hosted [J24I69 workflow](../../.github/workflows/j24i69-intraarm-placebo.yml) must run on the exact HEAD to earn provider replay credit. Until hosted execution finishes, only local detached calculations and inherited provider truth are claimed.

No new CMPCT benchmark execution, no product bytes, no codec invocation, no new functional claims, no threshold changes, no shipping acceptance.

## Concurrency and decision

The method respects the separate owners: #865 ZIP-codrift, #819/#821/#825 Builder process-history/stage instrumentation, #238/#715 full A/A experiment generation, #574 shared Discovery cache. No owner files or shared discovery state modified.

**Decision-changing bounded negative:** retire the family of post-hoc per-cell temporal normalizers and the proposal to let an intra-arm flag automatically waive timing failures. The decisive next evidence cannot come from these four medians alone. A genuinely different prospective lane should retain seven original ordered timing samples, actual sampling chronology, CPU+wall and loaded-code identity, or shift toward a product/representation/ownership frontier; do not run another expensive blind full-matrix job just to relabel historical noise.

**Counterfactual:** the four original per-cell sweep medians were already present in the provider ZIPs. A single same-arm comparison would have exposed a scoped confound without spending any new provider compute. This is a local experimental-economics lesson, **not** enough repeated evidence to self-modify global discovery policy.

**Falsifier:** if the hosted original-provider replay has mismatched SHA, source/corpus or no 19/7/7 result, this result must be retracted until reconciled. Any attempt to infer a causal correction factor from within-arm data is outside this claim.

