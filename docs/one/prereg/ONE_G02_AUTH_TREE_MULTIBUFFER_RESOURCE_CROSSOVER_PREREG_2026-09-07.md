# ONE-G0.2 multi-buffer authentication resource/crossover preregistration

**Frozen before result-bearing execution.**

## Mission lock / Referee

The exact hosted same-level multi-buffer SHA-256 prototype passed its first frozen speed gate at 64 KiB and 256 KiB: median candidate/baseline elapsed was 0.7804x, both balanced 112-byte rows were <=0.7651x, all roots matched the independent oracle, and all candidate staging/allocation/job setup remained charged.

That result is not yet sufficient to place multi-buffer hashing behind ONE's native writer dispatch. The prototype has fixed batching workspace and setup cost, and the prior matrix did not test tiny roots or process CPU. ONE explicitly values elapsed time, CPU work and memory traffic rather than wall-clock speed alone.

> **Hypothesis:** multi-buffer SHA has a reproducible node-count crossover: below it scalar hashing is preferable, while above it lane batching reduces both wall elapsed and process CPU enough to justify an implementation dispatch. The crossover can be learned on a frozen discovery set and survive irregular-size holdout roots without semantic regressions.

This experiment is about implementation dispatch for one exact authentication primitive, not a reader-visible codec/mechanism portfolio.

## Frozen semantics

Use the exact same binary SHA-256 authentication tree and independent Python oracle as the prior positive:

- leaf: `"ONE-L\\0" || le64(index) || le64(total) || payload`;
- parent: `"ONE-P\\0" || le32(level) || left32 || right32`;
- root: `"ONE-R\\0" || le64(total) || le32(leaf_bytes) || tree_root32`;
- 32-byte SHA-256 commitments;
- binary duplicate-right tree;
- fixed leaf width **112 bytes** for crossover study;
- candidate public-burst staging remains inside every candidate timing.

Intel Multi-Buffer is still only an external research oracle/prototype pinned at commit `4f808234a91e87147a4f26167df40f3fd7c7f0c6`.

## Frozen timing/resource instrumentation

For each build record both:

1. wall elapsed from `CLOCK_MONOTONIC_RAW`;
2. process CPU from `CLOCK_PROCESS_CPUTIME_ID`.

Record medians independently over **31 alternating repetitions** after three paired warmups.

Also record exact explicit writer workspace bytes allocated by each implementation:

- baseline tree buffers;
- candidate tree buffers plus `IMB_JOB` array, batch message arena and length array;
- candidate extra workspace over baseline;
- exact staged authenticated-message bytes/source ratio.

The multi-buffer manager/library initialization remains outside each per-tree timing as in the first frozen experiment. Every per-tree allocation and message copy remains inside.

## Frozen discovery and holdout sizes

Discovery roots, in bytes:

- 1 KiB, 2 KiB, 4 KiB, 8 KiB, 16 KiB, 32 KiB, 64 KiB, 128 KiB, 256 KiB.

Holdout roots, never used to choose the crossover:

- 6 KiB, 12 KiB, 24 KiB, 48 KiB, 96 KiB, 192 KiB.

Payload generation remains deterministic and identical to the earlier native profile.

## Frozen crossover learner

On **discovery rows only**, choose the smallest `node_count` T such that:

- that row's wall candidate/baseline <= **0.95x**;
- every larger discovery row has wall candidate/baseline <= **0.95x**;
- the median process-CPU candidate/baseline across discovery rows at or above T <= **0.90x**.

If no such T exists, the crossover hypothesis fails.

Define a prospective native dispatch after T is learned:

- `node_count < T` -> scalar baseline;
- `node_count >= T` -> multi-buffer candidate.

No other threshold, leaf-width condition, corpus type, architecture exception or after-the-fact rescue is allowed in this experiment.

## Frozen holdout gate

Advance the **node-count implementation dispatch principle** only if all of the following hold on the six irregular holdout roots:

- zero root/geometry/accounting mismatches;
- dispatched wall ratio <= **1.00x** on every holdout row, where scalar-selected rows count as exactly 1.00x;
- every multi-buffer-selected holdout row has wall ratio <= **0.97x**;
- median process-CPU ratio among multi-buffer-selected holdout rows <= **0.92x**;
- candidate extra explicit workspace is bounded independent of root size apart from the same tree buffers baseline already needs, and reported exactly;
- no integer overflow/allocation/accounting anomaly.

The experiment may PASS even if tiny roots correctly stay scalar. That is not a reader-visible fallback: both paths compute the identical SHA-256 representation and proof semantics, and the dispatch variable is a cheap writer-side node count known before hashing.

## Hostile Reviewer / disproof

Strong disproofs include:

- crossover moves unpredictably between discovery and irregular holdout sizes;
- elapsed improves only by consuming more total CPU;
- a multi-buffer-selected holdout row regresses;
- fixed workspace is large enough to violate bounded-writer expectations;
- any exact-root mismatch.

A PASS would authorize only creation of a narrow ONE-owned hash-batch dispatch abstraction with scalar fallback. It would **not** authorize Intel Multi-Buffer as a permanent dependency, nor solve authenticated-placement storage/access overhead, end-to-end ingest, portability, energy, or non-x86 support.
