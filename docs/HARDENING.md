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

## Deliberate non-goals of this increment

This is a structural preflight foundation, **not a claim that hostile-input work is finished**.

In particular:

- ordinary `CMPCT(...)` opens do not yet automatically run the full preflight;
- payload decompression paths still need direct per-operation resource budgets;
- `read()` may intentionally materialize a complete logical file and therefore still needs a caller budget for untrusted archives;
- no property-based or coverage-guided fuzzer is committed yet;
- golden revision-24 binary conformance vectors are not committed yet;
- nested recipes, chunk maps, sparse extents and journal operations still need byte-level mutation coverage in addition to the structural mutation matrix;
- parser behavior has not yet been cross-checked against an independent implementation.

### Known path-normalization collision to resolve

The current structural validator converts backslashes to `/` when checking traversal components, but duplicate-path detection still keys the original path string. The extractor also converts backslashes to `/` before constructing destination paths. Therefore two distinct index strings such as `a/b` and `a\\b` can currently survive the structural duplicate check yet name the same extraction destination.

This should be fixed as part of the normal-reader validation integration, with one canonical lexical path key shared by preflight and extraction. Do not paper over it with an expected-failure test: the desired regression must prove that colliding archive paths are rejected before any destination file is written. Platform-specific separator and Unicode normalization rules still belong in the normative specification.

The explicit preflight command is intentional for this first increment: it creates one testable, fuzzable safety boundary without silently adding latency to every existing reader hot path before the cost is measured.

## Next hardening sequence

1. Run the complete regression suite against this preflight layer and fix any false positives.
2. Add golden revision-24 archives/vectors for every storage kind and codec.
3. Add property tests and a byte-level mutation/fuzz corpus for headers, MessagePack structures, blob framing, chunk maps, sparse maps, nested recipes, journal chains and path relationships.
4. Add per-read/per-extract decompressed-byte and work budgets; then integrate bounded validation into the normal reader constructor under an explicit policy, including canonical path-collision rejection shared with extraction.
5. Benchmark preflight/open overhead across tiny, source, media, sparse, nested and combined corpora.
6. Turn validated structural maxima and canonical encodings into the normative byte-level spec.
7. Cross-check the Python parser with the future memory-safe native reader.

## Revision rule

No format revision bump is required for this increment because it writes **no new field, record, codec, transform or storage semantic**. If later hardening requires a reader-visible on-disk rule, that change must follow the repository's normal revision/spec/history/current-state/conformance gate.
