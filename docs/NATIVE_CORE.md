# Native CMPCT core frontier

Status: **released interoperability floor r24; provisional shared r24/r25 portability layer active on the v0.30 integration branch**.

`native/cmpct-core/` remains the mature memory-safe revision-24 read-only foundation. `native/cmpct-portable/` is the provisional v0.30 shared dispatcher that places genuine r24 fallback and the fixed canonical revision-25 profiles behind one native process/C ABI surface. Platform shells must not grow independent parsers when either shared native layer can supply the required operation.

## Provisional v0.30 shared portable layer

The v0.30 integration branch adds `native/cmpct-portable/` as the release-facing native boundary for every representation the canonical selector may publish:

- genuine revision 24 `CMPCT24\0`, delegated to the mature `cmpct-core` semantics rather than reinterpreted as r25;
- revision-25 Geometry-Mosaic `CMP25G4\0` / `C25G4TL\0`;
- revision-25 PrefixGraph depth-1 `CMP25PG\0` / `C25PGTL\0`;
- explicit refusal of research-only `CMPNX*` identities as canonical product input.

The portable crate supplies one dispatcher, a native CLI (`cmpct-portable`), and an opaque C ABI for archive open/profile detection, logical entry enumeration, bounded member reads, verification, extraction/export operations and locality statistics. Canonical r25 parsing shares the same bounded MessagePack/path/resource policy across native operations rather than letting Android or another platform shell reproduce the grammar.

Revision-25 filesystem semantics are authenticated through the reserved manifest described in `docs/FORMAT.md`. Native open cross-checks manifest-declared regular-file identities against the authenticated content graph before exposing the public tree. Direct regular files and hardlink owners stream through the selected Geometry/PrefixGraph reader; symlink and directory semantics remain manifest-owned.

### r25 materialization safety

The shared native materializer repeats safety rules at the final publication boundary rather than relying only on parser preflight:

- symlink targets are checked under **both POSIX and Windows lexical separator rules** independent of the host running extraction;
- absolute/rooted/drive/UNC-like targets and any `..` component under slash or backslash interpretation are rejected by safe extraction;
- `mtime_ns` remains a bounded **signed i64** through restoration, using checked add/sub around the Unix epoch so pre-1970 values cannot wrap through an unsigned cast into the distant future;
- uid/gid/xattr application remains best-effort where host privilege/APIs cannot represent it, while authenticated archive metadata itself is never fabricated or silently rewritten.

Footnote: parser safety and materializer safety are intentionally both tested. A target admitted safely on Linux must not become traversal-capable when the same bytes are later extracted on Windows, and accepting a signed timestamp in the manifest is incomplete if the extractor cannot preserve its sign.

### r25 independent evidence surface

The release-facing native gate is `.github/workflows/v030-native-authority.yml`. Its intended exact-candidate evidence includes:

1. Python canonical product-boundary and profile-isolation tests;
2. builder-independent fixed revision-25 golden reproduction from `tests/conformance/v030-r25-canonical.json` via `tests/generate_v030_canonical_goldens.py --check`;
3. Rust formatting and `cargo clippy --all-targets -- -D warnings`;
4. Rust hostile/parser/materializer tests and release build;
5. canonical CMP25 CLI/C-ABI recovery and filesystem acceptance through `tests/native_v030_canonical.py`;
6. complete revision-24 verification and truthful locality through `tests/native_v030_r24_verify_authority.py`;
7. CI-topology self-validation.

The canonical Python wrapper, preserved implementation module, profile-isolation loader and native crate are all trigger paths because changing any of them can alter the profile/dispatch contract native code must match.

The presence of this code is **not yet release authority**. T01 stays open until the exact frozen v0.30 candidate has durable native/recovery/ZIP/platform receipts and the strict release lock accepts them.

---

## Revision-24 native foundation

