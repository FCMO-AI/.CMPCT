# O5 outcome — byte-stable source epoch is stricter than valid ZIP reconstruction

Date: 2026-10-23
Class: **scientific negative against equivalence of two acceptable ownership policies**, not a product defect/fix.
Prediction preregistered at `9b01ceec2dbc600a70fb0b5e50c8d9c6512fa410` **before** executable `aa8d0bd6f5fecdd8028935241132c18143ef0982`.
Hosted exact-head [run 40022495589](https://github.com/FCMO-AI/.CMPCT/actions/runs/40022495589), job `120650294191`, source `3eb80e5cbf6928d387325f501d8ced641b58241f`: **SUCCESS**. Artifact ID `12531336302`; SHA-256 `f5efbc3a6a53233586e04f9ba4807aafd336ac1417c02be08e9e60444a80faa1` includes O2–O5 original JSON and source/Reader/prereg SHA identities.

## Exact mechanism

RFC 1951 stored Deflate final block header has `BFINAL=1; BTYPE=00` in its three least significant bits. Its remaining five bits before the byte boundary are ignored. For the O2 frozen level-0 stream, flipping **0x08** in the first byte changes *only an unused alignment bit*. Independent raw zlib decompression confirms the same plaintext and length. Physical wire SHA changes; original logical SHA256, CRC32 and length do not. No header/index metadata was rewritten.

| Case | Result | Interpretation |
|---|---|---|
| Alternate valid Deflate bytes installed before normal PR #284 export | exported ZIP was accepted by independent `zipfile` and decoded exact original logical bytes | existing product supports semantically equivalent physical representations |
| Equivalent alignment-bit change *after* owner preflight, then O3 private staged ZIP + final logical CRC/SHA proof | **published** a valid logical ZIP; replaced prior user target | output-semantic acceptance |
| Same equal-plaintext change after verifier-fed O4 wire SHA, before private raw-Deflate copy | **rejected**; prior target preserved; staging cleaned | strict physical-source-epoch consistency |

CI witness: `WIRE_EPOCH_REJECTS_EQUIVALENT_DEFLATE_WHILE_OUTPUT_LOGICAL_PROOF_ACCEPTS`.

## Decision changed

O4's wire-hash binding survives O2's corrupt source race, but **is more conservative than reconstructed ZIP logical validity**. It rejects a concurrent change whose bytes decode *exactly* as required. This is not proof of an O4 integrity bug; it is a source ownership/product-policy choice.

- **Strong physical epoch semantics:** If every export must be drawn from the exact compressed-byte snapshot validated during preflight, O4's conservative rejection is intended. It may avoid repeated postcopy decompression per alias, but must be integrated into real ZIP staging with correct metadata/source ownership and output lifecycle.
- **Logical end-product semantics:** If only the emitted ZIP's exact logical bytes, metadata and integrity matter, O3's full staged-output CRC/SHA is the simpler already-proven control; different valid compressed encodings may be accepted. It requires another decode/read/hashing pass per output member.
- **Unmodified immutable source contract:** both strategies should agree and succeed on clean original inputs. The source must be genuinely immutable throughout operation if any check-then-copy is promoted as sufficient.

An *independently proven* equal-logical-but-different-physical same-length Deflate control already exists in PR #284 at `benchmarks/v031_deflate_wire_identity_negative.py` (zlib level1 vs level9); this O5 specifically adds a deterministic **postpreflight mutation** into the two recovery architectures.

## Research scope/debt

This is a real revision-24 source and real full ZIP for O3; O4 remains a separate detached raw-Deflate stream oracle. No global concurrency ownership, all-codec valid snapshot, native/Windows/macOS semantics, benchmark CPU/wall/RSS/temp IO, snapshot permission, or crash recovery is proven. Concurrent mutation *inside* a staged output file is not covered; temp ownership must be enforced in a product fix. Physical stored-alignment-bit changes are equal at the logical contract but not byte-identical at the compressed-wire level. Exact CMPCT archive reconstruction and ZIP logical extraction are distinct surfaces; do not conflate them.

**Next owner decision:** explicitly choose source-epoch vs output-semantic integrity boundary and its exported CPU/temp/alias carrying cost before implementing. PR #284 remains product owner. No canonical source modification, merge, format bump, release, or discovery-policy update is authorized by this result.
