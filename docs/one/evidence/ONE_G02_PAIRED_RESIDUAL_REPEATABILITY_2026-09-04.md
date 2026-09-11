# ONE-G0.2 — Paired residual owner repeatability constraint

**Branch:** `research/cmpct1`  
**Experimental version:** `ONE-G0.2`

## Question

Is the post-counter paired ladder stable enough across exact-head hosted reruns to justify optimizing one residual layer in isolation?

This is a repeatability interpretation over two immutable result-bearing executions of the same paired A-B-B-A attribution family. It does not rewrite either prior result.

## Run A — earlier exact source

Exact source `295d2ebee91bedc914f2dc673688712893753a7b`, workflow `33941247183`, job `101238990108`, artifact `9961886850` (`sha256:992c0ee03943dd0533f2afcdb0395a1103a798e57db2dce8daac8bbbd2e65435`) reported cross-case median incremental costs:

- buffer/prefix: **0.662275 ns/input-byte**;
- dense suffix: **1.459584 ns/input-byte**;
- exact selection: **1.406956 ns/input-byte**.

Frozen run-local owner: `dense_suffix`.

## Run B — later exact head

Exact source `dbf5a940ce22c058567dcd4889c13e64200cc741`, workflow `33941921029`, job `101240913254`, artifact `9962137880` (`sha256:1d26f23ffb18017d95a0d6d1540eab798c8e8cafe2067ef46818170c60708527`) repeated the same 9 warm-started adjacent-layer A-B-B-A protocol and reported:

- buffer/prefix: **0.713417 ns/input-byte**;
- dense suffix: **1.775622 ns/input-byte**;
- exact selection: **1.779149 ns/input-byte**.

Frozen run-local owner: `exact_selection`.

Every displayed large-case incremental layer remained positive. In Run B, selection exceeds dense suffix by only **0.003527 ns/input-byte**, about **0.20%** of either layer. In Run A the ordering is reversed by about **0.052628 ns/input-byte**.

## Decision

**Scoped negative constraint: do not treat `dense_suffix` or `exact_selection` as a stable isolated global owner on hosted timing evidence. Treat them as one co-dominant suffix+selection causal cluster until an intervention separates them.**

The stable fact across both executions is not which of the top two wins by a few percent; it is that buffer/prefix is materially smaller and the combined suffix/selection region dominates post-counter discovery cost. The rank flip is exactly the kind of runner-sensitive boundary that should block micro-optimization aimed at one member of the pair.

## Causal consequence

The next useful Builder should remove work shared by, or transferred between, suffix construction and exact selection. Examples that remain admissible are a fused suffix/query representation, layout that directly carries sufficient argmin information, or a loop fusion that eliminates an intermediate state walk while preserving the exact rightmost-min semantics. An intervention that makes suffix construction cheaper only by making selection equivalently more expensive is not progress.

This reopening condition is explicit: a single-layer optimization becomes justified only if a paired intervention shows a stable, material (> noise-scale) separation across repeated exact-head runs without exporting elapsed, memory, source-traffic or correctness debt.

No implementation is promoted here. This creates no reader, Law, wire, stored-byte, product-speed, comparator or release authority.
