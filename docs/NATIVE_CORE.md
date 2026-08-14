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
- reads bounded slices from ordinary direct Zstd and raw Deflate members by decoding at most one direct member, enforcing a 256 MiB direct-decode cap, verifying exact decompressed length and SHA-256, then copying only the requested range to the caller;
- returns typed C statuses for null pointers, I/O/format errors, resource limits, out-of-range requests and unsupported representations.

The Zstd path is intentionally correctness-first. Ordinary Zstd frames are not intrinsically byte-seekable, so a range request on one direct compressed member currently decodes that member in full. This is still materially better than requiring whole-archive extraction and is the correct bridge to native archive browsing. Large ordinary files are normally chunked by the encoder; native fixed/CDC chunk-map support is the next step needed for range-local compressed large-file access.

## Integrity boundary

Direct RAW partial reads cross-check authenticated index metadata and physical framing, but a partial RAW read does not claim to authenticate the unseen remainder of the member.

Direct Zstd reads currently decode the complete member and compare SHA-256 to the physical blob identity before returning requested bytes. A malformed stream, length mismatch or content-hash mismatch fails rather than returning unauthenticated content.

Future range-proof or authenticated-chunk designs may allow strong verification of partial reads without touching the whole direct object; revision 24 does not currently provide such proofs.

## Fixed conformance inputs

`tests/conformance/v24-direct-codecs.json` now supplies the first builder-independent golden archives for the native implementation. The set freezes exact revision-24 archive bytes for direct RAW, ordinary Zstd and raw Deflate members and records archive SHA-256, logical SHA-256 and a known range answer for each member.

The important property is provenance: these bytes were hand-assembled from the revision-24 framing/schema contract rather than written by the Python `Builder`. Native RAW/Zstd behavior can therefore be checked against a fixed format artifact instead of only against whatever the current Python encoder happens to emit. The Deflate vector is now consumed through the C ABI as the acceptance oracle for native codec-4 support.

## CI conformance gate

`.github/workflows/native-core.yml` must keep the following gates green:

1. Rust formatting, clippy with warnings denied, unit tests and release build;
2. native entry enumeration compared against a Python-built revision-24 archive;
3. a non-Rust `ctypes` caller loading the produced shared library;
4. RAW range bytes compared against the Python oracle;
5. direct-Zstd range bytes compared against the Python oracle, with the fixture asserting that the selected member is physically codec 1 rather than accidentally RAW;
6. as the golden suite is wired into native CI, the same ABI must consume the committed RAW/Zstd vectors directly and the direct-Deflate milestone must pass the committed codec-4 vector before it is documented as implemented.

A future representation is not considered implemented merely because a Rust function can decode it. It must cross the C ABI and agree with both the Python oracle where applicable and a committed golden archive once one exists for that representation.

## Next implementation order

1. fixed and content-defined chunk maps with range-local decoding and whole-file verification paths;
3. sparse extent reads without materializing holes;
4. Zstd-dictionary and WAV/FLAC direct blobs;
5. virtual ZIP reconstruction/range access;
6. sequential member streams and extraction APIs;
7. full structural-preflight parity and decompression/work budgets;
8. committed tail/journal recovery and prior-generation fallback;
9. platform bindings using this API rather than format-specific parsing.

No item above requires a format revision unless implementing it reveals that revision-24 bytes are insufficient to express the required reader semantics. In that case the normal specification/version/conformance gate applies.
