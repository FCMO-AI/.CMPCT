# ONE-G0.2 — Paired post-counter residual attribution

**Branch:** `research/cmpct1`  
**Exact source:** `295d2ebee91bedc914f2dc673688712893753a7b`  
**Workflow run:** `33941247183`  
**Result-bearing job:** `101238990108`  
**Artifact:** `9961886850`  
**Artifact ZIP SHA-256:** `992c0ee03943dd0533f2afcdb0395a1103a798e57db2dce8daac8bbbd2e65435`  
**Experimental version:** `ONE-G0.2`

## Why this supersedes the unpaired owner ranking

The existing post-counter ladder timed Gear-only, buffer/prefix, dense-suffix and exact-selector variants in separate batches. Exact-head reruns swapped the apparent largest residual between suffix construction and selection, so choosing the next Builder from that ranking alone was not stable enough.

This preregistered diagnostic used **9 warm-started A-B-B-A rounds** for each adjacent ladder pair on every large case and selected an owner only when the largest cross-case median incremental cost remained positive on every large case.

## Result

**Paired dominant owner: `dense_suffix`.**

Cross-case median incremental cost:

- buffer/prefix: **0.662275 ns/input-byte**;
- dense suffix: **1.459584 ns/input-byte**;
- exact selection: **1.406956 ns/input-byte**.

Dense suffix remained positive on every large case and narrowly but consistently exceeded exact selection in the frozen cross-case ranking. Representative per-case dense-suffix medians were about **1.416--1.479 ns/input-byte**; exact-selection medians were about **1.383--1.416 ns/input-byte** in the displayed cases. Buffer/prefix is materially smaller, about **0.65--0.68 ns/input-byte**.

## Interpretation

This does not mean "optimize suffix at any cost." The immediately preceding cached-recurrence experiment already showed why: removing a logical suffix reread did not materially change generated machine work or paired elapsed time. The next Builder must reduce **actual suffix construction work**, fuse it with work the selector already needs, or change the representation so suffix and selection cost collapse together. Moving the same cost from suffix build into query-time indirection is not progress.

The exact-selector layer is close enough to dense suffix that global carrying cost matters: a suffix optimization that adds selection branches/indirections can easily lose the benefit. Therefore the target is **combined suffix + selection work**, with dense suffix as the current first causal owner, not a local counter metric.

## Research direction

The next decisive experiment should compare the promoted counter representation with the 41,056-byte offset-only representation under paired order-neutral timing and an explicit Pareto/non-inferiority law. That determines whether removing duplicated suffix values is already a free state reduction, merely a cost transfer, or a true regression before any more elaborate suffix representation is invented.

No implementation is promoted by this diagnostic. It creates no Law, wire, reader, stored-byte, product-speed, v0.29/v0.30 or release authority.
