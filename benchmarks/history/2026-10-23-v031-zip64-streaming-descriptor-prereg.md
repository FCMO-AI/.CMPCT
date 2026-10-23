# v0.31 — ZIP64 streaming data-descriptor boundary (secondary preregistration)

**Date:** 2026-10-23. **Status:** UNEXECUTED at commit. **Owner boundary:** adjacent wire experiment in draft PR #275; PR #260 alone owns native product ZIP64 writer. No Reader or exporter edits permitted.

## New scientific question

Following exact-head O0 metadata success for pre-known sizes/offsets, can a ZIP64 writer emit a >4 GiB logical member whose **local header does not know final CRC/sizes at write start**, encode the final 64-bit CRC/size descriptor after a sparse logical payload, then write a small member using a normal 32-bit data descriptor at an offset >4 GiB? Does CPython `zipfile` + Info-ZIP retrieve the trailing raw Deflate stream exactly? This probes the prospective *streaming writer* architecture rather than repeating fixed metadata.

## Prediction before executing

P1: With GP bit 3 set on both members, giant local header ZIP64 size sentinels and 0/0 ZIP64 placeholder lengths, a signed 64-bit data descriptor (`0x08074b50 + CRC32 + csize64 + usize64`), late small member using 32-bit descriptor, and truthful central headers/ZIP64 extras, independent readers will retrieve the small file correctly.

P2: The central directory remains authoritative for name/offset/CRC. Corrupting **only** the trailing small member's data descriptor CRC may or may not be rejected by mature readers; if accepted, report **negative evidence** that reader acceptance does not independently validate that descriptor's CRC. Do not force a disproof requiring a parser to check data it does not promise to check.

## Controls / resource budgets / kill conditions

- Strong control: the *known-size* ZIP64 offset oracle already passed on exact GitHub head `8c3cade599ee71d4632fd4f82e9895c1c8930680`, workflow `39998087137`.
- Cheap discriminator: standalone sparse ZIP writer, no CMPCT engine; two ZIP readers parse late member. Inspect on-wire local GP flags, ZIP64 placeholder extra and DD records independently with struct; do not rely only on readers.
- Bound physical file allocation to 32 MiB and Python buffers to small slabs. Honest CRC of giant conceptual zero data is computed boundedly. Record logical bytes, physical blocks, runtime and exact code source.
- Fail/narrow on divergent late payload, broken central offset/count, malformed claimed data-descriptor structure or external reader rejection. An unexpected **acceptance** of a tampered DD must be preserved, not rewritten into a false failure.
- Even a positive result is **only O0 streaming ZIP wire feasibility**, not O4 CMPCT product acceptance, not actual streaming input or portable constant memory. Native copying/recompression, checkpoint/recovery, index ownership, release conditions and performance remain unproven.

## Decision

If P1 passes, pursue a separately measured native streaming ZIP64 product candidate when PR #260's owner is ready, preserving compressed-stream copy, fallback and strict release constraints. P2 diagnoses where checksum authority actually resides. No format/version/policy promotion from this study.
