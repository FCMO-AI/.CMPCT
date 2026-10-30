# J24I46 — seek-first selective FLAC: 288 clean-input observations and a decisive integrity negative

Date: 2026-10-30 UTC. **RESEARCH / O0–O1 ONLY; NOT A CMPCT PRODUCT WIN.** This conclusion is conditioned on preregistered J24I46/J24I46b, current released source `main@80c358f8824ec1b20d349c92ed94c898090969b0`, native candidate `#788@2a6dbd5407731c5660faf71d04a4ef5de2d431bd`, and source-exact local artifact `research/j24i46/j24i46_seek.py` (Git blob `b81f5723a36f259ce188ce8340f1654795d0d0fb`; local Git blob compared equal against the remote). Hosted self-reproduction is separately pending; no current CI result is credited here.

## The different-worldview question

Can seekable **single** FLAC preserve nearly all of the selective-access benefit of independent FLAC decode islands with zero new archive bytes, before anyone pays new codec segment/index costs? The stronger simple control is libsndfile frame seeking on an unchanged FLAC; the opposing control is full sequential decoding of that identical FLAC using that identical libsndfile. Both reconstruct the **same requested 4KiB** original PCM range. No Builder selection, CMA4 authenticated index, native Archive::read_range, or whole archive equivalence is asserted.

## Local direct instrument, exact inputs and results

Environment: Linux; NumPy 2.3.5; soundfile 0.13.1; libsndfile 1.2.2; freshly launched interpreter per observation. Two fixed-seed structurally distinct 32MiB PCM16 inputs (stereo 48kHz with correlated left/random-walk and periodic right, mono 44.1kHz nonperiodic). Each WAV is 33,554,476 bytes. FLAC stored bytes: stereo 12,164,541; mono 15,113,811; no seektable is needed in this particular libsndfile test. Original WAV PCM independently reconstructed from FLAC byte-exactly; reference `flac --test` and reference raw PCM reconstruction both passed.

Each 4KiB request: 25%, 75%, last 4KiB, aligned to complete PCM frames. Twelve ABBA/BAAB cycles at each of six case/position combinations, 24 observations per method per combination = **288 total**. Timed region opens one `SoundFile` instance, seeks (B) or decodes all (A), returns requested bytes; Python **process creation, importing NumPy and reference-WAV validation are excluded from this inner timing**, but measured separately as a significant startup tax. All requested SHA-256 digests agreed within/between methods and with original WAV.

| Input / requested position | Full median inner wall | Seek median inner wall | Full/seek inner wall | Compressed bytes returned to decoder: full / seek |
|---|---:|---:|---:|---:|
| Stereo 25% | 148.475ms | 0.749ms | 198.2x | 12,164,553 / 40,972 |
| Stereo 75% | 147.340ms | 0.796ms | 185.1x | 12,164,553 / 49,164 |
| Stereo tail | 149.672ms | 0.639ms | 234.0x | 12,164,553 / 15,664 |
| Mono 25% | 172.675ms | 0.645ms | 267.7x | 15,113,823 / 40,972 |
| Mono 75% | 170.391ms | 0.680ms | 250.7x | 15,113,823 / 40,972 |
| Mono tail | 168.719ms | 0.585ms | 288.4x | 15,113,823 / 14,768 |

Read-byte counts are instrumentation at libsndfile's file-like read interface, **not disk blocks or a proof of internally decoded FLAC frames**; they can exceed payload size due to small header revisits. Rust Claxon has different APIs and may lack effective seek support. Local source-byte and raw receipt: `raw.json` SHA-256 `8f6ebc2ea8d88da637f9cc1b5f7f9c2a2766c64c1797961145f0891dfa80561c`, summary lines SHA-256 `ac36ce2f9661aec20248ee06db5a24d1091204572af1e26490af4ee26c6cbec9`. Exact-hosted raw artifact remains pending from the new workflow.

**Counter-control for process startup:** twelve fresh Python invocations per method for stereo 75%: median external start→exit **892.752ms full vs 751.419ms seek** (only ~1.19x). Internal within those invocations **157.186ms full vs 0.833ms seek**. This stark split is why the >185x numbers are **not** cross-process CLI or installed-product speedups. `process-boundary-raw.json` SHA-256 `15480815a396f83d63e1ffcbb708eb13acc429d224a21209040c99ef13b83bb7`.

## The stronger negative — distinct physical source with identical requested range

Prospective J24I46b modified **one bit** (`xor 0x04`) at physical offset **10,339,859** of original stereo FLAC (85% of the encoded byte stream), well outside early requested 25% 4KiB PCM range. Original FLAC SHA-256 `983dc069c4189ac92450f221e8e18b01bcd022388ed5e274efa3acd1ff2071e1`; mutant SHA-256 `9d5fa32f9607f3367b323b566aa378505d3d83da7c585c31fdc896e0b117ec3e`. The mutant early-range libsndfile seek **accepted** and returned the exact original 4KiB. The same mutant's full libsndfile decode **rejected**; independent `flac --test` also **rejected**, citing an audio frame CRC mismatch. Clean original passes both. Mutant evidence SHA-256 `3f581413678b5ce7f02ae5671f1e433531ebe74590451ba625d1327a4afc794d`.

