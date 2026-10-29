# J24I39 — File-backed bounded WAV/FLAC strong-verify oracle (prospective preregistration)

Date: 2026-10-29 UTC. **Scientific O0/O1 only; no product, format, ABI, release, benchmark or evaluator mutation.**

## Exact upstream custody / ownership
- Released `main@80c358f8824ec1b20d349c92ed94c898090969b0` v0.30.0/r24 unchanged.
- This experiment is stacked on source-exact genuine Builder WAV admission and high-RSS oracle J24I38 #774 at `793da74881e5180d982df29d2ef08bacbe6d7933`; #765/#759 own native product verification.
- Existing source: `native/cmpct-core/src/lib.rs` blob `46fa87930a9229f42233594816330f35f0505e71`; `vzip_dispatch.rs` `27e4d7962ccfed6a822010383158d98e20d823dd`; `wavflac.rs` unchanged. No competing product implementation.
- Concurrency: research-only new `research/j24i39` and its workflow; do not change `docs/discovery/STATE.json` unless decision-changing active frontier changes. No `CONCURRENCY_PROTOCOL.md` on main as retrieved.

## Baseline and causal question
Actual Builder-issued 32-MiB PCM16 WAV codec2 files trigger 5 complete decodes in 8-MiB `Archive::verify_complete()` windows; #774 source-bound hosted: 1.29–1.49 s, rchar ≈79.4 MiB, VmHWM 59 MiB vs optimistic full-buffer one-shot 0.30–0.34 s and VmHWM ≈84 MiB. High-RSS one-shot is not a safe replacement.
**Question:** Can an independent, file-backed `claxon::FlacReader::samples()` pass consume encoded codec2 FLAC once and emit the EXACT prefix → PCM16 LE → suffix SHA-256/CRC32 and logical-size identity without ever building the complete WAV or compressed FLAC in memory?

## Competing frames
A. Preserve complete `Archive::verify_complete()`: correct pinned baseline but repeats codec2 decode.
B. Cache entire logical WAV: faster one-shot, known +24 MiB RSS and no meaningful boundedness; inferior control.
C. File-backed Claxon with fixed-size digest updates, metadata/prefix/suffix and explicit byte count. This is the primary oracle; it may reveal soundness/stream termination limits.
D. FFI libFLAC/libsoundfile streaming callback: alternative if C fails due to Claxon limits, introduces dependency/portability burden.

## Prospective experimental controls and decisions
Use unchanged J24I38 actual Builder WAV fixtures (8/32 MiB), and its detached parser/soundfile auditor. Extract only the already-audited physical codec2 metadata and FLAC payload; do not regenerate or reinterpret member identity, rewrite data, or bypass SHA/CRC. Compile a disposable standalone Rust probe into the same unchanged cmpct-core crate in CI. Verify exact source SHA-256, CRC32, logical PCM bytes, channels/rate/bits and full prefix/suffix for *both* sizes. Repeat independent processes in ABBA/BAAB; measure in-process wall ns, Linux `rchar`, post-exec `VmHWM`, and raw observations with declared warmups. Compare source-identical `Archive::verify_complete` A against file-backed Claxon digest B. **This is a lower-rung oracle with different trust boundary; never award product credit.**

Falsification or narrowing: any hash/CRC/sample-count disagreement, non-Build-er selection, inability to iterate FLAC from `File`, or error in source pin invalidates this oracle. Do not mask malformed/trailing/multiframe cases by reporting merely happy-path correctness. Even if B wins (>1.5x A/B rchar, lower VmHWM at 32 MiB), missing hostile encoded-frame/full-consumption tests, archive index/header authentication, source mutation safety or cross-host parity leaves productization BLOCKED. Capture any hostile test evidence separately and explicitly.

## Reuse/negative knowledge / strongest self-critique
Claxon may consume only the declared samples, leaving trailing compressed bytes unvalidated; no claim of fully authenticated encoded stream until explicitly proven. A standalone FLAC stream from an independently authenticated archive is not the same as the production Reader's full open/preflight and may omit semantic and error costs. `rchar` is process read-character accounting, not disk sectors. A fixed-shape deterministic random-walk WAV cannot establish corpus incidence. No release/frozen threshold changes. Future comparison must account for all bytes, CPU, wall, RSS, decoded work, index/open/preflight, mutation and portability.
