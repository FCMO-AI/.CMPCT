# O204b — NumPy installed, SoundFile missing: three-host source-exact result

**2026-10-26 UTC**. Separate preregistered follow-up to O204 ([preregistration](2026-10-26-o204b-numpy-only-prereg.md)), distinct from O204's `numpy`+ `soundfile` absent court ([earlier result](2026-10-26-o204-audio-optional-result.md)).

## Exact source / result-bearing identity

- Original source development `4545d7d5b2a0b712b4b00f5a9c291d4a3a9e169b`, historical codec blob `29526db4203723d83523fc95d074c346b63d7587`.
- Original owner product fix is pre-existing [PR #225](https://github.com/FCMO-AI/.CMPCT/pull/225), candidate codec blob `6e116ee1fc348b78d81a541fcaf5cf3d6912d3c4`.
- Result-bearing instrument HEAD: `1e0b74f9491a0a7b0854539f943532014d19de0b`.
- [Hosted run #40397842486](https://github.com/FCMO-AI/.CMPCT/actions/runs/40397842486), **Ubuntu 24.04, macOS 14, Windows 2022 3/3 SUCCESS**. Independent [push run #40397837924](https://github.com/FCMO-AI/.CMPCT/actions/runs/40397837924) also 3/3 SUCCESS.
- Every OS used real package-owned native ABI, Python 3.11, installed `numpy>=1.26` with *no* SoundFile and exact identical source/fixtures except historical vs candidate `codec.py`.

## Decision

The original historical control **failed with `ModuleNotFoundError: No module named 'soundfile'`**, not missing NumPy, proving the independently reported second issue path. On each host the unchanged existing candidate completed a revision-24 CMPCT archive with **5/5 logical files verified and whole/range logical SHA-256 correct**, full archive size **4,170 bytes**. All five logical content fingerprints matched the previous O204 no-audio result.

The ordinary non-audio corpus produced a **1,152-byte byte-identical archive** in historical and candidate arms on each host. Direct WAVFLAC candidate returned `None` for the tested WAV forms rather than raising. **O204b question: CONFIRMED.**

The full archive hash still differs Windows vs POSIX despite identical logical hashes and 4,170 bytes. No cross-host physical byte-identity credit. No CPU/RSS/full frozen parity claim. No decoder-with-audio-extras claim, and this does not make the unmerged owner fix a released product.

## Original evidence and remaining gates

[Run #40397842486](https://github.com/FCMO-AI/.CMPCT/actions/runs/40397842486) artifacts:

- Ubuntu [artifact 12686294955](https://github.com/FCMO-AI/.CMPCT/actions/runs/40397842486/artifacts/12686294955), ZIP SHA-256 `b1734677169d32cfe4b21533a226e4a868eb7e22ed4e5e243b94b3012ddca35e`.
- macOS [artifact 12687367611](https://github.com/FCMO-AI/.CMPCT/actions/runs/40397842486/artifacts/12687367611), ZIP SHA-256 `889ce4751aa0db5e0f475577e5bcc29cdc37f0295cf7246d8543232445005bdc`.
- Windows [artifact 12688295197](https://github.com/FCMO-AI/.CMPCT/actions/runs/40397842486/artifacts/12688295197), ZIP SHA-256 `3af7731e2114823f7ae30d2334d15b8093fc6e7d1e699da1b5aa584a4997c2ce`.

All original O204 and O204b science is preserved; a later workflow topology check at `1e0b74...` was red solely because the automatic workflow did not declare top-level concurrency. Follow-up `341c21d...` adds the required concurrency group and `cancel-in-progress: true` without modifying experiment claims; **its final-head CI must be assessed separately**.

**Next executable:** owner PR #225 should adopt both source-exact proofs, reconcile reported issue #538, and close full general/unchanged parity/portability/release gates. No merge, format or version bump from this evidence PR. Discovery policy and `docs/discovery/STATE.json` unchanged.
