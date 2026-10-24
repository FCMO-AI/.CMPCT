# O2 — source-exact paired same-runner ABBA for authenticated delta replay

Date: 2026-10-24 (UTC). **Prospective experiment; created before implementation of the O2 court.**

## Authority and scope
Continuation of O0 [#344](https://github.com/FCMO-AI/.CMPCT/pull/344) and implementation O1 [#346](https://github.com/FCMO-AI/.CMPCT/pull/346). Source/candidate parent is exact commit `fb887d8610dced551acf5a84778ba539d08dac59`. Historical product control is **the actual** `src/cmpct/validation.py` Git blob `51c2849061f99a4afeddb7666956b24566ce7de0` from `agent/v031-development@4545d7d5b2a0b712b4b00f5a9c291d4a3a9e169b`. Never rewrite historical source or O0 experiment. PR #342 separately owns hardlink graph memoization; no shared `validation.py` edits or competing implementation in O2. No format, safety, release threshold or evaluator weakening permitted.

## Primary falsifiable question
Does source-exact candidate O1 replay materially reduce **real, installed-package** `preflight_archive()` wall/CPU attributable to `_apply_delta` on the **same signed r24 archive bytes** when run against the **real historical validation module** on one machine, without altering return values, memory boundedness, source/codec compatibility, or easy checkpoint results?

## Court and stronger controls
1. Use the unchanged O0 Builder/signed-delta generator once per sample size N=128/512/2048/4096. Hash each complete physical input and replay exactly the same file paths/bytes through both source versions. Reconstruct content with the real CMPCT Reader and confirm same-final-index signed checkpoint as a separate structural control, not a same-physical-byte control.
2. Load and execute **the entire exact historical `validation.py`**, retrieved from the pinned Git blob, as a separate `cmpct` package module, not a handwritten `_apply_delta` surrogate or a simulated model. Check Git blob and dependencies; load the actual installed candidate `validation.py`. Compare complete preflight answers and exception class/message on ordinary/signed cases, and independently retain O1's random-op/property tests.
3. Alternate control/candidate in ABBA/BAAB blocks, with warmups, using `time.perf_counter_ns` and `time.process_time_ns` only around `preflight_archive()`; attribute replay with equally instrumented wrappers. Keep all raw samples, not just medians. Do not fold startup/import/Builder generation into preflight.
4. In a separate pass run `tracemalloc` for each source version to measure peak incremental Python allocations; note that this is **not** total host RSS and is not an overall memory guarantee. Include complete stored bytes and exact content identity.
5. Host under GitHub Actions, bind checkout/head and blob identities, preserve JSON/log artifacts and failures. A green workflow by itself is not release evidence.

## Kill / narrow conditions
Any changed preflight answer, content/index discrepancy, historical blob mismatch, codec/relative import failure, substantial regressions at small sizes, or uncontrolled memory/exported cost **narrows or blocks promotion**, even if N=4096 accelerates. Treat noisy ratios as ambiguous; never adjust workloads, comparator source, limits or semantics to make a win. If no CI runner can execute the exact sources, leave the question pending with immutable evidence and do not invent a speedup.

## Decision boundaries
An authentic same-runner source-exact ABBA can earn **focused product-performance candidate credit**, not full release parity. Canonical strict performance gate, inherited 4 reds, native/platform agreement, recovery, and integration with PR #342 remain independent obligations. Reconcile Git state before any late shared write. No `docs/discovery/STATE.json` edit without new decision-changing evidence.
