# Native CMPCT core frontier

Status: **active portability/conformance work / format revision 24 unchanged**.

`native/cmpct-core/` is the shared memory-safe read-only foundation intended to back the future native CLI, Android document provider, desktop archive browsers, Apple document integrations, Linux helpers, and eventually other bindings. Platform shells must not grow independent parsers once this core can supply the required operation.

## Implemented read surface

The native core currently:

- authenticates and decodes the revision-24 primary index with bounded index allocation;
- validates the revision and host-independent lexical path policy;
- bounds the base blob table and cross-checks direct physical blob framing against authenticated index metadata;
- enumerates entry path/kind/mode/mtime/size through Rust and an opaque C ABI;
- reads genuinely range-local slices from direct RAW members;
- reads bounded slices from ordinary direct Zstd, raw Deflate and Zstd-with-dictionary members by decoding at most one direct member, enforcing a 256 MiB direct-decode cap, verifying exact decompressed length and SHA-256, then copying only the requested range to the caller; codec-3 reads also authenticate and bound the index-selected dictionary blob before decoding;
- validates revision-24 fixed and content-defined chunk maps at open time, including blob references, per-chunk declared lengths and exact logical-size accounting;
- reads fixed/CDC ranges by decoding only chunks that intersect the caller's requested interval, with mixed RAW/Zstd/Deflate chunks supported through the same blob decoder;
- validates revision-24 sparse extent maps at open time, including sorted/non-overlapping extents, logical-file bounds, blob references and exact stored-byte accounting for every extent;
- reads sparse ranges by zero-filling logical holes and decoding only stored chunks in extents that intersect the caller's requested interval, without allocating the logical file size;
- verifies the logical whole-file SHA-256 when a caller requests a complete fixed/CDC/sparse member, while selective reads retain per-touched-blob integrity semantics;
- returns typed C statuses for null pointers, I/O/format errors, resource limits, out-of-range requests and unsupported representations;
- builds `cmpct-native`, a small read-only process surface for authenticated `info`, `list` and raw-byte `range` operations without importing the Python encoder/mutation stack. The CLI caps one requested output range at 64 MiB and deliberately inherits the core's representation/integrity policy rather than adding a second parser.

The compressed direct-member paths are intentionally correctness-first. Ordinary Zstd frames and raw Deflate streams are not intrinsically byte-seekable in revision 24, so a range request on one direct compressed member currently decodes that member in full. This is still materially better than requiring whole-archive extraction and is the correct bridge to native archive browsing. Large ordinary files are normally chunked by the encoder; fixed/CDC chunk maps are range-local in the native core, and sparse members synthesize holes without decoding or allocating unrelated logical regions. A small read therefore stays proportional to touched stored data rather than to the whole member or archive.

The native CLI is an implementation milestone, not yet a benchmark claim or shipping package. Its purpose is to make list/range launch paths independently measurable without CPython startup so future ZIP-parity records can compare CLI-vs-CLI on symmetric process boundaries.

## Integrity boundary

Direct RAW partial reads cross-check authenticated index metadata and physical framing, but a partial RAW read does not claim to authenticate the unseen remainder of the member.

Direct Zstd and raw Deflate reads currently decode the complete member and compare SHA-256 to the physical blob identity before returning requested bytes. A malformed stream, length mismatch or content-hash mismatch fails rather than returning unauthenticated content.

Fixed/CDC selective reads authenticate every compressed chunk they touch before copying its overlap. RAW chunks remain genuinely range-local and, like direct RAW, do not claim authentication of unseen bytes. A complete fixed/CDC read additionally verifies the logical whole-file SHA-256 stored in the authenticated index.

Sparse selective reads use the same touched-blob policy while leaving holes as semantic zeroes. The committed sparse ABI gate proves locality by corrupting a compressed blob in an untouched extent and requiring a disjoint range to remain readable, then requiring a range that touches the corrupted extent to fail. A complete sparse read additionally verifies the logical whole-file SHA-256 across both stored extents and synthesized holes.

Future range-proof or authenticated-chunk designs may allow strong verification of partial reads without touching the whole direct object; revision 24 does not currently provide such proofs.

