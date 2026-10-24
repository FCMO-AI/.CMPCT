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

### macOS APFS/HFS+ destination aliasing — v0.31 draft candidate, not shipping

The revision-24 **logical index** is byte-distinct for `café` (NFC) and
`cafe\u0301` (NFD). Apple's APFS comparison is normalization-insensitive even when
case-sensitive; common default APFS also treats many case variants as the same directory
entry. A portable lexical path key therefore cannot itself guarantee a one-to-one
**physical** extraction tree on macOS. This is a destination policy, not a reason to
normalize or rewrite archived POSIX paths. Primary host semantics:
https://developer.apple.com/library/archive/documentation/FileManagement/Conceptual/APFS_Guide/FAQ/FAQ.html

Exact unmodified development-source macOS-26.6.2 ARM64 evidence: PR #334, run
`40072645196`, HEAD `3487ad223a3c26f22464863a4a1f15d5b3fe7f22`. Actual
NFC/NFD `samefile` alias was observed; three product `extractall` courts failed
because the reference extractor accepted two physical aliases instead of refusing
the tree. Ubuntu controls passed. The preregistration and test source predate the
product modification and remain unchanged.

Candidate `src/cmpct/path_policy.py::macos_comparison_component` uses
NFD→casefold→NFD and strict UTF-8 encode. `CMPCT.extractall` applies a parent-node-ID
prefix ownership map before any member writes on `sys.platform == 'darwin'`, rejecting
conflicting original component spellings at the same normalized prefix. The first
candidate run `40072814609` passed **8/8 run Mac tests** (plus one skipped) and
**3/3 Ubuntu tests** (six skipped); the exact candidate source is
`edf81a6da61b5d4cdd3291944922e374f1c1fc66`. Linux remains byte-distinct.

A second prospective Mac-specific discriminator exposed a **distinct link-owner hole**:
even after the O1 guard, a hardlink could name `cafe\\u0301` as its source
although only the NFC `café` owner existed in the logical archive.
APFS resolved the physically equivalent missing source and extraction succeeded.
O2 preregistration commit `cf4665193f28626b76c2139bf6112bd28f5760c3`
preceded unchanged test commit `b1f1d7dfb0c8bb9dc6554d018cfba569fc6a4cae`;
hosted run `40073080938` recorded **one genuine macOS product assertion
failure** (`DID NOT RAISE OSError`, 9 other passed), with Linux controls green.
The standalone structural preflight already requires a hardlink's exact
logical owner to exist. O2 therefore mirrors that existing rule during
ordinary Mac extraction, before touching any file. Candidate source
`138368dd0eabd160d7c65aa993fd9b26e31c9821` passed source-exact
unchanged O0/O1/O2 courts in hosted run `40073261470`: **10 Mac passed /
1 skipped**, **3 Ubuntu passed / 8 skipped**. The valid exact-owner hardlink
control reconstructs shared inode and content correctly.

Explicit limitations: Python's current Unicode tables are not the complete native
Apple Unicode-9.0 comparison algorithm; case-sensitive APFS may legitimately accept
some case-distinct names rejected by this conservative policy; destination symlinks,
reparse points, concurrent filesystem mutations, mountpoints and preexisting aliases
are not solved. The current court runs the **real Reader extraction method** on
directory-only preconstructed rows and does not prove an authenticated full Builder/
Reader roundtrip or platform-wide release fitness. Host CPU/RSS and official ABBA
economics remain pending. Until reconciled with the Reader owners and promotion
gates, this is an unmerged safety candidate only.

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

### Cross-owner Win32/APFS union O0/O1/O2 — v0.31 draft, not shipping

Independent host-specific extraction protections in PR #332 (Win32) and #334
(APFS) change the same Reader/path-policy files. Draft integration PR #336,
based on #334 exact `be60184c76bd89da7d2f31614717e174393907fc`,
imports the unchanged original #332 Win32 helper, Reader guard, tests and
workflow. Joint source retains APFS Unicode normalization/casefold, implicit
prefix collision and exact logical hardlink owner checking; r24 archive
path spelling remains unchanged and POSIX byte-distinct names remain legal.