This is a **direct disproof** of the claim “seek-only is a free, contract-equivalent replacement for current native codec-2 selective reads.” Inspection of #788 source shows `Archive::read_range` does a whole-member `decode_wav_flac_blob` and checks complete decoded SHA256 **before** returning a slice. A rapid early seek can be blind to a corrupted late frame. **No invalid CMPCT container was constructed here** and there is no claimed current product security bug; it is a proposed-optimization semantic mismatch.

## Scientific decision / cheapest next action

The **locality engineering opportunity** survives: mature decoder seek consumes a tiny fraction of compressed bytes and internal processing for 4KiB clean PCM slices, on both structures without an extra FLAC island format. However a full-authentication equivalence gate **fails**. Retire “simply replace direct-PCM partial read with libsndfile seek” as invalid. Do not invest in islands **solely** on the assumption single-FLAC cannot seek. Instead examine a *new authentic locality proof boundary* (segment digests/proofs charged to stored bytes and reader complexity; or already-authenticated immutable source/cached digest; or same-archive authenticated segment frames). Reuse existing frame seek capability only if that independently justified authentication/ownership path survives security, crash/recovery, portability and full-system economic gates. The current strong-full-SHA baseline remains valid and may win.

Do not interpret the new frame-seek instrument as a rewrite request for owner #788. Native complete verification and selective read are different questions. No product code, format, ABI, benchmark, thresholds, version or release state changed. `docs/discovery/STATE.json` remains owned by #574 and was not edited. This one counterfactual suggests inspecting **what authenticity is checked before returning a range** *before* testing micro-optimization, but is not sufficient to modify the normative discovery policy. The confirmed negative and its exact source are the durable decision.

## CI / limits

New deep-lane `v031-j24i46-seek-oracle.yml` is configured for 288 exact-source samples, independent summarizer, one-bit late-frame falsifier and fail-closed downloadable GitHub artifact on an admitted latest-HEAD PR. **The current report does not claim the hosted job has completed**. No full-product competitor benchmark, native Claxon equivalent, universal malformation proof, cold OS cache, actual disk-sector I/O, or installed-package release gate was executed as part of this experiment. Source library versions, Python startup memory and compressed file size can substantially affect outcomes. Physical memory counters reflect the whole Python interpreter, not Claxon native RSS.

## Next independent scientist
Inspect latest PR #796 HEAD and its exact-head hosted run/artifact; if green, recalculate the 288 samples against pinned source and attest the late-frame mutant. Check root #788/#765 owners before any native change. Cheapest genuinely new fork: independently determine whether a bounded, *authenticated* frame-range proof with fully charged metadata/dependency/cold-open cost beats full whole-blob verify on ordinary Builder-admitted WAV, without weakening existing SHA semantics. Baseline may win.

## Source-exact hosted repetition on PR #796

The independent GitHub Actions run [#40988904900](https://github.com/FCMO-AI/.CMPCT/actions/runs/40988904900) completed **SUCCESS**, attached to source/head `90af00155a08d25ecd3afa9f8e35872b173a5089`. Its hosted workflow generated and validated the distinct PCM16/FLAC sources, executed all 288 repeated ABBA/BAAB observations, ran the independent `summarize.py` exact-source and 24-per-arm checks, and ran the preregistered late-bit-flip falsifier with reference `flac -t` rejection. The log explicitly recorded reference `FLAC__STREAM_DECODER_ERROR_STATUS_FRAME_CRC_MISMATCH` plus loss of sync, while the test's required early seek control stayed exact.

The source/physical/negative artifact is [artifact #12948008513](https://github.com/FCMO-AI/.CMPCT/actions/runs/40988904900/artifacts/12948008513), GitHub reports 34,533,976 uploaded artifact bytes. It includes both original FLACs, one independently corrupted FLAC, numerical observations, independent result JSON, input generation metadata and pinned source-code fingerprints. **The hosted result establishes reproduction and an exact-input counterexample, not native CMPCT performance.** The physical ZIP has not been separately re-audited outside the hosted job in this run; its contents are reported from logs/workflow and must not be misrepresented as externally audited.

At this scientific HEAD, CI Topology and Version Discipline completed **SUCCESS**, while Engineering Evidence initially **FAILED** due to missing mandatory PR dossier headings, not due to decoder corruption. The PR body was updated with the mandatory problem, falsifiability, negative, safety, performance, portability and quality-ratchet disclosures without changing any experiment criterion. CI re-evaluation of the updated body remains independent of the result and must be checked at the latest event/head. General Tests are not presumed green. No merge or release.
