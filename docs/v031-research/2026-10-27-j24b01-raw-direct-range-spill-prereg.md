# J24B01 — RAW S_BLOB selective physical-boundary falsifier (preregistered)

**Date / scope:** 2026-10-27; independent scientific question on released v0.30.0 / revision 24, `main@80c358f8824ec1b20d349c92ed94c898090969b0`. No product, format, frozen benchmark, evaluator, or release gate edits.

## Primary question

Can `CMPCT.read_range()` for direct RAW `S_BLOB` return bytes *beyond its declared physical owner's frame* when a fully reauthenticated revision-24 index assigns an oversized logical member length, even though strict preflight and full `read()` reject the archive?

## Causal hypothesis, baseline, control, uncertainty

Released `reader.py` binds a range only to `row[4]` (index logical size). The RAW fast path computes `base = record_offset + BHDR.size + physical_meta_len` then returns `self.mm[base+start:base+end]` without bounding `end` by the physical header/index owner length. Python mmap slicing can therefore return bytes from the subsequent copied tail index. A valid index directs `row[4] == physical blob usize`, so normal files are unaffected.

Create **Builder-independent** images with one `S_BLOB` RAW frame and primary/tail indexes fully recomputed; keep physical frame, CRC32, SHA-256, blob table and footer framing legitimate. Negative case alters only `row[4]` from 128 to 136. A legal `read_range('direct.bin',128,8)` under the altered logical index is predicted to return exactly the first eight stored bytes of the *tail encoded index*, despite no physical member bytes beyond 128. A distinct in-frame range must return correct original content; an untouched archive must serve exact full and selected bytes and pass preflight/read/verify.

**Strong simpler comparator:** ordinary `CMPCT.read()` should reject the same altered archive due to logical length mismatch and structural `preflight_archive()` should reject it; direct `read_range` should not silently relax physical ownership. If the constructor or an inherited gate already rejects the altered image, the hypothesis is falsified (not rescued by changing data). If range returns no spill / raises before publication, hypothesis falsified. If strict preflight unexpectedly accepts it, report a different, broader defect rather than claiming the predicted split.

## Evidence rung and adversarial design

1. Instrument synthetic fixed-wire r24 RAW with physically independent archive fields (no Builder use). Freeze/reveal source SHA and on-disk case SHA-256, original physical payload/hash, exact tail bytes, tuple arithmetic, range responses and individual error types.
2. Run the **authentic installed package** in fresh GitHub Actions on Ubuntu CPython 3.11, exact HEAD, with source fixture and no source edits.
3. Check both fully reauthenticated bad index and unmodified strong control. Independently validate wire offsets and JSON report with an auditor that does not call CMPCT; corrupt report data intentionally to establish fail-closed evidence.
4. If significant, hand off only a bounded `S_BLOB` RAW physical-geometry guard to the composed Reader owner #569, with no implementation collision.

## Differentiation / concurrency

Existing research #263/#274 owns **optional content-authenticated RAW selective reads** (CRC/SHA policy); J24K01/#598/#601 owns **S_PACK** physical slice geometry; #560/#564/#568 owns sparse/CDC/fixed geometries. This is instead a **physical frame ownership** boundary of ordinary direct RAW `S_BLOB` without claiming a new cryptographic authenticity tier. Initial open PR/issue search found no narrow implementation owner for this exact signed direct RAW logical-size spill. If another owner appears, collaborate and avoid parallel product changes.

## Costs, disproof, limits

Expect constant-time bounds from existing physical metadata in a candidate repair, not a full archive preflight per selected read. That expectation is unmeasured. Only ordinary direct RAW and an attacker-inconsistent metadata index are probed; no claim of arbitrary file disclosure, externally signed authenticity, compression benefit, Windows/macOS transfer or release readiness. Source/format remain unchanged, all past science/evaluators preserved.

**Scientific decision:** confirmed only after authentic installed Reader plus independent wire/receipt evidence. Otherwise mark falsified/ambiguous; no positive claim inferred from static reading.
