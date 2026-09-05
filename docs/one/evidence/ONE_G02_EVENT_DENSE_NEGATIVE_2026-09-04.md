# ONE-G0.2 — Event-driven dense selection negative receipt

**Status:** exact-head scoped negative + causal attribution  
**Source:** `e65a25f6d22515750c52b17b42f6c6bc2aa3c8b4`  
**Workflow:** `33938985256`  
**Job:** `101232484865` (`event-minimizer-evidence`)  
**Artifact:** `9961142744`, `one-g02-event-e65a25f6d22515750c52b17b42f6c6bc2aa3c8b4`  
**Artifact digest:** `sha256:1a3205295d676705dc66dac91aa5256289d285eb264f260746f8321621feb2b8`  
**Instrument:** `benchmarks/one/one_g02_minimizer_event_ab.py`

## Hypothesis and frozen gate

The preceding record-suffix experiment removed about 99.3% of suffix writes but became much slower, showing that replacing dense direct lookup with sparse cursor control was a bad trade. This follow-up therefore kept the promoted dense suffix representation exactly and changed only **when** it is queried/reselected.

A dense suffix entry already stores its rightmost argmin offset. That offset is an expiration pointer: while the advancing window start has not passed the argmin, the suffix candidate cannot change. Prefix minima change only on a new rightmost minimum; complete middle-block minima are constant within the current block. The preregistered Builder recomputed the global selected minimum only on those events.

Frozen promotion law:

- exact independent-oracle anchor trace, final Gear state and considered count on every case;
- event-driven elapsed <=0.85x promoted tail-aware dense baseline on every large case (>=15% faster);
- <=1.05x on every tested case;
- <=1.01x modeled state;
- zero source rescans;
- on every large case, both selection recomputes and suffix candidate loads <=25% of mature windows.

Any violation rejected promotion. No threshold was mutable after execution.

## Result

`decision = reject_event_driven_dense_maintenance`

All 50 ONE semantic/hostile tests passed and every benchmark row matched the independent anchor trace exactly. State remained equal to the promoted dense layout and source-byte rescans remained zero.

The event-sparsity hypothesis was strongly confirmed:

| Large case | event / tail elapsed | selection recomputes / mature windows | suffix loads / mature windows |
| --- | ---: | ---: | ---: |
| random 1 MiB | **0.9229x** | 1.46% | 0.72% |
| zlib-random ~1 MiB | **0.9263x** | 1.47% | 0.74% |
| exact pair | **0.9308x** | 1.45% | 0.72% |
| shifted pair +1 B | **0.9221x** | 1.46% | 0.72% |
| repeated 64 KiB basis | **0.9200x** | 1.39% | 0.65% |

The hostile 16,385-byte shifted-starvation case improved to 0.9653x. The 4,160-byte boundary was essentially neutral at 0.9889x. The below-enablement row was faster but is not selector evidence.

However, every large case missed the frozen <=0.85x promotion bar. The gain was only about **6.9%–8.0%**, not the required >=15%.

## Causal interpretation

Per-window suffix lookup/global candidate selection is a measurable but **secondary** owner. Eliminating roughly 98.5% of selection recomputes and more than 99% of suffix candidate loads recovers only ~7–8% large-case time. Therefore the majority of the promoted tail-aware kernel's residual versus Gear-only lives elsewhere.

Combined with the record-suffix negative, the evidence now says:

1. dense suffix **write count alone** is not the owner (99.3% write removal regressed 25–32%);
2. dense suffix **per-window query/reselection** is not the owner (~99% query/reselection removal improves only 7–8%);
3. the next diagnosis should isolate the cost of derived Gear-state buffering, dense suffix construction/materialization, block-transition work and compiler/vectorization behavior rather than continuing query-path tuning.

## Decision / reopening predicate

Do not promote the event-driven variant under the frozen gate and do not lower the 15% threshold post hoc. Preserve the ~7–8% gain as causal evidence, not as a baseline switch.

The tail-aware dense four-segment implementation remains the promoted encoder-discovery baseline because it already passed the stronger original all-case gate against masked deque. Reopen event scheduling only if it composes essentially for free with a later maintenance redesign or if new profiling shows query/reselection again dominates after larger owners are removed.

No stored-byte, Law, wire, reader, product-speed, v0.29, v0.30 or full-CMPCT1 superiority claim is created by this receipt.
