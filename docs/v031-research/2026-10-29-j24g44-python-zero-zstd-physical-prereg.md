# J24G44 — Python encoded-empty Zstd physical verification: preregistration

Date: 2026-10-29 UTC. State: **PROSPECTIVE; no product source modified at this commit**.

## Authority and scope
Canonical `FCMO-AI/.CMPCT` main `80c358f8824ec1b20d349c92ed94c898090969b0`, release v0.30.0 / r24, next work v0.31. Independent J24G43 [#763](https://github.com/FCMO-AI/.CMPCT/pull/763) and [#764](https://github.com/FCMO-AI/.CMPCT/issues/764) already proved a signed, structurally valid, nonempty Zstd frame decoding to zero logical bytes can be corrupted and still accepted by Python complete verification; no need to repeat that discovery as new. Research-only #763 remains frozen. Native owner #759 and #762 independently own Rust complete verification and CRC. This branch owns **only the shipping Python native codec adapter** and new source-exact regressions. No native crate/format/release/matrix/discovery change.

## Primary scientific engineering question
Can the installed Python Zstd adapter validate a **nonempty encoded frame even when claimed output size = 0**, without breaking valid empty decoded frames or historical empty encoded sentinels, altering bytes on write, allocating proportional to missing logical content, or silently relaxing the independent source/coded-byte distinction?

**Prediction:** `ZSTD_decompress` via CMPCT's existing package-owned Rust ABI, supplied a 1-byte caller-owned output capacity for zero logical output, returns `0` for a structurally valid empty frame and a nonzero error for a corrupt magic. Apply the same rule to `decompress`, `decompress_using_dict`, and `DictDecoder.decompress`; retain existing zero-copy return on *both* empty encoded bytes and zero claimed output to preserve legacy. Nonzero-sized decode must execute unchanged.

**Control:** unchanged `b''` encoded-empty/claimed-empty paths; first-party Builder RAW empty r24; valid Zstd empty r24 derived from that Builder source with fully regenerated signed primary/tail index; nonempty direct-codec conformance vectors. Different-root independent `zstandard` decoder validates the encoded frame.

**Kill/narrow:** any valid encoded-empty r24 or frozen nonempty conformance regression; successful decoding of the deliberately magic-corrupt frame; native ABI out buffer requirement >1 byte or contradictory zero-byte semantics; dictionary regression; unsafe/large temporary memory; new change to emitted archive wire. A mere unit mock is insufficient as final product evidence.

## Minimum decisive evidence ladder
1. Direct system-libzstd ABI probe with one-byte output (not product proof), valid and invalid empty frames.
2. Implement only the adapter's nonempty-encoded-zero-output path; test all three Python APIs using the actual installed CMPCT cdylib, valid/corrupt frames, and zero-coded legacy.
3. Construct genuine Builder r24 empty source; independently derive a signed direct-Zstd empty record and a single-byte corrupted variant; check `CMPCT.verify()==1` for valid and raises for invalid, plus independent decoded-stream verdict and source hashes.
4. Run exact-head hosted Ubuntu/macOS/Windows installed package; preserve raw artifacts, source SHA and CI truth. No commit/PR green automatically earns release promotion.

## Baseline / alternatives / cost accounting
Baseline released `src/cmpct/native_codec.py` short-circuits solely on `usize==0`; both standard and dictionary entrypoints do not examine physical frame. Simpler control is reject all encoded zero logical payloads, but it would incorrectly reject valid Zstd empty frames and the signed r24 derived wire. Alternative: always call native decode including empty coded input; could alter valid historical zero-coded sentinel semantics and adds unnecessary library work. Alternative separate Python `zstandard` dependency doubles codec authority. Prefer existing shared native decoder and same buffer ownership.

For `usize==0` and nonempty encoded input, the new work is exactly one compressed-frame decode, with 1 byte of caller-owned destination plus input buffer already needed by Reader; no claim of zero CPU or full-resource parity. No change for `usize>0`. Charge any measured wall/RSS/temporary allocation in hosted observations; important multi-frame/trailing-byte policy and native strong-verify work remain separate. Scope excludes Rust native reader, arbitrary symlink/sparse composite, malicious huge compressed bytes, and all-codec proof.

## Concurrency / authority guard
GitHub open PRs inspected: #750 (direct-row SHA, Reader semantics), #759 (Rust native symlink verify), #762/#765 (native CRC), #763 (frozen scientific negative). We do not touch their files or tests. Reinspect this narrow mutation surface before late shared write, and coordinate via issue #764 / parent owners. Do not touch `docs/discovery/STATE.json` or freeze/evaluator/format/release authority. This is **draft research/product candidate**, not permission to merge.
