# J24K01 — PACK selective-range structural consistency (prospective preregistration)

Date: 2026-10-27 UTC
Status: PREREGISTERED BEFORE INSTRUMENT AND BEFORE PRODUCT MUTATION
Source authority: `FCMO-AI/.CMPCT`, shipping `main@80c358f8824ec1b20d349c92ed94c898090969b0`, release v0.30.0, revision 24.
Independent fixture/control owner: PR #307 (`256a263748b9f65b4bc00dd572799e4f00ae06e7`), hostile native index oracle: PR #314 (`4c76440be1a84b60e574d602617740b70025df47`).
Branch is intentionally stacked on #314; DO NOT MERGE / RELEASE without owner reconciliation, exact-head CI and full release gates.

## Question and predicted observation

Can a fully authenticated but **structurally invalid** revision-24 S_PACK index make ordinary Python `CMPCT.read_range()` return success or short/wrong data although (a) strict Python preflight rejects the same archive, (b) Python `read()` rejects it and (c) the independent native C ABI correctly refuses the malformed index at open?

The read-range implementation currently slices `pack[base+start:base+end]` but does not check the declared PACK slice length against the logical file size or blob boundary. Python's slice semantics silently truncate. Prediction:
- `S_PACK` declared slice length increased by one: preflight and `read()` reject; `read_range(0,size)` returns success with the original full bytes, silently ignoring invalid declared length.
- `S_PACK` offset set to `pack_size - logical_size + 1`: preflight and `read()` reject; `read_range(0,size)` returns fewer than requested bytes without exception.
- `S_PACK` offset beyond unsigned 64-bit accepted Python integer range: preflight and `read()` reject; `read_range(0,size)` returns empty bytes.
These are predictions, not measured facts at preregistration.

## Exact controls, evidence and falsifiers

Reuse unchanged RAW and Zstd **independently assembled, fixed-wire** archives from #307, each with four logical members sharing exactly one physical PACK owner. Bind immutable archive SHA-256, source Reader Git blob and original expected bytes. Forge metadata via #314's `authenticated_mutation`: decompress signed primary index, modify only `omega.bin` S_PACK tuple, recompress and authenticate both index copies, preserve byte-identical physical blob and its CRC/SHA header.

Before calling `read_range`, independently establish: positive archive opens, `read`, `verify`, and `read_range` exact; each mutated archive is self-consistent, `preflight_archive` refuses specifically S_PACK geometry; `read()` must refuse invalid members. Then inspect `read_range` actual bytes, error class and requested/returned length. The *referee* cannot merely trust the instrument-reported labels: verify hashes, signed metadata identities, physical bytes, expected immutable content and exact observed outcomes in an independent pass.

Falsification: If ordinary Reader refuses these malformed forms before or during selective read, or returns no silent success/short data, the hypothesized discrepancy is falsified. If decoder errors for unrelated reasons (e.g. corrupted physical CRC) the experiment is invalid and must be repaired, not counted as a positive result.

## Better control / alternative explanation / kill condition

The correct native S_PACK validator in #314 and strict Python preflight already reject all malformed tuples; the question is specifically the **ordinary Python Reader selective API**, not whether structural validation exists anywhere. A benign short read at EOF is not a false positive because this test requests the entire declared in-bounds *logical* member. The fake archives are not claimed authentic to a trusted external signer; index integrity only means internally consistent bytes, not provenance.

Initial work is **science/test-only**, not an unreviewed Reader fix in the already-owned #569 composition. After decisive evidence, the cheapest candidate may enforce O(1) tuple checks at ordinary S_PACK selected read or centrally at Reader open; evaluate full-read compatibility, cold-open cost and strict-geometry owner overlap before choosing.

## Cost and promotion

At most 2 immutable vector families × 3 forged metadata cases; small existing physical blobs, no large allocation or archive benchmark distortion. No new codec, format revision, source-specific dispatch, historical evaluator relaxation, score gardening or release-credit claims. This is a structural cross-API consistency test, with any future product change requiring source-exact integrated Reader, cross-host portability and regression measurement.

## Concurrent ownership and next decision

#314 owns native S_PACK malformed-index rejection; #307 owns immutable PACK goldens; #569 owns broad composed Reader admission. This branch ONLY investigates ordinary Python selective behavior and will communicate a bounded result to those owners without modifying their branches or mutable discovery-state cache. If the mismatch is confirmed, the next unclaimed action is smallest O(1) geometry admission at the selected S_PACK read boundary, but only after owner coordination and performance accounting.
