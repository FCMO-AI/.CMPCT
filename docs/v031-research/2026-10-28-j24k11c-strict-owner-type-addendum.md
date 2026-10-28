# J24K11c — Hostile reference-type transfer after J24K11b PASS

Date: 2026-10-28 UTC. Status: **NEW ADVERSARIAL COUNTEREXAMPLE, PREREGISTER REPAIR BEFORE PATCH**.

## New observation (do not retroactively disguise as original prereg)
After the otherwise green J24K11b bridge court, a separately constructed local negative revealed an omitted strong Reader index-type guard: `CMPCT._vzip_physical_stream_size` checks `type(idx) is int` for signed `rawref` or `streamref`, but the modeled `project()` first performs Python list indexing with the untyped index. A signed `rawref=True` is interpreted by `blobs[True]` as `blobs[1]` and the resulting projected 7-field tuple is an *ordinary valid integer-only* tuple; the C batch scanner accepts it. The actual Reader would reject the bool index before physical checking. This falsifies general semantic inheritance for the current J24K11b adapter despite valid-data speedups and 54 earlier signed-size/BHDR negative cells.

**Local reproducer before source fix (2026-10-28 UTC):** `idx=True`, `type(idx) is int == False`, Python `blobs[True]` resolves element 1, `native.scan(...)` returns True. This is an adapter *research flaw*, not a demonstrated exploit in the published Reader; the scanner is not installed there.

## Frozen new question before the repair
Can a **strictly typed** per-query projection reject malformed indices (bool, int subclass, negative and beyond upper bound), reject unsupported method/mode, while retaining J24K11b's preregistered >=1.5x wall+CPU advantage at 4096 across all six modeled cells, with source-exact original audit and no evaluator weakening?

Require a new distinct strict-reference adversarial test on raw `payloads` before projection. Never count native FFI input acceptance as proof when the adapter may have transformed a malformed reference. Test all index positions for STORED and DEFLATED modes, including bool, subclass, out-of-bounds, and invalid method/stream_mode. For a hostile case, **both strong direct Python and projected native must reject**. Record exact mismatch before repair and positive/negative after repair. Preserve all original 54 cases, 648 samples, and eight receipt-fraud checks, and repeat the valid-data 4096 court with new guards charged.

If the typed adapter fails or eliminates the 1.5x benefit, classify this branch as **NO SECURE PRODUCT ROUTE** even if old valid-data numbers were fast. No product edit or changes to original evaluators; add a distinct test/receipt and source SHA on the exact branch. Signed index and format semantics override any speedup.
