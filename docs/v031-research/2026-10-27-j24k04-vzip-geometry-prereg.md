# J24K04 — Preregistered S_VZIP physical/logical geometry falsifier

**Date:** 2026-10-27 UTC. **Stage:** prospective research; no product, format, release or benchmark mutation.
**Exact source:** published CMPCT v0.30.0 / physical revision 24 `main@80c358f8824ec1b20d349c92ed94c898090969b0`.
**Immutable builder-independent oracle:** `tests/conformance/v24-virtual-zip.json`, original archive SHA-256 `bed3a5d3bf3987f4c123e782effe9cc21a5d7253a9b2eca8a9af7b2522f4d839`.

## Single primary scientific question

Can a completely reauthenticated index declare a virtual ZIP logical length larger than its physically reconstructible skeleton-plus-payload bytes, pass strict `preflight_archive()` and cause ordinary `CMPCT.read_range()` to silently return fewer bytes than the authenticated request?

## Baseline, mechanism and strong simpler control

The unchanged golden declares a 128-byte virtual ZIP with literal skeleton lengths [39,77], and one 12-byte stored payload. Exact reconstruction has 39+12+77=128 bytes. The strong control must preflight, completely read, verify SHA-256, and return the frozen correct range. The tested mutation changes *only* the authenticated recipe total field and owning file row's logical size from 128 to 129, leaves every physical blob/record and each literal length, payload and recipe digest unchanged, and recompresses/re-hashes **both** primary/tail indexes and footer. It is not corruption of CRC or index checksum.

Prediction: strict preflight **ACCEPTS** the contradiction because it validates `recipe.total == row.size` but does not compare the total against physical skeleton length and stored payload contribution. Full `read()` **REJECTS** due to reconstructed length mismatch; `verify()` also rejects. Selective `read_range('nested.zip',128,1)` **RETURNS b''** rather than refusing the impossible request. A valid control's request at offset 128 must be out of logical bounds.

Counter-explanations: a corrupted index hash; physically changed data; invalid original frozen golden; footer recovery using old index; malformed MessagePack; incorrect reconstructed ZIP bytes; an already-enforced VZIP geometry check. The instrument explicitly checks these.

## Decision and disproof conditions

If preflight refuses, or selective read returns a typed error, or the golden itself fails control, preserve the negative and retire/narrow the proposed defect. An unexpected result must not trigger editing the predicted criteria or the frozen golden. A succeeding scientific court only establishes the narrow Python r24 structural/range disagreement; it is **not** a patched product, a data exfiltration claim, native parity, cross-platform generality, or release credit.

## Alternatives / BONK and ownership

Cheapest local source inspection already shows `validation._validate_recipe` checks shape/field types but not physical skeleton contribution; `codec.range_vzip` slices skeleton bytes under an independent logical upper bound. An independent fixed-wire experiment is cheaper and sharper than changing the Reader or rebuilding an archive. S_PACK (J24K01/K02) and direct RAW (J24B01/B03) defects are not this representation; do not repeat their mutation surface. VZIP SHA/integrity is separately researched in PRs #436/#443. The composed Reader is owned by PR #569, so this branch changes **no** Reader/Validator product code. Reconcile with that owner if reproduced.

## Resource, semantics, controls

Original golden ~642 physical bytes, one 128-byte logical file; no large allocations. Charge the exact changed index bytes, keep archive content and physical record bytes unchanged, compare independent logical source bytes/hashes and both index copies. No benchmark speed or compression credit. This uses existing fixture and independent Python MessagePack/Zstandard primitives through CMPCT's package-owned codec for index encoding; it is not an independent implementation of the Reader. Strong independent raw-receipt checks should be added if the hosted observation is decisive. All data are public fixed synthetic bytes.

## Expected handoff

Source/head/test blob SHA, direct operation outcomes, exact output length, archive/index/physical SHA, original negative if any, workflow status and artifact identity; compare against concurrent PR owners before any implementation. Keep Discovery Engine state unchanged while #574 owns its reconciliation.
