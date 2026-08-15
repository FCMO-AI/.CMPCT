# Parser hardening and conformance frontier

Status: **P0 foundation in progress / format revision 24 unchanged.**

This document records parser-safety work separately from the format contract so future agents can continue the hardening campaign without inventing context from chat. `docs/FORMAT.md` remains the on-disk contract; this file describes validation policy and unfinished work.

## Why this is the immediate frontier

Revision 24 already has broad format capability, but breadth is not the same as a defensible parser. The original reader validates decoded content well, yet several archive-controlled lengths and references can be consumed before a dedicated structural/resource-limit gate has rejected them.

That ordering matters for hostile input. A corrupted or deliberately malicious archive should fail cheaply and predictably before it can request absurd decompression buffers, walk an unbounded journal chain, index outside the archive, or construct cyclic logical relationships.

This directly implements the first mission in `docs/CURRENT_STATE.md` and the P0 hardening work in `docs/ROADMAP.md`. It does **not** change revision-24 bytes.

## First hardening increment

The additive `cmpct.validation` layer provides:

- `ParserLimits` — explicit caps for index/generation/blob sizes and structural counts;
- bounded primary-index and transaction-generation decoding;
- bounded transaction-chain traversal with cycle detection;
- strict MessagePack container limits;
- structural validation for file, blob, recipe, chunk, sparse and pack references;
- duplicate-path and hardlink-cycle rejection;
- dictionary and filesystem-metadata reference validation;
- physical blob-header cross-checking against the logical blob table without decompressing payloads;
- a library entry point: `preflight_archive(...)`;
- a CLI entry point: `cmpct preflight archive.cmpct`;
- adversarial regression tests covering oversized index/generation declarations, corrupt blob framing, truncated archives and latest-generation fallback;
- a direct structural mutation matrix covering unknown codecs, blob policy limits, pack bounds, fixed/CDC chunk accounting, sparse extent accounting, missing virtual-ZIP recipes, duplicate paths, unsafe paths, hardlink targets/cycles and filesystem-metadata references.

### Default limits

The initial defaults are intentionally generous for legitimate pre-1.0 archives while still placing finite ceilings on hostile declarations. They are policy, not format constants, and can be overridden with `CMPCT_MAX_*` environment variables or a `ParserLimits` instance.

A future normative specification must distinguish format maxima from implementation policy limits.

## Fixed revision-24 conformance vectors

The first committed golden archive set lives at `tests/conformance/v24-direct-codecs.json`. It contains fixed byte-for-byte revision-24 archives for direct RAW, ordinary Zstd and raw Deflate members, together with archive SHA-256, logical SHA-256 and known byte-range answers.

These vectors were deliberately hand-built from the revision-24 framing/schema rules rather than emitted by `cmpct.builder.Builder`. That distinction is important: builder-to-reader round trips prove internal agreement, while fixed bytes that are independent of the builder can expose parser drift across implementations. The JSON records the generator-tool provenance used to freeze the bytes; future readers must consume the existing archive bytes rather than regenerate fixtures around changed behavior.

The Deflate vector gates native raw-Deflate support through the C ABI, including strong content-hash failure behavior. `tests/conformance/v24-chunk-maps.json` adds builder-independent `S_CHUNKS` and `S_CDC` archives whose known ranges cross chunk boundaries and mix RAW/Zstd/Deflate physical blobs. `tests/conformance/v24-sparse.json` freezes `S_SPARSE` semantics independently of the builder: its logical member contains leading/interior/trailing holes plus data extents backed by RAW, Zstd and raw Deflate blobs, with known ranges crossing hole/data and codec boundaries. The Rust C ABI consumes all three sets.

`tests/conformance/v24-zstd-dictionary.json` freezes the codec-3 relationship independently of the encoder. The archive contains a RAW dictionary blob referenced by authenticated `dict_blob` metadata plus a direct Zstd-with-dictionary member whose compressed payload cannot be decoded as ordinary codec-1 Zstd. Its archive bytes, dictionary identity, logical identity and known range answer are fixed and consumed by both the Python reference reader and the native C ABI with bounded dictionary/member allocation and corruption refusal.

`tests/native_pack_abi.py` now restores native `S_PACK` regression coverage that had been lost during an Android rebase. The test requires the canonical revision-24 Builder to produce a micro-solid tiny-file forest, then reads every packed member through the public C ABI and additionally proves a non-zero-offset seek within each logical member. This closes a real platform-read gap, but because the fixture is Builder-produced it remains **regression/portability evidence rather than an independent conformance vector**. A frozen builder-independent pack archive is still required.