The remainder of this document preserves the detailed r24 capability/conformance record. It remains relevant because genuine r24 is the v0.30 product floor and fallback path.

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
- validates micro-solid `S_PACK` tuples as checked `[offset, offset + length)` slices of one referenced blob, requires the slice length to equal the logical member size, and translates requested logical ranges into bounded reads of that shared blob;
- verifies the logical whole-file SHA-256 when a caller requests a complete fixed/CDC/sparse member, and for a complete packed member when the authenticated file row supplies logical identity, while selective reads retain representation-appropriate touched-data integrity semantics;
- parses independently conformance-gated `S_VZIP` recipes for ZIP_STORED payloads and retained exact Deflate stream mode 1 from authenticated index metadata, validates recipe/blob/literal accounting, and serves requested nested-ZIP ranges through `cmpct_entry_read_range` by projecting only intersecting skeleton/payload slices through the existing blob decoder. Complete virtual-member reads enforce the recipe logical SHA-256. Revision-24 Deflate mode 0 now has an independent fixed archive oracle and a bounded authenticated physical-Deflate slice primitive, but archive dispatch intentionally remains typed unsupported until projection segments distinguish logical blob slices from physical codec-4 payload slices. Deflate mode 2 remains unsupported and does not yet have its independent fixed-byte oracle;
- returns typed C statuses for null pointers, I/O/format errors, resource limits, out-of-range requests and unsupported representations;
- builds `cmpct-native`, a small read-only process surface for authenticated `info`, `list`, `stat`, bounded whole-member `read`, and raw-byte `range` operations without importing the Python encoder/mutation stack. `stat` exposes one authenticated logical entry without forcing callers to parse the full JSON list; `read` emits one complete regular member to stdout with a 64 MiB process-surface allocation ceiling; `range` retains the same 64 MiB per-request output ceiling. These commands deliberately inherit the core's representation/integrity policy rather than adding a second parser.

Revision-24 WAV/FLAC reconstruction lives in `native/cmpct-core/src/wavflac.rs`. Codec 2 stores a FLAC stream plus MessagePack reconstruction metadata containing the original WAV prefix/suffix and audio properties. Native archive dispatch now reads those bounded fields, reconstructs PCM16/PCM32 byte-for-byte, validates FLAC channel/rate/bit-depth and exact logical length, verifies the reconstructed WAV against the physical blob SHA-256, and only then returns the requested slice through `cmpct_entry_read_range`. This is intentionally a full bounded direct-object reconstruction before slicing; revision 24 does not provide independently authenticated seek points inside a direct FLAC stream.

The compressed direct-member paths are intentionally correctness-first. Ordinary Zstd frames, WAV/FLAC direct streams and raw Deflate streams are not intrinsically byte-seekable in revision 24, so a range request on one direct compressed member currently decodes that member in full. This is still materially better than requiring whole-archive extraction and is the correct bridge to native archive browsing. Large ordinary files are normally chunked by the encoder; fixed/CDC chunk maps are range-local in the native core, sparse members synthesize holes without decoding or allocating unrelated logical regions, packed tiny files map to bounded slices of one shared physical blob, and supported virtual ZIP reads project only the requested nested-container regions. A small read therefore stays proportional to touched stored data for mapped/packed/virtual members rather than to the whole archive.

The native CLI is an implementation milestone, not yet a benchmark claim or shipping package. Its purpose is to make metadata lookup, bounded member reads and selective range paths independently measurable without CPython startup so future ZIP-parity records can compare CLI-vs-CLI on symmetric process boundaries.

## Integrity boundary

Direct RAW partial reads cross-check authenticated index metadata and physical framing, but a partial RAW read does not claim to authenticate the unseen remainder of the member.

Direct Zstd, WAV/FLAC, Zstd-dictionary and raw Deflate reads currently reconstruct/decode the complete member and compare SHA-256 to the physical blob identity before returning requested bytes. A malformed stream, metadata mismatch, length mismatch or content-hash mismatch fails rather than returning unauthenticated content. WAV/FLAC metadata is archive-controlled input; it is parsed under the same bounded operation and must agree with the FLAC stream properties before reconstruction succeeds.

Fixed/CDC selective reads authenticate every compressed chunk they touch before copying its overlap. RAW chunks remain genuinely range-local and, like direct RAW, do not claim authentication of unseen bytes. A complete fixed/CDC read additionally verifies the logical whole-file SHA-256 stored in the authenticated index.

Sparse selective reads use the same touched-blob policy while leaving holes as semantic zeroes. The committed sparse ABI gate proves locality by corrupting a compressed blob in an untouched extent and requiring a disjoint range to remain readable, then requiring a range that touches the corrupted extent to fail. A complete sparse read additionally verifies the logical whole-file SHA-256 across both stored extents and synthesized holes.

