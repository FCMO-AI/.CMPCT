# CMPCT v0.29 generalization — creation-cost optimization #1

Status: **pre-registered scheduling optimization; no v0.29.0 claim**  
Parent: `docs/MOSAIC_V029_GENERALIZATION.md`  
Accepted byte mechanism: attempt #5 Residual Program Packing

## Observed failure

The first inherited-frontier generalization run showed that attempt #5's **bytes generalize** but its
portfolio creation cost does not yet satisfy the frozen <=3.0x aggregate budget.

Measured aggregate result before this optimization:

- embedded v0.28: ~370.9 s;
- attempt #5 portfolio: ~1,346.3 s;
- aggregate ratio: **3.63x**;
- median workload ratio: ~**1.99x**.

One workload dominates the excess: `10_large_mixed_binary` is a single 32 MiB logical file whose
attempt-5 build costs ~559 s versus ~24.5 s for v0.28 (**22.8x**) and then selects the exact v0.28
fallback anyway.

The v0.29 generalization gate remains unchanged. This optimization must reduce exported creation work;
it may not raise the 3.0x ceiling or manufacture a new byte win.

## Mechanism hypothesis

Multi-root Mosaic exists to explain one logical target from several independent logical sources. On a
**one-file tree where v0.28 itself rejects its resemblance graph and selects inherited v0.25**, spending
minutes constructing the broader Mosaic Placement graph is a poor portfolio bet: there is no second
logical source file, and the immediately inherited graph already failed its own byte tournament.

The optimization therefore fast-rejects only the conjunction:

1. logical file count == 1; and
2. exact embedded v0.28 selected `entropygraph-v025-fallback`.

The exact v0.28 artifact is emitted unchanged and all research statistics are recorded as zero/skipped.

## Why the reject is narrow

- Multi-file trees always run the full accepted attempt-5 compiler.
- A single-file tree where v0.28's resemblance graph **wins** also runs the full compiler; residual
  packing may still improve real graph deltas there.
- Raw `build_graph()` callers are not fast-rejected; they explicitly requested the research graph.
- The accepted attempt-5 source file remains untouched. The scheduler is a separate wrapper so prior
  evidence remains reproducible.

## Falsification

The optimization fails if any of these occur:

- any v1/v2 accepted attempt-5 archive byte changes;
- the frozen full-artifact gate loses a previously accepted workload;
- the 15-workload generalization candidate gains a size regression;
- the large mixed binary still executes the research graph path;
- the generalization aggregate creation ratio remains >3.0x after baseline-substrate repair;
- tests show the reject can apply to multi-file input or a v0.28 resemblance winner.

## Expected leverage

The measured outlier contributes more than 500 seconds of avoidable research work. Replacing it with one
v0.28 build should move the aggregate creation ratio from ~3.63x toward ~2.2x without changing any
accepted research bytes.

Footnote: that ratio is a prediction from the failed run, not acceptance evidence. Only the next clean
same-runner generalization run can validate it.