`tests/conformance/v24-wavflac.json` freezes codec 2 independently of the builder. It contains an exact revision-24 archive carrying MessagePack reconstruction metadata plus a libsndfile-produced FLAC payload, with fixed archive/logical SHA-256 values and a known byte-range answer. The Rust component independently reconstructs the WAV, and native archive dispatch now consumes the same frozen archive through `cmpct_entry_read_range`, including complete-byte parity and physical logical-content hash corruption refusal.

`tests/conformance/v24-virtual-zip.json` freezes the first `S_VZIP` recipe independently of the builder. It contains a hand-built revision-24 archive whose nested ZIP is reconstructed from an authenticated skeleton plus one stored payload, with fixed outer archive/logical ZIP/member identities and known byte-range answers. Native archive parsing consumes this stored-payload recipe through `cmpct_entry_read_range`, while component tests retain the locality proof that a skeleton/payload/skeleton range touches only those intersecting slices.

`tests/conformance/v24-virtual-zip-deflate-mode1.json` freezes ZIP method 8 with stream mode 1. The exact RFC-1951 stream is retained as a separate ordinary CMPCT blob and projected directly between skeleton literals. The fixed archive records outer/nested/member identities, exact Deflate bytes and cross-boundary ranges. Python reconstructs it byte-for-byte and validates it with the standard ZIP reader; the Rust planner selects the retained exact-stream blob without recompression; the public C ABI consumes the same frozen archive and rejects complete-member corruption.

`tests/conformance/v24-virtual-zip-deflate-mode0.json` now independently freezes ZIP method 8 with stream mode 0. This shape deliberately has no retained duplicate stream blob: its exact RFC-1951 bytes are the physical payload of the codec-4 content blob. The Rust `deflate_physical` component authenticates the bounded physical stream by decoding it, checking declared logical length and logical SHA-256, and only then exposing the requested exact compressed slice. The public archive ABI intentionally keeps mode 0 typed unsupported until virtual projection segments distinguish logical blob reads from authenticated physical codec-4 payload reads; that refusal is itself committed as a negative conformance gate.

An independent virtual-ZIP vector is still required for Deflate stream mode 2. Mode 2 requires byte-for-byte zlib-compatible regeneration from raw content plus the recorded level; merely producing an equivalent Deflate stream is insufficient because the nested ZIP must reconstruct exactly.

Future golden sets still need an independent pack archive, links/metadata, committed transaction generations and virtual-ZIP Deflate stream mode 2.

## Deliberate non-goals of this increment

This is a structural preflight foundation, **not a claim that hostile-input work is finished**.

In particular:

- ordinary `CMPCT(...)` opens do not yet automatically run the full preflight;
- payload decompression paths still need direct per-operation resource budgets;
- `read()` may intentionally materialize a complete logical file and therefore still needs a caller budget for untrusted archives;
- no property-based or coverage-guided fuzzer is committed yet;
- golden revision-24 coverage is still partial: direct RAW/Zstd/Deflate/WAV-FLAC/Zstd-with-dictionary, fixed/CDC chunk maps, sparse extents, stored-payload virtual ZIP, retained-exact Deflate mode 1, and the independently frozen Deflate mode-0 virtual-ZIP oracle exist; native pack reads have Builder-derived ABI regression coverage but not yet an independent fixed pack oracle; links/metadata, committed generations and virtual-ZIP Deflate mode 2 remain missing;
- nested recipes, chunk maps, sparse extents, pack descriptors and journal operations still need byte-level mutation coverage in addition to the structural mutation matrix;
- parser behavior has begun independent cross-checking: the Rust core authenticates/decodes the primary index, matches Python entry enumeration/path policy, cross-checks bounded direct RAW/Zstd/WAV-FLAC/Deflate/Zstd-dictionary ranges, independently validates/reads fixed and CDC chunk maps plus sparse extent maps through the C ABI, has Builder-derived complete/seeked `S_PACK` C-ABI coverage, independently parses/reads stored-payload and retained-exact-Deflate virtual-ZIP goldens through the same public ABI, and independently authenticates exact physical mode-0 Deflate slices at the component boundary. Full structural parity, tail/journal recovery, mode-0 archive dispatch, virtual-ZIP Deflate mode 2, independent pack conformance and extraction are not yet complete.

### Canonical lexical path aliases

Resolved in the current revision-24 implementation: preflight, ordinary reader open and extraction now share one lexical path key. Backslashes are treated as archive separators, `.`/`..`/empty components are rejected, and aliases such as `a/b` and `a\\b` are rejected before extraction creates any member. Hardlink targets use the same policy.