`S_PACK` is not a separate codec. The authenticated file row names one ordinary blob plus an offset and length. Native open rejects overflow, out-of-blob ranges and length/logical-size disagreement. A range read adds the logical member offset to the authenticated pack offset and then goes through the ordinary blob range decoder, so compressed shared blobs retain the same whole-blob authentication rule while RAW shared blobs retain the same partial-RAW boundary. A complete packed-member read verifies the logical member SHA-256 when that identity is present.

Supported virtual ZIP payloads follow the same boundary. The authenticated recipe produces only the skeleton/payload slices intersecting a request; each touched slice goes through normal blob framing/codec validation. ZIP_STORED payloads project their raw-content blob, while Deflate mode 1 projects the retained exact RFC-1951 stream blob directly and therefore performs no recompression. RAW slices retain the native core's existing partial-RAW rule and do not claim strong authentication of unseen bytes. A complete virtual-member read additionally verifies the reconstructed nested ZIP against the recipe SHA-256, so whole-member corruption cannot cross the public ABI unnoticed.

For Deflate mode 0, revision 24 requires projecting the exact *physical* RFC-1951 payload of a codec-4 blob rather than the blob's decoded logical content. The committed `deflate_physical` component caps both compressed and decoded sizes, decodes the bounded stream, verifies authenticated logical length and SHA-256, and only then returns the requested exact compressed slice. That primitive is intentionally not yet reachable through archive dispatch; the public ABI negative gate requires a valid mode-0 archive to open/enumerate but return `Unsupported` on member reads until the virtual projector carries an explicit physical-source kind.

Future range-proof or authenticated-chunk designs may allow strong verification of partial reads without touching the whole direct object; revision 24 does not currently provide such proofs.

## Fixed conformance inputs

`tests/conformance/v24-direct-codecs.json` supplies builder-independent golden archives for direct RAW, ordinary Zstd and raw Deflate. `tests/conformance/v24-chunk-maps.json` extends that boundary to `S_CHUNKS` and `S_CDC`, deliberately mixing RAW/Zstd/Deflate blobs across known cross-chunk ranges. `tests/conformance/v24-sparse.json` freezes sparse hole/data semantics independently of the encoder. `tests/conformance/v24-zstd-dictionary.json` is the fixed codec-3 acceptance oracle and includes corruption refusal for the authenticated dictionary/member relationship.

`tests/native_pack_abi.py` exercises `S_PACK` through the public C ABI using a normal revision-24 archive produced by the canonical Builder. It requires the encoder to actually choose micro-solid packing for a forest of tiny files, then proves complete and non-zero-offset range reads for every packed member. This is deliberately classified as a **regression/portability gate, not an independent conformance oracle**: a future builder-independent fixed pack archive is still required to pin pack semantics independently of the encoder.

`tests/conformance/v24-wavflac.json` freezes codec 2 independently of `cmpct.builder.Builder`. It contains one exact revision-24 archive with a libsndfile-produced FLAC payload plus MessagePack reconstruction metadata, along with archive SHA-256, logical WAV SHA-256 and a known byte-range answer. Python consumes the fixed archive directly. The Rust component gate reconstructs the frozen metadata/payload independently; the archive ABI gate then opens those exact archive bytes through the produced shared library, proves known-range and complete-member parity with the Python oracle, and rejects a physical logical-content SHA corruption before returning bytes.

`tests/conformance/v24-virtual-zip.json` freezes the first `S_VZIP` recipe independently of `cmpct.builder.Builder`. It uses one ZIP_STORED payload so the first Rust milestone isolates authenticated recipe shape, skeleton/literal accounting and range-local projection without conflating those rules with Deflate-stream reconstruction.

`tests/conformance/v24-virtual-zip-deflate-mode1.json` independently freezes ZIP method 8 with stream mode 1. The exact RFC-1951 member stream is retained as a separate ordinary CMPCT blob, and the recipe projects those bytes directly between skeleton literals. The vector freezes archive/nested-ZIP SHA-256 values, exact Deflate bytes and ranges that cross skeleton → Deflate stream → skeleton. Python's standard-library ZIP reader validates the reconstructed member, Rust component coverage proves that the planner selects the exact-stream blob without recompression, and the public C-ABI gate consumes the same fixed archive and requires complete-read corruption refusal.

