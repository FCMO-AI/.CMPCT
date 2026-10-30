# J24I52 — Native Zstd codec boundary versus r24 binary-create release red (preregistered)

Date: 2026-10-30 UTC. Classification: research/causal attribution only. Parent exact source: `0b80ecb9b1742a6c20756f4c9e8e097103881cb4` (PR #807). Direct comparison source: `f456370e75b71a619104f9e9bb6c622929ba8db8` (PR #803).

## Problem / measured baseline

The unchanged official r24 ZIP gate failed twice on the same #807 commit: run #41010383696's physical artifacts `12958091919` and `12959912309` report binary/library/create 171.668→199.447 ms (+16.18%) and 141.103→161.638 ms (+14.55%). Base/candidate complete `src/` trees are unchanged across the exact comparison; only native `cmpct-core` API/library and tests/workflows/docs changed (verified by GitHub compare). The source-identical full-harness A/A PR #715 previously produced gate-scale false red (+7.35% binary, +6.02% combined), so repeated official reds may not identify causal code by themselves. **Both official reds remain promotion blockers until direct-base official evidence closes them.**

## Primary falsifiable question

Can an intrinsic performance difference between the *two actual separately packaged native Rust codec libraries* explain the r24 `binary/library/create_s_median` slowdown, under identical Python caller, equal input buffers, equal Zstd level, balanced ABBA/BAAB order, and fully charged output equality?

H1 (native ABI/codegen explanation): candidate `cmpct_codec_zstd_compress` has a repeatable large slowdown relative to the base native library on representative 256 KiB to 2 MiB chunks from the same deterministic public binary corpus. H0: the native primitive does not reproduce a meaningful candidate slowdown, narrowing this mechanism but leaving the official release red intact.

## Controls / competitors / alternative explanation

- Stronger simple control: **same process, same exact Python ctypes caller**, two independently built, SHA-attested native libraries; no Builder, filesystem scan, output publication or different Python module source in the timed region. An A/A label/order placebo from one library estimates scheduling/caller drift.
- Alternative: candidate worktree/path/import and cumulative harness/runner/cache factors cause the full-corpus effect; the native primitive can be neutral even when the original benchmark is genuinely red.
- Prior-art boundary: PRs #238, #711 and #715 already ran A/A and source-pair attribution on *other* commits. Do not repeat their full harness. This experiment targets a new Rust-ABI codegen/codec boundary introduced by #807.
- The baseline and candidate share unchanged `src/cmpct/builder.py`, `codec.py`, `native_codec.py`, `benchmarks/zip_parity_bench.py`; avoid inventing a Python Builder code-change mechanism.

## Prospective experimental contract

1. Build candidate native package from exact #807 head and separate base worktree native wheel from #803 source using existing materialization tool.
2. Derive deterministic binary random16m and pattern32m bytes from `benchmarks/universal_bench.py` with the same PRNG ordering as `make_corpora()`. Use bounded representative fixed slices (256 KiB/512 KiB/1 MiB) of random/pattern payload and levels 3/5. **These are primitive-level samples, not a claim that the Builder's CDC distribution matches the chosen slices**.
3. Require distinct exact native libraries and record file bytes/SHA, origin Git SHAs, input SHA, native ABI binding, Python host/environment, raw repeated wall+CPU, Zstd output SHA and bytes. Reject candidate/base output differences or any error.
4. Interleave ABBA and BAAB sequences, with warmups, no process startup in timed spans and a same-library sham; compute robust per-arm medians and report the raw repeats.
5. If the candidate is materially slower at both levels and the same-library sham is not, advance a native-codegen explanation for a future full-context profiler. If neutral, **narrow native primitive** and prioritize caller/import/cache/runner chronology. If sham also swings or bytes diverge, classify as ambiguous or invalid; never repair the result by changing samples/thresholds after observing it.

## Kill/narrow, evidence ladder, bounds

This is a lower-rung codec oracle. Its evidence cannot clear a release gate, prove whole-Builder timing, infer memory peak of the product, or earn release/public performance credit. The earliest decisive discriminator is direct primitive A/B; do not buy another 45-minute full matrix or rewrite the native core before it.

Admission is non-promotional. Correctness, physical archive formats, release thresholds, historical evidence, ABI semantics and corpus contents are immutable. Product byte+CPU+wall, RSS, temp I/O, portability, recovery and malicious inputs remain separate obligations.

Expected artifact: `j24i52-native-codec-court-<HEAD>` containing physical JSON of all trials and SHA-attested candidate/base library identity. The decision remains UNLOCKED until hosted exact-head execution is inspected. Do not update shared `docs/discovery/STATE.json` for an unmeasured hypothesis.

## Counterfactual / future leverage

If this primitive had been measured immediately after the first #807 red, a neutral result could have ruled out a new native compression-speed owner without inventing causal claims about identical Python source. Prospectively applicable to future ABI-only additions causing Builder benchmark reds; the result alone cannot justify a Discovery Engine policy mutation.
