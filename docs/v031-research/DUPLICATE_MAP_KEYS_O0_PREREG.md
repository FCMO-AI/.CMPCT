# CMPCT v0.31 — root MessagePack duplicate-key parser-divergence O0

Date: 2026-10-24
Status: **PREREGISTERED before authentic native/Python product execution. Research negative-falsifier only; no product/release/format authority.**
Base: `agent/v031-development@4545d7d5b2a0b712b4b00f5a9c291d4a3a9e169b`.

## Question and source-exact prediction

Can two actual CMPCT revision-24 Readers interpret the **same fully authenticated primary index** into different logical trees when an archive supplies the same MessagePack root key twice?

- Python `src/cmpct/reader.py` currently uses `msgpack.unpackb(index, raw=False)` (ordinary Python dict: last duplicated root key survives).
- Rust `native/cmpct-core/src/lib.rs` uses `rmpv::decode::read_value`, `map_field().iter().find_map(...)` (first duplicate root key survives).

**Prediction:** An index with two `"files"` fields, one empty and one containing the actual member, passes valid header SHA, both dual-index copies, footer identity and full physical blob framing. Python and Rust both open it but expose opposite member counts. For first-empty/last-valid, Python=1, Rust=0; reversing field order reverses counts. Repeat for independent RAW, Zstd and Deflate fixed goldens. A genuine rejection at open by either side, or equal counts, falsifies this prediction.

## Controls and evidence standard

Use existing committed independent `tests/conformance/v24-direct-codecs.json` for three immutable original archive bytes and archive SHA-256. Do not use CMPCT Builder. Transform only serialized MessagePack root map key multiplicity; re-Zstd the MessagePack index, recompute SHA-256, header, dual index and footer, and prove the physical blob is byte-identical to the signed original. Positive-controls: both Readers open and read each unchanged golden member correctly.

Read both candidates via actual installed Python Reader and actual built Rust C ABI on identical archives, in the same runner. Report exact-head source, per-case results, and actual error codes; do not count a Python-only parser experiment as native proof.

## Distinct alternatives / BONK

Ordinary checksum corruption would trivially fail and does not answer conflicting semantic ownership. Builder-generated fixtures share encoder assumptions. Source review predicts the difference but is a lower rung, and cannot earn product truth. The selected hosted same-wire dual-reader court is the cheapest decision-changing test.

## Kill/decision and costs

If mismatch confirmed: preserve as **negative product conformance evidence**, open precise corrective issue, and require both Readers to reject ambiguous authenticated maps before publication. Do not bless either the first-wins or last-wins policy merely because it is convenient. If no mismatch, retire/narrow source hypothesis and preserve actual native behavior.

Carrying cost limited to one scientific test file and one focused workflow. No product, format, codec, parser, benchmark or release-gate modification in this scientific lane. CI adds one native build + <10 tiny fixtures; it is **not** a performance benchmark. Product compatibility, Windows/macOS/Android, long-tail nested maps and comprehensive fuzzing remain unmeasured.

Concurrency: this question does not duplicate PR #307/#314 S_PACK slice/physical integrity, PR #270 Reader composition, or PR #306 benchmark evaluation. Avoid touching those implementation branches.
