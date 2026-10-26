# O204 — Real package/CLI optional audio acceptance: positive three-host result

**Date:** 2026-10-26 UTC. **Status:** RESULT-BEARING POSITIVE, NOT A CORE RELEASE.
**Preregistration:** [O204](2026-10-26-o204-audio-optional-prereg.md), committed before first run.
**Owner implementation:** [PR #225](https://github.com/FCMO-AI/.CMPCT/pull/225); this derivative evidence lives in [PR #541](https://github.com/FCMO-AI/.CMPCT/pull/541). Source defect: [issue #538](https://github.com/FCMO-AI/.CMPCT/issues/538).

## Source identity and exact experimental boundary

- Original revision-24 v0.31 source commit `4545d7d5b2a0b712b4b00f5a9c291d4a3a9e169b`; exact original `src/cmpct/codec.py` blob `29526db4203723d83523fc95d074c346b63d7587`.
- Existing candidate/owner PR #225 `4361424ddbe356463a6eab94361f3b950c120967`; codec blob `6e116ee1fc348b78d81a541fcaf5cf3d6912d3c4`.
- Hosted code HEAD carrying the instrument: `6ab429391d88c541ef9ce7975e5d789c26704d63`. The two Python execution trees are byte-identical except the authenticated codec blob. Source is read from canonical Git objects, not platform-converted checkout bytes.
- Both copies received the **same real compiled package-owned Rust/Zstd cdylib** on each host. The venv installed the unmodified product `pip install -e .`, including declared mandatory `msgpack` and build tools; no `numpy` or `soundfile`. Neither platform was permitted to claim victory through mocking the real binary.
- Both arms used authentic `python -m cmpct create/info/verify/preflight/cat/range` with identical fixture inputs, CLI serial workers, reproducible mode, and all logical SHA-256 assertions.

## Hosted result and evidence

Exact-HEAD GitHub Actions [run #40396610203](https://github.com/FCMO-AI/.CMPCT/actions/runs/40396610203) — **3/3 SUCCESS**; independent push run [#40396604144](https://github.com/FCMO-AI/.CMPCT/actions/runs/40396604144) — **3/3 SUCCESS**.

| Host | Candidate full CMPCT bytes | Candidate archive SHA-256 | Historical WAV abort | Candidate verify/exact read |
|---|---:|---|---|---|
| Ubuntu 24.04 | 4,170 | `290d83e68863ff54f02c3bce385a3a4c9821ab062b356e6d6aa6d18646b8b0f1` | missing `numpy` | PASS / 5 members |
| macOS 14 | 4,170 | `290d83e68863ff54f02c3bce385a3a4c9821ab062b356e6d6aa6d18646b8b0f1` | missing `numpy` | PASS / 5 members |
| Windows 2022 | 4,170 | `658090eba64bcd95f221ddf1b977f05d92275ba3ef3f305779b0109d32626058` | missing `numpy` | PASS / 5 members |

In **every host**: the original source aborted through `wavflac_compress -> _audio_modules -> ModuleNotFoundError: numpy` (rc=1), while the pre-existing owner candidate returned `None` to the optional WAV candidate path and created a complete r24 archive. All five logical source SHA-256 fingerprints were identical across hosts:

- `pcm16.wav`: `485937d1ffc7d0141f7275399ca152c8eca37cf233ea623f1255090ad6a60edb`.
- `pcm32.wav`: `0b7b5368ba3eba52ad0ccd32d0470e8d4349af0de0f4e9d6f60886f652e27e56`.
- `pcm8.wav`: `fafa19018a81f1efca9ffa0bcc6430206992d2268c84c819a51a8cd5b26bf048`.
- `invalid.wav`: `ca2b98630828727d75d128cd9b61960a7bcbfa2cdcb60261e1c2c758c51fbdcc`.
- `ordinary.bin`: `b2b6773335b4f3b80012c1175b238964f2bb345a57ed6ee521a6791e1e447712`.

The ordinary-only archive was **1,152 bytes and byte-identical** between historical/candidate source on each host. Direct candidate codec tests returned `None` for PCM16/PCM32/PCM8 without optional modules. All normal archive verification, preflight, whole reads and range reads passed.

Per-platform structured artifacts (runtime/pip freeze/native binary SHA/complete raw checks):
- [Ubuntu artifact 12685954773](https://github.com/FCMO-AI/.CMPCT/actions/runs/40396610203/artifacts/12685954773); artifact ZIP SHA-256 `54c98abcb2617b61ea77d6d288a0444f684f6dd27724b14bf35dee3f2e496066`.
- [macOS artifact 12685614481](https://github.com/FCMO-AI/.CMPCT/actions/runs/40396610203/artifacts/12685614481); artifact ZIP SHA-256 `904902d0278b3ddcf9df3d94cce2a3b1650baab4bb6132d5d75e2f146228b9bb`.
- [Windows artifact 12687336087](https://github.com/FCMO-AI/.CMPCT/actions/runs/40396610203/artifacts/12687336087); artifact ZIP SHA-256 `0331a8575b8b0e5f2a7a6646aef6eac3c349cbb89ff3f43ff80802850c80b6b8`.

## Failed original court, causal repair, and negatives

Initial O204 [run #40396274755](https://github.com/FCMO-AI/.CMPCT/actions/runs/40396274755) **failed on all three hosts before audio**: copying Python source alone excluded package-owned `cmpct_core` cdylib, which is a genuine mandatory runtime binary despite the absence of NumPy/SoundFile. Windows also exposed checkout newline conversion that made reading `codec.py` bytes from the working tree differ from the canonical Git blob. Follow-up compiled the real package first, copied the identical ABI library into each source tree, and used `git show HEAD:path` for exact source. These are **instrument repairs**, not weakened criteria or product fixes; original red remains public.

**Important cross-host negative:** Linux/macOS and Windows produced different 4,170-byte full CMPCT SHA-256 even with reproducible CLI mode, while all five logical SHA-256 fingerprints matched. The causal source of the physical-byte divergence was not established; it may reflect filesystem permission/metadata semantics. Do not claim cross-OS byte-identical archives or silently classify this as a compression regression. This court's byte-identity claim is **same-host historical vs candidate on the ordinary corpus only**.

## Decision and debt

**PRIMARY QUESTION: POSITIVE on three genuine installed-product runners.** O225 candidate closes the specific *absent audio extras while creating WAV-containing archives* fault in the tested semantics. Existing PR #225 remains the product source; O204 changes no product code or on-disk format.

Not earned: optional-dependency `soundfile`-only missing variant, WAVFLAC decoder conformance with `[audio]` installed, complete hostile WAV coverage, full release-parity benchmark, timing/RSS, Windows metadata parity, generic suite completion or release promotion. A green hosted **negative-control** does not prove all future audio inputs or platform semantics.

**Next decision:** owner of PR #225 should incorporate/link O204 evidence and run its untouched full release/integration gates, preserve/diagnose physical archive divergence only if cross-platform reproducibility is in scope. Do not introduce mandatory NumPy/SoundFile to solve this create failure. Keep #538 open until owner implementation is integrated and released or explicitly reconciled.

**Discovery Engine:** this was a convergence/evidence proof, not a new scientific family or policy change. Reusing the earlier proven but unhosted implementation was less costly and less collision-prone than creating a duplicate WAV codec; no `docs/discovery/STATE.json` update or policy rewrite.
