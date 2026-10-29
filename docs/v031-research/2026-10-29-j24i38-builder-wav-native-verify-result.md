# J24I38 — First-party Builder WAV/FLAC verification work: source-exact positive result

**Science positive / native-product unchanged / NO MERGE / NO RELEASE.** 2026-10-29 UTC. This decision is scoped to canonical Builder producing a direct WAV-FLAC file, *not* to ordinary-population WAV frequency, not an RSS-equivalent replacement, not general release performance.

## Prior prediction and exact source

Pre-result hypothesis committed first at `430220da7bec194536c2dc6aef0c047f3c4651c5` in [preregistration](2026-10-29-j24i38-builder-wav-native-verify-prereg.md). Source inherited from #772 at `2d0dd4031b8c0fb2c42b715b6a4569199a2309a3`, first result-bearing trial **GitHub [#40924016677](https://github.com/FCMO-AI/.CMPCT/actions/runs/40924016677)**, exact experimental product-source HEAD `6eee048dad0850d7494bae2123d9e6b88e5576be`. GitHub CI job `123624585094` **SUCCESS**. Original provider artifact `12919642471`, containing both unmodified source WAVs, both Builder physical archives, signed-custody manifest, detached physical audit, raw repeated trials, and original summarizer result. GitHub original artifact size 55,370,621 B; retention 30 days. **Immutable durable raw copy:** `research/j24i38/hosted_raw_recalculation.json` (64 source-logged observations including 16 warmups, 48 post-warmup observations) independently recalculated from original hosted log, not from a screenshot or source-level prediction.

Pinned product source Git blobs:
- `src/cmpct/builder.py`: `663ef0922992b1fbb8f19e6eea88d55c10a56044`
- `src/cmpct/codec.py`: `29526db4203723d83523fc95d074c346b63d7587`
- `native/cmpct-core/src/lib.rs`: `46fa87930a9229f42233594816330f35f0505e71`
- `native/cmpct-core/src/vzip_dispatch.rs`: `27e4d7962ccfed6a822010383158d98e20d823dd`
- frozen direct-codec reference Git blob `d10b7dab9126d39e819a74279c186363a163f2ef`.

No product source, frozen corpus or evaluator was modified.

## Exact physical admission and independent logical proof

**Both fixed prospective inputs were independently admitted as one direct `S_BLOB` /`CODEC_WAVFLAC=2` by actual unmodified Builder**, not by a fabricated CMA4 record. Installed Python Reader `verify()==1` and range-read exactness passed. A detached auditor that never imports CMPCT decoded the actual FLAC stream via libsndfile/soundfile, rebuilt the original PCM16 RIFF/WAVE, compared **every reconstructed source byte**, and independently validated CMA4 SHA-256/CRC32, MessagePack metadata, dual index copies and footer. Audit result **PASS**.

| Source | Actual logical bytes | Complete archive bytes | Physical FLAC bytes | Physical archive SHA-256 |
|---|---:|---:|---:|---|
| 8 MiB PCM + 44 B WAV | 8,388,652 | 3,983,501 | 3,982,561 | `9250964815f67891c3e106c9d87aadc67d4f2c3dce8b3e4e1873813a13a6fac7` |
| 32 MiB PCM + 44 B WAV | 33,554,476 | 15,879,805 | 15,878,863 | `cf4a826209b3ffff0af86c765db28068386c8f95e6c1405ee29099113b88baa9` |

The large WAV source is byte-for-byte authentic and signed by the existing r24 hashes, not an arbitrarily injected synthetic direct-Zstd representation. A single deterministic random-walk PCM construction is **not** a random sample of general audio workloads.

## Measured unchanged native verify vs optimistic non-equivalent full-buffer oracle

Ubuntu 24.04 hosted GitHub Actions. Same exact physical archive. `A`: compiled `Archive::verify_complete()` with existing 8-MiB chunk schedule. `B`: compiled `Archive::read_range(0,0,N)` into one N-byte buffer, followed by a complete SHA-256 and CRC32 check. ABBA/BAAB alternating lanes, 12 warmup-excluded samples **per arm and input** (48 non-warmup measurements). Same single implementation/semantic source; source changes forbidden by workflow. Timing inside Rust process; `rchar` is Linux process read-character accounting, not actual disk sectors.

