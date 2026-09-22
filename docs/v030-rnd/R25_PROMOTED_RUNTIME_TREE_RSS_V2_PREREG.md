# Promoted runtime whole-process-tree RSS companion v2 — preregistration

Status: **FROZEN SUPERSEDING CUSTODY/FORGE D5 MEMORY AUTHORITY / ZERO TIMING OR RELEASE CREDIT**

Supersedes only the measurement implementation and interpretation of `cmpct-v030-release-performance-tree-rss-v1`. The v1 receipt and its failure remain immutable.

## Causal basis for supersession

The first result-bearing v1 receipt measured all required whole-process-tree RSS ratios below the existing `1.25x` ceiling, but its Python sampler ran inside the measured worker. It also inflated CPU-heavy pack wall ratios enough to fail timing bands owned by the separate promoted-runtime authority.

v2 tests one narrow causal correction: **move RSS sampling out of the measured worker process while preserving the worker, product, target matrix, operation code and RSS ceiling**.

No release threshold, benchmark target, comparator, archive grammar, product behavior, corpus identity, strong-verification rule, recovery rule, size rule or memory ceiling changes.

## Frozen instrument

- measured worker: unchanged canonical `benchmarks/v030_perf_worker_canonical.py`;
- product front door: unchanged `experiments/entropygraph_v030_release_product.py`;
- target/corpus/order/identity contract: inherited unchanged from `benchmarks/v030_release_performance_product.py`;
- RSS sampler owner: the harness parent process, never the measured worker;
- sample interval: `<=10 ms`;
- sampled domain: worker root plus all live transitive descendants;
- decisive RSS per operation: `max(worker RUSAGE_SELF ru_maxrss, sampled simultaneous process-tree VmRSS)`;
- exited-child high water remains charged because the maximum sampled tree value is retained for the operation;
- sampling errors or missing expected operation receipts invalidate the result.

The sampler process/thread itself is not part of the product process tree and is not charged as product RSS. Its job is observation. It must not execute in the measured worker or share that worker's Python GIL.

## Frozen scientific decision surface

This companion grants **zero timing decision credit** and **zero release credit**. The independent promoted-product runtime job remains the sole authority for the frozen runtime ratios.

v2 records worker wall times only as descriptive instrumentation diagnostics.

The v2 memory receipt advances only if all are true:

1. exact frozen target count;
2. stable accepted-v0.29 historical identity;
3. stable canonical-v0.30 product identity;
4. every expected pack/verify/extract worker execution has an external tree-RSS receipt;
5. no RSS sampler errors;
6. maximum decisive pack/extract RSS ratio across the frozen matrix is `<=1.25x`.

Terminal decisions:

- custody/identity/missing-sample failure -> **`INVALID_TREE_RSS_V2_RECEIPT`**;
- all memory gates pass -> **`WHOLE_TREE_RSS_PRODUCT_MATRIX_SUPPORTED`**;
- valid receipt but any decisive RSS ratio exceeds `1.25x` -> **`WHOLE_TREE_RSS_PRODUCT_DEBT_REMAINS`**.

Timing cannot change any of those decisions. A timing red belongs to the independent promoted-runtime authority, not this instrument.

## Oracle honesty and carrying cost

No child memory is gifted. The PrefixGraph child, interpreter startup, temporary artifact, receipt handling and every other descendant that is live during a measured operation remain inside the sampled process tree.

This experiment adds no shipping mechanism and no format/parser/native/platform complexity. Its only carrying cost is CI measurement code. A green therefore proves only the D5 memory envelope on the frozen hosted matrix; it does not replace recovery, native, Windows/macOS/Android, adversarial, competitor or final strict release authorities.

## Immutability

After the first result-bearing v2 execution, this preregistration, sampler ownership, interval, comparator, target matrix, identity rules, `1.25x` ceiling and terminal vocabulary are immutable. Any material change requires a new superseding freeze while preserving both v1 and v2 evidence.