This intentionally solves only host-independent lexical aliasing. Unicode normalization, platform case-folding, Windows reserved names/device paths and other host-specific rules still belong in the normative specification and platform policy layer; they must not be guessed independently by each handler.

The explicit preflight command is intentional for this first increment: it creates one testable, fuzzable safety boundary without silently adding latency to every existing reader hot path before the cost is measured.

## Native direct/map-decode safety boundary

The shared Rust reader has bounded bridges for ordinary direct Zstd/WAV-FLAC/raw Deflate/Zstd-dictionary, fixed/CDC/sparse maps, micro-solid `S_PACK` slices, and the independently gated stored-payload plus retained-Deflate-mode-1 virtual-ZIP recipes. A direct compressed/reconstructed object cannot allocate/decode above 256 MiB and must match physical framing, exact logical length and blob SHA-256 before a slice is returned. WAV/FLAC additionally requires codec metadata to parse cleanly and agree with FLAC stream channel/rate/bit-depth before reconstruction succeeds. Fixed/CDC maps are checked for valid blob references, declared-length agreement and exact logical-size accounting before use; selective reads decode only intersecting chunks, and complete reads additionally verify the logical whole-file SHA-256.

Sparse maps additionally require sorted, non-overlapping extents within logical EOF and exact equality between each extent length and the sum of its referenced blob lengths. Sparse selective reads synthesize holes as zeroes and decode only stored chunks in touched extents. The fixed ABI gate proves this locality by corrupting a compressed blob in an untouched extent: a disjoint range still succeeds, while a range touching the corrupted extent fails. RAW partial reads remain range-local and deliberately do not claim whole-member verification of unseen bytes.

`S_PACK` open validates the authenticated tuple as a checked slice of a referenced ordinary blob, rejects offset/length overflow and out-of-blob ranges, and requires the packed slice length to equal the logical member size. Range reads translate logical member offsets into that shared blob and reuse the same blob decoder/integrity boundary. Complete reads verify the member logical SHA-256 when present. The implementation now has a Builder-derived public-ABI regression gate; independent fixed-byte pack provenance remains the next conformance step.

Supported virtual ZIP validates recipe shape, skeleton/payload alternation, blob references, literal totals and logical size from authenticated metadata. Selective reads project only intersecting recipe slices and route them through the normal blob decoder. ZIP_STORED uses the raw content blob; Deflate mode 1 uses the retained exact-stream blob directly, so it preserves exact nested-ZIP bytes without invoking a compressor. Complete reads additionally verify the reconstructed nested ZIP against the recipe logical SHA-256. Revision-24 Deflate mode 0 is independently frozen and has a bounded authenticated physical-stream primitive but intentionally remains unsupported at archive dispatch until the projector can select that physical source kind. Deflate mode 2 remains unsupported pending its independent fixed-byte oracle and byte-identical regeneration evidence.

This is a representation-specific safety increment, not a replacement for full native preflight parity. Pack has native regression coverage but still needs independent fixed-byte conformance; virtual-ZIP Deflate modes 0/2 at the archive-dispatch level and journal structures remain incomplete before the shared handler is representation-complete.

## Next hardening sequence

1. Wire the already-frozen virtual-ZIP Deflate mode 0 through archive dispatch by adding an explicit physical-codec-payload projection source and routing it through the authenticated `deflate_physical` primitive; then freeze and gate Deflate mode 2. Freeze an independent pack archive alongside links/metadata and committed-generation shapes.
2. Add property tests and a byte-level mutation/fuzz corpus for headers, MessagePack structures, blob framing, chunk maps, sparse maps, pack descriptors, nested recipes, journal chains and path relationships.
3. Add per-read/per-extract decompressed-byte and work budgets; then integrate bounded validation into the normal reader constructor under an explicit policy, including canonical path-collision rejection shared with extraction.
4. Benchmark preflight/open overhead across tiny, source, media, sparse, nested and combined corpora.
5. Turn validated structural maxima and canonical encodings into the normative byte-level spec.
6. Expand the Rust/Python cross-check beyond authenticated primary-index enumeration plus implemented direct/map/pack/virtual ranges to complete structural validation, representation-complete virtual member reads, extraction and tail/journal recovery before treating the native reader as an independent conformance implementation.

## Revision rule

No format revision bump is required for this increment because it writes **no new field, record, codec, transform or storage semantic**. If later hardening requires a reader-visible on-disk rule, that change must follow the repository's normal revision/spec/history/current-state/conformance gate.
