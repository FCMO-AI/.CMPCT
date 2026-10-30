# J24G93 — Preregistered legitimate orphan-tail recovery counterexample

**Date:** 2026-10-30 UTC. **Owner scope:** source-exact research only, no Reader/Writer/validation/format/version/release edits.

## Parent authority and prior knowledge
- Published v0.30.0 r24 `main@80c358f8824ec1b20d349c92ed94c898090969b0`, Reader blob `e716233403dabd0966863c45635e18fa5ac6afb8`.
- Parent **#856** exact `f29561c5e2d36a8f47aa35f61191911c0611be6b` established on Ubuntu and Windows that a one-field footer `prev` rewrite can skip a true DELETE with unchanged payload SHA (Issue #857). This new narrow question is a **counterfactual guard design disproof**, not another duplication of that test.
- Earlier Issue #649 owns *N-orphan quadratic decoding cost*, not this correct post-recovery link topology.
- A local independently constructed *wire-only* O0 (before this prereg) showed a legitimate-looking successor could link past a SHA-valid unrooted orphan. That O0 has **zero installed Writer/Reader credit**.

## Primary question / prediction
Can the unchanged **public Writer** successfully append a new committed DELETE after an archive contains a SHA-256-valid but **unrooted orphan delta** at the end, and correctly link its new footer to the most recent recoverable committed footer *behind* that orphan?

The hypothesis H1 predicts the newly appended valid newest footer's immediate physical predecessor is a standalone SHA-valid orphan footer **that is not its logical `prev`**. The actual Writer must choose the prior complete signed chain rather than the nearest physically present footer. H2 predicts Reader read/verify and strict preflight return the full prior state with the new DELETE, and damaged-newest-footer recovery ignores the latest and returns the correct prior state. H1 is falsified if the public Writer rejects or emits an incorrect `prev`; H2 is falsified if exact logical/physical validation fails. Preserve failures, don't weaken semantics.

## Baseline / simpler controls
- New 16 and 128 file deterministic Builder archives; apply three actual public `append_delete` commits. All hashes/contents verified.
- Append one extra *syntactically valid* orphan kind=delta footer with uncompressed `msgpack.packb({'blobs': [], 'ops': []})` and SHA-256 of its own payload, but `prev=0`: it has no reachable checkpoint ancestor. Verify the Reader continues selecting the earlier valid chain.
- Call **unmodified public `append_delete`** on one more member. Verify its new physical SHA-valid footer chooses the latest previous recoverable generation (skipping orphan), produces exactly one more deletion, remains readable/strict-preflight-correct. Check the independent wire lineage and compare against a fresh normal control without orphan.
- Tamper terminal footer SHA: same archive should recover the state *before* this fourth delete.

## Alternatives / falsifier and exported costs
A naive guard that requires the nearest physically present SHA-valid footer as parent may detect J24G92's altered predecessor but could also reject this correct crash-tail repair. This experiment is the cheapest physical falsifier before choosing any r24 reader guard. Stronger sequence binding in a future format, external archive attestation, explicit anomaly warnings and parser-side bounded scan are different future design classes. This court does **not** establish which is best.

All cases use actual installed product with exactly the inherited Reader blob, two hosts Ubuntu and Windows, genuine Builder/Writer mutations and original size/SHA receipts, detached raw wire checker. It does not emulate a power-loss or assert cross-filesystem durability; it manually injects a valid orphan with no checkpoint ancestor to exercise recovery semantics. No release benchmark, RSS, native or macOS claims. Keep original full and modified archive SHA distinct.

## Decision
If H1+H2 pass on both hosts, **RETIRE naive nearest-physically-present-SHA-valid-footer ancestry validation as a general backward-compatible fix**. This is a counterexample to a tempting guard, not proof that no r24 integrity mitigation is possible. If any counterexample fails, preserve exact witness and narrow. Result belongs to Issue #857 and parent PR #856; leave shared Discovery STATE under #574 unchanged.
