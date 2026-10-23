# O5 preregistration — equal-plaintext different-wire postpreflight export

Date: 2026-10-23
Status: **FROZEN BEFORE O5 CODE/RESULT**.
Research branch: `agent/phased3-v031-deflate-export-mutable-source-o2-20261023`; current O4 result persisted at `cc93965c55f8e099a987905735372eb35d07ac93` (check live branch before implementation).
Product owner PR #284, unchanged Reader blob `b0c8eb5eddd5591524b3e9c9a640d9266ccbbbdb`.
Episode: `v031-deflate-equivalent-wire-epoch-o5`.

## Discriminating question

O2 found a real invalid-ZIP output after source mutation between physical verification and copy. O3 full staged-ZIP semantic verification prevents invalid publication. O4 compressed-wire SHA binding also rejects, with potentially lower alias CPU but a *stronger source epoch identity policy*. Is that stronger rejection essential to exact logical ZIP reconstruction? Can source bytes differ while both physical Deflate encodings produce the same *correct* logical content, checksum and SHA?

### Frozen mechanism and control

Use Builder-independent revision-24 direct-Deflate level0 archive from O2. RFC1951 stored blocks align the first three header bits BFINAL=1, BTYPE=00; the remaining five padding bits are ignored. Flip **0x08** in the first stream byte *after* original validator returns. Stream length, raw decoded bytes, CRC32 and SHA256 remain unchanged while physical SHA256 changes. Verify with independent `zlib.decompress(-15)` before running export.

- Control A: static verified owner export after switching the padding bit **before** preflight must produce a valid ZIP; original Reader logical `read()` remains correct.
- Control B: deterministic padding flip **after** O3 owner preflight but before ZIP copy. O3's stage-then-full-logical-integrity check should accept/publicly replace (valid logical ZIP) despite compressed stream SHA mismatch to original.
- Control C: same equal-plaintext padding flip after O4 initial wire preflight. O4's wire-match guard should reject/preserve prior destination because bytes changed, although independent compressed stream still decodes exactly.

Expected fork: O3 allows semantically valid postcheck compressed wire variation, O4 is stricter and may reject such concurrently produced *valid content*. This is neither a security failure of O4 nor proof that accepting mutable sources is optimal; it identifies the source-epoch **policy cost**. If flipping alignment padding is rejected by any independent zlib or changes logical SHA, this mechanism hypothesis is falsified and we must not attribute downstream behavior to equivalent physical encodings.

Strong control: PR #284 already independently demonstrated equal-plaintext equal-size 8-byte level-1 vs level-9 Deflate streams for 512 'a' bytes. O5 uses an even smaller one-bit RFC1951 header padding perturbation and reuses O2/O3/O4 source. No runtime performance evidence or broad generalization claim.

## Decision

If prediction holds, product owner must choose explicitly: strict source-epoch snapshot consistency via wire binding (reject equal-content concurrent changes) or reconstructed-output semantic consistency via actual ZIP logical SHA/CRC verification (may accept equal-content source changes). Neither permits corrupt-output publication. No release thresholds, format, test evaluator, committed historical data, or product implementation may change. Source stays research-only. Hosted run must preserve original JSON and exact commit. O4's earlier positive becomes *narrowed*, not negated.
