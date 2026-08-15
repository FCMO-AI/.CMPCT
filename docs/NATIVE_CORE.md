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
- parses independently conformance-gated `S_VZIP` recipes for ZIP_STORED payloads and retained exact Deflate stream mode 1 from authenticated index metadata, validates recipe/blob/literal accounting, and serves requested nested-ZIP ranges through `cmpct_entry_read_range` by projecting only intersecting skeleton/payload slices through the existing blob decoder. Complete virtual-member reads enforce the recipe logical SHA-256. Revision-24 Deflate modes 0 and 2 remain typed unsupported until they have independent fixed vectors;
- returns typed C statuses for null pointers, I/O/format errors, resource limits, out-of-range requests and unsupported representations;
- builds `cmpct-native`, a small read-only process surface for authenticated `info`, `list`, `stat`, bounded whole-member `read`, and raw-byte `range` operations without importing the Python encoder/mutation stack. `stat` exposes one authenticated logical entry without forcing callers to parse the full JSON list; `read` emits one complete regular member to stdout with a 64 MiB process-surface allocation ceiling; `range` retains the same 64 MiB per-request output ceiling. These commands deliberately inherit the core's representation/integrity policy rather than adding a second parser.

Revision-24 WAV/FLAC reconstruction lives in `native/cmpct-core/src/wavflac.rs`. Codec 2 stores a FLAC stream plus MessagePack reconstruction metadata containing the original WAV prefix/suffix and audio properties. Native archive dispatch now reads those bounded fields, reconstructs PCM16/PCM32 byte-for-byte, validates FLAC channel/rate/bit-depth and exact logical length, verifies the reconstructed WAV against the physical blob SHA-256, and only then returns the requested slice through `cmpct_entry_read_range`. This is intentionally a full bounded direct-object reconstruction before slicing; revision 24 does not provide independently authenticated seek points inside a direct FLAC stream.

The compressed direct-member paths are intentionally correctness-first. Ordinary Zstd frames, WAV/FLAC direct streams and raw Deflate streams are not intrinsically byte-seekable in revision 24, so a range request on one direct compressed member currently decodes that member in full. This is still materially better than requiring whole-archive extraction and is the correct bridge to native archive browsing. Large ordinary files are normally chunked by the encoder; fixed/CDC chunk maps are range-local in the native core, sparse members synthesize holes without decoding or allocating unrelated logical regions, and supported virtual ZIP reads project only the requested nested-container regions. A small read therefore stays proportional to touched stored data for mapped/virtual members rather than to the whole archive.

The native CLI is an implementation milestone, not yet a benchmark claim or shipping package. Its purpose is to make metadata lookup, bounded member reads and selective range paths independently measurable without CPython startup so future ZIP-parity records can compare CLI-vs-CLI on symmetric process boundaries.

## Integrity boundary

Direct RAW partial reads cross-check authenticated index metadata and physical framing, but a partial RAW read does not claim to authenticate the unseen remainder of the member.

Direct Zstd, WAV/FLAC, Zstd-dictionary and raw Deflate reads currently reconstruct/decode the complete member and compare SHA-256 to the physical blob identity before returning requested bytes. A malformed stream, metadata mismatch, length mismatch or content-hash mismatch fails rather than returning unauthenticated content. WAV/FLAC metadata is archive-controlled input; it is parsed under the same bounded operation and must agree with the FLAC stream properties before reconstruction succeeds.

Fixed/CDC selective reads authenticate every compressed chunk they touch before copying its overlap. RAW chunks remain genuinely range-local and, like direct RAW, do not claim authentication of unseen bytes. A complete fixed/CDC read additionally verifies the logical whole-file SHA-256 stored in the authenticated index.

Sparse selective reads use the same touched-blob policy while leaving holes as semantic zeroes. The committed sparse ABI gate proves locality by corrupting a compressed blob in an untouched extent and requiring a disjoint range to remain readable, then requiring a range that touches the corrupted extent to fail. A complete sparse read additionally verifies the logical whole-file SHA-256 across both stored extents and synthesized holes.

Supported virtual ZIP payloads follow the same boundary. The authenticated recipe produces only the skeleton/payload slices intersecting a request; each touched slice goes through normal blob framing/codec validation. ZIP_STORED payloads project their raw-content blob, while Deflate mode 1 projects the retained exact RFC-1951 stream blob directly and therefore performs no recompression. RAW slices retain the native core's existing partial-RAW rule and do not claim strong authentication of unseen bytes. A complete virtual-member read additionally verifies the reconstructed nested ZIP against the recipe SHA-256, so whole-member corruption cannot cross the public ABI unnoticed.

