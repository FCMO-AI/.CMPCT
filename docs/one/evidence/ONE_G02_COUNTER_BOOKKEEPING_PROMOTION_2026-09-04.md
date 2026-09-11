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

Exact result-bearing ratios (`counter / prior tail-aware`):

| case | tail ns | counter ns | ratio | change |
|---|---:|---:|---:|---:|
| below enablement, 4,159 B | 9,961 | 6,595 | 0.6621x | -33.79% |
| at enablement, 4,160 B | 18,136 | 9,527 | 0.5253x | -47.47% |
| random 1 MiB | 5,217,013 | 4,481,457 | 0.8590x | -14.10% |
| zlib-random ~1 MiB | 5,405,121 | 4,348,012 | 0.8044x | -19.56% |
| exact pair 512 KiB + 512 KiB | 5,160,530 | 4,508,091 | 0.8736x | -12.64% |
| shifted pair +1 B | 5,254,947 | 4,440,659 | 0.8450x | -15.50% |
| repeated 64 KiB basis, 1 MiB | 5,096,467 | 4,551,907 | 0.8931x | -10.69% |
| hostile shifted-starvation 16,385 B | 77,489 | 62,781 | 0.8102x | -18.98% |

Large-case median ratio is **0.859008x**, i.e. about **14.10% faster**. The worst ratio anywhere in the frozen matrix is **0.893150x**, so every tested case improved; there is no hidden small-input regression.

All emitted anchors, final Gear states and considered-position counts match the independent oracle. Reserved state remains **49,248 B** when enabled; derived-state reads and suffix-block build/skip counts are unchanged; source-byte rescans remain zero.

This is a material encoder-discovery speed win with no representation or state tradeoff.

## Causal code-generation review

A same-compiler `-O3` disassembly companion built the prior tail-aware kernel and the counter Builder and inspected the target functions with `objdump`.

**Decision:** `division_removal_mechanism_supported`.

- prior tail-aware function: **366** decoded instructions, **1 integer division instruction**;
- counter Builder: **362** decoded instructions, **0 integer division instructions**.

This static result does not replace elapsed evidence, but it directly supports the intended causal explanation instead of leaving the speed win as unexplained code motion.

## Adjacent hypotheses resolved in the same exact-head run

### Event-driven dense selection

The immutable event-driven dense-maintenance experiment was replayed and its frozen decision recovered without modifying its old thresholds or instrument.

**Decision:** `reject_event_driven_dense_maintenance`.

It reduced selection recomputes to only about **1.39%–1.47% of mature windows** and suffix candidate loads to about **0.65%–0.74%** on the large cases, but that bookkeeping did not buy elapsed speed. Large-case event/tail ratios were **0.9700x–1.0576x**: four of five large cases regressed, including zlib-random at **1.0576x**, while only repeated-64-KiB improved. The below-enablement 4,159 B case regressed to **1.7294x**. This is strong causal negative evidence: eliminating most nominal selection events does not imply lower wall time when event-state/control overhead replaces cheap regular compares.

Do not combine this mechanism into the promoted baseline merely because its event counts look attractive.

### Offset-only dense suffix values

A new Builder retained four derived Gear-state blocks and stored only `uint16` suffix argmin offsets instead of duplicating every suffix minimum as both value and offset. It keeps direct indexing and deliberately avoids the retired sparse-record cursor/control path.

Enabled-state reservation falls from **49,248 B** to **41,056 B**, **0.833658x** (about **16.63% less**). Exact selector semantics and suffix lifecycle match, with zero source rescans.

**Decision:** `offset_only_dense_suffix_inconclusive`.

The large-case signal is promising rather than negative: all five large rows improved, with ratios **0.9394x, 0.9551x, 0.9892x, 0.9689x, 0.9489x** and a median **0.955091x** (about **4.49% faster**), while reducing reserved state 16.63%.

But the small/startup rows export real debt: 4,159 B is **1.1194x** and 4,160 B is **1.0937x** the counter baseline. That violates the frozen <=1.05x all-case promotion condition, while the large rows remain far inside the retirement boundary. The mechanism therefore has a plausible **size-dependent crossover**, not a promotion and not a retirement.

Preserve it for a separately preregistered crossover characterization; do not choose a size threshold retroactively from these rows.

## Current residual attribution caveat

The same run replayed the older cost ladder. On the quotient/remainder baseline it attributes roughly **2.52–2.68 ns/input-byte** to buffer/prefix bookkeeping, **1.50–1.82 ns/B** to dense suffix construction, and only **0.02–0.28 ns/B** to event-style exact selection on the five large cases. However, the newly promoted counter implementation changes the first layer materially. Those old decomposition magnitudes are now historical diagnostics, not current ownership percentages. A new residual ladder must use the counter baseline.

## Hostile review / claim boundary

This receipt establishes an encoder-discovery microkernel improvement only. It does **not** establish stored-byte improvement, reader/wire improvement, full observer or product speed, superiority to v0.29/deferred-v0.30, or release authority.

The September 11 same-input 15-workload Genesis gate remains mandatory and unchanged.

## State transition

The counter-based tail-aware four-segment kernel supersedes the quotient/remainder tail-aware kernel as the strongest evidence-backed implementation of the current rightmost-minimum selector. The old implementation remains evidence and comparator history; it is not rewritten.

Next decisive work:

1. rebuild the residual cost ladder against the counter baseline;
2. separately characterize the offset-only suffix crossover across preregistered geometric input sizes before considering any size gate;
3. target the largest measured post-counter owner rather than continuing isolated micro-tuning.
