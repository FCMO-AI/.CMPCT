# J24P12 — PCM predictive-Zstd without FLAC dependencies: a negative generality result

Date: 2026-10-31  
Status: **RESEARCH O0 — GENERAL FIXED-PREDICTOR FAMILY RETIRED / NO PRODUCT CREDIT**  
Authority: [source-first issue #872](https://github.com/FCMO-AI/.CMPCT/issues/872); prior empirical driver [#849](https://github.com/FCMO-AI/.CMPCT/pull/849); WAV capability owner [#225](https://github.com/FCMO-AI/.CMPCT/pull/225).  
Released baseline: `main@80c358f8824ec1b20d349c92ed94c898090969b0`, CMPCT v0.30.0, revision 24. This branch does **not** update Reader, Writer, codec policy, format, dependencies, release tests or Discovery state.

## Why this was tested

A missing `numpy`/`soundfile` dependency causes current WAV compression to fail; a naïve graceful skip loses 270.93% archive bytes on a deterministic chirp, 49.35% on noisy three-tone, and 62.17% on a correlated random walk against the present FLAC-backed canonical encoding (J24P11 [#849 comments](https://github.com/FCMO-AI/.CMPCT/pull/849)). Can a cheap statically reversible predictor and universal Zstd substitute without exporting bytes or unacceptable CPU?

The initial single-host O0, **preregistered before results** in #872, froze three J24P11 WAV source families, a random stereo hostile control, and simple order-1/2, modular 16-bit residuals with ZigZag and optional byte-plane separation. Charge preserved 44-byte WAV header, one method selector, all Zstd payload bytes, and separate encode/decode work. Strongest simple control = **minimum of entire WAV Zstd-9 and byte-plane Zstd-9**; mature specialized control = SoundFile FLAC.

## O0 initial favorable ceiling, narrower than it looks

| PCM16 source | Strong Zstd control | Best fixed transform | Actual FLAC-level-1 + header | Fixed vs strong | Fixed vs FLAC |
|---|---:|---:|---:|---:|---:|
| Chirp | 125,018 B | 70,989 B | 32,939 B | -43.22% | **+115.52%** |
| Three-tone/jitter | 125,324 B | 99,008 B | 83,613 B | -21.00% | +18.41% |
| Correlated random walk | 77,920 B | 64,102 B | 65,053 B | -17.73% | -1.46% |

The precommitted 3-input O0 gate (>=10% stronger-control win in >=2/3 and <=20% larger than FLAC in >=2/3) passes. **This is a gifted decoder/format O0, not a CMPCT product.** A separate direct Zstd fallback wins noisy/incompressible sources. The first version of the SoundFile comparator inadvertently used default compression settings, unlike shipping `cmpct/codec.py` which uses `compression_level=1.0`; the table above is the **corrected stronger shipping-level control on the same exact WAV sources and method family**. The earlier false encode-time field included decode time; v2 subsequently separated these without altering byte outcomes. No prior numbers were erased.

## Native execution hypothesis and correctness

The exact small C candidate is preserved at [research/j24p12_pcm_transform_native.c](../../research/j24p12_pcm_transform_native.c), SHA-256 `863a6f7f31b7796cd01d8eaf5b0e2d8e162cca0e8de43ce9df47d0edf04ff722`. It is **not** linked, imported or used by CMPCT. An independent Python reference agreed byte-for-byte on 30/30 cases (five frozen waveforms × order0/1/2 × normal/plane). Original compiled C compared 60–144× favorably against **unoptimized Python**, which proves only an implementation issue, not superiority to FLAC.

The source-level sanitized oracle `research/j24p12_pcm_transform_sanitizer_court.c` produced **3,696/3,696** random exact reversible tests across one to eight channels and multiple lengths, including zero-length, with 32-byte canaries, rejecting malformed arguments. Verified locally under both GCC and Clang `-fsanitize=address,undefined` with no report; not yet measured on macOS/Windows.

Reproduce bounded C test on Linux with Clang or GCC:

```sh
cc -std=c11 -O1 -g -Wall -Wextra -Werror -fsanitize=address,undefined \
  -fno-omit-frame-pointer research/j24p12_pcm_transform_native.c \
  research/j24p12_pcm_transform_sanitizer_court.c -o /tmp/j24p12-court
ASAN_OPTIONS=detect_leaks=1 /tmp/j24p12-court
```

This does not reproduce stored-byte/FLAC outcomes; those require the full bounded oracle and waveform generation. Their raw receipts and complete scripts are preserved in activation evidence, with the decisive scalar outcomes repeated in issue #872. Do not treat this C test as an archive, ABI, packaging or source-provenance validator.

## Prospectively held-out structural transfer: **FAIL**

Before the trial, nine new morphologies and seed `20261101` were frozen in [#872](https://github.com/FCMO-AI/.CMPCT/issues/872#issuecomment-6537127848). Existing six methods, strongest control and FLAC-level-1 stayed fixed. Passing required **both** >5% complete-byte improvement over the stronger of ordinary and byte-plane Zstd on >=5/9, **and** within 20% of FLAC on >=4/9. All exact reconstructions succeeded; only **4/9** beat the stronger control by >5%, therefore the preregistered broad-family claim **failed** (FLAC closeness on 9/9 does not rescue it).

| Family | Transform bytes | Strong control bytes | Gain vs control |
|---|---:|---:|---:|
| Ramp/clipping | 89 | 658 | +86.47% |
| Pulses | 74 | 71 | -4.23% |
| Sparse impulses | 1,626 | 1,065 | -52.68% |
| Independent stereo tones | 16,050 | 18,298 | +12.29% |
| Correlated stereo | 121,542 | 125,371 | +3.05% |
| Amplitude steps | 989 | 1,631 | +39.36% |
| Low-bit precision | 73,883 | 68,572 | -7.75% |
| Noise-modulated signal | 181,651 | 192,059 | +5.42% |
| Blockwise DC changes | 418 | 354 | -18.08% |

The *unweighted* 4/9 cardinality is not a compression benchmark of heterogeneous archive trees, and spectacular favorable small-byte cases cannot replace generic admission with explicit fallback.

## CPU and exported cost

One Linux host, 45 warm repetitions each on identical in-memory WAVs; sources and emitted bytes SHA-verified. Medians are process-local and **posthoc best-method native C+Zstd**, not fully charged winner discovery:

| Original waveform | Native C+Zstd-9 encode | SoundFile FLAC level 1 encode | Direct Zstd encode |
|---|---:|---:|---:|
| Chirp | 1.150 ms | 1.370 ms | 0.224 ms |
| Three-tone | **1.863 ms** | **1.490 ms** | 0.204 ms |
| Random walk | 0.556 ms | 1.246 ms | 0.220 ms |

The six-way variant audition and admission cost are recorded separately, but not eliminated. Decoding medians are smaller for the native trial on this host; that does **not** provide full CMPCT extraction/verification evidence. Zstd was dynamically loaded through system `libzstd` (not stdlib), SoundFile invoked actual native libsndfile; dependencies, temporary PCM buffers, decoder ownership, full archive metadata, reader complexity and three-host packaging remain uncharged as products.

## Falsification and decision

An independent stdlib-only receipt referee accepted the complete original records, recalculated raw timing medians, SHA correlations and gain arithmetic, and rejected **12/12** deliberate receipt mutations. A passing receipt referee is not a second independent implementation of Zstd/FLAC/native PCM, and cannot validate the first party's experiment beyond its recorded evidence.

**Decision: retire the universal fixed delta1/delta2+planes replacement family.** Keep narrowly promising transformations as evidence only; no new variant/threshold gardening after the held-out loss. #849's explicit base dependency policy remains a legitimate option pending a genuinely different generic codec/admission mechanism that meets strong same-input FLAC and full-system economics. A future re-opening needs a prospectively recognizable content predicate, substantially different entropy/ownership mechanism, correct PCM16/other WAV chunk semantics, independent native/format conformance, full archive size/create/extract/RSS, Windows/macOS controls and zero change to the baseline correctness/release gates. The strongest simpler default is allowed to win.

**Concurrency and governance:** no shared state, Discovery policy, other owner implementation, comparator, performance gate or release version was touched; source and local research diagnostics deliberately live in a separate draft. Re-review against current Git before any later proposed product integration.
