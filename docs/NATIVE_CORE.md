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

A reusable pure-Rust revision-24 WAV/FLAC reconstruction component now also lives in `native/cmpct-core/src/wavflac.rs`. It parses the authenticated codec-2 MessagePack metadata, validates FLAC channel/rate/bit-depth against that metadata, bounds reconstructed output by the caller-provided logical size, decodes PCM16/PCM32, and copies the original WAV prefix/suffix bytes verbatim. The component is compiled and exercised against the fixed builder-independent codec-2 oracle before being wired into archive dispatch. **Codec 2 is not yet exposed through the C ABI**, so platform handlers must still treat WAV/FLAC archive members as unsupported until that final integration lands.

The compressed direct-member paths are intentionally correctness-first. Ordinary Zstd frames and raw Deflate streams are not intrinsically byte-seekable in revision 24, so a range request on one direct compressed member currently decodes that member in full. This is still materially better than requiring whole-archive extraction and is the correct bridge to native archive browsing. Large ordinary files are normally chunked by the encoder; fixed/CDC chunk maps are range-local in the native core, and sparse members synthesize holes without decoding or allocating unrelated logical regions. A small read therefore stays proportional to touched stored data rather than to the whole member or archive.

The native CLI is an implementation milestone, not yet a benchmark claim or shipping package. Its purpose is to make list/range launch paths independently measurable without CPython startup so future ZIP-parity records can compare CLI-vs-CLI on symmetric process boundaries.

## Integrity boundary

Direct RAW partial reads cross-check authenticated index metadata and physical framing, but a partial RAW read does not claim to authenticate the unseen remainder of the member.

Direct Zstd, Zstd-dictionary and raw Deflate reads currently decode the complete member and compare SHA-256 to the physical blob identity before returning requested bytes. A malformed stream, length mismatch or content-hash mismatch fails rather than returning unauthenticated content.

Fixed/CDC selective reads authenticate every compressed chunk they touch before copying its overlap. RAW chunks remain genuinely range-local and, like direct RAW, do not claim authentication of unseen bytes. A complete fixed/CDC read additionally verifies the logical whole-file SHA-256 stored in the authenticated index.

Sparse selective reads use the same touched-blob policy while leaving holes as semantic zeroes. The committed sparse ABI gate proves locality by corrupting a compressed blob in an untouched extent and requiring a disjoint range to remain readable, then requiring a range that touches the corrupted extent to fail. A complete sparse read additionally verifies the logical whole-file SHA-256 across both stored extents and synthesized holes.

The standalone WAV/FLAC component validates codec metadata, FLAC stream properties and exact reconstructed length before returning bytes. Physical blob SHA-256 enforcement remains the responsibility of the archive core when codec 2 is connected to `read_blob_range`; the component gate intentionally does not pretend to authenticate archive framing by itself.

Future range-proof or authenticated-chunk designs may allow strong verification of partial reads without touching the whole direct object; revision 24 does not currently provide such proofs.

## Fixed conformance inputs

`tests/conformance/v24-direct-codecs.json` supplies builder-independent golden archives for direct RAW, ordinary Zstd and raw Deflate. `tests/conformance/v24-chunk-maps.json` extends that boundary to `S_CHUNKS` and `S_CDC`, deliberately mixing RAW/Zstd/Deflate blobs across known cross-chunk ranges. `tests/conformance/v24-sparse.json` freezes sparse hole/data semantics independently of the encoder. `tests/conformance/v24-zstd-dictionary.json` is the fixed codec-3 acceptance oracle and includes corruption refusal for the authenticated dictionary/member relationship.

`tests/conformance/v24-wavflac.json` now freezes codec 2 independently of `cmpct.builder.Builder`. It contains one exact revision-24 archive with a libsndfile-produced FLAC payload plus MessagePack reconstruction metadata, along with archive SHA-256, logical WAV SHA-256 and a known byte-range answer. Python consumes the fixed archive directly. The Rust component gate extracts only the already-frozen metadata/payload bytes from that archive, reconstructs the logical WAV without Python audio decoding, and must match the fixed whole-file identity and known range exactly.

The important property is provenance: fixed bytes are acceptance targets, not regenerated snapshots of the current encoder. A future representation is not considered implemented merely because two implementations agree on bytes emitted during the same test run.

## CI conformance gate

`.github/workflows/native-core.yml` keeps the following permanent gates:

1. Rust formatting, clippy with warnings denied, unit tests and release build;
2. native entry enumeration compared against a Python-built revision-24 archive;
3. a non-Rust `ctypes` caller loading the produced shared library;
4. direct RAW/Zstd range checks and corruption refusal;
5. builder-independent RAW/Zstd/Deflate direct-codec ABI vectors;
6. builder-independent fixed/CDC chunk-map ABI vectors;
7. builder-independent sparse ABI vectors, including untouched-corruption locality;
8. builder-independent Zstd-dictionary ABI vectors, including dictionary/member corruption refusal;
9. `cmpct-native info/list/range` cross-checked against Python plus CLI-vs-CLI ZIP semantic-parity smoke coverage;
10. builder-independent WAV/FLAC component reconstruction against `v24-wavflac.json`, including exact SHA/range agreement and malformed metadata rejection.

The WAV/FLAC gate is a component milestone, not yet the final codec-2 ABI gate. The representation becomes native-handler complete only after the same frozen archive succeeds through `cmpct_entry_read_range` with physical hash corruption refusal.

## Next implementation order

1. wire the tested WAV/FLAC component into direct-blob dispatch and cross the fixed codec-2 archive through the C ABI;
2. virtual ZIP reconstruction/range access;
3. sequential member streams and extraction APIs;
4. full structural-preflight parity and decompression/work budgets;
5. committed tail/journal recovery and prior-generation fallback;
6. platform bindings using this API rather than format-specific parsing.

The native CLI should continue to be benchmarked against mature ZIP tools using CLI-vs-CLI/process-start semantics; do not mix its results with in-process library measurements.

No item above requires a format revision unless implementing it reveals that revision-24 bytes are insufficient to express the required reader semantics. In that case the normal specification/version/conformance gate applies.
