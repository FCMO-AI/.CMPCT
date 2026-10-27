# J24R01 — explicit unverified physical-salvage evidence tier (preregistration)

Date: 2026-10-27 UTC. Repository: FCMO-AI/.CMPCT. Scientific parent: O0 falsifier PR #291, exact source 61d585ecf8cbe00f628c6f1f8b2d3ad9868415c4. Target: public `recover_blob_records` and `cmpct recover-blobs` only. On-disk revision 24, published v0.30.0 unchanged.

## Baseline / observed negative
Issue #292 and the frozen O0 court establish that an intact RAW header, a one-byte-payload-corrupted RAW record, and a forged uncommitted RAW record can all be enumerated while the scanner returns the **header-declared** SHA-256. The normal Reader rejects tampered payload. Scanner current source falsely describes these as valid self-hashed blobs, with no per-result warning.

## Primary falsifiable claim
Add **explicit unverified classification** to every discovered physical blob candidate, preserving current observed header fields and scanning semantics. In the independent fixed controls, an ordinary valid record, a corrupted record and a forged uncommitted record must all retain their declared metadata and carry `verified: false`. JSON CLI must preserve that marker. The scanner must never imply membership in a committed generation or successful CRC/SHA/codec decoding.

## Strong simpler control / alternative
The cheapest safe fix is documentation and explicit classification; verifying the entire payload or scanning with bounded memory is a separate question and cannot be claimed as a property of this patch. A full verification mode would add codec, resource-budget and provenance obligations; do not introduce it without an independent decoder and bounded hostile controls. Do not relabel an unverified SHA field as computed authentication.

## Kill / narrow conditions
Reject the candidate if any previously discovered record disappears, any of the existing fields change, the CLI loses JSON interoperability, any marker incorrectly states verified=true, the genuine Reader integrity behavior changes, a legacy O0 hostile result becomes green by weakening its claim, or the new marker is absent for a candidate. General tests and platform validation remain necessary for product promotion.

## Decision and proof plan
First implement an additive `verified: false` boolean and a precise function docstring/comment; preserve existing `sha256` field as unverified *declared metadata*. A separately written installed-package court tests genuine Builder RAW, one-byte corruption, uncommitted framed forgery, CLI JSON and unchanged source integrity checks. Compare to O0 frozen falsifier. Three-host source-exact GitHub Actions if available. This is an **integrity-communication product candidate**, not verified recovery or reduced RAM. Measure/label full-scanner O(archive size) RAM debt explicitly; no numerical product-performance claims.
