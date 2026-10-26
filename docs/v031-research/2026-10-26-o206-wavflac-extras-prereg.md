# O206 — Hosted enabled-audio WAVFLAC compatibility, prospective preregistration

Date: 2026-10-26 UTC. Status: preregistered hypothesis, **no result or product credit yet**.
Repository: FCMO-AI/.CMPCT. Branch: agent/phased2-v031-o206-wavflac-extras-source-exact-20261026.
Exact direct base: O204 evidence PR #541 HEAD `072c95637ad835ec1aa5dd9bbe9bee2b02e11c54`, stacked on product owner PR #225 `4361424ddbe356463a6eab94361f3b950c120967`.
Product codec candidate Git blob `6e116ee1fc348b78d81a541fcaf5cf3d6912d3c4`; historical pre-fix `29526db4203723d83523fc95d074c346b63d7587`.
Released floor v0.30.0, revision 24; no version/format/new-codec mutation.

## Baseline and question

O204/O204b #541 gave real installed 3-OS evidence for **missing** NumPy, then **missing** SoundFile. They did not test the inverse important product duty: with `.[audio]` extras intentionally installed, does existing candidate #225 preserve the historic *supported PCM16 WAVFLAC* exact create/decode behavior, including an independently frozen r24 codec-2 archive, on Ubuntu/macOS/Windows? This question is materially different from missing-extras fallback. The frozen `tests/conformance/v24-wavflac.json` is generated outside the Builder and contains archive SHA `6fb51d28f74346239c8a99a3ea76eb9fd7d307d03f91a609c92b528f112b8956`, logical SHA `29f685e2326c29a164f164c35bad830b3340b0b8e3ad0e29b57463481ae9ef83`.

Prior-art BONK: O14 PR #372, hosted run #40119076117, already identified source filesystem mode differences as a cross-OS reproducible archive explanation on another workload. Do not re-run the mode-normalization family or claim O204 cross-host SHA mismatch is a new format defect without independent contrary evidence. O206 owns *positive enabled-extras codec compatibility only*.

## Competing actions and priority

- Strongest simple control: frozen Builder-independent codec-2 archive with unchanged public Reader and independent SHA/known range; no synthetic active-codec assumptions.
- Direct A/B: original codec vs owner candidate, identical authentic Reader/Builder/native library, same host, same WAV bytes and dependency versions, real supported PCM16 codec outcome. The two codec modules must produce **identical exact compressed FLAC payload+metadata** for each supported case in the same process/host.
- Cheap alternate path: direct codec round-trip without full r24 archive. Necessary, but cannot alone earn installed-product credit; therefore execute both frozen vector and real package CLI.
- Rejected as redundant: further 'missing audio modules' negative controls already closed by #541; another source patch competing with #225; cross-host metadata threshold tuning.

## Predictions / disproof

Three platforms Python 3.11, declared `.[audio]` extras installed through genuine package build. Verify `numpy` and `soundfile` imports and their versions. On each host:
1. Independent fixed revision-24 WAVFLAC vector exact archive SHA, full logical SHA and known range must pass authentic Reader `verify/read/read_range` and CLI preflight. Corrupt frozen vector must fail rather than emit wrong bytes.
2. Same eligible PCM16 WAV payload, original historical `wavflac_compress` vs #225 candidate, must both return an actual FLAC stream and reconstruct byte-identical WAV, with identical compressed payload and msgpack reconstruction metadata within each host. At least two channel/frame structures, including a nonempty, aligned case and a genuinely noisy/harder supported case.
3. On genuine CLI `create` with enabled extras and same source corpus, original/candidate archives must be byte-identical **within each host**; original/candidate strong `verify`, `cat`, `range` and logical SHA must match all sources. Inspect stored codecs and record whether PCM16 actually wins the Builder competition; no forced winner, no candidate-only fixture.
4. A deliberately unsupported PCM32 WAV must return `None` under candidate (where historical may throw); full candidate archive still reconstructs it exactly. This does not make PCM32 a positive FLAC claim.

Fail closed for unexpected original archive changes on admitted supported PCM16, missing extras, frozen vector disagreement, wrong logical bytes, unsupported 'success' with corrupt hash or inconclusive host setup. Preserve negative/ambiguous outcomes. Do not alter thresholds or source to earn a pass.

## Evidence tier and limits

Evidence tier: real Python package install and independent frozen r24 oracle on three operating systems, not complete release parity. Inspect exact-head code fingerprints (from Git objects, not platform-converted checkout), OS/library provenance, raw per-case results and upload artifacts. Performance and memory whole-system measurements remain unearned. Possible SoundFile/libFLAC cross-OS compressed-byte differences are recorded honestly and **not** a release failure absent a cross-OS physical-byte contract: same-host source exact A/B is the acceptance. Keep archive-creation startup distinct from native codec cost.

Owner coordination: product PR #225 remains sole source implementation; PR #541 original missing-extras evidence remains intact. No `src/`, `native/`, historical tests, gates, Discovery state or release mutations. Next decision: if all hosted positives pass, give owner #225 a precise evidence handoff, then normal general/format/parity gates; if a supported-codec regression exists, retain failing raw artifact and narrow causal source before considering any product code.
