# O0 — Authenticated revision-24 transaction delta replay CPU amplification

**Preregistered 2026-10-24 UTC before adding tests or modifying source.** Owner: independent Phased1 scientific lane. Base: `agent/v031-development@4545d7d5b2a0b712b4b00f5a9c291d4a3a9e169b`. Scope: **research/evidence only** until a decision; no shared `validation.py` edits. This is distinct from the concurrently owned hardlink-owner graph memoization PR #342 and from Writer mutation correctness.

## Observation, baseline and bounded question

Current `src/cmpct/validation.py` `_apply_delta` applies each authenticated `ren`/ `put` by scanning `index['files']` from the start, and each `del` by filtering the full list. Current `ParserLimits` bounds the index/generation byte counts, file count and delta depth, **not the total number of file-row comparisons during delta replay**. A single permitted authenticated delta with N operations on N files may consume Θ(N²) CPU even though the index and generation occupy Θ(N) bytes.

**Primary question:** Does a valid, fully committed r24 checkpoint plus an authenticated one-generation delta with N unique renames exhibit materially superlinear actual `preflight_archive()` work versus a same-cardinality valid signed checkpoint control? The mechanism must be attributable to delta application rather than Builder time, physical payload or process startup.

## Prior controls and concurrency

Checked current open PRs/branches at orientation. PR #342 owns hardlink-chain preflight memoization and already measured a distinct Θ(N²) relationship; do not duplicate or overwrite that code. The dormant `agent/phased2-v031-delta-put-amortized-preflight-20261019` branch points at unchanged canonical development, with no observed result-bearing PR. PR #341 owns prospective release-custody composition; #320/#328 own skipped performance admission. Research here stays isolated; before any `validation.py` edit, recheck overlapping owners and reconcile exact current files.

## Experimental design and prediction

Produce one authentic CMPCT Builder file, derive a content-preserving, fully SHA-committed checkpoint containing N logically distinct members that share the original physical stored bytes, and append one real revision-24 signed delta carrying N disjoint rename operations. Verify both checkpoint and delta integrity/format, exact physical payload identity, logical final namespace and readable original bytes. Measure actual installed-library `preflight_archive` wall/CPU using repeated in-process runs (separately report subprocess/startup if tested) for N = 128, 512, 2048, 4096 as resources permit. Preserve raw repetitions and full stored archive bytes. A same-N fully committed checkpoint with the **same final logical names** but no delta is a lower-work structural control. An independent indexed in-memory replay is a generous upper-bound oracle only; it gets **zero product credit**.

**Prediction:** after subtracting same-size checkpoint validation/control costs, authenticated delta work grows approximately quadratically in N; physically unchanged members and index SHA preserve identical logical outcome. Product materiality is assessed using actual end-to-end preflight, not an isolated loop.

**Kill/narrow rule:** retire the hypothesis if the genuine installed-product preflight does not show meaningful superlinear delta overhead, if index/metadata decoding dominates at measured N, if source controls fail or archive generations aren't authentic and committed, or if an already-owned current implementation resolves this exact surface. Source-level loop complexity and detached Python loop measurements alone are **not** product measurements.

## Invariants, alternative explanations and exported costs

Preserve released r24 bytes/semantics, recovery fallback, independent SHA correctness, valid delta grammar, parser limits, duplicate/cycle refusal, arbitrary logical member identity and exact data reconstruction. Alternative explanations include zstd/msgpack decode overhead, index scan and archive footer scanning, filesystem cache effects, variable compression ratio and non-equivalent delta payload sizes. The same final logical tree control isolates output semantics, while raw size/encoded index/gen bytes distinguish representation cost.

Potential repairs after decisive evidence: (a) operation-scoped indexed replay preserving first-match and operation-order semantics, including repeated names, rename collisions and later deletes; (b) explicit bounded-work validation with proven max and honest rejection of valid-but-costly archives; (c) changed transaction journal representation/normalization gated by compatibility. No speculative fix receives credit before actual semantics and product-ratio controls.

## Planned results / counterfactual

Outcome PENDING. No CI, benchmark, new product effect or performance improvement claimed in this preregistration. A cheaper prospective discriminator is the per-operation number of scanned file rows; it can falsify the performance path but cannot by itself establish product costs. Keep outcomes/negative evidence append-only and leave Discovery STATE unchanged unless a decision-changing result warrants conflict-safe reconciliation.
