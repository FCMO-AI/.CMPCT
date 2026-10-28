# J24G06 — Product candidate: bounded negative-ancestry reuse in genuine Reader

**PREREGISTRATION BEFORE PRODUCT SOURCE EDIT.** Exact parent J24G05 source `220f765de6c14da0487fe985ac490f0401038aca`, Reader original Git blob `e716233403dabd0966863c45635e18fa5ac6afb8`. Original released main/v0.30.0/r24, full original scientific negatives and existing benchmark limits immutable. Work is an isolated DRAFT candidate; #358/#365 Reader/journal/limit owners notified via issue #649 and PR comment; avoid merging without coordinated composition.

## Inherited decisive real-product source evidence

- Scientific J24G04b [#647](https://github.com/FCMO-AI/.CMPCT/pull/647) installed released Reader: N=256 valid-hash orphan parent chain adds 20,736B and causes 32,897 actual decoder invocations / 194.512 ms median whole open/read/verify; same-size nonmagic suffix one call / ~0.153ms. Correct content and original authentic footer chosen.
- Unchanged original Reader J24G05 [#648](https://github.com/FCMO-AI/.CMPCT/pull/648) independent source-bound ephemeral wrapper: 32/128/256 nested orphan calls 529/8257/32897 → 33/129/257; N=256 original 202.913ms → oracle 1.963ms median (103.38x). Equal-sized flat SHA-authentic `prev=0` tails already O(N) under both readers. Positive real Builder/Writer rename content unchanged.
- First flawed initial assumption about Builder checkpoint retained as negative historical CI; J24G04b corrected prior to result. No product credit granted yet.

## Hypothesis / minimal mutation

In `src/cmpct/reader.py`, create a transient failed-footer set **local to one** `_latest_generation` search. Extend only `_index_from_footer` with an optional set argument; reuse its EXACT existing SHA/footer/generation decoding and MessagePack replay. Whenever a candidate returns None after visiting >1 known-invalid ancestor positions, record the actual visited positions as invalid only when a bounded cache can store them; if a later candidate begins at a cached invalid address, return None without replaying. Cache only failure paths, not successful indexes/checkpoints. Caching is not a data-authentication shortcut: a candidate already failed in the same complete Reader-open scan. On overflow, skip caching and retain unchanged legacy cost/correctness. Never alter an index, result payload, Reader selection priority, archive bytes or format.

Set a conservative per-open maximum **16,384 positions**; actual Python set memory/peak RSS still needs independent measurement. Avoid adding a new module/interface, preserve original function signature for direct callers via optional argument. Skip memo creation for single-footer invalid candidate chains to keep flat-tail overhead low.

## Stronger control / disproof

Run unchanged original and candidate real Reader on identical original Builder/Writer archives and exact orphan chain N=32/128/256, same-size flat orphan SHA tail, equal-size no-magic tail, and first-party valid `append_rename`. Check read/range/verify byte-exact, selected index, delta depth and archived SHA, raw repeated CPU/wall, actual decoder calls. Require candidate 1+N calls on shared chain, original 1+N(N+1)/2, and at least 2× whole Reader wall improvement at N=256 on same environment; flat tails should not incur >1.25× median wall cost vs actual original (no evaluator change). Valid no-tail and Writer cases must remain bit-exact and no >3ms absolute cold overhead. Caching correctness on cyclical/corrupted parent and legitimate >1 signed generation remains required; if resource ceiling/selected footer or behavior differs, reject.

Explicitly preserve fail-closed per-generation resource gates from #365 on any later merge. One-run original public Reader may lack the later resource patch; its absence is historical, not permission to weaken modern limit semantics. Before merge reconcile with #358 source changes, #569 Reader and #365 policy.

## Memory and adversarial concurrency boundary

Even if 16,384 cached positions is finite, transient original per-candidate `seen` sets can be larger; do not claim bounded aggregate memory or deny all hostile archive CPU without a proper stress test. Concurrent same-inode archive mutations may invalidate cached negative facts; existing code also lacks an atomic immutable filesystem snapshot. **No concurrent mutation-safety claim** and no merge until either source snapshot/custody is established or the supported trusted-immutability boundary is explicitly documented. Do not falsely claim nonremote exploit details.

## Decision rules

A real code source patch plus focused tests is only a candidate; no product success until independent original/candidate host court, inherited positive/hostile recovery tests, multi-OS, full root CI, exact-head performance parity with unchanged comparator, memory and source mutation assessment. If the bounded cache cannot survive these, retire or restrict rather than relax safety benchmarks. No release or version change.
