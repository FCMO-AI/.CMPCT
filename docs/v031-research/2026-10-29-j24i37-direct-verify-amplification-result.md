# J24I37 — Source-exact native complete-verification amplification: decisive research result

**Decision:** `SOURCE_MECHANISM_SUPPORTED` for a valid, directly Zstd-compressed revision-24 single-member archive of 8/32/64 MiB. **No product/release performance credit; no native product code, format, conformance vector or comparator changed.**

## Immutable prospective custody
- Preregistered before implementation: `d81425491af331381de357f09ff03a52ecfda938`, `docs/v031-research/2026-10-29-j24i37-direct-verify-amplification-prereg.md`.
- Research branch: `agent/phased3-v031-j24i37-direct-verify-amplification-20261029`, [PR #772](https://github.com/FCMO-AI/.CMPCT/pull/772), stacked on existing #765 native CRC branch exact product source `9ef1644d8c6129de4d7d8008bfdadad5fffcbe06` (itself stacked on #759).
- Exact hosted scientific implementation HEAD: **`1286300197793f1776c785d257cf0d0125ed52ce`**. [Completed Actions #40916036285](https://github.com/FCMO-AI/.CMPCT/actions/runs/40916036285), scientific job `research-amplification` **SUCCESS**.
- Original CI artifact: ID **`12915264466`**, [GitHub ZIP](https://github.com/FCMO-AI/.CMPCT/actions/runs/40916036285/artifacts/12915264466); original ZIP SHA-256 (separately inspected): `22c8863af9bbe85cfe4cfe07f68a6cc2c4c58dfaa83a2f1c66687e75df5c8b7e`.
- Native Rust core and dispatcher source are unchanged from owner #765: `native/cmpct-core/src/lib.rs` Git blob `46fa87930a9229f42233594816330f35f0505e71`, `native/cmpct-core/src/vzip_dispatch.rs` `27e4d7962ccfed6a822010383158d98e20d823dd`; frozen direct-codec golden Git blob `d10b7dab9126d39e819a74279c186363a163f2ef`. GitHub exact-head source pin step passed.
- Three original physically framed archives, Python installed verification and detached no-CMPCT physical auditor **PASS**, Rust release probe compiled and completed. Original corpus samples SHA-256/CRC, both indexes, CMA4 headers and footer preserved in artifact.
- An additional independent audit was run after downloading the original ZIP, using **a fresh Python parser calling system libzstd through ctypes**, msgpack, zlib and hashlib; it re-parsed and authenticated all three physical r24 archives *without importing CMPCT*, and independently recalculated all 96 raw observation lines and reported medians/ratios. It returned **INDEPENDENT_PASS**. Not a second host/independent CPU benchmark, only evidence verification.

## Exact original observations

One valid direct Zstd file per specimen. A = actual `Archive::verify_complete()` with 8-MiB logical output buffer; B = one full `read_range` plus separate SHA-256 and CRC32 on the same content. Eight interleaved outer lanes (ABBA/BAAB); one warmup + three measured iterations per lane = 12 real raw observations per arm, per size.

| Input logical size | Actual A median ms | Optimistic B median ms | A/B wall | A rchar | B rchar | A/B rchar | A VmHWM KiB | B VmHWM KiB |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 8 MiB | 16.503 | 16.987 | **0.972×** | 272,982 | 272,918 | **1.000×** | 21,626 | 21,620 |
| 32 MiB | 147.077 | 65.418 | **2.248×** | 1,226,611 | 306,710 | **3.999×** | 46,370 | 70,784 |
| 64 MiB | 539.733 | 127.181 | **4.244×** | 2,813,507 | 351,766 | **7.998×** | 79,122 | 136,390 |

The complete stored archives were **273,110 B**, **306,902 B**, and **351,958 B** for 8/32/64 MiB logical sizes, respectively. Their source/archive/content SHA-256 and CRC32 are in `manifest.json` and `detached-audit.json` within original artifact.

**Decision-changing scientific statement:** repeated direct-compressed full member decode and record read in `verify_complete` is measured, not merely hypothesized: ~4× and ~8× `rchar` scaling for 32 and 64 MiB respectively, with 2.25× and 4.24× extra verification wall compared with a strictly same-payload but high-RSS one-shot control. The 8-MiB case did not show a benefit, as prospectively predicted. **This is not a speedup of CMPCT**; current product A was slower than a research-only, larger-memory mechanism B.

## Losses, counterfactuals and bounded inference

- The B control **is not memory equivalent**: at 64 MiB Linux VmHWM was ~136,390 KiB vs ~79,122 KiB for A (about 57,268 KiB higher), because the one-shot path holds entire output. Neither VmHWM nor `rchar` is peak-only allocation or physical disk I/O; `rchar` is kernel character-read accounting including cache.
- Encoded bytes were deliberately repetitive deterministic-tile synthetic input. They prove an execution-architecture bottleneck within this valid r24 mechanism, not prevalence or win on arbitrary application archives. Ordinary large files commonly use CDC, and the direct-WAV exception needs a genuinely Builder-produced held-out test before product economics.
- The test does **not** establish safety of a future streaming decoder: preserve full SHA-256, CRC32, decoded length, physical compressed length and trailing bytes/frames, dictionary dependency, source descriptor custody, read_range admission, resource bounds, transaction/recovery semantics and Windows/macOS compatibility. Existing #765 CRC perf regression and unrelated native/package/fingerprint CI negatives remain.
- The cheapest earlier prospective discriminator was a small 8-vs-64 MiB A/B with actual physical `rchar`; source inspection alone predicted the repeated 8-MiB decode but could not earn product impact. Our measured 8-MiB control prevents falsely generalizing a speedup to small direct files.
- Two instrument-only CI failures were preserved: initial shallow checkout missing pinned base SHA ([#40915657913](https://github.com/FCMO-AI/.CMPCT/actions/runs/40915657913)) and then filename mismatch after successful generation/auditing/compile ([#40915785075](https://github.com/FCMO-AI/.CMPCT/actions/runs/40915785075)). Corrected only the source checkout and instrument path; neither evaluator nor data/threshold was weakened.

## Next executable decision
**Advance a separately preregistered bounded streaming direct-Zstd complete-verification candidate** on authentic source-bound r24 with pathological one-frame, concatenated/multi-frame, trailing garbage, truncated, CRC/SHA cross-identity, source-live-mutation and per-read corruption controls. Measure 8/32/64 MiB and real Builder-produced WAV/FLAC, CPU/wall/rchar/RSS/I/O, with A and a strong (RSS-equivalent) streaming oracle. If no broad Builder owner or if incremental streaming exports larger dependency/maintenance or integrity debt, retire it as a research finding and avoid adding code. Reconcile with owners #765/#759 and related-but-distinct packed-decode question #315.

**Policy:** Evidence teaches a local research prioritization lesson (profiling complete-work amplification beats further sub-2% header micro-optimizations on this direct family); it does not warrant changing the general Discovery Engine, `docs/discovery/STATE.json`, frozen benchmarks, release law, thresholds or version.
