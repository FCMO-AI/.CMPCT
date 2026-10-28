# J24K06 — preregistered signed mode2 prefix-stream verification

Date: 2026-10-28 UTC. Status: PROSPECTIVE, before implementation. Owner: Phased1 independent candidate branch off J24C07 PR #638 `f33fa91995043bf731e5a4a786fdec0b2dcfd4eb`.

## Question and real inherited failure

On the guarded Reader of PR #638, a reauthenticated S_VZIP mode2 archive with a genuinely regenerated 14-byte raw-Deflate stream but a declared 15-byte stream is accepted by metadata-only preflight, correctly rejected by full read, yet `read_range(130, 1)` returns a full-length wrong byte. Three-host failing case: #640 and hosted #40626003178. The inherited `tests/test_j24c07c_signed_mode2_regeneration.py` must remain unchanged and turn green without XFAIL.

## Mechanism, alternative and hypothesis

`range_vzip` trusts earlier mode2 `csize` as a coordinate without regenerating skipped streams. A bounded prefix proof can be made at the selective-read boundary: for every mode2 stream starting before the requested range end, regenerate it once and compare its actual compressed length to the signed `csize`; only materialize a stream into the result when its bytes overlap. Keep early-prefix literal reads lazy, and preserve existing mode0/mode1/STORED behavior. Reject mismatches with the inherited selective-length error rather than returning incorrect coordinates. Simpler full `rebuild_vzip` on every range is a correctness control but loses selective access, whole-file memory and CPU bounds. Alternative is a creator-side authenticated precomputed stream-length proof, a format/index change and out of scope for this exact r24 repair.

## Acceptance and kill conditions (frozen before code)

1. The exact inherited signed 130-to-131-byte mode2 falsifier fails closed on `read_range(130,1)` on Linux/macOS/Windows; positive frozen mode2 archive and complete SHA/ZIP/verify controls still succeed. Keep the frozen original and original failing test bytes untouched.
2. Add direct representation-level multistream adversarials: signed csize +1 and -1 in a skipped earlier regenerated stream must reject suffix reads; a requested range overlapping a lying mode2 stream must also reject, even if the slice alone would have correct length; honest streams produce exact bytes for arbitrary prefix/middle/suffix offsets. `get_stream` must not be called for early-prefix ranges finishing before mode2.
3. Keep mode0/mode1/STORED selected-range and preflight tests intact; do not alter `reader.py`, `validation.py`, frozen vectors, official gates or format revision.
4. Measure the added work honestly. Expected worst-case suffix mode2 range must regenerate all prior mode2 streams; this is decoder-work amplification (not full archive logical materialization). Track calls/bytes on direct oracle; do not claim product performance from a unit test. A full-product release benchmark remains pending.
5. Unchanged evaluator failures or all-host CI failures block product promotion; no waiver. The candidate may be retained as a research/fix PR even when general suite/version-fingerprint checks are red.

## Falsifiable controls and bounded scope

Compare exact candidate behavior to independently concatenated literal/stream slices; include two distinct mode2 streams with authentic zlib raw-Deflate regeneration, plus a crafted signed length lie. Run the installed CMPCT wheel on three hosts through a dedicated scientific court with exact source/receipt identity, and run the unmodified J24C07 inherited positive/negative tests. Check full `read` already rejects the lie (strong control) and demonstrate early-prefix laziness (cost control). This fixes byte-position trust, NOT authenticity of arbitrary equal-length malicious Deflate streams in partial reads, physical file races, general Reader recovery, or the inherited cold-open deficit. Compare latest #638 and adjacent PRs immediately before late writes; no direct writes to #638/#624/#630/#569/#637/#641 or shared Discovery STATE.

Decision predicate: `PROMOTABLE RESEARCH FIX` only on unchanged hostile regression PASS and independent exact-oracle agreement. `NO MERGE/RELEASE` until inherited general/release/portability/performance law passes.
