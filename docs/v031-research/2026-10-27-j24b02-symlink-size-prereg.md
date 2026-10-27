# J24B02 — direct S_BLOB symlink size-consistency probe (preregistered)

**Date:** 2026-10-27. **Source:** released CMPCT v0.30.0 / r24 main@80c358f8824ec1b20d349c92ed94c898090969b0; J24B01 physical-frame experiment already established. Separate semantic question on the same Builder-independent RAW frame. **No product, release, format, policy or original J24B01 frozen-test modification.**

## Primary question and forecast

Does a fully reauthenticated **K_SYMLINK** / **S_BLOB** logical row with declared size 136 but exactly 128 actual physical target bytes survive `preflight_archive`, full `CMPCT.read`, and `CMPCT.verify`, unlike the analogous ordinary K_FILE row, while `read_range(128,8)` returns the first eight bytes of the following compressed index?

**Prospective mechanistic prediction:** yes. In currently released code, `validation._validate_storage` validates symlink tag/ref but does not compare size to blob `usize`; `CMPCT.read` returns `_blob` directly for K_SYMLINK before the normal S_BLOB length guard; `verify()` compares physical content SHA but does not compare row size; RAW `read_range` trusts row size when slicing mmap. The generator will use two complete authentic revision-24 archives: control with declared 128 and hostile with declared 136, **same 128 physical bytes and framing**, distinct correctly authenticated primary/tail index and footer. The logical row kind is K_SYMLINK in both. Exact bytes, SHA-256, CRC32 and tail provenance must be recorded.

**Kill/narrow conditions:** any rejection by constructor/preflight/read/verify of the malicious symlink disproves that predicted acceptance tier; any selected range rejection / bytes not matching the tail disproves the range-spill part. Preserve unexpected values and failed assertions; never move the prospective gate to report a success. The unmodified regular-file J24B01 observed result is a **different control**, not an independent symlink reproduction. External symlink safety/extraction are not credited absent direct tests.

## Cheapest evidence

1. Use independent complete-wire synthetic revision-24 generator (no Builder), same physical target across paired archives. Authentic installed `CMPCT` Reader in GitHub Actions Ubuntu 24.04 / CPython 3.11.
2. Measure `preflight_archive`, `CMPCT.read`, `CMPCT.verify`, `CMPCT.read_range` both ordinary and crossing. Emit full raw observations even on prospective FAIL.
3. Distinct-root framing/index auditor independent of `cmpct`: verify decoded MessagePack row kind, blob/frame CRC/SHA, authenticated index/footer, same physical payload, actual returned tail bytes and adversarially corrupted receipts.
4. If confirmed, append a **new specific finding** to existing issue #605 for #569 owner to include symlink semantics in the same bounded size guard. Do not create duplicate product implementation or change J24B01 history.

## Costs, portability, alternatives

The shorter derivation is insufficient to claim a shipping defect across all platforms; a hosted genuine package run is required. A global preflight per read would be a weaker performance architecture than one geometry check using already available blob/index fields. Neither strong cryptographic hash of payload nor the presence of a tail index proves declared member size. No benchmark/throughput/product regression or Windows/macOS transfer claim until measured. Current JSON/index bytes are internal authentication, not an external signature.
