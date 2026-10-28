# A14-O1c — Symmetric codec oracle, frozen before result (2026-10-28 UTC)

## Causal challenge to O1b

The O1b preregistration and observed negative tested only Zstd-19 after checksum removal, while its direct comparison correctly allowed Zstd-19, XZ-9 and Brotli quality 11. That asymmetry does **not** justify retiring *all* codec-mediated checksum folding. Preserve the original O1b decision scoped to its exact candidate. This new, separately preregistered, bounded and more favorable oracle tests whether a **stronger candidate compressor** changes the decision on exactly the same selected real PNG/GZIP inputs and SHA-256 source identities. No dataset or threshold changes after seeing the O1b results.

## Oracle and controls

- Reuse O1b's exact deterministic 64 PNG / 64 GZIP natural source selection, no new search, no sample replacement.
- Reconstruct independently every original byte from CRC-deleted data with **each** decoder: zstd-19, xz-9, brotli-q11; reject any semantic mismatch; compare candidate's actual complete bytes (58-byte format/codec/length/SHA header plus compressed CRC-free stream).
- Source-compressed control is the minimum of the *same* three codecs, measured on identical original bytes. Charge the full three-way encoder search work and decompression/CRC recomputation, not a gifted optimal codec selector; report CPU/wall where available.
- Compute a separate generous **zero-header** size oracle only as lower-rung headroom; it is not product evidence.
- Preserve original O1b result as a negative for Zstd-only. Any O1c positive would reopen only a bounded format-specific research path, not assert general data success.

## Frozen decision

**ADVANCE** only if both unrelated format families contain >=2 actual natural files each with >=5% full-artifact savings against best source control and aggregate >=1% savings per family. Else **PARK** the whole tested format-container-specific CRC folding class for near-term CMPCT product use. If fewer than 16 source-valid inputs per family or a decoder is unavailable, report **INSUFFICIENT**, not negative.

## Cost/safety/adversarial boundaries

All headers/codec IDs/original SHA are charged; original PNG CRC or gzip footer is independently validated; no false-repair of invalid source. Never weaken tests or truncate inputs to win. A simple per-format information bound (4 bytes per PNG chunk / 8 bytes per single-member gzip) is compared to measured size to see whether the result was prospectively predictable without expensive codec work. Gzip derived CRC requires complete bounded inflate, unlike PNG. Source files and paths remain local; only SHA identifiers and aggregate evidence are public. No product, release, schema, workflow-policy, benchmark, Discovery State, or source-code changes.

**Evidence rung:** fully charged format-known, codec-favorable scientific oracle; no CMPCT whole-product credit. O1c may falsify the notion that O1b lost only because its candidate codec was asymmetrically weak.