A first genuine three-host union court at `e239972f880f6906ec016e814fba2bc1c9add5e0`
was **green Windows/Ubuntu but red macOS**: the original Windows
non-Windows-positive fixture expected `Case` and `case` to coexist on every
POSIX filesystem, contradicting the intentional APFS conservative alias refusal.
O0 evidence: [Actions 40076842895](https://github.com/FCMO-AI/.CMPCT/actions/runs/40076842895).
O1 prospectively limited that *unchanged* Windows positive assertion to its
original Linux/Windows host domains; every other original Windows test, the
entire original APFS suite, and the joint policy tests remain on the three-host
matrix. O1 [Actions 40077116609](https://github.com/FCMO-AI/.CMPCT/actions/runs/40077116609)
passed on **all three real hosts**; platform skips and the one explicitly
excluded incompatible Mac assertion are preserved, not silently counted
as passes.

A prospective O2 revealed a distinct real Windows logical-identity defect:
`Alpha` as a regular archive member and a hardlink `alias` naming `alpha`
could be accepted due to Win32 case-insensitive filesystem lookup even when
`alpha` was **not** an authenticated logical member. Original source/test
at `2204f71c117550d8dcc148e5df982837c076cdc8`, Windows hosted [Actions
40077537326](https://github.com/FCMO-AI/.CMPCT/actions/runs/40077537326):
**1 FAIL / 14 PASS / 8 SKIPPED**, `DID NOT RAISE OSError` after an
independent `samefile` proof of physical aliasing. Linux and macOS controls
remained green. The first repair, `0d689154f6823001ad3ee31cff575b273e8499d0`,
requires hardlink sources to belong to the full exact logical member set on
Windows before any extraction write, mirroring the existing Mac requirement
without weakening Windows path/device admission. The original O2 test is
unchanged. The repair has **no positive hosted result at this record's first
write**; inspect exact-head CI before granting product evidence.

These guards do **not** prove native filesystem collation equivalence,
pre-existing symlink/reparse-point safety, concurrent-root confinement, full
transactional rollback, or Win32 deep-tree preflight performance. The original
Windows prefix checker repeatedly joins entire prefixes, with quadratic-in-depth
byte work; bounded node-ID ownership is a promising *mechanism-level* future
control, not yet a tested product improvement. Nothing in this draft grants
merge/release authority.


### Signed non-directory ancestor extraction — v0.31 draft PR #338

A revision-24 archive can carry two **SHA-256-consistent indexes** that
individually describe readable regular files `parent.bin` and
`parent.bin/child.bin`, although those two logical members cannot both be
materialized on a filesystem. Neither the original canonical path duplicate
guard nor platform-specific Win32/APFS alias checks rejected this
**kind-of-ancestor** inconsistency. A real Builder-created r24 archive with
only its indexed child path mutated and both index commitments regenerated
preserves every physical blob byte and lets `CMPCT.read` return both exact
contents. This proves signed byte integrity is not tree-topology proof.

Immutable O0 preregistration: commit `6698eab2e3705d962f67b47d2695c7cf61c3defd`;
test-only baseline `02efed57cdf074ef3f888d1efb403ff12f22cd57`.
[GitHub Actions baseline 40078750750](https://github.com/FCMO-AI/.CMPCT/actions/runs/40078750750)
has **two genuine negative assertions (partial `out/parent.bin` publication)
and two positive controls on each of Ubuntu, macOS and Windows**. Failing
assertions and immutable original tests are preserved.

Draft fix `e929f3ec65fe88fc8d20b0e26b4b28e13e64b88d` inserts a bounded
component-trie check in the existing `extractall` prewrite pass. A proper
ancestor whose index entry has kind `K_FILE` or `K_HARDLINK` now fails
before materializing archive members. **The original unchanged same-input
court passed 4/4 per host on genuine Ubuntu, macOS and Windows** in
[exact-head Actions 40078888706](https://github.com/FCMO-AI/.CMPCT/actions/runs/40078888706).
At that exact implementation HEAD, original Win32, APFS, tri-platform union,
Native Core and Continuous Fuzzing workflows also report SUCCESS; general
and full parity release evidence are separate and must be checked independently.

The distinction matters: `CMPCT.read` may legitimately read individually
correct members from an archive whose *aggregate* namespace cannot be
extracted. This check is extraction policy, not an on-disk revision change.
A separate question remains whether strict `preflight_archive` must refuse
the same tree. Costs: trie additional work/space scale with total path
components; no valid complete-product ABBA/RSS result is claimed. The
extractor can still create the requested destination root before this
check, and unrelated failure paths can still partially extract. Existing
destination symlinks, concurrent inode/path rebinding, network filesystems,
source snapshot races, mount pivots, and platform-specific collation are
**not** solved by this lexical preflight. PR #338 remains draft, not
merged or released; do not weaken the inherited release/parity court.


### Strict signed-tree preflight parity — v0.31 draft PR #339 (stacked on #338)

The extraction-side correction in PR #338 refuses SHA-authenticated revision-24
trees where a regular file or hardlink acts as another member's proper path
ancestor, before publishing any archive members. The separate **strict
structural validator** `preflight_archive()` previously checked each file row,
canonical path aliases and hardlink cycles but did not reject the same
unmaterializable tree. Ordinary Reader member reads remain independently valid
on these files and must not be conflated with whole-tree extraction safety.

Independent O0 prediction was frozen **before test or product source** in
`docs/v031-research/2026-10-24-signed-tree-preflight-o0-prereg.md`
(commit `f275dd1c5d54`). Signed inputs are created with the real r24 Builder:
only logical index rows are mutated, both index commitments and footer are
regenerated, and the physical blob bytes are unchanged.
[Source-exact negative run 40080840083](https://github.com/FCMO-AI/.CMPCT/actions/runs/40080840083)
at test-only `f86063920b4f19dfacba447a95e11788a7a26335`
proved **5/5 preflight assertions failed (`DID NOT RAISE ValidationError`)**
and **2/2 valid controls passed** independently on Ubuntu and macOS.
The same files were individually readable, and #338's extractor rejected them
without publishing file members. A Windows result must be checked separately.

Candidate `src/cmpct/validation.py` change first landed in
`5d86a2b524e35494accf21067753b0a08ff0a2db`: a single-pass,
order-independent component trie rejects a regular/hardlink node with any
descendants (regardless of insertion order) within the current ParserLimits.
The fix does not invoke extraction, read payloads, alter r24 bytes, rewrite
Reader source, or change symlink policy. The **same unchanged signed hostile
and valid controls** must pass on the candidate's exact HEAD before this is
counted as product evidence; CI was pending when this note was written.

Resource accounting: trie work/space are O(total canonical path components)
in the bounded decoded index. An **isolated Python model**, not CMPCT product
measurement, observed ~9.1ms/0.35 MB for 1k, 83.7ms/3.08 MB for 10k,
and 1,088.7ms/31.68 MB for 100k three-component rows with tracemalloc.
These measurements are not complete-product wall, peak RSS, or release parity
evidence. Public release, full compatibility/performance and strict destination
containment remain independent gates. In particular, nested symlink admission,
hardlink target type and order, existing filesystem objects and concurrent
rebindings are separate questions; accepting a tree's **logical** topology
never proves its **physical** extraction environment is safe.


#### O1 held-out signed hardlink target-kind boundary (same #339 lane)

Prospective O1 preregistration was committed in
`docs/v031-research/2026-10-24-hardlink-owner-type-preflight-o1-prereg.md`
at `884535f6cd310b66357d4d50bb9acb0f335a70b8`
before appending any O1 test or source edit. The existing strict preflight
checked only exact hardlink owner existence and cycle-freedom: it did not
require the terminal owner to be a **regular file**. A reauthenticated r24
archive can therefore add `z_dir_alias` as `K_HARDLINK` targeting a real
`K_DIR` named `folder` and still pass strict preflight, although authentic
Reader extraction cannot create this directory-hardlink relationship.
The Builder's complete original blob bytes, real directory and regular-file
controls, and both newly authenticated index commitments were preserved.

Test-only exact source `14fbeb7d8df8d869129c1d49565ca16977830a5b`
reproduced **1 failed O1 strict preflight assertion: `DID NOT RAISE
ValidationError`; 7/7 inherited O0 tests passed** on genuine macOS and
Windows in [negative run 40081342588](https://github.com/FCMO-AI/.CMPCT/actions/runs/40081342588);
Ubuntu result must be reconciled separately. The ordinary extraction
`OSError` check and all physical/semantic controls passed before the sole
strict validator assertion.

A type-bound fix in `src/cmpct/validation.py` first landed at
`6b02d287d3d4f1f7d7accbc268ca0a89aea52679`:
record each canonical member's kind during bounded index scanning; after
the unchanged hardlink chain/cycle check, reject any terminal owner not
`K_FILE`. This is not a directory hardlink feature nor a change to the
released format. Positive exact-head installed-product CI for the
**unchanged eight-test** court is separately required and was pending at
the moment of this record. The check adds O(member count) bookkeeping
for kinds and O(1) terminal-owner lookup to the existing cycle traversal.
It does not fix pre-existing extract-time races, namespacing aliases or
the existing potential O(number-of-hardlinks × chain-depth) repeated cycle
work; these remain separate potential product costs.

### Authenticated hardlink chains and strict-preflight CPU — v0.31 draft O0/O1 (not released)

A finite file-count limit does **not** by itself impose a proportional CPU-work
bound when graph edges are repeatedly traversed. The strict revision-24
`preflight_archive` in source-exact PR #339 (`3494a58e`, validator blob
`14df3f7492fc2db8b7dc7574868a333b4fe400c4`) re-walked every
hardlink-alias target chain to confirm its ultimate `K_FILE` owner. N valid
aliases arranged as a chain cause ~N(N+1)/2 owner-pointer inspections versus
N for independent star aliases.

Independent real Builder archives with both authenticated index copies and
unchanged physical content were measured in PR #342 [O0 run 40084916000]
(https://github.com/FCMO-AI/.CMPCT/actions/runs/40084916000),
exact source `c6a5592aa1027b6003278a4e85aa88389fcaa241`. Five-repeat
median strict preflight at 4096 aliases: **730.438 ms chain** vs **16.489 ms
star**, a **44.30× chain/star** ratio; at 2048 aliases: 185.027 vs 8.369 ms.
Raw timing, complete archived/index/physical bytes, corpus hashes and source
identity reside in
[artifact 12556257687](https://github.com/FCMO-AI/.CMPCT/actions/runs/40084916000/artifacts/12556257687).
These are research product-cost observations, **not** release benchmark credit.

A second authentic signed adversary, a hardlink chain ending at a nonexistent
terminal target, caused an uncaught `KeyError` rather than the documented
`ValidationError` in the unmodified preflight. Source-bound [negative O1
run 40085228916](https://github.com/FCMO-AI/.CMPCT/actions/runs/40085228916)
preserves this failure and nine passing new controls (plus inherited preflight
tests); no evaluator was weakened.

PR #342 proposes a bounded **iterative** terminal-owner memo, caching only
after checking each traversed edge, cycle and terminal regular-owner type.
The initial O1 product-head `966b995ac0553ecc33cfc2486492b5a7dfc5461b`
passed all **18** focused authentic signed-graph and inherited topology tests
in [run 40085358527](https://github.com/FCMO-AI/.CMPCT/actions/runs/40085358527).
Its contribution remains **draft**. Same-runner identical-archive baseline
vs candidate ABBA, peak Python allocations, final exact-head inherited CI
and broader portability/release comparisons must be examined independently
before any performance or promotion claim. The general Reader, native ABI,
frozen r24 format and public v0.30.0 release are unchanged.

A future hardening rule should distinguish **object-count budgets** from
**work-amplification budgets** for any archive-controlled ownership/reference
graph. Do not protect the CPU budget by silently rejecting legitimate deep
acyclic hardlink chains when an O(N) algorithm can validate them exactly.
