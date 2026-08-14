from __future__ import annotations

from pathlib import Path


def patch(path: str, replacements: list[tuple[str, str]]) -> None:
    p = Path(path)
    text = p.read_text()
    for old, new in replacements:
        count = text.count(old)
        if count != 1:
            raise SystemExit(f"{path}: expected one match, found {count}: {old[:80]!r}")
        text = text.replace(old, new, 1)
    p.write_text(text)


patch(
    "docs/NATIVE_CORE.md",
    [
        (
            "- reads bounded slices from ordinary direct Zstd and raw Deflate members by decoding at most one direct member, enforcing a 256 MiB direct-decode cap, verifying exact decompressed length and SHA-256, then copying only the requested range to the caller;\n- returns typed C statuses",
            "- reads bounded slices from ordinary direct Zstd and raw Deflate members by decoding at most one direct member, enforcing a 256 MiB direct-decode cap, verifying exact decompressed length and SHA-256, then copying only the requested range to the caller;\n- validates revision-24 fixed and content-defined chunk maps at open time, including blob references, per-chunk declared lengths and exact logical-size accounting;\n- reads fixed/CDC ranges by decoding only chunks that intersect the caller's requested interval, with mixed RAW/Zstd/Deflate chunks supported through the same blob decoder;\n- verifies the logical whole-file SHA-256 when a caller requests a complete fixed/CDC member, while selective reads retain per-touched-blob integrity semantics;\n- returns typed C statuses",
        ),
        (
            "Large ordinary files are normally chunked by the encoder; native fixed/CDC chunk-map support is the next step needed for range-local compressed large-file access.",
            "Large ordinary files are normally chunked by the encoder; fixed/CDC chunk maps are now range-local in the native core, so a small read does not inflate unrelated chunks. Sparse maps are the next storage representation needed for broad filesystem-image portability.",
        ),
        (
            "Direct Zstd and raw Deflate reads currently decode the complete member and compare SHA-256 to the physical blob identity before returning requested bytes. A malformed stream, length mismatch or content-hash mismatch fails rather than returning unauthenticated content.\n\nFuture range-proof",
            "Direct Zstd and raw Deflate reads currently decode the complete member and compare SHA-256 to the physical blob identity before returning requested bytes. A malformed stream, length mismatch or content-hash mismatch fails rather than returning unauthenticated content.\n\nFixed/CDC selective reads authenticate every compressed chunk they touch before copying its overlap. RAW chunks remain genuinely range-local and, like direct RAW, do not claim authentication of unseen bytes. A complete fixed/CDC read additionally verifies the logical whole-file SHA-256 stored in the authenticated index.\n\nFuture range-proof",
        ),
        (
            "The important property is provenance: these bytes were hand-assembled from the revision-24 framing/schema contract rather than written by the Python `Builder`. Native RAW/Zstd/Deflate behavior can therefore be checked against a fixed format artifact instead of only against whatever the current Python encoder happens to emit. The Deflate vector is consumed through the C ABI as the acceptance oracle for native codec-4 support.",
            "The important property is provenance: these bytes were hand-assembled from the revision-24 framing/schema contract rather than written by the Python `Builder`. Native RAW/Zstd/Deflate behavior can therefore be checked against a fixed format artifact instead of only against whatever the current Python encoder happens to emit. The Deflate vector is consumed through the C ABI as the acceptance oracle for native codec-4 support.\n\n`tests/conformance/v24-chunk-maps.json` extends that builder-independent boundary to `S_CHUNKS` and `S_CDC`. Both archives deliberately mix RAW, Zstd and raw Deflate chunks, and their known range answers cross a chunk boundary. The permanent C-ABI gate also corrupts a touched physical chunk identity and requires the native reader to refuse bytes.",
        ),
        (
            "6. the committed RAW/Zstd/Deflate golden archives consumed directly through the same C ABI, including rejection of a Deflate archive whose physical content identity is corrupted while the raw Deflate stream itself remains decodable.",
            "6. the committed RAW/Zstd/Deflate golden archives consumed directly through the same C ABI, including rejection of a Deflate archive whose physical content identity is corrupted while the raw Deflate stream itself remains decodable;\n7. committed fixed/CDC golden archives consumed through the C ABI for cross-boundary selective and complete reads, including rejection of a range touching a chunk whose physical content identity was corrupted.",
        ),
        (
            "1. fixed and content-defined chunk maps with range-local decoding and whole-file verification paths;\n2. sparse extent reads without materializing holes;\n3. Zstd-dictionary and WAV/FLAC direct blobs;\n4. virtual ZIP reconstruction/range access;\n5. sequential member streams and extraction APIs;\n6. full structural-preflight parity and decompression/work budgets;\n7. committed tail/journal recovery and prior-generation fallback;\n8. platform bindings using this API rather than format-specific parsing.",
            "1. sparse extent reads without materializing holes;\n2. Zstd-dictionary and WAV/FLAC direct blobs;\n3. virtual ZIP reconstruction/range access;\n4. sequential member streams and extraction APIs;\n5. full structural-preflight parity and decompression/work budgets;\n6. committed tail/journal recovery and prior-generation fallback;\n7. platform bindings using this API rather than format-specific parsing.",
        ),
    ],
)

