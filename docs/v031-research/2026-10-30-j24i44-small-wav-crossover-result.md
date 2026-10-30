# J24I44 — authentic small WAV native product verification crossover court

**Measured 2026-10-30 UTC.** Prospective preregistration commit `2f39dabd00e789137ec508c69983d445928f48ee`, **before** the generator, auditor, A/B probe or workflow existed. Candidate is **unmerged** #788; not a release, general codec theorem or end-to-end archive performance claim.

## Source and physical custody

- Repository: `FCMO-AI/.CMPCT`; PR [#788](https://github.com/FCMO-AI/.CMPCT/pull/788); candidate **exact source HEAD** `ff203b5ee2095d7e44b1ce64dac14d3523a75f7f`.
- Installed/native A baseline: exact #784 commit `0faa25827e7393f927252876d40e9f6cb53e5a24`.
- Installed/native B candidate: exact #788 commit above. Both were independently built in Rust release mode, each executing actual `cmpct_core::Archive::verify_complete()`; same Builder-generated physical CMPCT archive given to each.
- [J24I44 GitHub Actions run #40982263846](https://github.com/FCMO-AI/.CMPCT/actions/runs/40982263846): **SUCCESS** on Ubuntu 24.04, original [evidence artifact #12944799530](https://github.com/FCMO-AI/.CMPCT/actions/runs/40982263846/artifacts/12944799530), SHA-256 `7f1b1bbf2f394756404d48d65b0cc7997da8e38528dade6cd523737d3cf2786d`, 20,461,951 bytes, 30-day retention. Includes physical Builder archive/source pairs, manifest SHA256, detached auditor, source pins, ABBA raw observations, recomputed summary and an inner .tar.gz receipt.
- **Builder was unchanged.** Six PCM16 mono 44.1kHz random-walk cases (seed 24144; PCM 64 KiB, 256 KiB, 1 MiB, 2 MiB, 4 MiB, 8 MiB, each WAV has 44 additional header bytes) all genuinely selected **direct codec-2 WAV/FLAC** without forcing representation. Python Reader verified each archive exactly. A separate auditor with **no CMPCT imports** validated physical r24 header, identical double index, footer, CMA4, decoded FLAC with libsndfile, logical SHA256, CRC32 and all bytes of original WAV for **6/6**.
- ABBA/BAAB process order A B B A B A A B; 12 `verify_complete()` calls per arm/size/process, first 4 discarded per process, **32 used observations per arm and size** = 384 post-warmup observations total (576 raw including warmups). Recomputed from raw job log and from retained summary; `rchar` is Linux process read-character accounting, not disk-sector I/O. `VmHWM` is per-process Linux high-water, not a proved universal memory bound.

## Actual measured small-size result

| PCM input (WAV adds 44 bytes) | A old median verify | B stream median verify | A/B speed ratio | A/B Linux rchar median | A/B VmHWM maximum |
|---|---:|---:|---:|---:|---:|
| 64 KiB | 0.526800 ms | 0.482095 ms | **1.0927x** | 31,225 / 31,161 | 2,848 / 2,824 KiB |
| 256 KiB | 2.246095 ms | 1.952136 ms | **1.1506x** | 123,744.5 / 123,680.5 | 3,228 / 2,824 KiB |
| 1 MiB | 9.044154 ms | 7.850238 ms | **1.1521x** | 493,866 / 493,802 | 5,212 / 2,792 KiB |
| 2 MiB | 18.343547 ms | 15.771245 ms | **1.1631x** | 993,141 / 993,077.5 | 7,680 / 2,816 KiB |
| 4 MiB | 37.413383 ms | 31.673059 ms | **1.1812x** | 1,998,417 / 1,998,354 | 12,800 / 2,824 KiB |
| 8 MiB | 136.833631 ms | 63.254881 ms | **2.1632x** | 7,982,461 / 3,991,250 | 22,964 / 2,768 KiB |

All six group medians nominally favor B. For **sub-8-MiB** inputs, the baseline does one complete FLAC decode and `rchar` is effectively equal (new saves roughly 64 metadata-read bytes); the observed 9–18% median improvement therefore cannot be attributed to eliminating repeated decoding. It is consistent with removing full-WAV materialization and copying plus differences in the digest execution path, but no CPU profiler attribution was performed. **At 8 MiB+44B**, the old verifier's 8-MiB chunk boundary forces two complete FLAC decodes; the 2.16x / 2x `rchar` observation isolates that larger owner.

## Honest negative/ambiguity

- At **64 KiB**, per-process A medians vary **0.515–0.623 ms**, B **0.473–0.578 ms**; inter-process noise is nontrivial relative to the 0.045 ms median difference. The ratio is a measured nominal median, **not** a robust small-file universal speedup guarantee or a release-gate determination. A/A drift and environmental process timing are not zero.
- At 256 KiB through 4 MiB, A/B per-process medians are more separated (e.g. 256KiB A 2.244–2.256ms vs B 1.943–1.961ms), but all input cases belong to **one synthetic random-walk family** and share a seed. Structural transfer, noisy/periodic PCM, multichannel, alternative WAV layouts and larger direct codec-2 inputs are not newly accredited by this court.
- The candidate uses a bounded 64-KiB output staging buffer, but Claxon decoder buffers, metadata, OS cache and concurrency remain outside that figure. `VmHWM` is direct per-process evidence only.
- This A/B is **native component complete verification**, not CPU-time accounting, process startup, selective reads, creation, extraction, packaging, recovery, entire archive product, or release parity. Unchanged full physical archive bytes are validated per arm, not new archive-size wins.
- Existing inherited General Tests and Installed Native Package aggregation remain **FAILURE** on exact previous #788 head; this court cannot resolve or waive those checks. Historical J24I34 source-pinned failure also remains. No new product code, API, ABI, format, thresholds, benchmark fixtures, version or release changes.

## Decision, BONK and continuation

The cheapest decisive **single-family crossover test** did *not* find evidence that streaming must be disabled for small, authentic mono PCM16 direct-FLAC files. It **narrows** rather than proves the stronger hypothesis of universal positive economics. A size-threshold dual verifier would add complexity and duplicate tests without demonstrated local benefit, so do not implement it now.

Counterfactual: checking *actual Builder admission* and the smallest admitted direct-flac sizes before adding a size-dispatch branch would have prevented a speculative hybrid policy. This lesson is local and not grounds to edit the Discovery Engine.

**Next unclaimed discriminator:** one held-out, structurally different authentically selected codec-2 WAV (different channels and/or less predictable sample structure), with same exact native/source controls and hostile/logical parity. If no release decision hinges on that narrower exploration, prioritize existing #788 native-core ownership reconciliation with #765, general test/fingerprint and installed-package gate investigation without weakening historical controls, and genuine full-product performance/portability. Preserve #788 as draft until promotion law is earned.

**Discovery cache:** `docs/discovery/STATE.json` remains a staleable v0.30 cache, and a separate open PR owns its reconciliation. No collision/duplicate same-narrow implementation observed. Do not rewrite it from this experiment.
