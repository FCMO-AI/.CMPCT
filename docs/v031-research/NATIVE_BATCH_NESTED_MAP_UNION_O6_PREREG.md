# O6 preregistration — exact-source native batching + authenticated nested-index ambiguity union

Status: prospective, prediction-only. Frozen on parent PR #325 HEAD `8054e7861fae0aabc6cf2bc8ea93f5a9e336ee2d` before cross-owner source integration. Security ownership: PR #316 (Python/native root duplicate-map), PR #321 (Python Reader open/failure resource lifetime), PR #324 (native nested-map rejection) at `c8cc83bd75fd1cd7a6335e70eb6bc033faa997af`. Performance/ABI owner: PR #322 and O5 PR #325.

## Primary scientific/product question
Can the exact verified one-owner S_PACK batching and O5 metadata discovery code coexist with *the complete inherited authenticated MessagePack unambiguous-map security contract*, without cross-owner source regression or relaxing either independently frozen hostile oracle?

## Prediction before implementation
A source-exact composition that imports Python reader, validation, msgpack policy, both duplicate-index courts and nested native-map walker from their canonical owners will pass (i) three independent good r24 RAW/Zstd/Deflate archives; (ii) all six root ambiguous map wires; (iii) all eighteen nested/binary/non-text authenticated ambiguous wires; (iv) reader failed-open resource lifetime; (v) independent good raw/zstd packed archive and real two-owner/native batch O3/O5; (vi) C header compiles with both optional API symbols. The product is a *draft integration candidate* regardless of court success.

## Precommitted controls / disproof
- Compare SHA-256 Git blobs for every imported source/test/doc from #324 and #321 to exact owner heads, **excluding combined Rust**: no hand-edited reinterpretation of their security logic.
- Combine Rust additively: #325 existing `read_pack_batch`, `cmpct_entry_pack_owner`, C exports, plus #324's **exact** `reject_ambiguous_index_maps()`, call before logical index interpretation, and original four native Rust tests.
- Compile and run exact-head: Python root and nested oracle, fixed raw/zstd pack good bytes, O3 multi-owner + O5 grouping. Require every test substantive, not a green workflow whose classifier skipped content.
- Independently inspect no invalid index begins to decode or leak filesystem information before rejection; no replaced Builder, format, fingerprint, version, evaluator, comparator, release gate.
- Killer: inherited Python/native mismatch on authenticated index; any O3/O5 output changed or allowed on corruption/mixed owner; any original #324 hostile accepted; version/format mutation; accidental modification of owner blobs; incorrect existing ABI.

## Alternatives
Treat reader parser hardening as optional (rejected, integrity veto); maintain two divergent Rust parsers by separate releases (unsustainable); cherry-pick only nested walker without Python correctness change (not an exact product union, cannot claim parity). Instead import exact existing owner code once and measure.

## Scope / limitations
Adjacent draft composition, not a new MessagePack parser family or new compression mechanism. Copies original scientific court source, does not alter frozen tests, thresholds or benchmark semantics. Product release not authorized; this branch is stacked on #325 and cannot supersede separately owned PRs #316/#321/#324. Portability/full-product ABBA unchanged; any inherited four historical CI reds remain open rather than "fixed" by composition. No update of Discovery Engine STATE, whose owner is independent.