`tests/conformance/v24-virtual-zip-deflate-mode0.json` independently freezes ZIP method 8 with stream mode 0. Unlike mode 1 it contains no retained duplicate stream blob: the exact RFC-1951 bytes are the physical payload of the codec-4 content blob. The Rust `deflate_physical` component is tested against those bytes with corruption, identity, range and resource-limit failures. The public archive ABI intentionally treats this representation as unsupported for now, which is itself a committed negative conformance gate rather than an untested gap.

Mode 2 remains intentionally ungated. It regenerates an exact raw Deflate stream from content plus a zlib level; an equivalent-but-different encoder output is not sufficient because the nested ZIP identity must remain byte-for-byte identical. It needs a builder-independent fixed-byte oracle plus evidence that the native implementation can reproduce the recorded zlib stream identically before dispatch can be enabled.

The important property is provenance: fixed bytes are acceptance targets, not regenerated snapshots of the current encoder. A future representation is not considered independently conformance-pinned merely because two implementations agree on bytes emitted during the same test run.

## CI conformance gate

`.github/workflows/native-core.yml` keeps the following permanent gates:

1. Rust formatting, clippy with warnings denied, unit tests and release build;
2. native entry enumeration compared against a Python-built revision-24 archive;
3. a non-Rust `ctypes` caller loading the produced shared library;
4. direct RAW/Zstd range checks and corruption refusal;
5. builder-independent RAW/Zstd/Deflate direct-codec ABI vectors;
6. builder-independent fixed/CDC chunk-map ABI vectors;
7. builder-independent sparse ABI vectors, including untouched-corruption locality;
8. Builder-derived `S_PACK` C-ABI regression coverage for complete and seeked packed-member reads; this does not replace the still-required independent pack golden;
9. builder-independent Zstd-dictionary ABI vectors, including dictionary/member corruption refusal;
10. `cmpct-native info/list/stat/read/range` cross-checked against Python plus CLI-vs-CLI ZIP semantic-parity smoke coverage;
11. builder-independent WAV/FLAC component reconstruction against `v24-wavflac.json`, including exact SHA/range agreement and malformed metadata rejection;
12. builder-independent WAV/FLAC archive reads through `cmpct_entry_read_range`, including exact known-range/full-member parity and physical hash corruption refusal;
13. builder-independent virtual-ZIP component coverage for ZIP_STORED plus retained exact Deflate mode 1, and the mode-0 authenticated physical-Deflate component against its fixed oracle, including exact reconstruction/ranges, locality, corruption refusal, explicit resource bounds and malformed/ungated-representation refusal;
14. builder-independent ZIP_STORED and Deflate-mode-1 virtual-ZIP archive reads through the public C ABI, plus the mode-0 negative ABI contract, including exact known ranges for supported modes, complete nested-ZIP SHA-256, typed bounds refusal, complete-read payload corruption refusal, and typed `Unsupported` for mode 0 until physical-source projection is wired.

## Revision-24 next implementation order

1. wire the already-frozen virtual-ZIP Deflate stream mode 0 through archive dispatch by extending projection segments with an explicit source kind and routing physical codec-4 slices through the existing authenticated `deflate_physical` primitive; preserve the current negative ABI gate until that path passes the fixed oracle end-to-end;
2. freeze an independent revision-24 vector for virtual-ZIP Deflate stream mode 2 and prove byte-identical zlib-compatible RFC-1951 generation for the recorded level before enabling it;
3. freeze a builder-independent revision-24 `S_PACK` archive so the restored pack path graduates from regression/portability evidence to an independent conformance gate;
4. sequential member streams and extraction APIs beyond the bounded whole-member process helper;
5. full structural-preflight parity and decompression/work budgets;
6. committed tail/journal recovery and prior-generation fallback;
7. platform bindings using this API rather than format-specific parsing.

The native CLI should continue to be benchmarked against mature ZIP tools using CLI-vs-CLI/process-start semantics; do not mix its results with in-process library measurements.

No r24 item above requires a format revision unless implementing it reveals that revision-24 bytes are insufficient to express the required reader semantics. The provisional r25 layer is separately governed by `docs/FORMAT.md`, `docs/V030_RELEASE_GATES.md`, `docs/V030_CANONICAL_PRODUCT_ARCHITECTURE.md` and the strict v0.30 release lock.
