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
- reads bounded slices from ordinary direct Zstd, WAV/FLAC, raw Deflate and Zstd-with-dictionary members by decoding at most one direct member, enforcing a 256 MiB direct-decode cap, verifying exact reconstructed/decompressed length and SHA-256, then copying only the requested range to the caller; codec-3 reads also authenticate and bound the index-selected dictionary blob before decoding;
- validates revision-24 fixed and content-defined chunk maps at open time, including blob references, per-chunk declared lengths and exact logical-size accounting;
- reads fixed/CDC ranges by decoding only chunks that intersect the caller's requested interval, with mixed supported blob codecs routed through the same blob decoder;
- validates revision-24 sparse extent maps at open time, including sorted/non-overlapping extents, logical-file bounds, blob references and exact stored-byte accounting for every extent;
- reads sparse ranges by zero-filling logical holes and decoding only stored chunks in extents that intersect the caller's requested interval, without allocating the logical file size;
- verifies the logical whole-file SHA-256 when a caller requests a complete fixed/CDC/sparse member, while selective reads retain per-touched-blob integrity semantics;
- parses the independently conformance-gated stored-payload `S_VZIP` recipe from authenticated index metadata, validates recipe/blob/literal accounting, and serves requested nested-ZIP ranges through `cmpct_entry_read_range` by projecting only intersecting skeleton/payload slices through the existing blob decoder. Complete virtual-member reads enforce the recipe logical SHA-256. Revision-24 Deflate virtual payloads remain typed unsupported until their three stream modes have independent fixed vectors;
- returns typed C statuses for null pointers, I/O/format errors, resource limits, out-of-range requests and unsupported representations;
- builds `cmpct-native`, a small read-only process surface for authenticated `info`, `list`, `stat`, bounded whole-member `read`, and raw-byte `range` operations without importing the Python encoder/mutation stack. `stat` exposes one authenticated logical entry without forcing callers to parse the full JSON list; `read` emits one complete regular member to stdout with a 64 MiB process-surface allocation ceiling; `range` retains the same 64 MiB per-request output ceiling. These commands deliberately inherit the core's representation/integrity policy rather than adding a second parser.

Revision-24 WAV/FLAC reconstruction lives in `native/cmpct-core/src/wavflac.rs`. Codec 2 stores a FLAC stream plus MessagePack reconstruction metadata containing the original WAV prefix/suffix and audio properties. Native archive dispatch now reads those bounded fields, reconstructs PCM16/PCM32 byte-for-byte, validates FLAC channel/rate/bit-depth and exact logical length, verifies the reconstructed WAV against the physical blob SHA-256, and only then returns the requested slice through `cmpct_entry_read_range`. This is intentionally a full bounded direct-object reconstruction before slicing; revision 24 does not provide independently authenticated seek points inside a direct FLAC stream.

The compressed direct-member paths are intentionally correctness-first. Ordinary Zstd frames, WAV/FLAC direct streams and raw Deflate streams are not intrinsically byte-seekable in revision 24, so a range request on one direct compressed member currently decodes that member in full. This is still materially better than requiring whole-archive extraction and is the correct bridge to native archive browsing. Large ordinary files are normally chunked by the encoder; fixed/CDC chunk maps are range-local in the native core, sparse members synthesize holes without decoding or allocating unrelated logical regions, and stored-payload virtual ZIP reads project only the requested nested-container regions. A small read therefore stays proportional to touched stored data for mapped/virtual members rather than to the whole archive.

The native CLI is an implementation milestone, not yet a benchmark claim or shipping package. Its purpose is to make metadata lookup, bounded member reads and selective range paths independently measurable without CPython startup so future ZIP-parity records can compare CLI-vs-CLI on symmetric process boundaries.

## Integrity boundary

Direct RAW partial reads cross-check authenticated index metadata and physical framing, but a partial RAW read does not claim to authenticate the unseen remainder of the member.

Direct Zstd, WAV/FLAC, Zstd-dictionary and raw Deflate reads currently reconstruct/decode the complete member and compare SHA-256 to the physical blob identity before returning requested bytes. A malformed stream, metadata mismatch, length mismatch or content-hash mismatch fails rather than returning unauthenticated content. WAV/FLAC metadata is archive-controlled input; it is parsed under the same bounded operation and must agree with the FLAC stream properties before reconstruction succeeds.

Fixed/CDC selective reads authenticate every compressed chunk they touch before copying its overlap. RAW chunks remain genuinely range-local and, like direct RAW, do not claim authentication of unseen bytes. A complete fixed/CDC read additionally verifies the logical whole-file SHA-256 stored in the authenticated index.

