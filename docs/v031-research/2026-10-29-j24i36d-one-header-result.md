# J24I36d — CRC/SHA same-header custody result (2026-10-29)

**Status: component-level research + implementation; no full-product performance win, no promotion.**
Source: draft [PR #765](https://github.com/FCMO-AI/.CMPCT/pull/765), stacked on owner #759. Original **CRC-enabled** control `09ee165f3c74de7df65372a63a93b82115e3f695`, preregistration committed at `14ad2aed8caf65da72be54030577dbc5775bfbdb` *before* candidate source edits. Candidate implemented in `native/cmpct-core/src/{lib.rs,vzip_dispatch.rs}`, source first landed `847e21336c8707d05da7836a946df946ba6c5633`, CI instrumentation at `05cd51ac047099be22f17400cea8cbb0677a6f34`, later CI-style corrections `333d7556462909eaf6b3fc5e1539daa7caf93e3b` and `512fa23d404d1c71bcfbacb8cccb9dcd5bf59920`. The source comparisons and measurement both ran at `05cd51ac` (before those last formatting/workflow-only commits); do not attribute the measurements to a later exact HEAD without source reconciliation.

## Mechanism and retained exactness contract

The former CRC-enabled implementation called `complete_member_identity` (reading a validated 64-byte CMA4 header) and subsequently `checked_blob_layout` again, then sought/read the four CRC bytes at header offset 28. The candidate returns `(physical SHA256, CRC32)` from the **same validated header**, using a wrapper to retain the normal two-tuple helper. The verifier checks a present logical row SHA against the physical header SHA and then streams the same logical bytes into independent SHA256 and CRC32 states. It still fails for logical/physical SHA mismatch or CRC mismatch and excludes composite physical CRC from unsupported ownership cases. No code path relaxes or removes SHA, CRC, index or member validation.

This removes one redundant **header-level** read per direct verified member, *not* a second data traversal. Each compressed `read_range` still has its own physical header/data access, so this is a limited optimization rather than an end-to-end custody redesign. It does not authenticate an archive against concurrent edits and does not address zero-logical-length nonempty encoded Zstd frames (#763/#767 independently owned).

## Source-exact hosted A/B evidence

Two different runs of the **same** GitHub Actions job and archive, original run plus deliberate independent rerun, installed actual CMPCT/Python and compiled separate exact-source Rust binaries on Ubuntu 24.04:
- [Workflow run #40904686282](https://github.com/FCMO-AI/.CMPCT/actions/runs/40904686282), first job 123556112733, rerun job 123557482661.
- 64 independent 256-KiB source files = 16,777,216 logical bytes; one installed archive 16,783,044 physical bytes, SHA256 `b281d19c0f4db39e4903fcbea0db3951f64ee25a5c885d30c21e48d051064ab8`.
- Same archive and same method: independent A and B programs, each `Archive::verify_complete` seven times/call, first as warmup; run order `ABBABAAB`; 24 observed latency values/arm/run. Both programs must verify 64 payload members on every iteration.
- Frozen control A `09ee165f3c74de7df65372a63a93b82115e3f695`; candidate B source `05cd51ac047099be22f17400cea8cbb0677a6f34`. Program compilation, process startup and archive-open excluded from in-process timed span. Raw log and JSON receipts retained as GitHub Actions artifact `j24i36d-header-cost-40904686282`, artifact ID **12909704249** for first run; rerun also has separate raw log/receipt.

| Observation | A: prior CRC candidate | B: one-header candidate | Relative B/A | A/A late/early |
|---|---:|---:|---:|---:|
| Hosted attempt 1 | 9.061726 ms | 8.952321 ms | 0.987927 (−1.207%) | 1.006159 (+0.616%) |
| Hosted attempt 2 | 9.595207 ms | 9.5231965 ms | 0.992495 (−0.750%) | 0.992988 (−0.701%) |

First adjacent ABBA pair ratios: 0.995821, 0.963225, 0.990144, 0.987700; rerun: 0.993194, 0.985303, 0.993550, 0.998498. All eight favor B but A/A drift is of comparable magnitude; **do not claim a durable or meaningful product speed improvement**. Source code removes redundant header read and tightens one-read fact ownership, which is independently inspectable, but measured end-to-end CRC tax remains unresolved. The earlier valid original #759→CRC #765 component penalties (+2.31% and +5.89%) are not erased or reinterpreted by this *within-CRC* comparison.

**Measurement classification:** direct hosted native in-process component evidence, not full-product benchmark. No CPU-time, peak RSS, I/O, archive-size, create/extract cost, selective bytes, recovery, Windows/macOS cost, or final publication improvement measured in this A/B. No speculative multiplication by archive size.

## Independent safety / portability controls and adverse limitations

Inherited #765 unchanged original/mutant direct RAW, Zstd, Deflate, WAV/FLAC and Zstd-dictionary cases plus genuine symlink and physical payload SHA control remain mandatory. [Three-host CRC court #40904686154](https://github.com/FCMO-AI/.CMPCT/actions/runs/40904686154) completed all Ubuntu, Windows and macOS scientific test jobs **successfully on `05cd51ac`**. Treat later HEAD CI outcomes independently; native formatter and CI topology classifier originally failed at that HEAD and were repaired without changing a fixture or evaluator. Native component and topology full checks on final source must turn green before considering integration.

Strongest negative: a 0.75–1.21% micro decrease does not close the CRC-vs-uncorrected parent overhead in a release-complete system. Compressed direct decoding may hash and reconstruct repeated chunks; the one-header change cannot fix such broader execution architecture. No publication claim or edit to frozen benchmarks, thresholds, `docs/discovery/STATE.json`, release or on-disk format.

## Decision and next cheapest discriminator

**Disposition: narrower implementation seam advanced, substantial performance gain ambiguous.** Retain as draft pending source-exact current native CI, five-codec, genuine symlink and hostile-corpus tests, and parent-owner review. If passed, one-header custody is preferable to the previous duplicate read on simple ownership grounds; if new conformance/code complexity regressions appear, revert. Next meaningful investigation should trace complete native verify CPU/I/O by codec, especially repeated compressed decodes, before any further local CRC threshold-gardening. Preserve the old slower fused-CRC observations and any unresolved historical source-bound checks.

No change to Discovery Engine policy: one local duplicated-header mechanism plus noisy small component gain does not meet the standard for a transferable discovery-policy lesson.
