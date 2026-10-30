# J24G61 prospective experiment — signed one-op Reader chain cost attribution
Date: 2026-10-30 UTC
Status: PREDICTION / NO RESULT OBSERVED AT REGISTRATION

## Authority and source boundary
Exact research parent: PR #800 at `fb5d96cdb8855fe3e01868792e65b79d3d61661d`; its source parent is #795 at `1935c14c76f1bb39fd218d73cdbee93d3c2b76a1`. Published main remains v0.30.0, r24. PR #800 has already demonstrated on three hosts that a 2,048-member 63 × public single-rename history opens 9.99–14.41× slower than an additional same-state private checkpoint. This experiment owns *only independent cost attribution*, not Writer, Reader, shared helper, footer semantics, the previously measured pairwise speedup, or release promotion. Owners #795 (shared replay), #797 (many-ops indexed helper) and #800 (physical matched state) are not modified.

## Primary falsifiable question
Is repeated `_apply_journal_ops` (with O(N) name/lineage reconstruction and sorting) causally responsible for the **majority** of the measured 63-single-op Reader-open cost, rather than SHA/footer decode, MessagePack, repeated footer-search, Python/OS noise or reader canonical-path census?

**Prediction** on authentic source-exact 512- and 2,048-member archives: when both real signed chain and byte-equivalent same-state checkpoint are read in fresh child processes, the cumulative replay span constitutes at least **50% of additional median chain-open wall time** at N=2,048, d=63. A positive recommends a *separately owned* proof-of-concept for cross-generation replay-state reuse, not immediate indexed-helper productization. If replay share is **below 35%**, reject that attribution and inspect footer/payload/canonical path overhead first. Between these bounds remain ambiguous, not success. Require >3 ms total chain penalty for materiality; the already-measured #800 numbers are prior evidence, not new evidence.

**Strong simpler control**: #800 same-index same-content checkpoint and an additional uninstrumented sample showing tracer impact. A patched Reader symbol records actual span/call counts without changing any production bytes; independent `cProfile` on one source-bound N=2,048/d=63 case checks the attribution by a different observer. Instrumented and uninstrumented absolute times must never be mixed as one controlled A/B. Paired ABBA/BAAB blocks preserve raw observations. A slow old Reader that is semantically wrong is not a fair competitor; this uses exactly the same #795 package/source for both variants.

## Alternatives and competing explanations
1. Footer SHA/zstd/MessagePack across 64 generations dominates rather than replay (then indexing is not the first repair).
2. Reader's per-file canonicalization, mmap allocation or OS page cache dominates (then ordinary stable-index open needs separate work).
3. Helper overhead is a profiling artifact (then uninstrumented control or cProfile contradicts).
4. Per-generation fsmeta sparse metadata makes this workload unrepresentative (this archive has no xattrs; mark metadata-heavy generalization unmeasured).

## Hard kill / invalidation conditions
Any source pin mismatch, extra/missing public operation, mutated/invalid physical SHA, checkpoint index difference, unexpected replay call count, Reader/preflight failure, non-reproducible benchmark, absent per-sample receipt or fresh-process drift disallows a positive causal claim. Instrumentation overhead >15% of the matched uninstrumented chain penalty makes magnitude ambiguous. Contradiction between the wrapped span and independent cProfile requires investigation, never smoothing. Fresh process is **not** a claim of cold physical disk.

## Evidence rung and exact nonclaims
Research-level attribution, physically generated same-state r24 files, source exactness, three-host CI and independent second-root measurement where practical. No product code, format, native ABI, frozen benchmark, current release receipt, main, discovery STATE, release or claim of complete create/extract/RSS improvement. Store raw per-process wall/CPU and wrapped replay/footer spans, archive bytes, source/commit SHA, procedure limitations, per-host verdict and negative evidence. Only after results choose cross-generation reuse, footer architecture, or retire/redirect.
