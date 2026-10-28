# J24C07c — prospective genuine mode-2 regenerated Deflate compatibility falsifier

Pre-observation addendum, 2026-10-28 UTC. Scoped to PR #638's installed composed Reader, not a representation redesign or release claim.

## Baseline and distinct question
The original J24K05 court checks mode2 *metadata algebra* but does not execute a genuine revision-24 mode2 archive through the source-composed Reader. Mode2 regenerates Deflate from raw bytes; its compressed stream length cannot be inferred simply from raw blob uncompressed size. Is #638's stronger preflight still compatible with a legitimate mode2 signed archive, and does a signed but impossible mode2 length declaration fail closed at the actual selective/full reconstruction boundary?

## Exact frozen input and construction
Use existing independently frozen golden `tests/conformance/v24-virtual-zip-deflate-mode1.json`, SHA-256 `842896d0140844841e02b2c882ca4f81efda16771caacea6248787fe98273573`, 130 logical ZIP bytes, 12 raw bytes, 14 original compressed bytes, zlib level 6. First verify by independent zlib raw-deflate compression that its raw member reconstructs the original 14-byte stream exactly. This is a control, not an assumption. Then modify **only** authenticated index recipe mode from retained `1` to regenerated `2` and stream reference to the same raw blob, recalculate both matching indexes and their SHA-256; do not change any original physical blobs. This produces a valid mode2 archive with identical reconstructed ZIP bytes.

## Prediction, independent controls and kill
Positive: strict `preflight_archive` accepts, full `read` matches original raw ZIP SHA-256, `verify()` passes, real `zipfile.ZipFile` validates, and representative early/middle/end/empty ranges match the original. Negative: after changing the regenerated stream's declared compressed length from 14 to 15 and both logical totals +1, the signed recipe **may** pass metadata-only preflight because regenerated size is unknowable without compression. Do not mislabel this as a preflight win. However full reconstruction must raise and one logically in-bounds byte beyond the 130 physically reconstructible bytes MUST raise a short-read error, not silently return empty. If any positive fails or negative yields empty bytes, this compatibility claim fails.

## Resource and custody scope
The third-host court installs noneditable CMPCT, reuses same frozen reader and tests, logs complete archive SHA, index/digest identity and unchanged physical blob bytes. No changes to source, reader, frozen J24K04, official gates or experiment thresholds; only a new independently authored mode2 test plus a workflow inclusion. This is bounded correctness, not complete mode2 hostile proof, not a cryptographic claim for unchecked partial reads, not a product-wide benchmark. A failure preserves the actual contradiction rather than weakening #624's projection.
