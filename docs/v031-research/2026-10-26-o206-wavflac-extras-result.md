# O206 — Installed WAVFLAC enabled-audio acceptance: three-host positive result

**Date:** 2026-10-26 UTC. **Status:** research/evidence ACCEPTED on exact result-bearing HEAD, **not** integrated product/release authority.

**PR:** [#545](https://github.com/FCMO-AI/.CMPCT/pull/545) (evidence-only child of prior O204 [#541](https://github.com/FCMO-AI/.CMPCT/pull/541), itself child of WAV source-owner [#225](https://github.com/FCMO-AI/.CMPCT/pull/225)). **Released checkpoint:** v0.30.0 / format revision 24 unchanged. **Scientific preregistration was committed first:** `72d56367eb028f3367525843ce62b380d6183b71`; instrument commit `5a81238a669d7dd94c6c0bba24bdcd37d0b54281`, workflow commit `d94dab8819b7733af77c2f22422b1b7254affd79`.

## Primary question and scientific decision

O204/O204b proved #225 safely falls back when either **NumPy** or **SoundFile** is missing on all three major desktop OS hosts. They did **not** establish the other half of the optional-codec contract: when both extras **are installed**, do existing supported PCM16 WAVFLAC payloads still compress and reconstruct exactly, and can the Reader open a frozen independently constructed r24 codec-2 archive?

**Decision: `O206_SUPPORTED_WAVFLAC_EXTRAS_COMPATIBLE` in three hosted environments.** [GitHub Actions run #40404780837](https://github.com/FCMO-AI/.CMPCT/actions/runs/40404780837) on exact HEAD `d94dab8819b7733af77c2f22422b1b7254affd79` finished **3/3 SUCCESS** (Ubuntu 24.04, macOS 14 ARM64, Windows 2022). Each installed real package-owned native core and declared `.[audio]` Python extras. This is evidence for an **unmerged** existing codec fix; O206 did not change `src/`, `native/`, tests, source/format contracts or release thresholds.

## Exact-source control and frozen independent vector

Historical pre-fix codec Git blob `29526db4203723d83523fc95d074c346b63d7587` was materialized from canonical development commit `4545d7d5b2a0b712b4b00f5a9c291d4a3a9e169b`; already-existing owner candidate codec blob `6e116ee1fc348b78d81a541fcaf5cf3d6912d3c4` was resolved from the exact O206 Git tree. Baseline/candidate package trees were byte-identical apart from this codec file and used the same compiled native extension and process dependency environment. Direct codec comparison used **both real unmodified implementations**; no mocks.

The pre-existing **Builder-independent** revision-24 archive `tests/conformance/v24-wavflac.json` met all its immutable claims on every host:

- Whole physical archive: **541 B**, SHA-256 `6fb51d28f74346239c8a99a3ea76eb9fd7d307d03f91a609c92b528f112b8956`.
- Reconstructed WAV logical member: **108 B**, SHA-256 `29f685e2326c29a164f164c35bad830b3340b0b8e3ad0e29b57463481ae9ef83`.
- Exact 31 B known range at offset 41: PASS; frozen range SHA-256 `6b531336d13823c5539a6598e5275251d29b1444b2b8ffa7b79b19ccc5651ad2`.
- Real `cmpct preflight`, `verify`, `cat` and `range`: PASS.
- Hostile mutation of the independent archive's physical blob-header SHA-256: **rejected** on every host; silent acceptance would have invalidated the experiment.

## Supported PCM16 and complete real CLI A/B

Two eligible synthetic PCM16 WAV inputs (mono 2,048 frames and stereo 4,096 frames) were directly passed to both authentic codecs with audio extras available. **Actual FLAC streams were produced, and historical vs candidate streams and MessagePack reconstruction metadata were byte-identical on every host**. Both decoded to exact original WAV data.

| Supported WAV | FLAC payload B | FLAC payload SHA-256 | Decoded logical WAV SHA-256 |
|---|---:|---|---|
| mono.wav | 3,117 | `38ca761adad70b573fd06513645514f79fcc71c6c47a58b3d1355619cade1fe6` | `79ef6979b16e3d1483f71efa9c4a2ffb225eb68b7ae2ca3f3eace727c3724830` |
| stereo.wav | 12,603 | `0d999d515a0c375755d42492c48a4686b6a787b20f40382` | `3950adafaa3d28ae7c1dfaf0ac696ef615a3ee6d0f0e716be5005fe534a7d84f` |

**Builder was not forced to choose FLAC. It genuinely selected codec list `[1,2,2]`** for the sorted ordinary binary, mono WAV and stereo WAV blobs. Complete supported three-file r24 archive was **17,206 B on all three hosts**. Same-host historical/candidate complete archive bytes were identical; verify/preflight/read/range/all source SHA all passed.

Unsupported PCM32 WAV: candidate `wavflac_compress` returned `None` as required; real Builder emitted 2,446 B r24 archive using a RAW blob, and the resulting **1,576 B logical WAV** reconstructed with SHA-256 `d35024b2f2f11763c9742a0968a1d6679e496bbfc412e36c4e674d634079f5c1` on all three hosts. PCM32 is not claimed to encode as FLAC.

## Cross-host physical SHA limitation — preserve, do not silently normalize

For the **identical logical** supported three-file corpus, Linux/macOS complete archive SHA `9c565bb8db33b29c78d80dafca3d13dca224113e26b527f9524eae3aadac1259` differed from Windows `10014e6c444a65e0a2fe53355b20d6fa394cdf28c9420da26d789b7f268be7b8`, despite equal **17,206 B** size, all content SHAs, FLAC payload SHAs and metadata SHAs. The authenticated file-index modes were **420 (0o644)** on POSIX and **438 (0o666)** on Windows for each generated member. This is observed host metadata difference; a formal byte-difference causal replay is not attempted here. Strong prior research PR #372 O14 already identified file-mode normalization as sufficient to explain a different cross-host reproducible-mode SHA discrepancy. Do not create a second mode research claim or claim universal full-archive cross-host byte identity.

## Hosted artifacts and evidence continuity

The source-exact positive scientific court has per-host structured JSON uploaded to [Actions #40404780837](https://github.com/FCMO-AI/.CMPCT/actions/runs/40404780837):

- Ubuntu: [artifact #12689888155](https://github.com/FCMO-AI/.CMPCT/actions/runs/40404780837/artifacts/12689888155)
- macOS: [artifact #12689878216](https://github.com/FCMO-AI/.CMPCT/actions/runs/40404780837/artifacts/12689878216)
- Windows: [artifact #12690147356](https://github.com/FCMO-AI/.CMPCT/actions/runs/40404780837/artifacts/12690147356)

The court emits `O206_SUPPORTED_WAVFLAC_EXTRAS_COMPATIBLE` only after all the prospective checks. It is an exact **result-bearing HEAD** acceptance. Future documentation-only HEADs still require their own distinct CI status; do not retroactively green them.

## CI topology/evidence initial failure and correction

First result-bearing PR HEAD `d94dab8` had **Engineering Evidence FAIL** because its PR body omitted headings required by `tools/check_pr_evidence.py`, and **CI Topology FAIL** because new workflow omitted explicit `# ci-lane: ...`. Both are documented workflow/metadata errors, not failed scientific tests. The PR body has subsequently been populated with *concrete* section evidence. Workflow classification was corrected to `# ci-lane: deep` in `e0a12638d93866ba0b24432f2c3098cd95b3ce00` with no changes to the scientific instrument or acceptance. At the time of this note, **the final exact-head status is not presumed green**.

## Scientific disposition / BONK / next decision

**Advanced:** positive opt-in WAVFLAC create and decode compatibility in the three installed OS hosts with actual codec-2 selection and frozen independent vector. **Retired as redundant:** additional absent-extras replicates (O204/O204b already complete) and another cross-host mode normalization experiment (O14 prior art). **Not established:** real full-system CPU/wall/RSS and 15-workload parity, exhaustive WAV input coverage, historical legacy WAVEFLAC decoder behavior in an environment without installed extras, and universal cross-platform physical SHA convergence. No discovery-policy amendment and no `docs/discovery/STATE.json` update.

**Counterfactual:** The independent frozen codec-2 vector plus two direct eligible WAV samples and a same-host full-archive A/B was sufficient to decide whether early WAV capability admission broke the positive codec path; a broad fresh media corpus was not necessary. This single episode does not earn an RDE policy change.

**Next highest-leverage action:** owner #225 should adopt these positive-extras results alongside #541 missing-extras evidence, then reconcile the unchanged full general tests, conformance, parity, portability and release gates before any merge or version promotion. The existing product implementation is the sole code owner; O206 remains evidence-only. No release claimed.
