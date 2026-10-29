# J24I39 — hosted file-backed Claxon single-pass WAV logical digest oracle: scoped positive

**Observed 2026-10-29 UTC / RESEARCH-ONLY / NO NATIVE PRODUCT FIX, MERGE OR RELEASE.**
The scientific source is draft PR [#776](https://github.com/FCMO-AI/.CMPCT/pull/776), stacked on authentic Builder WAV #774 exact `793da74881e5180d982df29d2ef08bacbe6d7933`, ultimately unreleased native #765/#759. Shipped `main@80c358f8824ec1b20d349c92ed94c898090969b0` remains v0.30.0/r24. Preregistration at `4e6ec6da25fdd9c703ec140254b5d3b5b0b7b285` predates all implementation and measurements. First result-bearing HEAD: `9c5ed1da6fb30fde5d5b4e010cabe780710202df`. Do not attribute its measurements to a later HEAD merely because the research files are unchanged.

## Strongest directly observed result

[GitHub Actions #40933414714](https://github.com/FCMO-AI/.CMPCT/actions/runs/40933414714), Ubuntu 24.04, job `123657530534`, **SUCCESS with every actual step executed**. Physical source WAVs/archives constructed by **unchanged canonical Builder**; actual direct codec2 admission; J24I38 detached, no-CMPCT libsndfile audit PASS on both; exact SHA/CRC/encoded byte counts verified; source pins for Builder, codec, Rust Reader, WAV decoder, and J24I38 instruments PASSED. Research Rust code compiled from disposable `src/bin` copy with pinned crate source. The standalone Claxon iterator opened the split physical FLAC from a `File`, appended canonical codec2 prefix / PCM16 little-endian / suffix in order to fixed 64KiB digest chunks, and authenticated every logical byte against original physical CMA4 SHA-256 and CRC32.

Original GitHub artifact `12922588827`, [workflow artifact](https://github.com/FCMO-AI/.CMPCT/actions/runs/40933414714/artifacts/12922588827), original provider zip SHA-256 `4b2925fcfbf7b52d65749b013cf9d6240370bf74f38fee6af3d4f1e1dfec01db`, includes physical archives, FLAC/meta splits, independent audit, raw process observations and result JSON; 30-day retention. Durable repository mirror [64 original source-logged observations and independent recalculation](../../research/j24i39/hosted_raw_recalculation.json). 16 warmups + 48 post-warmup timings, 12 measured observations per arm/size; ABBA/BAAB.

| Genuine Builder WAV | Native complete A median | File-backed stream B median | A/B time | A/B rchar | A VmHWM | B VmHWM |
|---|---:|---:|---:|---:|---:|---:|
| 8 MiB PCM + 44 B | 132.359 ms | 56.190 ms | **2.356x** | **2.000x** | 22,956 KiB | 2,828 KiB |
| 32 MiB PCM + 44 B | 1,290.317 ms | 224.541 ms | **5.746x** | **5.000x** | 59,148 KiB | 2,852 KiB |

32MiB source exact physical SHA-256 `cf4a826209b3ffff0af86c765db28068386c8f95e6c1405ee29099113b88baa9`; physical FLAC SHA-256 `5ec89972e360c75f70e1bee6ea3019e1b4ae5adb493e67296b5df4c0e1f09e99`, logical WAV SHA-256 `2a1506d7f895c3035301ef466b3213d1ac71423e1efc879a161ab28a33917b2e`; CRC32 1005983092; exact 33,554,476 logical bytes. 8MiB original SHA `9250964815f67891c3e106c9d87aadc67d4f2c3dce8b3e4e1873813a13a6fac7`.

## Scientific decision and proof boundary

**Supported at O0/O1:** File-backed Claxon can reconstruct and calculate the exact *logical* prefix/PCM/suffix identity of these two authentic codec2 representations in one iterator pass without allocating the full WAV or FLAC to a Vec in the new instrument. The observed total-process B VmHWM 2.8MiB strongly favors this framing over native A's 59MiB for 32MiB. The fast B excludes archive source authentication/preflight, so 5.746x is **NOT a product speedup**, and 2.8MiB is NOT a general memory bound: Claxon internal state, metadata length, source mutation, and hostile frames remain untested. Linux `rchar` is process read characters, not disk sectors. The native original code continues unchanged.

**Contradiction/negative:** earlier optimistic full-buffer #774 one-shot B had approximately +24MiB RSS versus the verifier; this *different* file-backed iterator B does not, because neither the compressed nor uncompressed WAV is fully materialized. Both B mechanisms decode the same signed logical WAV but differ in input ownership, trust boundary, and memory costs. Do not compare a partial standalone decode against complete archive validation as though same-semantic; any production candidate must preserve the stronger contract.

## The next cheapest decisive falsifier

**Encoded tail / full-frame consumption:** the current Claxon `samples()` iteration proves decoded PCM and length but does not itself show the entire compressed stream was consumed nor that invalid/concatenated/trailing FLAC bytes are rejected. Local non-GitHub comparison on 2026-10-29 showed the reference `flac -t` rejected 21 trailing arbitrary bytes after an otherwise valid PCM16 FLAC (LOST_SYNC) while libsndfile accepted the decoded sample count; *this external reference is not a Claxon result nor evidence about a CMPCT-signed archive*. The cheapest important follow-up is an **exact compiled-Claxon hostile tail court** with valid, appended-garbage, truncated, and concatenated FLAC controls from the same builder-authentic data, preserving the raw outcome even if Claxon accepts. Then design a bounded full encoded-stream consumption check before Native Core productization.

Secondary hard gates: prefix/suffix/resource caps; full index/header/CMA4/CRC custody in original file descriptor; no extra open/race; frame CRC/length; signed mutation tests; Python C-ABI cross-host parity; CPU/wall/RSS on full product; recovery and release parity. Native product ownership remains #765/#759 and this research branch does not claim it. No Discovery Engine global policy change: a single measured positive plus external-frame warning does not justify process rewriting.

## Counterfactual and research economics

Before product rewrite, a file-backed 64KiB digest sink over the already shipped Claxon dependency was a cheap enough oracle to distinguish expensive full-WAV reconstruction from truly progressive logical identity. Because source-open and trust-boundary responsibilities remain unresolved, the reusable lesson is *prove progressive codec semantics before proposing full archive verifier replacement*, not *streaming is safely solved*. No `docs/discovery/STATE.json` update (stale cache and no global decision-state transition).
