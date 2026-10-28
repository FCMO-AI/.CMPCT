# J24B11 — independent signed sparse-quota regression transfer onto existing #573 Reader

**2026-10-28 UTC prospective preregistration BEFORE any J24B11 code or hosted measurements.** This is a separate independent validation of an existing owner, not a new implementation, and it must **not** change or supersede #573, #255, #270, #569, #574 or the original science #700.

## Exact inherited source

Branch parent: [PR #573](https://github.com/FCMO-AI/.CMPCT/pull/573) exact `9f269ce8a13b54e44679942d018b226e8dce4d6a`. #573 inherits sparse helper from owner #255, with `write_sparse_verified` validating extent geometry before writing decoded payload; #573 adds Windows portability handling. Published v0.30 main `80c358f8824ec1b20d349c92ed94c898090969b0` remains unchanged. The exact malformed signed r24 structure already independently proved in [#700](https://github.com/FCMO-AI/.CMPCT/pull/700) / [issue #701](https://github.com/FCMO-AI/.CMPCT/issues/701): original logical size 16384, RAW physical blob 8192, correct extent `[4096,8192,[0]]`, signed mutant `[16383,1,[0]]`, all index SHA / physical bytes reauthenticated and unchanged.

## One question / prediction

Does the **unchanged** candidate Reader from #573 reject this exact nonnegative-size hostile extent **before overwriting a pre-existing destination** (and without leaving temporary stage files), while still reproducing the valid original sparse archive exactly on Ubuntu 24.04, macOS 14, Windows 2022?

Prediction: normal valid archive reconstructs original 16384 bytes and full SHA; signed malformed archive is rejected by `extractall(max_bytes=16384)` with `sparse extent overrun` and cannot modify a preexisting canary or publish a new destination; the original with cap 16383 rejects before directory creation. Original/mutant physical region and schema must match previously frozen scientific SHA-256 from #700.

**Disproof:** any host accepts malicious artifact, changes canary/inode on failure, leaks stage, changes valid original bytes, imports checkout rather than installed package, mismatches original frozen corpus identities, or fails safe undercap. A source-identity mismatch or infrastructure error is not proof of product defect; preserve separately.

## Method and alternatives

- Cheapest dedicated installed three-host court, with genuine signed revision24 archives built by the same deterministic recipe as J24B10. Test negative, positive, canary preservation, no temporary stages, SHA and source evidence, raw artifacts on failure.
- Strong simpler controls: original released #700 three-host defect evidence; #573 already has independently tested sparse SHA/portability, so **do not** invent another sparse helper or duplicate its Reader edits.
- Alternative full cross-mechanism integration with #690/#609/#615 remains later productization, not silently inserted here.
- No product code, core test, release, archive format, threshold or evaluator is changed.

## Promotion boundary

A green test certifies only the precise J24B10 malformed-extent regression transfers to this existing #573 candidate. It does **not** retire #573's inherited 128MiB sparse-hole SHA extraction CPU regression (+101.6ms) or source/destination race, large sparse RSS, other storage kind size inconsistencies, release law, or all-extraction budget integrity. The owner must still reconcile full CI and performance before any merge/release.

No Discovery STATE update: #574 owns that surface, and neither this prereg nor test creates a new process lesson without repeated evidence.
