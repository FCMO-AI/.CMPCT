# O74 — ZIP metadata-only identity falsifier (prospective preregistration)

Date: 2026-10-25 UTC. Status: prediction locked **before** constructing or executing the collision oracle. Product: released v0.30.0, physical r24; experiment stacked exclusively on O71 scientific HEAD `330a1fa1c642d4bd4ddf2a1bd6cadd22b94cc19a` (PR #427). This is an **independent adversarial replication of a distinct question**, not an implementation of O63/O71 admission policy.

## Decision question
Can a cheap candidate-admission or cross-ZIP reuse policy treat ZIP central-directory facts `(member name, compression method, CRC32, uncompressed length, compressed length, time/flags)` as a **proof of identical decompressed bytes**, and then omit verifying the bytes, without violating CMPCT's exact lossless contract?

## Hypothesis and predicted evidence
No. A four-byte suffix on one of two different, equal-sized deterministic byte streams can be solved by 32-bit GF(2) linear algebra to make their standard ZIP CRC32 identical. If the sources are incompressible and the same ZIP settings/headers are used, their Deflate compressed sizes should also match. Predict two **valid, independently readable** single-member ZIPs whose complete local/central/end records, except the compressed stream payload, are byte-equal; their `ZipInfo` tuples will match while their expanded SHA-256 and compressed stream SHA-256 differ. Forcing one member's expanded payload as the other's would then demonstrably reconstruct incorrect bytes, not a valid deduplication.

## Exact strongest controls and alternative explanation
- Validate CRC patch with Python's *independent* `zlib.crc32` calculation; record full source SHA-256 and never rewrite it after observation.
- Parse both actual ZIPs using `zipfile`, compare complete central-directory bytes where offsets/sizes permit, exact member paths/dates/flags and complete containers. Independent whole-file SHA is required to differ.
- Positive control: byte-identical payloads must retain equality; per-member **cryptographic hash of expanded bytes** must distinguish adversarial collision.
- Optional product control: use the authentic installed CMPCT Builder/Reader to create, verify and extract both original physical ZIPs on the same filesystem; this tests current behavior but does not authorize an encoder change.
- Alternative explanation: CRC construction succeeds but Deflate compressed sizes differ; then the **full tuple** counterexample remains unproven, even if the weaker CRC+size collision holds. Preserve both outcomes without threshold gardening. Another possibility is a malformed ZIP; then reject the hypothesis rather than claiming a valid counterexample.

## Frozen decision criterion / evidence ladder
`FULL_METADATA_COLLISION` only if both standard ZIPs read completely, payloads differ, expanded payload SHA differ, CRC32+usize+csize+method+member metadata all match and *physical archive size* matches. Record compressed payload SHA/offset and full ZIP SHA. If any condition fails, `NARROW_OR_FAIL`, not a product bug. The strongest prospective outcome establishes a lower bound on what metadata-only inference **cannot** guarantee. It does not prove a VZIP predictor economically bad or imply CMPCT currently deduplicates on CRC alone.

The oracle is intentionally cheap: 64 KiB deterministic source streams, one 32-bit linear system, no expensive VZIP reconstruction to establish the information-theoretic distinction. Test local stdlib first, then an exact-source GitHub Actions scientific court with independent actual installed CMPCT r24 read/verify/extract where feasible. Preserve original failure or infrastructure misses. No format/reader/builder/codec/performance benchmark modification.

## Concurrency / scope
O63 #418 owns VZIP product changes, O68 #424 inflated ZIP economics, O70 #426 cohort locality, O71 #427 shared/independent payload controls and O73 #429 physical owner oracle. O74 only tests **whether metadata equality suffices to prove byte identity**. Do not duplicate their implementations, alter shared `STATE.json`, change thresholds, claim release credit or infer an unrelated performance win. If the proof succeeds, communicate the constraint to O71/O63 owners: metadata may prioritize cheap candidates but cannot replace an authenticated exact-content comparison.

## Cost / limitations / falsifier
A CRC collision by itself is unsurprising and may not represent product-practical inputs. ZIP authentication is not a signature; this court tests equality/proof semantics, not external malicious-source resistance. There is no promise of a throughput improvement, portable filesystem fidelity, or complete generality. A mature system may freely use metadata heuristics **if it subsequently verifies exactness**; the only disallowed shortcut is treating non-cryptographic metadata as sufficient content identity. All source data synthetic/public safe.
