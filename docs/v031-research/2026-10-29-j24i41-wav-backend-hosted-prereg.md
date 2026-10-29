# J24I41 — prospective hosted WAV/FLAC admission transfer (O1)

**2026-10-29 UTC; frozen before adding the instrument.** Scope: scientific/CI evidence on existing unmerged product candidate [#225](https://github.com/FCMO-AI/.CMPCT/pull/225) at exact parent `4361424ddbe356463a6eab94361f3b950c120967`. Released `main@80c358f8824ec1b20d349c92ed94c898090969b0` v0.30.0/r24 and development `agent/v031-development@4545d7d5b2a0b712b4b00f5a9c291d4a3a9e169b` remain untouched.

## Prior observation / ownership
Current development codec blob `29526db4203723d83523fc95d074c346b63d7587` calls `sf.write(...,format="FLAC",subtype="PCM_32")` for valid signed PCM32 WAV. The unmerged #225 codec blob `6e116ee1fc348b78d81a541fcaf5cf3d6912d3c4` prospectively rejects unsupported backend widths/frames/rates/channels and falls back. Independent local libsndfile 1.2.2 rejects FLAC PCM_32 as an invalid format/subtype combination. #225's 1024-case local study is meaningful but lacks committed focused tests and hosted exact-head conformance.

## Primary question and alternatives
Does the **actual built** #225 candidate preserve exact WAV bytes and safe fallback for diverse valid/unsupported WAV structures while retaining byte-identical admitted PCM16 archives versus the same-source predecessor, on hosted installed Python? This is not new codec policy and must not duplicate #225 implementation. Alternative A: accept prior local data without hosted conformance (insufficient promotion evidence). B: change codec logic again (premature, source collision). C: an independent source-pinned hosted, same-tree paired court (chosen). The control is original v0.31 source with the same input tree and same installed environment.

## Frozen protocol / pre-results prediction
- Produce deterministic 512-KiB-class RIFF/WAVE files with PCM16 mono/stereo, signed PCM32, PCM24, PCM8, PCM16 zero-frame, invalid frame alignment, nine channels and too-high sample rate. Preserve appended RIFF chunks where valid. No corpus identity/threshold encoded into the product.
- Verify the unchanged source fixture SHA-256; build **one separate CMPCT archive per case** with actual Builder, reproducible mode, single worker, and inspect decoded original bytes, stored logical SHA, strong `verify`, and selection when admissible. Require no archive abort for the candidate.
- Execute exactly the same admitted PCM16 cases using parent `agent/v031-development@4545d7d5...` in a distinct Git worktree. Candidate and control complete archive bytes and decoded content must be identical for those supported cases; no tolerance for differences.
- Independently establish whether original control aborts PCM32; the result is diagnostic, not a condition for test success in hosts with different backend versions. Record SoundFile/libsndfile versions.
- Preserve raw cases/measurements/results in a hosted workflow artifact with exact Git source SHA and checksum manifest; fail CI if artifacts are absent. On Linux and macOS/Windows where supported by dependencies; do not misclassify environment installation failures as product failures.
- No release benchmark credit from this focused test. No numeric version, format, reader/ABI, frozen-corpus or threshold changes.

**Predicted:** candidate exact round-trip for all cases; original control rejects PCM32 on hosted libsndfile; accepted PCM16 archive bytes identical to unchanged parent. **Kill or narrow:** any candidate Builder abort, silent lossy reconstruction, invalid SHA/CRC, or PCM16 archive byte difference contradicts the claim. If real Builder selects no codec2 for valid PCM16, narrow eligibility rather than forcing it. If package dependencies fail, classify infrastructure and preserve logs. This test alone cannot establish cross-platform release, all WAV edgecases, memory/CPU parity, or repair #225's promotion gate.

## Counterfactual / science
The pre-implementation code search found #225 before reimplementing a duplicate PCM32 fix; this is a concrete duplicate-family BONK. Prospective transferred lesson only if results show why the original local 1024-case evidence missed a material hosted failure. No Discovery Engine policy or `STATE.json` mutation merely for activity.
