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
