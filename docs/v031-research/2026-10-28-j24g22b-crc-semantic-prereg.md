# J24G22b — independent CRC-only semantic court (preregistered BEFORE instrument code)

Date 2026-10-28 UTC. Preserve original J24G22 prereg and hosted evidence at original exact Reader source `e716233403dabd0966863c45635e18fa5ac6afb8`; do not retroactively reinterpret/overwrite prior test. Parent research branch includes the *first* physical stdout court and its result. New question arose from its documented limitation.

## Primary disproof
Can a SHA-verified temporary spool of `CMPCT.read_range` be a **transparent semantic substitute** for current `CMPCT.read()` when an original RAW member has authentic payload bytes, its unchanged SHA field, an unchanged signed primary index, but a deliberately invalid **physical BHDR CRC32 field**?

## Predictions (before code)
- H0 stronger inherited `CMPCT.read()` fails with `blob integrity failure` before emitting output, since `_blob` checks CRC32.
- H1 simple `read_range` on RAW can still return bytes because that fast path bypasses `_blob` CRC and uses direct mmap slice.
- H2 prototype J24G22 SHA-only spool will accept/release the unchanged RAW payload because `file_sha256()` returns the intact BHDR SHA and digest matches, despite H0 rejection.
- If H2 occurs, spool is **FALSIFIED as transparent substitute**, even if it protected previous late-payload-corrupt case. Do not solve by weakening comparator or relabeling as safe.
- If H2 does not occur, record the counterexample and diagnose without changing original frozen J24G22 evidence.

## Exact experimental controls
Start from first-party `Builder`-generated revision-24 physical archive with an actual direct `S_BLOB/CODEC_RAW` member. Change exactly one low bit of the CRC32 field within the selected BHDR, at source-derived offset; mutate no payload byte, member SHA, index SHA, footer or file layout. Preserve pristine positive control. Use the unchanged frozen published Reader to compare `read()`, `verify()`, `read_range()` and the explicit research-only `file_sha256+temporary spool`. Capture emitted byte count only in a private digest sink, never user stdout. Independent referee validates frame offset/CRC and two-file physical hashes. No product changes.

## Limits and ownership
This tests only one BHDR CRC-only malformed class, not authentication of adversarial whole archives, external signatures, arbitrary codecs, mutable inodes or product-level performance. Scientific success is **finding an incompatibility**, not shipping a faster CLI. Keep existing source gate/release law and adjacent Reader owners untouched. Update result as a new additive episode, not by rewriting frozen prediction.
