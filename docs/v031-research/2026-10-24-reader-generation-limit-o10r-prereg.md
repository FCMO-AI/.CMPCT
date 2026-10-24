# O10R — ordinary Reader signed-generation resource-bound falsifier (preregistration)

**Date:** 2026-10-24 UTC. **Status:** PREREGISTERED / results unknown at registration.
**Owner:** independent Reader resource-ceiling research, not an O9 journal-speed implementation.
**Exact inherited source:** O9 PR #364 at `1d8701588bdb8ece69749149a60d4b70a643e12f`.
**Released floor:** CMPCT v0.30.0, physical revision 24; v0.31 draft, no merge/release authority.

## Primary question and falsifiable prediction

Does ordinary `CMPCT(path)` enforce the configured maximum signed generation payload and maximum journal depth **before** decoding/replaying untrusted footer metadata, consistently with `preflight_archive`? The Reader source currently appears to decode footer `usize` directly and traverse `prev` without the `ParserLimits` checks present in the strict validator. A footer whose payload is small in compressed bytes but exceeds `CMPCT_MAX_GENERATION_BYTES` is a cheap falsifier.

**Prediction O10R-1:** the inherited ordinary Reader will accept an otherwise valid Builder-created r24 archive with an authenticated, compressed, no-op journal generation whose decoded bytes exceed a low test-configured generation cap, even though strict `preflight_archive` raises `ResourceLimitError`. A signed journal must not bypass configured resource policy merely because it is valid and compressible.

**Prediction O10R-2:** with `CMPCT_MAX_DELTA_DEPTH=1`, two individually valid signed appended generations will be accepted by ordinary Reader despite strict preflight refusing the excessive depth.

## Cheapest real-product controls and disproof

1. Build a one-file archive using the current **authentic Builder**; assert positive normal Reader and strict preflight under the same environment.
2. Use authentic `transactions._append_generation` to append a list of non-matching `ren` operations (logical state unchanged), large enough that its **uncompressed MessagePack** exceeds a low generation cap (8,192 bytes). Require a real compressed footer and verify the precise `FTR.usize` field exceeds the cap. Assert strict preflight refuses it. The target Reader **must** also refuse it under the same cap.
3. Build a separate two-generation archive with real appends and `CMPCT_MAX_DELTA_DEPTH=1`; assert strict preflight refuses and Reader honors the same ceiling.
4. Preserve a control showing the archives remain readable and exact under ordinary unrestricted defaults. Never weaken SHA/checkpoint semantics, adjust limits in the product, or mislabel lower-rung structural observation as hosted end-to-end evidence.
5. If ordinary Reader already rejects both, retire the hypothesis; do **not** manufacture a bug. If the discrepancy is genuine, first preserve a negative court, then consider a minimal fix that does not turn checkpoint-only cold open into an eager expensive validator import. Measure side effects before product credit.

## Alternatives and risks

A global always-on `preflight_archive()` during open would duplicate archive traversal and cost cold startup; it is a strong correctness control but not a viable unmeasured production shortcut. A constant-only cap divorced from `ParserLimits` would diverge under overrides. Prefer shared policy with lazy resource loading or a small implementation-neutral limit accessor, and preserve any recovery contract. Handle malformed footer candidates without converting a recoverable partial tail into a fatal error.

A failure in Windows/macOS installed-wheel tests, cold startup, memory, hardlink/symlink semantics, or exact-head safety evidence blocks promotion, even if the focused resource test turns green.

## Concurrency / ownership

O9 PR #364 owns `_index_from_footer` replay and prewrite Reader composition. O10R owns only signed generation size/depth resource falsification, on its **own branch** based on the exact O9 HEAD. The O9 owner's branch and tests remain untouched; this is adjacent security/evidence work, not a second O9 implementation. If the owner modifies the same narrow surface before a late write, reconcile and do not overwrite.

**Research credit boundary:** branch/tests/proofs are draft evidence. No release, no new version, no assertion of complete DoS containment, no corpus-specific tuning. Keep the shared Discovery `STATE.json` unchanged until decision-relevant reconciled truth exists.