| Genuine Builder source | A verification wall median | B oracle wall median | A/B wall | A `rchar` | B `rchar` | A/B read-character | A VmHWM median | B VmHWM median |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 8 MiB PCM (+44B) | 153.378 ms | 87.967 ms | **1.744x** | 7,965,522 | 3,982,778 | **2.000x** | 22,810 KiB | 22,766 KiB |
| 32 MiB PCM (+44B) | 1,492.750 ms | 344.630 ms | **4.331x** | 79,395,070 | 15,879,081 | **5.000x** | 59,010 KiB | 83,586 KiB |

**Primary preregistered fork: supported.** The 32MiB `rchar` ratio **4.999979x** exceeds the fixed >1.5x discriminator. The 44-byte WAV header matters: logical N exceeds the nominal 8/32MiB boundaries, so the verifier requires 2 or 5 8-MiB slices respectively, not 1 or 4. In this native codec-2 implementation each slice requests a full decode/physical authentication. The observation is a source-level repeated-work mechanism, not a proposed change to thresholds.

**Exported cost is material.** On 32MiB one-shot comparator VmHWM increased by **24,576 KiB = 24 MiB**, and source code constructs a full-size `Vec` for the returned 32MiB logical member as well as internal reconstruction. It cannot replace a bounded-memory verifier as-is. The 8MiB `VmHWM` difference (B 44KiB lower) is measurement noise / allocator effects, not a memory victory. `rchar` includes process-level read characters, *not* physical disk I/O, and heavy codec work may be memory/CPU rather than disk-bound.

## Controls, contradictions and limitations

The strongest simpler control was source inspection: Builder's explicit `.wav` CDC exception and native WAV-FLAC full decode predicted the risk, but only the executed authentic Builder+independent audit established first-party incidence. A local independent uninstalled libsndfile+Zstd CLI prescreen predicted FLAC compression advantage but gave **no product credit**; the installed exact-source work resolved admission. J24I37 synthetic direct-Zstd 8×/4.24× remains separate historical research evidence; do not conflate the two size/sample distributions or add their gains.

The successful specialized GitHub test is not a product verification repair, and additional run of this same experiment would only replicate this source/host—not prove future bounded behavior. CPU cycles, cache misses, physical disk sectors, cold open, list, create and extract end-to-end, selective read, FLAC malformed/truncated/concatenated hostile streams, metadata size amplification, writable source mutation, Windows/macOS/Android and complete release parity **remain unmeasured**. Original native codec2 read_range already imposes full logical materialization; a new verifier may need a new private codec streaming primitive with new portable error and frame-boundary proof.

## Decision and next research question

**Advance (do not promote):** first-party generality for a WAV file was proven, and the earlier “only fabricated direct-Zstd workload” concern was materially narrowed. Strong measured owner is repeated **full codec2 reconstruction** in native verify. The next expensive intervention should be designed by current #759/#765 Native Core owners: compare a true **bounded single-pass FLAC decoder** with unchanged native complete verify on these same signed files; prove exact SHA+CRC, lengths, full encoded-frame consumption, metadata, no trailing/concatenated acceptance, hostile size/frame limits, Python/C-ABI semantics, recovery, portability and RSS **before** claiming product gain.

The one-line counterfactual discriminator available *prospectively* was: “Before designing a general native direct streaming rewrite, require one unmodified Builder-created >8MiB direct member with codec2 admission.” This transfers as a cheap pre-productization filter for other representation families. It is one local example, **insufficient to self-modify Discovery Engine policy**; no `docs/discovery/STATE.json` update.

## Coordination and promotion boundary

Source/patch ownership: #765/ #759. Related science: #772. J24I38 branch research owns only `research/j24i38/`, scoped CI, and this prereg/result. The r24 published release remains v0.30.0 on `main@80c358f8824ec1b20d349c92ed94c898090969b0`. Exact original run succeeded; any later documentation-only descendants require their own relevant exact-head checks. **No merge, release, numeric version, format, evaluator or source mutation.**
