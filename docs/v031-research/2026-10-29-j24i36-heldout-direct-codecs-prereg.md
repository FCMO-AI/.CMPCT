# J24I36c prospective held-out direct-codec CRC check — 2026-10-29

Status: **preregistered before new fixture generator, test or workflow code**. Source owner: [draft PR #765](https://github.com/FCMO-AI/.CMPCT/pull/765), inheriting #759 exact base `e67ed337e78e021ba91f7bc6bdc271ae0ddd6b51`. No release, format or frozen benchmark modifications.

## Decision question

The proposed native fused-CRC verifier applies to every `Storage::Direct`, but the original installed court tested only RAW (codec 0), Zstd (1), and Deflate (4). Does the exact candidate preserve first-party Python `verify` and compiled Rust `verify_complete` interoperability on *different* direct representations (WAV/FLAC 2 and Zstd-dictionary 3), each with a valid independent fixed-byte r24 archive, and detect a mutation to **only** the referenced direct blob's physical CRC field?

## Immutable controls and method

Use the **already frozen, builder-independent** `tests/conformance/v24-wavflac.json` (Git blob `f74e82b42821af0e9cb4a35e94e486c6b6582f75`) and `tests/conformance/v24-zstd-dictionary.json` (blob `d0f4329b6aba2a06a898bbb8d80dbde9a6d1e344`). Decode their exact archived base64 and validate their committed physical SHA and size **before** testing. Do not edit/regenerate these goldens.

Parse primary index framing and enumerate physical CMA4 records by **bounded lengths**, not guessed byte occurrences; select the record with codec 2/3 (not the dictionary's separate RAW record). Flip bit 0 in only the CMA4 CRC32 field at record+28; verify all other archive bytes including index and footer unchanged and confirm the full archived SHA differs. Keep original+mutant files/receipts as raw hosted artifacts.

Run installed real Python `CMPCT.verify()` and actual compiled native `Archive::verify_complete()` on identical original and mutant files. Both implementations must accept originals as one member and reject the CRC-only mutants. Existing three-codec and symlink courts remain mandatory. This extension earns **held-out conformance evidence** only; no whole-product benchmark or product-release credit.

## Prediction, alternatives, and disproof

Prediction: CRC describes decoded exact logical raw payload for every direct codec, even where encoded content is transformed (WAV/FLAC or dictionary). Thus the fused CRC compares the correct bytes with **no second full traversal**. Alternative: one codec's physical CRC binds a different representation or native reader has a codec-specific decoding mismatch. A valid unchanged golden rejected by either verifier **falsifies promotion** for the general direct-codec implementation. An accepted CRC-only mutant likewise falsifies it. Do **not** weaken a golden, change its hash, relax verifier semantics, or declare a skipped native test green.

There is still unmeasured cost for each direct codec, no composite physical-record CRC coverage, no claim about malformed zero-length encoded payloads (owned by #763/#767), and no authorization to change the public version. This is a bounded adjacent check on the current claimed mutation surface, not a competing native implementation.
