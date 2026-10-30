# J24I52 — native-codec source-cost attribution, hosted and independently audited

**Date:** 2026-10-30 UTC. **Decision:** `NATIVE_CODEC_INTRINSIC_SLOWDOWN_NOT_REPRODUCED` for the measured same-process `cmpct_codec_zstd_compress` micro-batch. **Scientific/attribution evidence only — no product/release credit.** Experiment preregistered at `b9d31f2b003f2046ec67829c74ec5f10808eaf78` before implementation.

## Primary question, baseline and authority

The official unchanged r24 core/ZIP release gate on #807 (`0b80ecb9b1742a6c20756f4c9e8e097103881cb4`) against direct base #803 (`f456370e75b71a619104f9e9bb6c622929ba8db8`) failed twice on `binary/library/create_s_median`:

| Official original ABBA court | Base | Candidate | Difference | Parallel ZIP create negative control |
|---|---:|---:|---:|---:|
| [run 41010383696 / original artifact 12958091919](https://github.com/FCMO-AI/.CMPCT/actions/runs/41010383696) | 171.668 ms | 199.447 ms | **+16.18%, +27.779 ms** | 561.867→562.867 ms (+0.18%) |
| [same source / independent attempt / artifact 12959912309](https://github.com/FCMO-AI/.CMPCT/actions/runs/41010383696) | 141.103 ms | 161.638 ms | **+14.55%, +20.535 ms** | 441.528→441.150 ms (-0.09%) |

The two artifacts were physically downloaded and their frozen base-a/candidate-a/candidate-b/base-b JSON records independently aggregated. All eight-corpus CMPCT and ZIP stored bytes matched across arms. The `src/` tree, Builder, codec Python, and official benchmark harness are identical across this comparison; native `cmpct-core` includes the new verification ABI and changes ELF size/codegen surface. Historical #715 [source-identical, full-harness A/A result](https://github.com/FCMO-AI/.CMPCT/pull/715) independently reproduced a false red on identical code, so the official #807 failures must not be attributed to a particular source change by assumption.

## Experimental controls and two source-exact hosted runs

The lower-rung J24I52 court separately built both *real physical* native cdylibs, required byte-identical Zstd compression and complete decompression on five deterministic public binary samples, and measured balanced A/A and A/B using the same Python ctypes caller, same process, same host, CPU+wall raw repeats, with no Python Builder or archive publication in the timed region. Distinct binary SHA-256:

- Base: `facc5c3872d0dff80dfbda78633b4bdcf30729fa40bca448ebf4c9f4cb1a08fd`
- Candidate: `591495782dc316e820216a1b7f3806aa33361c25dfed816682cda0fd2d8d2a33`

1. **First hosted run** [41022008838](https://github.com/FCMO-AI/.CMPCT/actions/runs/41022008838), artifact [12962027354](https://github.com/FCMO-AI/.CMPCT/actions/runs/41022008838/artifacts/12962027354), HEAD `0b290d8f5b70042c22921d2dfd2ab2da5fc435a7`: SUCCESS as a receipt but timing window **included receipt SHA hashing** after compression. A/A labeled difference +1.7546%; A/B source difference +0.9534%. These numbers are **confounded for intrinsic native-codec inference**; retained, not promoted.
2. **Corrected hosted run** [41022363545](https://github.com/FCMO-AI/.CMPCT/actions/runs/41022363545), artifact [12962715600](https://github.com/FCMO-AI/.CMPCT/actions/runs/41022363545/artifacts/12962715600), exact HEAD `2d0740b3545db7a7bfde03580106f4a46e52881b`: SUCCESS. Output SHA computation moved *after* the timed native compress/FFI/copy interval; every byte assertion and negative control retained. Native libraries identical to first run.

| Corrected same-host court, per-arm median of eight 7-repeat invocation medians | Label A | Label B | Difference |
|---|---:|---:|---:|
| Source-identical A/A | 0.5440005 ms | 0.5455285 ms | **+0.2809%, +0.001528 ms** |
| Source-exact base/candidate A/B | 0.5421435 ms | 0.5416025 ms | **-0.0998%, -0.000541 ms** |

CPU-median ratios: A/A 1.002684; A/B 0.998964. Each court contains 16 invocations × 7 original samples = **112 timed samples**, with four balanced ABBA/BAAB groups, not 112 independent product observations. Both native libs produced identical compressed bytes, five independent exact PCM/RAW roundtrips, and stable SHA-256 identities.

**Independent detached artifact audit:** verified ZIP integrity, exact evidence head, physical SHA-256 of both native binaries, reconstructed the complete public PRNG input sequence from Python stdlib only, independently reproduced all five codec compressed output SHA-256 digests and decompressed bytes by direct ctypes calls into *both saved physical libraries*, verified all 224 corrected wall/CPU time records and recomputed the summary medians. Physical ZIP SHA-256: `59bd17936bb9a1ce289b2d87bc9acb97592127a2fbbee2c398b1a0f105c61bf8`. Source SHA, archive, binary payloads and raw observations agree.

## Decision, strongest negative and boundary

The candidate's separately built native Zstd compression primitive is **not measurably slower** than the base on the sampled deterministic 256 KiB–1 MiB binary chunks, levels 3/5, and same-process ctypes execution. The `+14.55%/+16.18%` full-Builder signal is orders of magnitude larger than the `-0.10%` native-court difference. Thus **do not spend the next intervention rewriting the Rust Zstd compressor or attributing the release red to the new verification ABI's native codec codegen without new evidence**.

This **does not prove** that the official #807 red is a false positive. The court does not reproduce actual Builder CDC chunk topology, 32/16MiB filesystem IO, Python process import lifetime, full corpus execution order, native library startup, memory peaks, system cache chronology, or the official process/metadata semantics. Benchmark clock levels and runner environments differ; no cross-run direct numerical subtraction is valid beyond within-court ratios. The native codec court is evidence tier `micro/A-B`, not final-product proof.

The unchanged official red remains a **release/promotion blocker**. With the current mechanism narrowed, the cheapest next unclaimed discriminator is an exact-host, same-corpus **full Builder-context phase profiler / A/A chronology control** (filesystem scan, CDC/chunk count, native calls and output publication) under fixed native/source ownership, rather than a third blind full-matrix rerun. Coordinate with #807 owner and inherited #715/other A/A agents before implementation.

## External controls, concurrency and process lessons

- Previous controls: #238, #711 and #715 own other exact-source A/A and full-harness false-red evidence; no duplicated production/benchmark implementation.
- Other current agent PRs #814 journal replay and #574 Discovery STATE reconciliation own different lanes; no conflicting shared file edit.
- No change to `src/`, `native/`, format, ABI, r24/ZIP official gate, comparison thresholds, frozen corpora, history, project version or benchmark policy. No merge/release.
- Counterfactual: a direct native FFI codec comparison before a new Builder rewrite would have eliminated one possible causal explanation at low cost. This single result does **not** justify updating Discovery Engine policy or its staleable `STATE.json`; detailed evidence stays here and in GitHub artifacts.
