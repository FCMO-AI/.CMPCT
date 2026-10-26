# O193 — Bounded ZIP64 compatibility-member streaming (preregistration)

Date: 2026-10-26 UTC. Status: prospective BEFORE implementation and measurement.
Source authority: O191 PR #519 HEAD `9ce2b55d9b4ab8bcac2bb4618ac809557468c724`; O190 signed DOS-date conversion must remain exact. Released product v0.30.0 / format revision 24. This work is a stacked, separate *member ownership and memory* lane, NOT a revision of O191's calendar decision.

## Primary falsifiable question
Does replacing the ZIP64 compatibility branch's `ZipFile.writestr(ZipInfo, self.read(rel))` with `ZipFile.open(ZipInfo,"w")` plus *authenticated bounded-size* `read_range` chunks avoid complete logical-member allocation while preserving exact logical output, ZIP CRC, member order/names, local DOS calendar, Unix type/mode and genuine installed Reader semantics on small and representative chunked/sparse inputs?

Baseline: source-exact O191 fallback materializes complete file via `self.read`, which allocates a bytearray of declared size for `S_SPARSE` (among other modes). Thus it cannot credibly claim safe generic 4GiB extraction. O191 proved calendar-only synthetic fallback tests, NOT any genuine large member. O275 PR #275 proves only cheap ZIP64 *wire grammar* feasibility, not CMPCT streaming.

## BONK / alternatives / controls
- Safely decline ZIP64 fallback above a hard size ceiling: simplest safety control but sacrifices valid huge sparse archive export.
- Whole-file `self.read` into temporary file then ZipFile: moves RAM to temporary disk, doubles transfer work.
- Fully handwritten ZIP64 writer / raw Deflate reuse: may preserve compressed bytes but multiplies correctness/maintenance risk; defer unless python stdlib writer proves inadequate.
- **Selected:** stream independently bounded logical range reads into Python ZIP64 writer and incrementally verify logical SHA-256 before return; existing ordinary direct-Deflate path stays untouched.
- Keep O191 date/type mode semantics exactly. Do not alter compression policy, format, released source or existing evaluators.

## Exact prospective discrimination
1. Source-exact O191 fallback baseline must attempt `CMPCT.read` for a genuine >1MiB chunked or sparse input; test intercepts this *without shipping changes to the baseline*. Candidate must NEVER call `CMPCT.read` for the supported file types.
2. Authentic Builder-produced r24 inputs: medium/high-entropy multi-chunk regular file; physically sparse logical input if host reports legitimate hole accounting; ordinary small file; hardlink/symlink/directory when supported. Export by explicitly calling the exact same fallback helper used in the real `>=0xffffffff` dispatch, without inventing fake physical file sizes.
3. Independent stdlib ZIP must compare exact entries/bytes/CRC against source, Unix type/mode, O191 date. Ensure `ZIP_DEFLATED` and supplied compression level are effective, K_DIR remains empty.
4. Each source member is transmitted in reads no larger than 1MiB; incremental SHA-256 and expected byte count must match the authenticated CMPCT logical identity. Deliberately inject a single altered `read_range` chunk and require refusal (not a false success).
5. Record output ZIP bytes, source SHA, observed max logical read request, actual cumulative reads, peak RSS, CPU/wall and ZIP SHA from actual hosted evidence. Byte-for-byte ZIP identity versus old `writestr` is NOT required because legitimate streamed writers may use data descriptors/ZIP64 headers; decoded member equality IS mandatory.
6. Stream must not weaken existing security/fidelity law; known O143/O179 destination publication risk and ZIP name canonicalization #499 are separate owned lanes.

## Kill/narrow conditions
- Any corrupt or changed ZIP decoded payload/CRC, filename/date/type/mode or resource bound.
- Failure to verify authenticated per-file SHA before returning success.
- Compression level ignored or unexpected whole-member `read`/allocation on a supported streaming representation.
- Reader `read_range` can itself fully inflate an underlying huge compressed blob: report explicit *residual decode-unit limit*; do NOT call it universal bounded memory. If needed fail closed on unbounded physical frames instead of a false claim.
- Do not claim a real >=4GiB archive until a genuine source and complete resource-bounded run exists; tests under 4GiB are a rung-1 mechanism court only.

## Ownership and concurrency
O190 #518 owns signed DOS-date helper; O191 #519 owns fallback calendar. This new stacked branch isolates *streaming ownership of the same fallback* and must coordinate by PR, never silently overwrite #519. #275 owns cheap ZIP64 wire grammar and remains unchanged. #492/#512 own failure-atomic ZIP publication; #499 owns logical ZIP name handling. No writes to their branches, no change to `docs/discovery/STATE.json`, policy, format, frozen evaluators, version or release gate. Re-check parent/head and overlapping PRs before late writes. If source diverges, keep this PR draft and ask owner to reconcile through evidence, not a force-push.

## Promotion boundaries
A positive streaming mechanism with only sub-4GiB real archives cannot earn full ZIP64 product credit. True >4GiB end-to-end, RAM/CPU/temp I/O, independent ZIP parser/Info-ZIP, cross-platform conformance and same-input performance promotion remain open. Preserve a negative or scoped positive honestly.