## Fixed conformance inputs

`tests/conformance/v24-direct-codecs.json` supplies builder-independent golden archives for the native implementation. The set freezes exact revision-24 archive bytes for direct RAW, ordinary Zstd and raw Deflate members and records archive SHA-256, logical SHA-256 and a known range answer for each member.

The important property is provenance: these bytes were hand-assembled from the revision-24 framing/schema contract rather than written by the Python `Builder`. Native RAW/Zstd/Deflate behavior can therefore be checked against a fixed format artifact instead of only against whatever the current Python encoder happens to emit. The Deflate vector is consumed through the C ABI as the acceptance oracle for native codec-4 support.

`tests/conformance/v24-chunk-maps.json` extends that builder-independent boundary to `S_CHUNKS` and `S_CDC`. Both archives deliberately mix RAW, Zstd and raw Deflate chunks, and their known range answers cross a chunk boundary. The permanent C-ABI gate also corrupts a touched physical chunk identity and requires the native reader to refuse bytes.

`tests/conformance/v24-sparse.json` freezes `S_SPARSE` independently of the encoder. Its 64-byte logical member contains leading/interior/trailing holes plus two stored extents using RAW, Zstd and raw Deflate blobs. Known ranges cross hole/data and codec boundaries so an implementation cannot pass merely by returning stored extents contiguously.

`tests/conformance/v24-zstd-dictionary.json` is now the fixed acceptance oracle for codec 3. It contains a RAW dictionary blob named by authenticated `dict_blob` metadata and a direct Zstd-with-dictionary member whose archive bytes, dictionary SHA-256, logical SHA-256 and known range answer are frozen independently of `Builder`. The Python reference already consumes these exact bytes. The native C ABI now consumes this existing archive with bounded dictionary/member allocation and rejects both dictionary-payload corruption and member-identity corruption without rewriting the fixture.

## CI conformance gate

`.github/workflows/native-core.yml` must keep the following gates green:

1. Rust formatting, clippy with warnings denied, unit tests and release build;
2. native entry enumeration compared against a Python-built revision-24 archive;
3. a non-Rust `ctypes` caller loading the produced shared library;
4. RAW range bytes compared against the Python oracle;
5. direct-Zstd range bytes compared against the Python oracle, with the fixture asserting that the selected member is physically codec 1 rather than accidentally RAW;
6. the committed RAW/Zstd/Deflate golden archives consumed directly through the same C ABI, including rejection of a Deflate archive whose physical content identity is corrupted while the raw Deflate stream itself remains decodable;
7. committed fixed/CDC golden archives consumed through the C ABI for cross-boundary selective and complete reads, including rejection of a range touching a chunk whose physical content identity was corrupted;
8. the committed sparse golden archive consumed through the C ABI for hole/data cross-boundary and complete reads, including an explicit locality proof: corruption in an untouched extent must not poison a disjoint range, while a range touching that compressed blob must fail;
9. the committed Zstd-dictionary golden archive consumed through the C ABI for selective and complete reads, including refusal when either the authenticated dictionary payload or the codec-3 member identity is corrupted;
10. `cmpct-native info/list/range` cross-checked against the Python reader on the same archive, with missing-member and bounded-output failure behavior gated as well.

The dictionary gate is now permanent. A future representation is not considered implemented merely because a Rust function can decode it. It must cross the C ABI and agree with both the Python oracle where applicable and a committed golden archive once one exists for that representation.

## Next implementation order

1. freeze and implement WAV/FLAC direct blobs;
2. virtual ZIP reconstruction/range access;
3. sequential member streams and extraction APIs;
4. full structural-preflight parity and decompression/work budgets;
5. committed tail/journal recovery and prior-generation fallback;
6. platform bindings using this API rather than format-specific parsing.

The native CLI should then be benchmarked against mature ZIP tools using CLI-vs-CLI/process-start semantics; do not mix its results with in-process library measurements.

No item above requires a format revision unless implementing it reveals that revision-24 bytes are insufficient to express the required reader semantics. In that case the normal specification/version/conformance gate applies.