patch(
    "docs/CURRENT_STATE.md",
    [
        (
            "The member-access surface reads genuinely range-local slices from direct RAW members and bounded ranges from ordinary direct Zstd and raw Deflate members; Zstd currently decodes and SHA-256-authenticates at most one capped direct member before returning the requested slice. CI cross-checks entry enumeration plus RAW/Zstd range bytes against the Python oracle and exercises the shared library from a non-Rust caller. dictionary/WAV-FLAC direct blobs, chunked/sparse/virtual member access, sequential streams, journal recovery and full structural preflight parity remain unfinished.",
            "The member-access surface reads genuinely range-local slices from direct RAW members, bounded ranges from ordinary direct Zstd/raw Deflate members, and range-local fixed/CDC chunk maps that decode only intersecting chunks. Native open validates fixed/CDC blob references, declared lengths and exact logical-size accounting; complete chunked reads additionally verify the logical whole-file SHA-256. CI cross-checks the C ABI against both Python and builder-independent direct/chunk golden archives. Dictionary/WAV-FLAC direct blobs, sparse/virtual member access, sequential streams, journal recovery and full structural preflight parity remain unfinished.",
        ),
        (
            "The native core now proves two end-to-end selective-content paths across the C ABI: a non-Rust caller can open a Python-built revision-24 archive and read an arbitrary bounded slice from an incompressible direct RAW member or an ordinary direct Zstd member, with the bytes checked against the Python oracle. RAW reads remain range-local. Direct Zstd reads are capped at 256 MiB and authenticate exact decompressed length plus SHA-256 before returning bytes. This is a portability/conformance milestone, not yet a claim of representation-complete native reading.",
            "The native core now proves direct and chunked selective-content paths across the C ABI. Direct RAW remains range-local; direct Zstd/raw Deflate are capped and whole-object authenticated before slicing. Fixed and CDC members are validated from authenticated index metadata and answer cross-boundary ranges by decoding only intersecting chunks. Builder-independent golden archives deliberately mix RAW/Zstd/Deflate chunks, and full chunked reads enforce the logical whole-file SHA-256. This is a portability/conformance milestone, not yet a claim of representation-complete native reading.",
        ),
        (
            "- native memory-safe high-performance core beyond authenticated primary-index enumeration and direct RAW/Zstd range reads: complete structural validation, committed-generation recovery, Deflate/dictionary/WAV-FLAC codecs, chunked/sparse/virtual member access, sequential streams, extraction and verification remain unfinished;",
            "- native memory-safe high-performance core beyond authenticated primary-index enumeration plus direct RAW/Zstd/Deflate and fixed/CDC range reads: complete structural validation, committed-generation recovery, dictionary/WAV-FLAC codecs, sparse/virtual member access, sequential streams and extraction remain unfinished;",
        ),
        (
            "The current native slice authenticates/decodes the primary index, applies lexical path policy, enumerates entries, bounds base blobs, exposes a tested C ABI, reads direct RAW ranges without decoding unrelated data, and reads bounded ordinary direct-Zstd/raw-Deflate ranges with whole-member SHA-256 authentication. Next add fixed/CDC chunk maps so compressed large-file ranges become range-local, followed by sparse maps, dictionary/WAV-FLAC direct blobs and virtual ZIPs; then sequential member streams, committed-generation recovery and extraction.",
            "The current native slice authenticates/decodes the primary index, applies lexical path policy, enumerates entries, bounds base blobs, exposes a tested C ABI, reads direct RAW ranges without decoding unrelated data, reads bounded ordinary direct-Zstd/raw-Deflate ranges with whole-member authentication, and serves fixed/CDC maps range-locally across mixed codecs. Next add sparse maps, followed by dictionary/WAV-FLAC direct blobs and virtual ZIPs; then sequential member streams, committed-generation recovery and extraction.",
        ),
    ],
)