Sparse selective reads use the same touched-blob policy while leaving holes as semantic zeroes. The committed sparse ABI gate proves locality by corrupting a compressed blob in an untouched extent and requiring a disjoint range to remain readable, then requiring a range that touches the corrupted extent to fail. A complete sparse read additionally verifies the logical whole-file SHA-256 across both stored extents and synthesized holes.

Stored-payload virtual ZIP follows the same boundary. The authenticated recipe produces only the skeleton/payload slices intersecting a request; each touched slice goes through normal blob framing/codec validation. RAW slices retain the native core's existing partial-RAW rule and do not claim strong authentication of unseen bytes. A complete virtual-member read additionally verifies the reconstructed nested ZIP against the recipe SHA-256, so whole-member corruption cannot cross the public ABI unnoticed.

Future range-proof or authenticated-chunk designs may allow strong verification of partial reads without touching the whole direct object; revision 24 does not currently provide such proofs.

## Fixed conformance inputs

`tests/conformance/v24-direct-codecs.json` supplies builder-independent golden archives for direct RAW, ordinary Zstd and raw Deflate. `tests/conformance/v24-chunk-maps.json` extends that boundary to `S_CHUNKS` and `S_CDC`, deliberately mixing RAW/Zstd/Deflate blobs across known cross-chunk ranges. `tests/conformance/v24-sparse.json` freezes sparse hole/data semantics independently of the encoder. `tests/conformance/v24-zstd-dictionary.json` is the fixed codec-3 acceptance oracle and includes corruption refusal for the authenticated dictionary/member relationship.

`tests/conformance/v24-wavflac.json` freezes codec 2 independently of `cmpct.builder.Builder`. It contains one exact revision-24 archive with a libsndfile-produced FLAC payload plus MessagePack reconstruction metadata, along with archive SHA-256, logical WAV SHA-256 and a known byte-range answer. Python consumes the fixed archive directly. The Rust component gate reconstructs the frozen metadata/payload independently; the archive ABI gate then opens those exact archive bytes through the produced shared library, proves known-range and complete-member parity with the Python oracle, and rejects a physical logical-content SHA corruption before returning bytes.

`tests/conformance/v24-virtual-zip.json` freezes the first `S_VZIP` recipe independently of `cmpct.builder.Builder`. It uses one ZIP_STORED payload so the initial Rust milestone isolates authenticated recipe shape, skeleton/literal accounting and range-local projection without conflating those rules with Deflate-stream regeneration. Rust component tests consume the exact fixed archive, rebuild the nested ZIP to its frozen logical SHA-256, check both known ranges, prove skeleton/payload/skeleton locality, and require malformed accounting plus ungated Deflate payloads to fail closed. The archive ABI gate opens those same fixed bytes through `cmpct_open` and proves exact known-range/full-member output through `cmpct_entry_read_range`. Independent vectors for revision-24 Deflate stream modes 0/1/2 are still required.

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
9. `cmpct-native info/list/stat/read/range` cross-checked against Python plus CLI-vs-CLI ZIP semantic-parity smoke coverage;
10. builder-independent WAV/FLAC component reconstruction against `v24-wavflac.json`, including exact SHA/range agreement and malformed metadata rejection;
11. builder-independent WAV/FLAC archive reads through `cmpct_entry_read_range`, including exact known-range/full-member parity and physical hash corruption refusal;
12. builder-independent stored-payload virtual-ZIP component coverage, including exact reconstruction/ranges, range locality and malformed/ungated-representation refusal;
13. builder-independent stored-payload virtual-ZIP archive reads through the public C ABI, including exact known ranges, complete nested-ZIP SHA-256 and typed bounds refusal.

## Next implementation order

1. freeze independent revision-24 vectors for virtual-ZIP Deflate stream modes 0/1/2, then implement each mode without weakening range locality or exact reconstruction;
2. sequential member streams and extraction APIs beyond the bounded whole-member process helper;
3. full structural-preflight parity and decompression/work budgets;
4. committed tail/journal recovery and prior-generation fallback;
5. platform bindings using this API rather than format-specific parsing.

The native CLI should continue to be benchmarked against mature ZIP tools using CLI-vs-CLI/process-start semantics; do not mix its results with in-process library measurements.

No item above requires a format revision unless implementing it reveals that revision-24 bytes are insufficient to express the required reader semantics. In that case the normal specification/version/conformance gate applies.
