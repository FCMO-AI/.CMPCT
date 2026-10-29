# J24I31 — prospective S_PACK indexed-row digest custody (2026-10-29 UTC)

**Science only. Exact parent:** independent S_PACK fixed-wire PR #307 at `256a263748b9f65b4bc00dd572799e4f00ae06e7`. Shipping `main` remains v0.30.0 / revision 24. Do not modify Reader, Builder, native, format, frozen vectors or release gates.

## Primary question / predicted result
Can actual installed Python revision-24 `CMPCT.verify()` accept a physically unchanged, independently frozen RAW- or Zstd-backed `S_PACK` archive after **only one present logical file-row SHA-256** is replaced by a contradictory 32-byte digest and both ordinary unkeyed index digests recomputed? Prediction: **yes**, because current S_PACK `file_sha256()` uses `sha(self.read(name))` as the authority instead of the optional row `h`. A correct independent oracle should accept original/absent/empty/matching SHA controls, but identify the contradictory-payload-independent row as unsupported by strong verify. If current strong verify rejects the contradictory case, the hypothesis is falsified; if preflight rejects the rehashed index or the fixture differs, the instrument is invalid.

## Stronger simple control / alternatives
No custom pack generator: reuse original fixed-byte `tests/conformance/v24-pack.json` from #307 with *both* RAW and Zstd physical owners. Reuse the existing r24 two-index record layout; clone only authenticated indexes, preserve every packed physical byte, compare original and forged bytes and SHA. An inline static source audit already predicts the behavior, so this test must resolve whether that behavior is reachable on authentic parseable wire; no product-credit from syntax alone. A product fix, if warranted, belongs to existing present-digest owner #750; do not open a competing Reader patch. This is a structural transfer and not another codec threshold search.

## Falsifier / proof requirements
1. Verify frozen archive identity and original physical record identity; original `preflight`, `read`, `read_range`, `verify` must pass.
2. For each physical codec RAW and Zstd, mutate one PACK member's optional row digest among `None`, `b''`, correct SHA and a wrong 32-byte SHA; re-sign **both** authoritative index copies and preserve unchanged physical bytes.
3. Preflight must accept structurally valid variants. Actual installed Reader must reconstruct all four files with correct bytes; record exact verify verdict for each variant. In particular a wrong *present* row digest accepted by `verify` is a negative integrity result, not a success for product.
4. An independently computed physical blob digest/CRC and original-wire SHA must be captured; include source HEAD and file blob custody in hosted receipts. If valid controls unexpectedly fail, classify without rewriting prediction.
5. Host CI on Ubuntu and macOS first; Windows if economical. No lowering of comparator, historical frozen tests, SCIENCE negative assertion, or release law.

## Scope / debt
Optional row digests in authenticated but **unkeyed** index metadata are not a provenance signature. The unexpected digest is synthetic and represents signed-wire semantic inconsistency, not remote code execution or ordinary Builder emission. If accepted, the narrow result expands the #750/#751 logical-identity contract question from direct owners/aliases to packed members. It does not establish full archive authenticity, native ABI parity, streaming, recovery, or official compression/CPU/RSS wins.

**Promotion:** none. Close scientific PR after decisive authentic hosted evidence; inform #750 with exact receipts. Concurrency: do not edit #750, #751, #754, #574 or active stage/Reader integration surfaces.
