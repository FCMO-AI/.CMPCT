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

The first committed golden archive set now lives at `tests/conformance/v24-direct-codecs.json`. It contains fixed byte-for-byte revision-24 archives for direct RAW, ordinary Zstd and raw Deflate members, together with archive SHA-256, logical SHA-256 and known byte-range answers.

These vectors were deliberately hand-built from the revision-24 framing/schema rules rather than emitted by `cmpct.builder.Builder`. That distinction is important: builder-to-reader round trips prove internal agreement, while fixed bytes that are independent of the builder can expose parser drift across implementations. The JSON records the generator-tool provenance used to freeze the bytes; future readers must consume the existing archive bytes rather than regenerate fixtures around changed behavior.

The Deflate vector gates native raw-Deflate support through the C ABI, including strong content-hash failure behavior. `tests/conformance/v24-chunk-maps.json` adds builder-independent `S_CHUNKS` and `S_CDC` archives whose known ranges cross chunk boundaries and mix RAW/Zstd/Deflate physical blobs. `tests/conformance/v24-sparse.json` freezes `S_SPARSE` semantics independently of the builder: its logical member contains leading/interior/trailing holes plus data extents backed by RAW, Zstd and raw Deflate blobs, with known ranges crossing hole/data and codec boundaries. The Rust C ABI now consumes all three sets. Future golden sets still need dictionary Zstd, WAV/FLAC, packs, virtual ZIP recipes, links/metadata and committed transaction generations.

## Deliberate non-goals of this increment

This is a structural preflight foundation, **not a claim that hostile-input work is finished**.

In particular:

- ordinary `CMPCT(...)` opens do not yet automatically run the full preflight;
- payload decompression paths still need direct per-operation resource budgets;
- `read()` may intentionally materialize a complete logical file and therefore still needs a caller budget for untrusted archives;
- no property-based or coverage-guided fuzzer is committed yet;
- golden revision-24 coverage is only partial: direct RAW/Zstd/Deflate, fixed/CDC chunk maps and sparse extents now exist, while other codecs/storage descriptions/generations remain missing;
- nested recipes, chunk maps, sparse extents and journal operations still need byte-level mutation coverage in addition to the structural mutation matrix;
- parser behavior has begun independent cross-checking: the Rust core authenticates/decodes the primary index, matches Python entry enumeration/path policy, cross-checks bounded direct RAW/Zstd/Deflate ranges, independently validates/reads fixed and CDC chunk maps, and now independently validates/reads sparse extent maps through the C ABI. Full structural parity, tail/journal recovery, dictionary/audio codecs, virtual storage and extraction are not yet independently validated.

### Canonical lexical path aliases

Resolved in the current revision-24 implementation: preflight, ordinary reader open and extraction now share one lexical path key. Backslashes are treated as archive separators, `.`/`..`/empty components are rejected, and aliases such as `a/b` and `a\\b` are rejected before extraction creates any member. Hardlink targets use the same policy.

This intentionally solves only host-independent lexical aliasing. Unicode normalization, platform case-folding, Windows reserved names/device paths and other host-specific rules still belong in the normative specification and platform policy layer; they must not be guessed independently by each handler.

The explicit preflight command is intentional for this first increment: it creates one testable, fuzzable safety boundary without silently adding latency to every existing reader hot path before the cost is measured.

## Native direct/map-decode safety boundary

The shared Rust reader has bounded bridges for ordinary direct Zstd/raw Deflate and for fixed/CDC/sparse maps. A direct compressed object cannot allocate/decode above 256 MiB and must match physical framing, exact decoded length and blob SHA-256 before a slice is returned. Fixed/CDC maps are checked for valid blob references, declared-length agreement and exact logical-size accounting before use; selective reads decode only intersecting chunks, and complete reads additionally verify the logical whole-file SHA-256.

Sparse maps additionally require sorted, non-overlapping extents within logical EOF and exact equality between each extent length and the sum of its referenced blob lengths. Sparse selective reads synthesize holes as zeroes and decode only stored chunks in touched extents. The fixed ABI gate proves this locality by corrupting a compressed blob in an untouched extent: a disjoint range still succeeds, while a range touching the corrupted extent fails. RAW partial reads remain range-local and deliberately do not claim whole-member verification of unseen bytes.

This is a representation-specific safety increment, not a replacement for full native preflight parity. Pack, virtual, dictionary/audio and journal structures still need independent native validation before the shared handler is representation-complete.

## Next hardening sequence

1. Expand the golden revision-24 set to dictionary Zstd, WAV/FLAC, packs, virtual ZIP recipes, links/metadata and committed-generation shapes, and make each implemented native representation cross the fixed C-ABI oracle rather than only Python-generated archives.
2. Add property tests and a byte-level mutation/fuzz corpus for headers, MessagePack structures, blob framing, chunk maps, sparse maps, nested recipes, journal chains and path relationships.
3. Add per-read/per-extract decompressed-byte and work budgets; then integrate bounded validation into the normal reader constructor under an explicit policy, including canonical path-collision rejection shared with extraction.
4. Benchmark preflight/open overhead across tiny, source, media, sparse, nested and combined corpora.
5. Turn validated structural maxima and canonical encodings into the normative byte-level spec.
6. Expand the Rust/Python cross-check beyond authenticated primary-index enumeration plus direct RAW/Zstd/Deflate and fixed/CDC/sparse ranges to complete structural validation, tail/journal recovery, remaining codecs, virtual member reads and extraction before treating the native reader as an independent conformance implementation.

## Revision rule

No format revision bump is required for this increment because it writes **no new field, record, codec, transform or storage semantic**. If later hardening requires a reader-visible on-disk rule, that change must follow the repository's normal revision/spec/history/current-state/conformance gate.