patch(
    "docs/HARDENING.md",
    [
        (
            "The Deflate vector now gates native raw-Deflate support through the C ABI, including strong content-hash failure behavior. Future golden sets still need to cover dictionary Zstd, WAV/FLAC, fixed chunks, CDC maps, sparse extents, packs, virtual ZIP recipes, links/metadata and committed transaction generations.",
            "The Deflate vector now gates native raw-Deflate support through the C ABI, including strong content-hash failure behavior. `tests/conformance/v24-chunk-maps.json` now adds builder-independent `S_CHUNKS` and `S_CDC` archives whose known ranges cross chunk boundaries and mix RAW/Zstd/Deflate physical blobs. Future golden sets still need dictionary Zstd, WAV/FLAC, sparse extents, packs, virtual ZIP recipes, links/metadata and committed transaction generations.",
        ),
        (
            "- golden revision-24 coverage is only partial: direct RAW/Zstd/Deflate now exist, while other codecs/storage descriptions/generations remain missing;",
            "- golden revision-24 coverage is only partial: direct RAW/Zstd/Deflate plus fixed/CDC chunk maps now exist, while other codecs/storage descriptions/generations remain missing;",
        ),
        (
            "- parser behavior has begun independent cross-checking: the Rust core authenticates/decodes the primary index, matches Python entry enumeration/path policy, and cross-checks bounded direct RAW, ordinary-Zstd and raw-Deflate range bytes through the C ABI. Full structural references, tail/journal recovery, remaining codecs, chunk/sparse/virtual storage and extraction are not yet independently validated.",
            "- parser behavior has begun independent cross-checking: the Rust core authenticates/decodes the primary index, matches Python entry enumeration/path policy, cross-checks bounded direct RAW/Zstd/Deflate ranges, and independently validates/reads fixed and CDC chunk maps through the C ABI. Full structural parity, tail/journal recovery, remaining codecs, sparse/virtual storage and extraction are not yet independently validated.",
        ),
        (
            "The shared Rust reader now has a bounded bridge for ordinary direct Zstd members. It will not allocate or decode a direct compressed member above 256 MiB, checks physical blob framing against authenticated index metadata, requires the exact declared decompressed length, and verifies the decoded bytes against the blob SHA-256 before returning a requested range. RAW partial reads remain range-local and deliberately do not claim whole-member verification of unseen bytes.\n\nThis is a representation-specific safety increment, not a replacement for full native preflight parity. Large ordinary files are normally chunked by the encoder; native chunk-map validation and range-local chunk decoding remain necessary so a small range request never needs a giant direct allocation merely because a future encoder policy changes.",
            "The shared Rust reader has bounded bridges for ordinary direct Zstd/raw Deflate and for fixed/CDC chunk maps. A direct compressed object cannot allocate/decode above 256 MiB and must match physical framing, exact decoded length and blob SHA-256 before a slice is returned. Fixed/CDC maps are checked for valid blob references, declared-length agreement and exact logical-size accounting before use; selective reads decode only intersecting chunks, and complete reads additionally verify the logical whole-file SHA-256. RAW partial reads remain range-local and deliberately do not claim whole-member verification of unseen bytes.\n\nThis is a representation-specific safety increment, not a replacement for full native preflight parity. Sparse, pack, virtual, dictionary/audio and journal structures still need independent native validation before the shared handler is representation-complete.",
        ),
        (
            "1. Expand the committed golden revision-24 set from direct RAW/Zstd/Deflate to every storage kind, codec and committed-generation shape.",
            "1. Expand the committed golden revision-24 set from direct RAW/Zstd/Deflate plus fixed/CDC maps to every remaining storage kind, codec and committed-generation shape.",
        ),
        (
            "6. Expand the Rust/Python cross-check from authenticated primary-index enumeration plus direct RAW/Zstd member ranges to fixed/CDC chunk maps, then complete structural validation, tail/journal recovery, remaining codecs, chunk/sparse/virtual member reads and extraction before treating the native reader as an independent conformance implementation.",
            "6. Expand the Rust/Python cross-check beyond authenticated primary-index enumeration plus direct RAW/Zstd/Deflate and fixed/CDC ranges to complete structural validation, tail/journal recovery, remaining codecs, sparse/virtual member reads and extraction before treating the native reader as an independent conformance implementation.",
        ),
    ],
)

patch(
    "docs/PORTABILITY.md",
    [
        (
            "The current native Zstd bridge follows that rule and caps one direct decode at 256 MiB. The long-term\npath for large compressed files is the revision-24 chunk map: decode only chunks intersecting the\nrequested range.",
            "The current native Zstd/Deflate bridge follows that rule and caps one direct decode at 256 MiB. Revision-24 fixed and CDC chunk maps are now range-local in the shared core: a request decodes only chunks intersecting the requested range, which is the required behavior for large compressed-file browsing.",
        ),
        (
            "- native bounded range reads for ordinary direct Zstd members, with a 256 MiB per-direct-member decode ceiling, exact decompressed-length validation and SHA-256 verification before returning the requested slice;\n- CI that compares native entry enumeration plus RAW/Zstd range bytes against the Python oracle and exercises the produced shared library from a non-Rust caller.",
            "- native bounded range reads for ordinary direct Zstd and raw Deflate members, with a 256 MiB per-direct-member decode ceiling, exact decompressed-length validation and SHA-256 verification before returning the requested slice;\n- native fixed/CDC chunk-map validation and range-local reads across mixed RAW/Zstd/Deflate chunks, with complete-member logical SHA-256 verification;\n- builder-independent direct-codec and chunk-map golden archives exercised through the produced shared library from a non-Rust caller, including corruption refusal.",
        ),
        (
            "- complete memory-safe native reader/writer ABI beyond primary-index/open/enumeration and direct RAW/Zstd reads: full hostile structural validation, recovery, remaining codecs/storage descriptions, streams, extraction and mutation are still pending;",
            "- complete memory-safe native reader/writer ABI beyond primary-index/open/enumeration plus direct RAW/Zstd/Deflate and fixed/CDC reads: full hostile structural validation, recovery, remaining codecs/storage descriptions, streams, extraction and mutation are still pending;",
        ),
    ],
)