Future range-proof or authenticated-chunk designs may allow strong verification of partial reads without touching the whole direct object; revision 24 does not currently provide such proofs.

## Fixed conformance inputs

`tests/conformance/v24-direct-codecs.json` supplies builder-independent golden archives for direct RAW, ordinary Zstd and raw Deflate. `tests/conformance/v24-chunk-maps.json` extends that boundary to `S_CHUNKS` and `S_CDC`, deliberately mixing RAW/Zstd/Deflate blobs across known cross-chunk ranges. `tests/conformance/v24-sparse.json` freezes sparse hole/data semantics independently of the encoder. `tests/conformance/v24-zstd-dictionary.json` is the fixed codec-3 acceptance oracle and includes corruption refusal for the authenticated dictionary/member relationship.

`tests/conformance/v24-wavflac.json` freezes codec 2 independently of `cmpct.builder.Builder`. It contains one exact revision-24 archive with a libsndfile-produced FLAC payload plus MessagePack reconstruction metadata, along with archive SHA-256, logical WAV SHA-256 and a known byte-range answer. Python consumes the fixed archive directly. The Rust component gate reconstructs the frozen metadata/payload independently; the archive ABI gate then opens those exact archive bytes through the produced shared library, proves known-range and complete-member parity with the Python oracle, and rejects a physical logical-content SHA corruption before returning bytes.

`tests/conformance/v24-virtual-zip.json` freezes the first `S_VZIP` recipe independently of `cmpct.builder.Builder`. It uses one ZIP_STORED payload so the first Rust milestone isolates authenticated recipe shape, skeleton/literal accounting and range-local projection without conflating those rules with Deflate-stream reconstruction.

`tests/conformance/v24-virtual-zip-deflate-mode1.json` independently freezes the next virtual representation: ZIP method 8 with stream mode 1. The exact RFC-1951 member stream is retained as a separate ordinary CMPCT blob, and the recipe projects those bytes directly between skeleton literals. The vector freezes archive/nested-ZIP SHA-256 values, exact Deflate bytes and ranges that cross skeleton → Deflate stream → skeleton. Python's standard-library ZIP reader validates the reconstructed member, Rust component coverage proves that the planner selects the exact-stream blob without recompression, and the public C-ABI gate consumes the same fixed archive and requires complete-read corruption refusal.

Modes 0 and 2 remain intentionally ungated. Mode 0 projects the physical raw-Deflate payload of a codec-4 blob rather than that blob's decoded logical bytes, so it needs an explicit physical-stream access boundary in the native core. Mode 2 regenerates an exact raw Deflate stream from content plus a zlib level; an equivalent-but-different encoder output is not sufficient because the nested ZIP identity must remain byte-for-byte identical.

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
12. builder-independent virtual-ZIP component coverage for ZIP_STORED plus retained exact Deflate mode 1, including exact reconstruction/ranges, range locality and malformed/ungated-representation refusal;
13. builder-independent ZIP_STORED and Deflate-mode-1 virtual-ZIP archive reads through the public C ABI, including exact known ranges, complete nested-ZIP SHA-256, typed bounds refusal and complete-read payload corruption refusal.

## Next implementation order

1. freeze an independent revision-24 vector for virtual-ZIP Deflate stream mode 0, then add a narrowly scoped authenticated physical-codec-payload read path so virtual reconstruction can reuse the exact stored RFC-1951 bytes without decoding/recompressing them;
2. freeze an independent revision-24 vector for virtual-ZIP Deflate stream mode 2 and decide how to guarantee zlib-compatible byte generation across native platforms before implementing it;
3. sequential member streams and extraction APIs beyond the bounded whole-member process helper;
4. full structural-preflight parity and decompression/work budgets;
5. committed tail/journal recovery and prior-generation fallback;
6. platform bindings using this API rather than format-specific parsing.

The native CLI should continue to be benchmarked against mature ZIP tools using CLI-vs-CLI/process-start semantics; do not mix its results with in-process library measurements.

No item above requires a format revision unless implementing it reveals that revision-24 bytes are insufficient to express the required reader semantics. In that case the normal specification/version/conformance gate applies.
