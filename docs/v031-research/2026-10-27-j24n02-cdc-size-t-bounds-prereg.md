# J24N02 — native CDC size_t boundary repair (prospective experiment)

**Recorded before changing product source or running this candidate. 2026-10-27 UTC.**
**Parent:** #501 at `5e99cdcdc213d91792ca616881570976362b7d98`, which already owns the immutable gear-table and native ABI/concurrency court.
**New independent correctness question:** #606; #228/#501 remain owners of gear initialization, #607 of admission/prefix selection. No other product files, benchmark rules, or mutable discovery state will be changed.

## Baseline and sharp hypothesis

Actual `native/cmpct_cdc.c` on #501 preserves `hard_end = start + max_size; if (hard_end > n) hard_end = n`. For valid `n=48,min=1,avg=2,cap=256`, `max=48` yields 17 increasing ends, while `max=SIZE_MAX` returns zero because unsigned wrap moves `start` backward. The current experimental evidence in #606 is C-body transcription plus independent arithmetic simulation; actual-source C compilation is the first required evidence rung.

**Prediction:** Computing `remaining = n-start` (invariant `0<=start<=n`), bounding `hard_end` by `remaining`, and comparing `min_size` and `avg_size` against the bounded segment *before addition* will preserve the original cut pattern for all genuinely non-overflowing cases while producing exactly the `max=n` cuts for every valid `max>=n`. No new index, allocator, dependency, on-disk format, ABI, native global state, or Builder/Reader source modification.

## Controls / independent falsifiers

1. Compile **exact** #501 `native/cmpct_cdc.c` as historical control and candidate as separate executables/libraries. Verify its file blob identity before reporting historical claims.
2. Deterministic 48-byte reproducer from #606: `data[i]=(i*31)^(i/3)`; expected normal ends `2,5,8,11,14,17,20,23,25,28,30,33,36,39,42,45,48`. Original with `max=SIZE_MAX` should return 0, candidate should equal normal control; do not mislabel a controlled historical failure as candidate failure.
3. Test `max` values around `n`, `SIZE_MAX`, normal `min/avg/max` settings, `min/avg` beyond `n`, `n=0`, exhausted `cap`, null inputs, and multi-pattern reproducible cases; inspect strictly increasing offsets and final end equal `n`. Compare candidate against genuine original for ordinary in-range settings and against `max=n` when `max>=n`.
4. Differently rooted check: a standalone oracle that uses **remaining-length** arithmetic and independently derives cuts from the frozen SplitMix64 seed; do not simply copy candidate statements. Additional toolchain/OS builds where available, sanitizers on Linux, and actual SHA-bound source receipts.
5. Measure scoped CPU overhead on ordinary and extreme parameters against original from identical process boundaries, with repeated raw observations. Reconfirm the existing #501 immutable gear table (256 exact identities, unchanged bytes), ABI symbol and full r24 archives through inherited tests before promotion. Do not mistake benchmark workflow SKIPPED for substantive parity.

**Stop/kill:** changed ordinary cut boundaries, nonmonotonic output, uncontrolled termination, weakening `cap`, replacing original constants, changed exported signature, weakened error behavior, or meaningful normal-case CPU regression unsupported by cost leverage. Preserve all negative cases. Since `avg_size * 2 - 1` remains modular unsigned math for theoretical huge values, separately record that boundary's semantics instead of silently claiming universal mathematical CDC equivalence.

## PARETOBONK / alternative frames

- *No fix*: cheapest but leaves a confirmed valid-argument correctness failure.
- *Reject `max_size>n`*: avoids overflow but needlessly removes otherwise valid input and violates monotone maximum semantics; disfavored.
- *Saturating bounds using subtraction*: same cut loop/gear, exact for ordinary ranges, no storage/ABI overhead; chosen cheap decisive implementation.
- *128-bit intermediate*: compiler/platform-dependent; unnecessary complexity.
- *Explicit universal length validation*: potential alternative if subtraction path fails.
- Do not optimize CDC admission or other compression knobs in this experiment; the issue is a low-regret correctness defect, not a claimed compression win.

## Evidence classification / promotion law

Initial C-focused tests provide **native correctness evidence**, not complete archive/product parity. No actual product gain, size gain, 1.0 target, or numeric v0.31 release is awarded. Any hosted Actions run is counted only after verifying its exact source commit and original artifacts. A passing candidate still needs concurrent CI, native ABI, artifact-size/cold-build and full product checks. Keep #501's immutable table owner untouched and retain draft PR pending decisive hosted results.
