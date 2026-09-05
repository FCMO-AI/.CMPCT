# ONE-G0.2 — Counter Bookkeeping Promotion Receipt

**Experimental line:** `ONE-G0.2`  
**Primary branch:** `research/cmpct1`  
**Result-bearing source:** `4c906a13ceede4599d3052f22c3ee45058da7432`  
**Workflow:** `CMPCT1 ONE-G0.2 minimizer maintenance evidence` run `33939806976`  
**Job:** `101234876826`  
**Artifact:** `9961421301` (`one-g02-maintenance-4c906a13ceede4599d3052f22c3ee45058da7432`)  
**Artifact digest:** `sha256:923b6b6e0f69a9f9992c414090ca845bd181f60370f9666d205b73c8f1278aa6`

## Mission lock

The promoted tail-aware four-segment minimizer reconstructs the current block number and in-block offset on every considered Gear state with runtime quotient/remainder operations:

```c
q = state_index / block_size;
r = state_index % block_size;
```

`block_size` is supplied at runtime. The Builder changes only this block-coordinate bookkeeping. It advances `q` and `r` as monotone counters while leaving Gear identity, the 4,096-state rightmost-minimum selector, dense prefix/suffix maintenance, tail-dead-work elimination, source traffic, exact proof rules and reader surface unchanged.

The falsifiable claim was that runtime quotient/remainder reconstruction materially owns part of the surviving maintenance cost.

## Frozen promotion / retirement law

Before result-bearing execution:

- every emitted anchor trace, final Gear state and considered-position count must equal the independent Python oracle on every case;
- reserved state, derived-state reads and suffix-block lifecycle must equal the promoted tail-aware baseline;
- promotion requires every large case to be at least 5% faster (`counter/tail <= 0.95`), the median large case to be at least 10% faster (`<= 0.90`), and no tested case to regress by more than 5% (`<= 1.05`);
- retirement as the primary owner occurs if median large improvement is below 2% (`ratio >= 0.98`) or any large case exceeds `1.10x`; otherwise the result remains inconclusive.

No threshold changed after execution.

## Result

**Decision:** `promote_counter_bookkeeping`.

The exact-head workflow passed the semantic/hostile ONE test step and the result-bearing counter A/B. Therefore, by the frozen gate:

- every large case is at least **5% faster** than the prior tail-aware baseline;
- median large-case elapsed is at least **10% faster**;
- no tested case is more than **5% slower**;
- emitted anchors, final Gear state and considered-position counts match the independent oracle;
- reserved state, derived-state reads and suffix-block build/skip counts are unchanged;
- source-byte rescans remain zero.

This is a material encoder-discovery speed win with no representation or state tradeoff.

## Causal code-generation review

A same-compiler `-O3` disassembly companion built the prior tail-aware kernel and the counter Builder and inspected the target functions with `objdump`.

**Decision:** `division_removal_mechanism_supported`.

The prior baseline contains at least one integer `div`/`idiv` instruction in the inspected function; the counter Builder contains **zero**. This static result does not replace elapsed evidence, but it supports the intended causal explanation instead of leaving the speed win as unexplained code motion.

## Adjacent hypotheses resolved in the same exact-head run

### Event-driven dense selection

The immutable event-driven dense-maintenance experiment was replayed and its frozen decision recovered without modifying its old thresholds or instrument.

**Decision:** `reject_event_driven_dense_maintenance`.

Do not combine it into the promoted baseline merely because it reduces nominal selection events. It failed at least one of its original exact-oracle / all-case speed / large-case speed / state / event-ratio conditions.

### Offset-only dense suffix values

A new Builder retained four derived Gear-state blocks and stored only `uint16` suffix argmin offsets instead of duplicating every suffix minimum as both value and offset. It keeps direct indexing and deliberately avoids the retired sparse-record cursor/control path.

Enabled-state reservation is structurally reduced from **49,248 B** in the counter dense baseline to **41,056 B**, a ratio of **0.83366x** (about **16.63% less**), while source rescans remain zero and exact selector semantics passed.

**Decision:** `offset_only_dense_suffix_inconclusive`.

The candidate did not satisfy its frozen Pareto promotion gate, but it also did not cross its retirement boundary. Preserve it as an unresolved state-vs-elapsed tradeoff; do not make it the baseline and do not generalize it into a negative claim about offset-only representation.

## Hostile review / claim boundary

This receipt establishes an encoder-discovery microkernel improvement only. It does **not** establish:

- stored-byte improvement;
- reader or wire-format improvement;
- product creation/decode speed;
- full observer speed;
- superiority to v0.29 or deferred v0.30;
- release authority.

The September 11 same-input 15-workload Genesis gate remains mandatory and unchanged.

## State transition

The counter-based tail-aware four-segment kernel supersedes the quotient/remainder tail-aware kernel as the strongest evidence-backed implementation of the current rightmost-minimum selector. The old implementation remains evidence and comparator history; it is not rewritten.

The next decisive compute question is the residual cost **after** counter promotion. Re-run/decompose maintenance against the counter baseline before attacking another owner. Do not reuse cost ownership percentages measured on the quotient/remainder baseline as though they were still current.
