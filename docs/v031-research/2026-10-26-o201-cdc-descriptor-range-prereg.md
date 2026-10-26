# O201 — CDC declared-length versus actual-blob Reader semantic consistency (preregistration)

Date: 2026-10-26. **Classification: scientific court only, no implementation or release permission.**

## Authority / provenance

Canonical CMPCT v0.30.0, revision 24, prospective development baseline `agent/v031-development@4545d7d5b2a0b712b4b00f5a9c291d4a3a9e169b`, authentic Reader blob `e716233403dabd0966863c45635e18fa5ac6afb8`. Independent O198 #532 found sparse extent `ln` inconsistency on a different (S_SPARSE) representation; its owner retains that fix. This O201 question is **S_CDC descriptor semantics**, no competing sparse Reader patch. Reuse O198's verified wire-authoring/installed-source instrument structure with explicit attribution.

## One falsifiable question

For one complete checksum-consistent revision-24 file consisting of one RAW physical blob `ABCD`, indexed logical size 4, whole-file SHA of `ABCD`, and logical `S_CDC` records `[[declared_length, blob_0]]`: does a forged declared length 1 or 2 let `verify()` and `read()` return success while `read_range(2,2)` returns incorrect bytes/zeros? Does `extractall(metadata=False)` reject the descriptor because it checks individual decoded lengths? Positive control declared length 4 MUST pass verify, full read, full range, late range and extraction. Also test over-long length 5.

## Competing predictions and falsifiers

P1: ordinary full read ignores the declared per-CDC length and checks only concatenated bytes; range filtering trusts that length; the mismatched descriptor passes full verification yet returns wrong short/zero range. P2: Reader validates descriptor at admission, or range reconstructs by actual lengths, so no mismatch is observed. Existing per-chunk extraction may fail closed under P1: do not claim all endpoints incorrectly publish bytes. A valid control failing prevents attribution; changed or unsigned source prevents source-exact evidence. Archive/footer/index SHA and payload CRC must be fully authentic, not mocked; original Reader and conformance/release policy remain untouched.

## Cheapest decisive experiment

Adapt the already proven O198 authentic complete-wire court for S_CDC, run independent installed Python package on Ubuntu (expand to macOS/Windows if a real semantic divergence appears), save raw per-case hashes and observable outcomes, verify exact imported module bytes from head and prereg ancestry. Controls: `ln=4`, `ln=1`, `ln=2`, `ln=5`, all with same payload/blob/SHA. If no mismatch, retire this narrow hypothesis. If reproduced, preserve negative and notify the owning v0.31 Reader lane before attempting product repair. Do not merge/circumvent other Reader owners.

## Limits / economics

This is a synthetic, index-hash-consistent adversarial archive, not a proven corrupted real Builder output; not a remote exploit. It tests semantic consistency and existing extraction refusal, not release readiness, physical throughput, or end-to-end CPU/RSS. The follow-up candidate should prefer a single bounded geometry validator shared by CDC and sparse if ownership and genuine historical semantics permit, not duplicated ad-hoc checks. No gate weakened.
