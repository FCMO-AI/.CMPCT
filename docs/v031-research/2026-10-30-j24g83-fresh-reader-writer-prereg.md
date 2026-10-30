# J24G83 — prospectively frozen Writer Reader-lifetime control

Date: 2026-10-30 UTC. Status: **PREREGISTERED BEFORE INSTRUMENT/WORKFLOW**. Independent scientific comparison; no shipping product, release, format, benchmark, discovery-policy or version credit.

## Authority / collision check
This is a *different* question from #829 (J24G80 private session), #830 (J24G82 torn-prefix recovery), #823/#820 (single Reader open), #828/#832 (owned Reader physical and CI composition), and #295/#304/#409 (actual multi-Writer leases). Their code ownership and evidence remain untouched. Exact source base: #829 `d29c8b6b64017ab912cfd219d598501e00b62a72`. Current Writer blob `71bbc8a989d1da79d0f0dbe44f7f5c39f3304854`. Reuse the exact unmodified research OwnedCMPCT donor from #820's measured `c15459f70001800f3781925efc7356409eb03ffe`; import only in an isolated test-time redirect of `transactions.CMPCT`. Preserve full current shipped append_delete path and both original fsync boundaries. This is not merging Reader product code.

## Baseline, dominant cost and falsifiable question
#826 physically attributed 87.95–89.81% of repeated Writer work to Reader opening; #829's private, quiescent 63-op session achieved 29–32x overall with identical original physical generation bytes. But no same-host *whole Writer* control measures the materially simpler alternative: start a fresh, private, accelerated Reader on **each** original public Writer call, without keeping index/footer state across commits. Question: does that simpler, cross-commit-stateless route capture most of the attainable wall-time saving?

## Preregistered evidence
Build one deterministic 8,192-member/middle-delete and one 32,768-member/tail-delete archive per hosted Ubuntu run using #829's original Builder source helper; run the **same 64 DELETE names**, original Writer API, and checkpoint64. Compare three variants on copy-identical base files:
A = unchanged `tx.append_delete` with original CMPCT class;
B = unchanged `tx.append_delete` using only test-time `transactions.CMPCT=OwnedCMPCT` per operation, restored in finally;
C = exact unchanged #829 private-owned session oracle.
Order A/B/C then C/B/A, with independent full 64 physical commits for each trial. Time all 63 pre-checkpoint calls, plus each variant's own initial Reader time; record wall and process CPU per update. Compute direct medians, per-run wall, and recoverable-saving share `(A-B)/(A-C)`, only if `A>C` and all physical/correctness checks pass. Preserve raw observations and all negatives.

Each of 64 commit prefixes in every variant must match original physical SHA-256 **and byte count**. Final full files must compare byte-for-byte, including identical checkpoint64, index logical tree, preflight, SHA verify, authentic footer predecessor, and corrupted terminal footer rollback. Independently audit CMA4, all footers, each prefix and content without importing CMPCT using existing exact #829 external referee (no new parser/evaluator).

## Decision fork / kill conditions
- Prefer **simpler per-operation Reader** as productization route only if B is no more than 2x C on **both** sizes and captures >=75% of A-to-C saving on both (these are exploratory preference criteria, not release/benchmark thresholds).
- Strong **persistent session advantage** if B is >4x C on either family, with correct wire equality; this supports investigating bounded session ownership, never claiming concurrency safety.
- Between these: ambiguous/nondominated; choose next experiment by total safety/economics.
- Any byte, index, strong verify, preflight, signed-footer, checkpoint64 or recovery divergence falsifies route B's equivalence. Any `OwnedCMPCT` fallback/non-admission in a history expected to be admitted must be reported as a measured limitation, not hidden.
- If measurement noise makes the ordering non-decisive, do not invent a win. This is a science ladder and carries no product/release credit.

## Alternative explanations / exported costs
Opening a fresh optimized Reader still pays repeated remapping, footer decoding, per-append index deepcopy and hardlink-owner scan. The owned-session C avoids all but the last; B may capture little at 32,768. Test-time module aliasing has no multiprocess safety proof and is deliberately sequential. No new stored bytes should occur, but repeat-decode CPU, wall, per-call peak RSS, temp I/O, filesystem locks, recovery, process startup and portability are not interchangeable; RSS remains unmeasured unless instrumented separately. Kernel cache/noise confounding is mitigated by balanced A/B/C,C/B/A and physical equality, not eliminated.

## Integrity, release and scientific scope
Do not change `src/`, `native/`, external benchmarks, comparator, thresholds, parser, format, release law or immutable history. Source-attest donor SHA and the exact installed target Reader/Writer before measuring. Any imported donor code is scientific instrumentation, not another shipping implementation. The isolated candidate may be killed without deleting parent #829 evidence. After result, record raw host artifact/run SHA, counterfactual (could an earlier full Writer control have avoided session productization cost?), strongest negative, and transfer result to #824/#829/#820. Leave Discovery `STATE.json` to owner #574.
