# J24I55 — Source-identical Builder stage attribution: inconclusive at preregistered standard

**As of 2026-10-30 UTC. Scientific disposition: `NOT_STABLE_OR_SHAM_AMBIGUOUS`. No product/release credit.** This is a material **frame-review and bounded last attempt** following #816/#819/#821; do not open another small READ/BUILD history microvariant without evidence of a different causal frame.

## Authority, prediction, and original measured source

- Published main remains v0.30.0/revision-24. This experiment is a **draft stacked branch**, not canonical product.
- Exact parent #821 at `444401e36fcd27558c13702ad01c01cfa206cf7f`.
- Prospective prereg commit `9db7839bcad97748deb1110ca3944280e95ff1f8` **precedes** any measurement code. It predicts >=60% encode-stage ownership of positive total CPU effect with <=3ms sham absolute drift; no changing thresholds after observing results.
- First result-bearing source HEAD `d6471396da51c19c9f02d24530cb2214a0d46003`.
- [First hosted workflow #41043009754](https://github.com/FCMO-AI/.CMPCT/actions/runs/41043009754): **SUCCESS for execution and embedded independent numeric referee**; this is not `H1_SUPPORTED`.
- [Physical artifact #12971640885](https://github.com/FCMO-AI/.CMPCT/actions/runs/41043009754/artifacts/12971640885): ZIP SHA-256 `fe06a32e698d805e9cfd7dc8e77d8eed639429aeee553e90d8056717cc7132f1`, 17,572,829 B, original 36 timed full Builder operations with complete 12-child-process records plus output bytes and native library. Exact native SHA `591495782dc316e820216a1b7f3806aa33361c25dfed816682cda0fd2d8d2a33`.

## Scope and mechanism

`research/j24i55_phase_child.py` instruments the inherited unchanged `Builder.scan`, `_build_micro_packs`, `_prepare_deflate_reuse`, `_train_dictionary` and `ordered_worker_pull`, classifying the non-overlapping remainder as residual index/materialization/construction. The treatment is the real tiny/source/media BUILD prefix; the control is FRESH. The 12 independent subprocesses run two opposite-order treatment groups and a 4-child FRESH/FRESH sham, with identical immediate binary warmup and 3 timed full builds per child. No timing is excluded from full Builder wall/CPU. Post-call hashes and source-tree fingerprints enforce same-input, same-native-module, exact resulting archive identity. Linux resource minor/major page faults are measured per full operation; they are not proof of root cause.

## Direct observations (first physical hosted attempt)

| Instrument | FRESH median | BUILD median | BUILD-FRESH |
|---|---:|---:|---:|
| Full Builder wall | 194.373 ms | 203.670 ms | **+9.297 ms / +4.783%** |
| Full Builder process CPU | 277.940 ms | 294.969 ms | **+17.029 ms / +6.127%** |
| `scan` wall | 110.255 ms | 116.771 ms | +6.516 ms |
| `scan` process CPU | 110.251 ms | 116.752 ms | +6.501 ms |
| `ordered_encode` wall | 36.237 ms | 37.269 ms | +1.032 ms |
| `ordered_encode` CPU | 123.898 ms | 128.244 ms | +4.346 ms |
| residual wall | 47.864 ms | 49.236 ms | +1.373 ms |
| residual CPU | 47.865 ms | 49.237 ms | +1.373 ms |
| Minor process faults | 32,444 | 36,250 | +3,806 |
| Major process faults | 0 | 0 | 0 |

**Two reversed groups:** full process CPU +12.055 ms / +14.738 ms, full wall +11.346 ms / +9.123 ms; ordered encode CPU +2.525 ms / +4.387 ms, consistently positive but far from prereg encode-owner criterion.

**FRESH/FRESH sham:** wall +1.941 ms (+1.010%); CPU +3.265 ms (+1.193%). This **violates the preregistered absolute sham cutoff of 3ms**; it is not permissible to silently use a percentage-only cutoff. The full wall aggregate also fails the 5% criterion. Measured encode CPU change is only **25.52% of the total CPU median delta**, not >=60%. Individual phase medians are **not additive**, so the scanner plus encoder deltas cannot be treated as an exact cost decomposition.

**Disposition: H1 encode-dominant claim not supported; H2 non-encode claim not earned either because the sham veto fires; H3 ambiguity applies.** `scan` and minor faults are follow-up signals, not established causes. No new Builder optimisation can be justified from this sole hosted result.

## Detached physical oracle and scope limits

A separate Python script using independent libzstd, MessagePack, SHA-256 and CRC32 (no CMPCT imports) checked the original physical ZIP and archived r24 stream outside GitHub Actions. It verified the physical SHA-256 `5dd2ac701953aaca76b06bfc87b23f8cf9072853c7f4402cb7528014d18169f1` of the 16,793,315-byte retained CMPCT file, both matching compressed indices, index SHA, authoritative footer, and **all 123 contiguous CMA4 records**: 64 RAW and 59 Zstd, totaling 32,243,712 decoded bytes and 16,790,693 physical record bytes. Every decoded record's length, CRC32 and SHA-256 matched its authenticated header. All 36 recorded output SHAs were the same within this run. The latest source integrates `research/j24i55_physical_referee.py` into its hosted workflow so this proof is prospectively repeatable.

**Self-critique:** the instrumented source's absolute 194ms fresh wall cannot be compared causally to J24I54's ~153ms uninstrumented fresh wall, because it is different instrumentation/run/host conditions. No proof of exact phase exclusivity for platform kernel time, TSC scheduling or filesystem cache causation. Minor-fault counts may rise from allocator recycling unrelated to disk I/O. There is no held-out OS, workload, or fixed-hardware transfer result.

## Inherited product/release controls and implications

- [#807](https://github.com/FCMO-AI/.CMPCT/pull/807) retains **two unchanged official binary/library/create red gates**: +16.18% and +14.55%, both binding. This phase experiment is not a waiver, regression fix, full-harness parity reproduction or source-causal isolation of those two failures.
- [#816](https://github.com/FCMO-AI/.CMPCT/pull/816) already falsified intrinsic native Zstd ABI slowdown. [#819](https://github.com/FCMO-AI/.CMPCT/pull/819) showed source-identical BUILD-history overhead; [#821](https://github.com/FCMO-AI/.CMPCT/pull/821) produced contradictory READ-only sufficiency attempts. Repeating nearby READ/BUILD changes would be a saturated family.
- The mature [#715](https://github.com/FCMO-AI/.CMPCT/pull/715) source-identical full-matrix A/A already demonstrated that full-harness false positives exist; do not claim this run newly proved that or duplicate the exact experiment without a novel comparator/chronology control.

**Next actionable target:** retire this narrow micro-prefix family unless an *independent new observation* establishes stage ownership, and prefer a different-root official-harness chronology/provenance control or a separately owned correctness productization lane. No `docs/discovery/STATE.json` update: it is stale against v0.31 and already has a distinct open reconciliation owner #574; no discovery-policy modification is earned.

## CI and late state boundary

After the first successful scientific HEAD, a portable independent physical r24 referee was added in a further candidate commit with a new workflow step. The current exact-head CI and evidence dossier must be reconciled separately. A later documentation commit **does not retroactively change** the first source/head result, run ID, artifact bytes or its negative decision. No merge, release, canonical file mutation or format change.


## Independently hosted second attempt: contradictory higher-rung result

The **independent second hosted execution** of the *same preregistered science instrument*, augmented only with a detached physical authenticity check, produced a different prospective disposition. [GitHub Actions #41043653341](https://github.com/FCMO-AI/.CMPCT/actions/runs/41043653341) on exact code HEAD `402f85d5e7c6eef07c4cbb6272e27d91232741bc` completed **SUCCESS**, including the no-CMPCT-import numeric referee **and** the physically independent r24 referee; original [artifact #12971441653](https://github.com/FCMO-AI/.CMPCT/actions/runs/41043653341/artifacts/12971441653) is 17,573,203 bytes, ZIP SHA-256 `8c8328d726a7a47f6e2c0a67cbcc844a46872b2134878a0cab147fc66a0a337b`.

| Instrument | FRESH median | BUILD median | BUILD−FRESH |
|---|---:|---:|---:|
| Full Builder wall | 130.058 ms | 137.301 ms | +7.243 ms / **+5.569%** |
| Full Builder process CPU | 158.855 ms | 166.097 ms | +7.242 ms / **+4.559%** |
| Scan process CPU | 80.831 ms | 85.614 ms | +4.783 ms |
| Ordered encode CPU | 43.539 ms | 45.009 ms | +1.470 ms |
| Minor process faults | 32,444.5 | 36,251 | +3,806.5 |
| Major process faults | 0 | 0 | unchanged |

The FRESH/FRESH label sham was +0.639 ms (+0.497%) wall and +0.804 ms (+0.512%) CPU, within both preregistered bounds. Both reversed-order experiment groups retained positive >3 ms CPU and wall differences. As a result, this *individual execution* returned **`NON_ENCODE_STAGE_BURDEN_SUPPORTED`**. Encoded work accounted for **20.30%** of the aggregate median process-CPU delta rather than >=60%.

Its physical independent verifier checked the full 16,793,243-byte archived CMPCT file, index/footer exact framing and hashes, and every one of **123 contiguous CMA4 physical records** (64 RAW, 59 Zstd), requiring full decoded lengths, CRC32 and SHA-256. It reported archive SHA-256 `f00e7b90cc165da40ae88a1cf24d539a6f075952a14f130679ee770087fca5bb`, index SHA-256 `be6074e2efed19c91387adeccae0c48dcda593491b1755c329f3945a70f365b7`, total decoded 32,243,712 bytes, identical native library source SHA to the first attempt. No product source edits occurred between attempts; external auditing also separately reproduced these facts.

### Combined two-attempt decision, deliberately narrower than the second success

- **H1 encode-dominant CPU theory** was not supported in either attempt (25.52%, 20.30% of aggregate median delta); it is **falsified within this experimental frame**.
- **H2 non-encode/scanning** is a *plausible owner family*: scan CPU increased +6.501 ms in attempt 1 and +4.783 ms in attempt 2; minor faults rose by roughly 3.8k in both. However the first run **failed the preregistered FRESH/FRESH sham absolute veto**, so the strict H2 decision **does not replicate**. The scientifically valid cross-attempt claim is **directional evidence, owner not decisively established**.
- The first and second provider environments differed substantially: FRESH median wall 194.373 versus 130.058 ms; instrumented absolute numbers and raw file metadata cannot be treated as identical across providers. Differences are not evidence of improved product throughput.
- Do **not** retune the sham rule, ignore contradictory evidence or declare that scan or page-fault changes caused the two historical #807 candidate/base release-gate reds. Those failures remain binding.
- At this point the same research family has yielded useful negative knowledge but diminishing decision leverage. **Retire short prefix-treatment variants;** investigate a materially different full-harness chronology/provenance gate frame or an independently owned correctness productization boundary. Do not spend another hosted run solely to make a favored phase decision green.

**Counterfactual discriminator:** The FRESH/FRESH sham absolute cutoff immediately distinguishes the first run from the second; the independent second attempt prevents overclaiming a unique non-encode cause. No new global Discovery Engine policy change is earned. The present final documentation HEAD is a later *documentation-only* change: it has not changed either result-bearing science SHA or their physical evidence.

**CI caveat:** The two J24I55 specialized execution heads were SUCCESS, and the second additionally executed full independent CMA4 physical verification. Separate generic Engineering Evidence / General Tests on the latest documentation HEAD require their own exact-head check and must not be inferred from these earlier results.


## Cross-provider physical output control (independent third-root inspection)

I separately decoded the two original retained archive files from the *two* hosted ZIPs outside CMPCT. Their 16,790,693-byte **encoded CMA4 payload sections are byte-for-byte identical**, SHA-256 `0edfbe167875b075d922cbd8e9ce5b2e0a6b6cac3461926f870975cdb1193342`, despite whole-archive sizes of 16,793,315 versus 16,793,243 bytes. Both decoded MessagePack indices have identical file kinds, modes, sizes, content hashes, storage references, blob tables, recipes, fsmeta and features; **only two original source nanosecond mtime fields differ** across providers. Both decoded indices and corresponding physical archive SHA differ legitimately as a result. This is **payload identity, not full archive identity** and does not justify a cross-provider exact metadata parity or benchmark performance claim. The source-generating benchmark uses the same inputs inside each attempt but metadata is not normalized across different hosted attempts.
