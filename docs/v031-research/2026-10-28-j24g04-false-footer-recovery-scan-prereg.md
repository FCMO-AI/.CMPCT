# J24G04 — Prospectively preregistered invalid-footer recovery amplification court

**Status:** PREREGISTERED BEFORE INSTRUMENT / RESULT / PRODUCT CHANGE. Scientific question only; published v0.30.0, revision 24, benchmarks and release gates frozen. Source base main `80c358f8824ec1b20d349c92ed94c898090969b0`, Reader blob `e716233403dabd0966863c45635e18fa5ac6afb8`. No CMPCT product code is to change in this experiment.

## Primary question

Does the released Reader's `_latest_generation()` independently re-decode the same valid-but-orphaned signed footer ancestors for each candidate during recovery from an appended invalid transaction tail, producing ~N(N+1)/2 footer decodes instead of O(N) across N mutually chained candidates? This is a **recovery cost / hostile-tail availability** question, distinct from authenticated journal *operation replay* debt in #344/#358 and generation resource ceilings #365.

## Source-based prediction and simpler control

The Reader scans for each `FMAGIC` occurrence backwards and calls `_index_from_footer()`; the latter follows valid signed delta footer links until a checkpoint or missing predecessor, without carrying a negative-candidate cache across calls. Append N valid `FTR`-framed SHA-256 authenticated no-op delta payloads to one valid Builder archive, each pointing to the immediately preceding delta footer, while the oldest points to 0 (no checkpoint). None is a committed valid recovery chain; the original signed primary index remains authentic and readable. Prediction: the instrumented genuine Reader `_decode_generation_payload` is called exactly `N(N+1)/2` times for N=32,128,256, except where an unrelated earlier footer collision appears (which must be reported as a falsifier, not optimized around without prereg amendment). Original members still reconstruct byte-exactly through fallback.

Controls: identical original Builder archive, no appended tail; a same-length *non-magic* tail where footer framing is replaced by zero bytes; a valid first-party append-update/footer to show legitimate recovery does not suffer identical terminal behavior. CPU and wall per source-bound cold open will be recorded but **no numerical speedup is preregistered** and timing is not a release gate.

Alternative explanations: input scanning/mmap dominates rather than repeated decoding; valid linked deltas are simply accepted and short-circuit; deduplication already exists; original Builder base creates an earlier footer which changes the number of calls. Record observed counts even if prediction fails.

## Evidence / resource contract

Use a real installed Python CMPCT package at source SHA; use real `Builder.build`, `CMPCT.read`, `CMPCT.verify` and actual `FTR`/MessagePack/SHA constructors. Instrument only the instance/class method call count; do not replace `_index_from_footer` or the decoder result. Hash and record the source, base archive, mutated archive and content. Test N=32,128,256; compute and record archive bytes, open wall/process CPU, call counts, read/verify correctness, and control semantics. Use one bounded no-magic control and a valid append control. Explicitly cap test work (max N=256). Run on GitHub-hosted Ubuntu initially; Windows/macOS only after source evidence warrants.

The test is rejected as invalid if it uses a synthetic Reader, changes source code or benchmark thresholds, lacks exact SHA-authenticated footer records, changes the original primary index, or fails to read the original content. Lower-rung evidence may establish a resource flaw but earns **zero product/release credit**. Do not change the Reader in this PR. A future fix must coordinate with indexed replay owner #358/#365 and preserve genuine tail-crash recovery, older footer selection, and authenticated signing.

## Prospective decision

- **CONFIRM:** exact or close triangular decoder call counts on genuine Reader, unchanged logical bytes, with a no-magic control showing bounded scanning.
- **FALSIFY:** calls remain O(N), tails are not accepted as authentic delta framing, or verified content changes/Reader rejects instead of recovering.
- **AMBIGUOUS:** test/import/infrastructure failure or different counter source; preserve logs and narrow.
- **Next action if confirmed:** test memoizing invalid suffix roots / deepest bad ancestor as a *separate* small oracle with strict recovery safety, not a blind Reader change.

## Anti-duplication / release boundary

#358 owns signed journal operation-replay economics and #365 owns generation depth/size; they do not claim independent invalid-candidate scan caching in the latest available PR dossiers. If current work proves otherwise before implementation, retire this lane. No force-push, no release, no metadata/fingerprint rewriting, no evidence thresholds weakened. Discovery STATE remains untouched because this is a preregistered single experiment, not canonical frontier promotion.
