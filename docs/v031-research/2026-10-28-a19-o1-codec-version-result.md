# A19-O1 — same-host libzstd encoder-version transfer result

**2026-10-28 UTC. Source-exact scientific falsifier only.** O1 preregistered first at `7f19a1b88c5894cd805e88025b495dc655cdd666`. No rewriting the earlier O0 predictor, frozen thresholds, codec setting, benchmarks or product semantics.

## Original observed fork and the strongest control
The earlier A19-O0 [hosted run #40748875049](https://github.com/FCMO-AI/.CMPCT/actions/runs/40748875049) on Ubuntu/Python3.11/libzstd1.5.5 retained narrow two-stage progression headroom: best unary → best composition 16,385→16,216B (+169, 1.031%) and 16,457→16,260B (+197, 1.197%) for two seeds. A completely independent local Linux/Python3.13/libzstd1.5.7 replica reproduced original logical source SHA identities, but progression seed1 yielded 16,395→16,261B (+134, **0.817%**, below frozen 1% threshold). O0 research positive could be host- or codec-version-dependent rather than a general information-model advantage.

O1 made a *new, prospective* same-host Python3.11/Ubuntu test of both actual compressors on the **exact same 200 transformed original source programs**. Direct system C library is Zstd **1.5.5** at level19. Pinned `zstandard==0.25.0` wheel reports bundled Zstd **1.5.7** at level19. Both encode the exact same logical SHA, program and metadata bytes, round-trip decode, and store complete frames.

## Hosted and physical audit receipts
- [Source-exact hosted initial O1 run #40749789212](https://github.com/FCMO-AI/.CMPCT/actions/runs/40749789212), head `69c7353b31ebe4cab572164c2282e0c7a1e45187`, **SUCCESS**; artifact 12844000011 SHA-256 `c0920a4175355b0d25fb34558f4a118a7ba3b3e75147c118493d24c3ec7fdf99`.
- [Final physical-preservation run #40749885734](https://github.com/FCMO-AI/.CMPCT/actions/runs/40749885734), measured code head `4c205a1a4257b532d1aaa48be7d65112e247f120`, **SUCCESS**; artifact **12843451215**, ZIP SHA-256 `28816d616476610758712c48d93f072b05251774ea110a2247dfbf06680b721d`.
- Artifact preserves **400 physical full frames** (two codec versions × 20 programs × 10 source fixtures), unchanged original logical input hashes and complete per-frame metadata/codecs.
- A **third independent** offline physical audit downloaded artifact 12843451215 and verified its ZIP SHA-256, independently generated all ten SHAKE logical originals, decoded **all 400 actual stored Zstd payloads** with local libzstd, reversed each program independently to the exact original bytes, recomputed all best-unary/best-composed totals and original O0 threshold decisions. **No discrepancies**. **125/200** pairs of compressed frame payloads are byte-identical across versions; **75/200** differ. All 400 input/MessagePack descriptor identities are paired correctly.

## Same-host exact complete-byte transfer

| Fixture | System v1.5.5 unary→composed | Wheel v1.5.7 unary→composed | Version decision |
|---|---:|---:|---|
| Progression 0 | 16,385→16,216B (+169 / 1.031%) | 16,385→16,216B (+169 / 1.031%) | Both PASS |
| Progression 1 | 16,457→16,260B (+197 / **1.197%**) | 16,395→16,261B (+134 / **0.817%**) | **Threshold flips** |
| Quantized 0 | 28,786→29,061B (−275B) | 28,786→29,061B (−275B) | Both FAIL |
| Quantized 1 | 29,495→28,699B (+796B) | 29,493→28,433B (+1,060B) | Positive seed only |
| Heldout 0 | 53,319→48,619B | 53,319→48,619B | Structural observation, not primary gate |
| Heldout 1 | 53,338→48,161B | 53,338→48,159B | Structural observation, not primary gate |
| Random 0/1 | Direct wins | Direct wins | Correct fallback |
| Periodic 0/1 | Direct wins | Direct wins | Correct fallback |

**O1 decision: `VERSION_SENSITIVITY_SUPPORTED`**. Under **identical** Python3.11, host, source, transform, program metadata and Zstd19 *level*, merely changing the Zstd encoder implementation from 1.5.5 to 1.5.7 crosses the actual preregistered 1% threshold on progression seed1. This upgrades the version effect from a cross-host conjecture to source-locked same-host physical evidence.

This does not imply Zstd's compressed streams are unstable semantically—**both are exact and valid**—only their optimal compressed sizes for these exact inputs and codecs change with implementation version. A size win this close to 1% has inadequate implementation-version robustness for general-product promotion.

## Negative, control and handoff
O0 exact-head hosted positive remains an honest scoped research result, **not** a universal general-purpose gain. O1 does not retrospectively modify O0's frozen criterion. The initial O0 local lib1.5.7 negative also remains true. The imported Python XOR reconstruction on favorable progression cases still pays about **36ms** create and **5.5ms** decode versus about **11ms** and **0.15ms** direct Zstd on a 65KiB source. Twenty-arm search costs approximately **600ms CPU**. Larger benefits claimed from mixed heldouts are also beatable by a stronger fully charged but oracle-gifted split unary/direct control, so composition cannot claim sole explanatory ownership.

**Decision for next activation:** do **not** tune channels/lags/seed thresholds in this family. Retire its immediate production path; preserve the exact size/version effect as a scientific negative about codec-version sensitivity and simpler segmentation controls. Reallocate to already-owned correctness/productization lanes or a truly different information/reconstruction model. Neither O0 nor O1 measures a complete CMPCT archive, installed Reader/Builder, cross-OS performance, cold resource consumption or release gating. No on-disk version, merged code, Discovery STATE or policy mutation.
