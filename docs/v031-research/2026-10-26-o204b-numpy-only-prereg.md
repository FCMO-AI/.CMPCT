# O204b — isolate NumPy-present / SoundFile-absent WAV behavior

**Date:** 2026-10-26 UTC. **Status:** preregistered before any result-bearing O204b execution.
**Inherited context:** O204 exact-source three-host minimal-audio court [PR #541](https://github.com/FCMO-AI/.CMPCT/pull/541), [result](2026-10-26-o204-audio-optional-result.md). This is a **new distinct test**, not a retroactive amendment of O204.

## Question

Issue #538 reports a second failure after installing NumPy: `ModuleNotFoundError: soundfile`. Does existing product owner candidate PR #225 also correctly decline its optional WAVFLAC candidate and complete an exact archive when NumPy is present but SoundFile remains absent?

## Frozen controls and gates

- Same fixed original `src/cmpct/codec.py` blob `29526db4203723d83523fc95d074c346b63d7587` and candidate blob `6e116ee1fc348b78d81a541fcaf5cf3d6912d3c4`.
- Reuse the same O204 5-file byte-exact mixed corpus, ordinary binary control, exact Git source assertions, real package-owned native ABI and full real CLI/Reader path.
- Install the base package with mandatory dependencies, then explicitly install `numpy>=1.26` **without** `soundfile`. Assert NumPy is importable and SoundFile is absent. This test must not accidentally reuse the prior no-NumPy outcome.
- Historical create must fail *specifically* through missing SoundFile (not NumPy or other code). Candidate must create valid r24 archive, verify, preflight, reconstruct all 5 SHA-256 matches and give exact selective reads. Ordinary-only candidate archive must remain byte-identical to historical on the same host. Any unexpected failure/modified semantics kills the claim.
- Ubuntu/macOS/Windows; source-exact checkout, independent raw results. Full release parity/performance and supported WAVFLAC decode with extras installed remain outside claim.

**Decision:** confirm independently or retain ambiguity; do not credit O204's first success as proof of this second error. A successful no-dependency court is a necessary but not sufficient condition for accepting O204b. No product code or format changes.