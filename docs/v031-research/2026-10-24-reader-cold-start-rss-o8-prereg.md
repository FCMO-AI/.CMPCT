# O8 preregistration — genuine cold Reader startup and process RSS

**Date:** 2026-10-24 (UTC). **Status:** prospective and unmeasured at registration.
**Owner:** isolated research-only child of [O7 PR #358](https://github.com/FCMO-AI/.CMPCT/pull/358), exact source `2c5334392c57f9c0f685c3751712acf0e242efae`. Do not change O7's Reader/validator sources, test assertions, format revision 24, release gates or owner branches.

## Existing evidence / question
O7 exact-source warm-process ABBA demonstrated 33.42x less Reader construction wall time on 4096 authenticated delta renames vs original source (run 40101895509), preserving 54/54 focused three-OS tests. It explicitly **excluded imports and process launch** and did not measure operating-system RSS. The shared `cmpct.validation._apply_delta` helper is imported lazily on journal replay. Does the real optimization remain net positive on fresh Python interpreters, and does cold startup / resident memory export unacceptable cost on ordinary checkpoint opens?

## Competing actions / BONK
Another local replay algorithm is sunk-family refinement without demonstrated need. A further source-only 54-test rerun does not decide memory economics. Hostile extraction/signed symlinks already have separately claimed owners (#356/#361). Source-identical paired cold workers, with the actual immutable O7 source and original Git Reader, are the cheapest differentiating experiment. This is adjacent independent research and **does not claim the O7 implementation**.

## Predictions, falsifiers and stronger control
- **Control:** historical Reader source from commit `5f6c1462e30686687ea13cc2507c9702f13df116`, blob `604f6a81bf03bd97a4defb4ad7a1393d01ed491f`; same installed current cmpct dependencies; inspect both module provenance identities. Candidate Reader source must retain Git blob `6de2edcf5b804e224a1c651ca77361af5667dc2e`.
- Generate **one authentic signed r24 pair** per 512 and 4096 renames with O0's existing `make_case` and real Builder: journal and checkpoint represent the same exact final logical index and payload. Independently authenticate those inputs before comparison.
- **Prediction:** on Ubuntu, candidate median *fresh-interpreter import + Reader constructor* wall time for journal improves by at least 1.5x over historical source. Not credited if candidate checkpoint median slows by **both** >5% and >3 ms on the same workload. Compare separately: constructor-only, module import, parent-observed full child wall including interpreter launch, CPU, HWM RSS, post-open VmRSS.
- **Disproof / narrower decision:** no benefit after cold launch; importing shared validator causes a checkpoint cold-start regression; exact-index or payload mismatch; candidate >10 MiB AND >10% additional resident high-water on the 4096 journal relative to historical; high-water already saturated before open; large variability / host noise. Preserve raw observations and choose conservative `AMBIGUOUS` rather than calling memory free.
- Run ABBA/BAAB orders of separate complete subprocesses, min 5 repeats, both source versions and both archive types. No import/process startup cost may be silently subtracted from the cold metric. Report gross `total_process_wall` as distinct from measured in-process `import + open`.

## Scope and safety
Research/evidence enablement only: a new script, isolated workflow, receipt and interpretation. Same-source module (historical) is loaded under private qualified name `cmpct._reader_o8_historical` using `importlib.util`, with exact Git-blob custody. Source/test data are wholly synthetic. SHA-256 of complete archives and final logical indices must match across implementations. No Reader/Writer/codec/format/limiter mutations. No release credit, merged claim or cross-platform memory claim from Ubuntu-only resource measurements.

## Decision tree
If cold win survives and RSS is bounded in the measured regime, stop local replay refinement and promote **integration** as the next frontier; do not infer global Pareto domination. If not, identify whether Python imports, extra heap, or replay CPU is causal and preserve that bounded debt. Measure actual `/proc/self/status` and `ru_maxrss` before/after; if HWM plateau pre-exists, leave in-call maximum unresolved instead of zeroing it. The old O7 performance and full release gate remain independent.

**Concurrency:** PR #358 owns the shared replay implementation. This branch changes no product source, makes no lock or shared `STATE.json` edit, and should be composed downstream only after source/race reconciliation.
