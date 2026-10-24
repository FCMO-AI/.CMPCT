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

### v0.31 scoped candidate: failed Reader opens do not retain file or mmap resources

The Reader constructor owns the file descriptor from the moment `open()` succeeds. If index loading, `mmap()`, or canonical namespace checks fail, no usable Reader escapes and `close()` is unreachable. The isolated [PR #283](https://github.com/FCMO-AI/.CMPCT/pull/283) established a retained-exception baseline leak on the original revision-24 Reader and passed four adversarial tests after deterministic exception-path cleanup. This stacked composition carries **only that unchanged constructor** into the three-owner Reader/Public Proof/optional RAW-range candidate of PR #277, without restoring the older close order or altering other Reader operations. The source-bound control and negative outcome remain owned by PR #283; composed full-product CI and portability must be evaluated independently. No new parser-preflight, native-ABI, format or release claim follows from the constructor fix.

## Default limits

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

### Python opt-in RAW digest-range experiment (v0.31 draft; not promoted)

An experimental Python-only method `CMPCT.read_raw_range_verified(name,start,length,*,max_scan_bytes=64*1024*1024)` lives in draft PR #274. It supports direct `S_BLOB/CODEC_RAW` regular members and their hardlink aliases. Unlike default `read_range()`, it checks the complete physical RAW blob's CRC32 and SHA-256 against its committed physical record before returning a partial copy; a present logical SHA must agree too. The caller-visible scan budget rejects larger blobs before scanning. Unsupported storage kinds fail explicitly rather than silently escalating decoding or allocation. It does **not** change default fast range semantics, native ABI, or the revision-24 archive format.

This is a digest-*consistency* check against archive metadata, **not authenticity of origin**: an adversary who can rewrite both payload and physical digest can forge a self-consistent record. The method deliberately does not promise a concurrent mutable-file snapshot, and a clean verified read cannot be reused as a timeless trust cache. One requested byte can force CRC and SHA of the **whole** blob, with O(logical blob bytes) CPU/memory traffic and O(requested range) returned allocation. It is not a constant-time or sublinear cryptographically authenticated range proof; independent merkleized structures would need separate storage/native/format/economic evaluation.

The draft's focused regressions include stale CRC, repaired CRC but stale digest, off-range corruption, header corruption, hardlink alias parity, refusal of oversized scans and unsupported codecs, Python heap accounting, and an explicit digest-rewrite negative. They do not replace exact-head installed-package CI, full release performance, integrity/recovery, reader-owner integration or portability approval.

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


## v0.31 physical salvage candidate trust tiers (prospective; PR-local until merged)

`recover_blob_records` and `cmpct recover-blobs` enumerate syntactically framed physical **header candidates**. They are forensic aids, **not** authenticated recovered content. Every returned row preserves the previously exposed `offset`, `codec`, `usize`, `csize`, `crc32` and `sha256` header claims, but adds `verification: "unverified"` and `generation_membership: "unknown"`. A SHA-256 displayed in this output is a *declared value copied from the header*, not a verified calculation on decoded bytes. A plausible header can be uncommitted, forged or have a corrupted payload. The normal `CMPCT.read` path retains its independent integrity checks; this scanner never weakens them.

The candidate-only scan now reads the input in 1 MiB blocks and carries `BHDR.size-1` bytes across adjacent windows, retaining the original offset/order/framing semantics without `Path.read_bytes()` materializing the entire archive (including sparse logical holes). Peak *scan-buffer* size is at most 1 MiB + 63 bytes for the current 64-byte header, and tiny files allocate only `min(1 MiB, initial file length) + 63 bytes`: the scanner now reuses one `bytearray` via `readinto` rather than creating a second full block copy. The legacy library `recover_blob_records` API still returns a Python list proportional to the number of matched candidate headers; the CLI uses the private record iterator to stream its JSON array incrementally and retains the legacy pretty-JSON text shape with no candidate-list materialization. The scan captures the initial opened inode's `fstat` length and reads **at most that many bytes**, so concurrent append growth cannot create an unbounded tail-following workload; truncations or concurrent in-place modifications still produce no immutable-snapshot guarantee. File-backed streaming does not make a live concurrently changing archive an immutable snapshot. No CRC, content hash, codec reconstruction, generation membership or filesystem reconstruction is attested by this endpoint.

The PR's independent regression court compares every inherited record field/offset on boundary-straddling, nested/forged, truncated, unknown-codec and authentic revision-24 test archives, plus the CLI output. A Linux fresh-child ABBA court compares the real installed scanner with the original full-buffer algorithm on an identical 64 MiB sparse source, preserving CPU/wall and incremental peak RSS measurements without claiming a format/compression improvement. A future opt-in verified recovery mode requires per-codec bounded decode, hostile false-positive/decompression tests, distinct confidence tiers, authenticated output and proof of resource budgets; this PR does **not** implement that mode. Wire revision 24 and release evidence/gates remain unchanged.


## v0.31 integration candidate: strict signed MessagePack map admission with platform Reader safeguards (2026-10-24)

Integration PR #345 composes the independent exact-source nested-map policy of PR #326 with the existing signed-tree, verified PACK, Writer/recovery, and Win32/APFS namespace checks. SHA-256 authentication covers **wire bytes** but cannot resolve duplicate map-key semantics: legacy Python unpacking can retain the last value while native rmpv field lookup retains the first. The candidate therefore installs `object_pairs_hook=unique_map_pairs` at all three Python Reader index/delta decode boundaries and in validator preflight. Rust checks every authenticated map depth using an iterative walker before consuming index fields, requiring text/binary map keys and refusing repeated keys. The independent PR #326 authenticated nested-map oracle and Reader-open/FD-lifetime court are source-exact controls; CI results for this new composed HEAD must be checked separately.

This is a **candidate security convergence**, not a released version or a rewrite of the immutable v0.30 receipt. Parser denial must not leak Reader file/mmap handles, weaken the existing authenticated physical PACK verification or graph/path guards, change r24 archive bytes, or treat an administratively SKIPPED parity job as performance success. The new policy does **not** solve preexisting destination symlink pivots (Issue #265), descriptor-root race resistance, filesystem xattr/ACL fidelity, POSIX undecodable names, or universal Win32/APFS normalization identity. Full portability, exact-head hostile tests and the unchanged performance gate remain promotion requirements.


## v0.31 O7 — shared authenticated Reader/strict-preflight transaction replay (draft, 2026-10-24)

The ordinary Python Reader historically maintained a separate quadratic put/delete/rename interpreter in `_index_from_footer`; strict `preflight_archive` already had a tested position-indexed implementation. O7 draft PR #358 now reuses the **unchanged** `validation._apply_delta` for each SHA-authenticated generation, retains the historical per-generation row sort, and imports the validator lazily so checkpoint-only opens do not pay a new dependency-import cost. The core original-index/delta/physical revision-24 bytes, Member/Reader interface, nested MessagePack rejection, extraction namespace/TOCTOU contracts, footer scanning and other Reader methods are untouched.

The shared owner has existing independent first-match put/rename, all-match delete, repeated-name and parser-bound tests. Signed malformed unknown operation tags now reject consistently with strict preflight rather than being ignored by the former Reader; this is **a fail-closed input-acceptance change**, not proof of exact equivalence on malformed journals. New O7 authentic cases verify final index equality to a SHA-committed checkpoint, multi-generation collision/delete semantics, signed invalid-operation rejection, file-descriptor cleanup on failed construction, and recovery from a truncated unsigned tail.

[O7 first hosted result](https://github.com/FCMO-AI/.CMPCT/actions/runs/40101351497) measured the exact historical Reader source versus this candidate on identical authenticated archives/runner: 4096 signed renames opened in 240.870418 ms (historical) versus 10.1396565 ms (candidate), **23.76x** faster for this focused constructor workload. Complete physical archive bytes/final index agree. Linux/macOS both reported 18/18 focused tests. Initial Windows jobs stopped on a test-oracle source text/EOL discrepancy **before** product tests; no Windows positive claim follows from them. The refined source custody now pins the reviewed Reader Git blob on every host rather than relying only on Windows text slicing; its final CI remains a gate. Research specifics and negative evidence: `docs/v031-research/2026-10-24-reader-shared-replay-o7-result.md`.

Open obligations: separately verify malformed signed-generation recovery policy, cold one-shot validator import, Reader in-call peak RSS, cross-platform exact-head composition with symlink-prewrite PR #356, and actual official release-parity execution. The improvement is not an extraction atomicity claim, filesystem TOCTOU defense, new on-disk format, merged release or full-product economic domination.
