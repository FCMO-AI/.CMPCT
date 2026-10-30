# J24I45 — genuine Builder stereo WAV/FLAC transfer: hosted native product A/B

**Measured 2026-10-30 UTC; research outcome, not product release.** This report is subsequent to prospective preregistration `2e8bead8b883c1c88eb61b5821031feb20977bce`, deterministic test implementation, and complete [source-exact CI #40984092763](https://github.com/FCMO-AI/.CMPCT/actions/runs/40984092763).

## Exact source and evidence custody
- Candidate native source: **`2a6dbd5407731c5660faf71d04a4ef5de2d431bd`**, #788 original pinned parent. Latest *result-bearing* exact workflow HEAD: **`d4e98f07fd495605de492242b095c6a1823a6f70`**, containing ONLY child research scripts, workflow and prereg.
- Historical real native control source: `0faa25827e7393f927252876d40e9f6cb53e5a24` (#784), not rewritten or simulated. Both built separately as release Rust with *identical* unmodified `research/j24i44/native_small_wav_probe.rs`. J24I44's existing summary instrument was also reused unchanged.
- [CI #40984092763](https://github.com/FCMO-AI/.CMPCT/actions/runs/40984092763) / job `123830877567` **SUCCESS**. [Original physical evidence artifact #12945709471](https://github.com/FCMO-AI/.CMPCT/actions/runs/40984092763/artifacts/12945709471) **uploaded** at 2026-10-30T01:10:30Z, 30,211,731 B ZIP, SHA-256 `94c50ba1a65575cd6cca0dfdf153e218607ea6545f400ea1621734f57bc5ae62`, 30-day retention. Artifact includes two authentic original WAVs, complete Builder archives, physical mutants, detached audit, raw repeated observations, source pins, SHA receipts and inner evidence tarball.
- The new test invokes unchanged Builder and real Python Reader. Deterministic **48kHz stereo PCM16** with independent channel mechanisms: bounded cumulative walk in L, periodic integer ramp plus bounded noise in R; 2MiB and 8MiB PCM, each with 44-byte WAV header.
- Both cases **genuinely selected direct codec 2** without forcing selector; Python `read_range` matched original bytes and `CMPCT.verify()` accepted both. Detached auditor **without CMPCT imports** authenticated r24 header, duplicated index, footer, CMA4, FLAC 2-channel decode, logical SHA256, CRC32 and exact original WAV for both.

## Measured native result (in-process `Archive::verify_complete`)

Two archive sizes, 8 A/B process runs in A B B A B A A B order, 12 iterations/process, first 4 discarded. That is **192 raw** and **128 post-warmup** observed verification calls. Values below are independently recomputed from job log raw trial lines (distinct from retained summary report).

| PCM input | Old native median | Streamed candidate median | Old/new speed ratio | Old/new Linux `rchar` | Old/new max `VmHWM` |
|---|---:|---:|---:|---:|---:|
| 2 MiB + 44 B WAV | 14.2502685 ms | 12.4905640 ms | **1.140883×** | 1,030,919 / 1,030,856 | 7,664 / 2,904 KiB |
| 8 MiB + 44 B WAV | 107.7771185 ms | 50.1194455 ms | **2.150405×** | 8,277,977 / 4,139,008 | 22,988 / 2,904 KiB |

At 8 MiB+44 B, old `verify_complete` crosses its 8MiB range boundary and decodes the entire FLAC twice; the measured read-character ratio is **1.9999906×**. At 2MiB the `rchar` ratio is **1.0000611×**, so its ~14.1% nominal time advantage **cannot be attributed to removal of duplicate FLAC decode**. Allocation/copy/digest differences are possible but not profiled and therefore not causal claims.

## Adversarial physical negatives

For **each** of the two Builder outputs, independent auditor generated one-bit CMA4 CRC-only (decoded SHA unchanged), one-bit in FLAC middle and one-bit FLAC magic mutations. **Both** native old and streamed verifier reject **all six physical mutants**: **12/12 rejects**, preserving original 2/2 successes. CI output includes each `REJECTED_MUTANT` line and no `ACCEPTED_MUTANT`. This is scoped negative verification, not universal FLAC parser security, same-inode concurrent mutation coverage or a demonstrated exploit.

## Decision and limits

**Decision changed:** the native single-pass WAV verification advantage transfers from mono random-walk to a genuine differently structured **stereo/48kHz/2-channel** Builder source in both tested sizes. **No evidence supports adding a size threshold or dual verification path:** the cheaper, simpler candidate is nominally faster at both tested sizes. That does not prove all stereo/channel counts/layouts benefit.

Strongest critique: only one deterministic synthetic stereo family; 2MiB and 8MiB, Linux hosted single runner, per-process time variance (including 8MiB old 104.8–126.6 ms), no CPU profiler, no full product create/extract/CLI/read-range, no direct v0.30 full release gate, no Windows/macOS result in *this* test, no generalized in-place concurrent mutation, no universal memory bound. `rchar` counts Linux process read characters rather than actual sectors. The fixed 64KiB staging buffer excludes decoder internals, metadata and OS cache. A positive specialized native A/B is not license to merge or publish.

Counterfactual discriminator: a real Builder-selected structural multichannel case, with a detached PCM reconstruction referee, could distinguish codec-general architecture transfer from mono/fixture-specific acceleration sooner than threshold experiments. This local lesson is useful; it does **not** meet the bar for modifying discovery policy or `docs/discovery/STATE.json`.

## Concurrency, inherited gates and executable next action

J24I45 changes **no product source** and does not compete with #788's native implementation, #765's CRC ownership or #352's prospective installed-package aggregation. An independent parallel audit of [#788 exact-head installed-package run #40982724661](https://github.com/FCMO-AI/.CMPCT/actions/runs/40982724661) confirmed 18/18 successful feeder jobs but a red desktop aggregator using the historical v0.30 fingerprint. Already owned [#352](https://github.com/FCMO-AI/.CMPCT/pull/352), [run #40095303436](https://github.com/FCMO-AI/.CMPCT/actions/runs/40095303436), has 18 successful feeder jobs **and** a green prospective exact-HEAD aggregate. Source-exact workflow donor reconciliation is recommended; no gate was weakened here. Detailed owner handoff was posted in #788 comment `6512427745`.

The **next highest-value implementation** is source-exact reconciliation onto #765/#788 with #352's prospective installed evidence, plus the real general-test/fingerprint failures and product benchmark/portability gate. Preserve draft status; don't declare published improvement.

**Release:** still `main@80c358f8824ec1b20d349c92ed94c898090969b0`, v0.30.0/r24; no merge or release. No changes to `docs/discovery/STATE.json`, frozen inputs, thresholds, comparator semantics or published releases.
