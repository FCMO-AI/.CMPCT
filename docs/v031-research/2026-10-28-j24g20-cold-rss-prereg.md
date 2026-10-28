# J24G20 — cold Reader RSS-floor crossover court (prospective preregistration)

Date: 2026-10-28 UTC. **Research only. Frozen before the new instrument or its results.** Parent #691 at exact `e15553bf409f4bb3b339af2ec1af83062af2926a`; released main v0.30.0 / r24, Reader blob `e716233403dabd0966863c45635e18fa5ac6afb8`; inherited experimental Reader blob `f13c5492f5acfa1cfcfec97cdbe0da71e41e327b`. No product, gate, version, or format changes.

## Primary question and different mechanism

#691 measured large signed projection CPU wins (8.34x), but its Ubuntu worker returned *the identical 68,912 KiB process ru_maxrss for all three Reader arms and all eight cases, including the tiny checkpoint*. That is a plausible **process-wide historical peak floor** rather than a demonstrated absence of incremental allocation. A static inspection cannot distinguish a high import baseline, a shared downstream peak, or a real projection failure. Separately, the original #691 >=16 MiB 200k-case hosted-RSS hypothesis remains FAILED and must not be relabeled.

Test whether a **genuinely cold, stage-separated, payload-count sweep** isolates the component's RSS and reveals at which source-agnostic metadata size authentic Reader materialization starts exceeding common startup RSS. This is a resource-instrumentation and ownership falsifier, not a new parser or a threshold adjustment to rescue #691.

## Strongest controls and explicit alternatives

- Actual historical published Reader vs inherited #691 parent vs certified candidate, same bytes for all arms; if historical loader requires source Git, compile it before measured sections as in #691.
- A no-archive/import-only control for every arm, plus existing checkpoint, 200,000-object linked delta, and **new 400,000 and 800,000-object linked valid deltas** (each <16 MiB signed payload); each case executes at least 3 fresh processes per arm. Fixed synthetic family only estimates scaling, not generic performance.
- Record before-open and after-open `/proc/self/status` VmRSS/VmHWM and `resource.ru_maxrss`; record after read/range/verify separately, ordinary end-to-end peak, process CPU/wall excluding import and physical-file generation; archive SHA/bytes/footer SHA; exact selected generation and reconstructed bytes.
- Extra cold component A/B control without CMPCT imports on the *identical extracted signed delta bytes*, to isolate certificate/skip effects from Reader/runtime. Do not compare across different physical inputs or process setup regimes.
- Consider and explicitly test the alternative that downstream verification or import dominates peak RSS; a component-only memory saving cannot earn Reader/product RSS credit.

## Frozen decisions

H1 (instrument validity): cold no-archive / checkpoint peak and pre-open peak must be recorded and explain whether the 200k-case 68,912 KiB was already hit before metadata parsing. If not, mark the cause unresolved; do not assert 'import floor'.

H2 (cross-over): for 800k authentic signed linked delta, the projected Reader must preserve the exact latest valid generation and reconstructed bytes and reduce fresh process peak VmHWM by >=16 MiB versus the same-input inherited and published Readers. If not, no full-Reader RSS credit at 800k. The original 200k H2 failure remains a historical negative whatever this new result.

H3 (semantic and ordinary economics): all arms pass latest-generation selection, read/read_range, verify, hash and malformed controls; for the original 10k ordinary MessagePack component control projected CPU overhead <=25%. Any mismatches retire transparent integration.

H4 (whole-system): record absolute and delta RSS and CPU/wall, archive/logical bytes, signed payload bytes, any temporary I/O, native C compilation/dependency and limitations of Linux measurement. Do not claim global bounded memory or native portability.

Any single same-archive semantic mismatch is a kill; any `/proc` unavailable or contaminated stage measurement is an inconclusive RSS verdict. A natural product promotion still requires inherited gates and multi-platform verification. The experimental workflow remains research evidence only.

## Concurrency and owner

J24G19 #691 owns certificate/projection; this branch is an isolated **independent falsification** and may reuse its source without changing it. #574 owns `docs/discovery/STATE.json`; do not modify that file. Inspect live owner refs before final writes, never force push. Detailed evidence/negative outcomes remain append-only, source-locked. No duplicate product implementation. No release credit.
