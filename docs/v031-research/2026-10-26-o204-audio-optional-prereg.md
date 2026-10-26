# O204 — WAV/FLAC optional-dependency installed-product court (preregistered)

**Status:** PREREGISTERED, before the first result-bearing O204 workflow run.
**Date:** 2026-10-26 UTC.
**Authority:** `AGENTS.md`, `docs/AGI_ENGINEERING_STANDARD.md`, `docs/discovery/DISCOVERY_ENGINE.md`, `docs/PRE1_RELEASE_POLICY.md`.
**Ownership:** independent evidence continuation of existing owner PR #225; no product-code mutation, no attempt to supersede owner. Issue #538 independently reports the missing-dependency failure.

## Question and exact controls

Can the existing O225 `src/cmpct/codec.py` candidate perform lossless, general-purpose archive creation in a *fresh Python environment with only its declared mandatory dependency, msgpack*, when input contains a valid PCM16 WAV, unsupported-but-valid PCM32/PCM8 WAVs, malformed WAV-like bytes, and unrelated binary data?

Freeze before measurements:

- Historical development control: `agent/v031-development@4545d7d5b2a0b712b4b00f5a9c291d4a3a9e169b`; `src/cmpct/codec.py` blob `29526db4203723d83523fc95d074c346b63d7587`.
- Existing unmerged candidate: PR #225 `4361424ddbe356463a6eab94361f3b950c120967`; codec blob `6e116ee1fc348b78d81a541fcaf5cf3d6912d3c4`.
- Both run **the same fixture bytes and identical 0.30.0 r24 CLI/Reader**, changing only the single codec module's contents; a byte-for-byte copy of the candidate's remaining Python source is used for the historical control. Git blob identity of both codecs is checked before use.
- Fresh venv installs only `msgpack`; assert `numpy` and `soundfile` are missing, not simply unused. Do not add undeclared mandatory dependencies as a workaround.
- `PYTHONPATH` is pinned to each isolated product-source copy. The CLI must run in a subprocess, not as an in-process monkeypatch, and must create a real self-contained archive.
- All logical members must be read back byte-exact, validated with independent SHA-256 and `CMPCT.verify()`/CLI `cat`/`range`. Check revision 24. CRC alone cannot prove identity.

## Prospective decisions

1. **Positive expected historical fault:** baseline create on PCM16 WAV exits nonzero with an explicit missing optional audio dependency (numpy/soundfile), *not* an unrelated error. If the baseline succeeds or fails differently, attribution is unproven and O204 must report ambiguity rather than adjust the control.
2. **Positive candidate:** candidate creates a valid archive, verifies it, and all expected file bytes match, with no audio extras. Candidate's `wavflac_compress` returns `None` for valid supported PCM16 when optional audio is unavailable, and also returns `None` for PCM32 (unsupported) rather than raising.
3. **No regression control:** an independent ordinary-binary-only corpus completes in both source variants with matching file reconstruction (the candidate is not granted archive-size credit merely from this).
4. **Negative/kills:** any candidate abort, lost/corrupted content, changed r24 grammar, or hidden dependency invalidates the product-acceptance claim. Exact-head generic CI and full performance/portability gates remain separate promotion obligations.

## Evidence and limitations

Hosted runs must retain the exact commit SHA, parent and candidate codec blob SHAs, runtime version, pip freeze and per-case create/verify/read outcomes. This is a **minimum-runtime source-and-semantics acceptance**, not a released-product, complete 15-row performance, optional FLAC-decoder portability, or Linux/macOS/Windows file-permissions guarantee. Preserve full red outcomes. A future run may add an `[audio]`-enabled court as separate evidence, without revising this frozen gate.

## PARETOBONK

The smaller control is the historical one-file difference already proposed in #225, not a new WAV codec rewrite. The candidate's low-cost exact-byte court has direct product value and can disambiguate #538 without duplicating implementation. Additional research on audio format variants or new numerical selectors is lower-value until this already-existing candidate earns actual hosted evidence.