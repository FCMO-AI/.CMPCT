# J24I30 — Native r24 strong verification of symlink payloads (prospective)

**Frozen question — before instrument or candidate implementation.** Research-only, no product/source mutation, no format/release/promotion claim. Base exact `aba3f2d72212b484d58bef4ca56ceaaf8dda9d09` (#750), published `main@80c358f8824ec1b20d349c92ed94c898090969b0` v0.30.0/r24.

## Evidence-based starting point

The installed Python #750 Reader now checks an optional present file-row SHA for direct `K_FILE` and `K_SYMLINK` when strong `CMPCT.verify()` is called. Native `cmpct-core` `Archive::verify_complete()` in `native/cmpct-core/src/vzip_dispatch.rs` blob `60e53b1e85c30d413e379052bb288ed3b51ec30d` visibly continues past every entry with `kind != 0`. The read-only native archive parser resides in `native/cmpct-core/src/lib.rs` blob `463c50633be74423e92a074b7d7577db6a4b0cf9`. A source inspection is a prediction, not yet a hosted product result. Native core and Python have different intended extraction surfaces, but a method named *verify_complete* should not silently claim strong verification of archived symlink payloads unless this limit is explicit.

## Preregistered question and hypotheses

**H1 (expected):** For one authentic r24 archive containing only a genuine regular symlink entry, the native `Archive::verify_complete()` returns success with 0 regular entries both on an unmodified source and on a syntactically valid rehashed-index variant whose optional 32-byte symlink row SHA contradicts unchanged authentic physical payload. The #750 Python strong verifier rejects the contradictory variant. A separate physical-blob mutation may also be accepted because native does not traverse symlink entries. If the native parser rejects either variant during open/preflight, classify the source-based prediction as falsified or narrowed, not a negative product result.

**H0 / simpler alternatives:** Native accepts only regular files intentionally and symlink entry contents may not be within the documented public portable verify contract. The experiment must distinguish **semantic coverage gap** from corruption of index format or archive construction. Accepted original and rejected row-hash-variant under native would refute H1. An error during setup/build cannot count as refutation of product logic.

## Cheapest evidence rung and controls

Use the exact already-proved #750 `source_parts` / `with_row_hash` wire converter (blob `c024b6e05926c6968301e32dcba8b2502a7125ca`) and a genuine one-symlink archive built by the unchanged Builder. Do not modify original frozen r24 direct-codec vectors or production Reader. Re-sign both unkeyed indexes and authenticate original physical bytes separately. The independent boundary is a Rust integration test invoking `Archive::open` and `verify_complete` from the actual crate, not Python code pretending to model native behavior. Controls: no-attack valid symlink, correct present digest, wrong present digest, wrong physical payload byte; absent/empty hash unchanged. Confirm Python strong verification on the same byte specimens and verify that normal source archive hashes remain unchanged. Require a PASS on the valid control before interpreting negative. The observed number of verified entries is part of the result.

**Kill condition:** Any native refusal of a reauthenticated wrong-present-SHA symlink, any archive structural mismatch, identity drift, missing original control, or source/build mismatch kills or narrows the predicted acceptance. Native read/extract may legitimately have narrower semantics; do not infer exploitability from a source-only or test-only result. Use installed same-source Rust/Python on Ubuntu (and macOS if the small court is portable), retain logs/JSON and exact source SHA.

## PARETOBONK and ownership

Do not duplicate #750's direct-member Python fix or #751's separate hardlink-alias SHA court. This question targets **native complete-verify coverage of symlink entries**, a different codepath/meaning. Review related native/portable/metadata owners before any product patch. Other alternatives — change native verifier immediately, add a parser copy, rewrite the wire format — are more expensive and not justified before a cheap falsifier. If negative confirmed, communicate a precise compatibility/proof gap and owner control; do not self-authorize release. Global size/create/CPU/RSS/I/O impact is zero for this test-only experiment; impact of a future native fix is unmeasured.

## Independent criticism and next decision

The physical digest is not keyed authenticity. Re-signing indexes demonstrates internal consistency, not adversarial forgery under a cryptographic signature. The present row hash is synthetic, since Builder normally emits absent values for some direct entries. A native result cannot alone prove an ordinary released archive is vulnerable to external modification; it can demonstrate that a public strong verification claim has insufficient coverage. Require exact-head CI + raw artifacts before declaring a result. Keep Discovery STATE under its current separate owner (#574).
