# ONE-G0.2 native AuthTree packed-state RSS transfer — preregistration

Date: 2026-09-08
Branch: `research/cmpct1`
Experimental version: `ONE-G0.2`

## Mission lock

The exact-source native AuthTree batch gate advanced a single native construction boundary that preserves the generic authenticated-range tree exactly and returns all node digests as one packed arena. Separate prior work showed true multi-buffer SHA can win elapsed-only but lost its resource-aware crossover because of complete-message staging and extra workspace.

Question: does the new packed scalar/native construction shape preserve its implementation advantage without increasing fresh-process peak resident memory relative to the current Python reference AuthTree that materializes every digest as Python objects/tuples?

This is a resource-transfer test, not another SHA throughput contest.

## Hypothesis / disproof

Hypothesis: on large roots, packed native state has materially lower or equal incremental process peak RSS than the Python reference tree despite the current ctypes-output -> Python `bytes` copy at return.

Disproof: any root mismatch; any decisive row with candidate incremental peak RSS >1.05x reference; fewer than two of three 16 MiB leaf-width rows at <=0.90x reference; or any 4 MiB row >1.10x reference.

A HOLD is valuable: it would identify the current duplicate ctypes-buffer/`bytes` handoff as resource debt even though construction speed advanced.

## Frozen matrix

Linux hosted evidence only, because `resource.getrusage(...).ru_maxrss` is interpreted as KiB.

Root sizes: 4 MiB and 16 MiB.
Leaf sizes: 80, 112, 192 bytes.
Cold fresh processes: 7 per arm/row, alternating arm order.

Each child:

1. imports the same reference/native modules;
2. constructs the same deterministic source bytes;
3. records `ru_maxrss` immediately before tree construction;
4. constructs exactly one reference or native tree and retains it;
5. records `ru_maxrss` after construction;
6. emits root, node count, logical stored-index bytes, packed bytes when applicable, before/after RSS and `incremental_peak_kib=max(0, after-before)`.

The parent compares roots, node counts and logical stored-index bytes exactly and uses medians of incremental peak KiB.

## Frozen decision

`ADVANCE_NATIVE_AUTH_TREE_RSS` only if:

- complete matrix and exact semantic/accounting equality;
- all three 16 MiB candidate/reference incremental-RSS ratios <=1.05;
- at least two of three 16 MiB rows <=0.90;
- all three 4 MiB rows <=1.10.

If an arm's median incremental RSS is zero, the row invalidates because the measurement resolution is insufficient for the decision.

Semantic/accounting mismatch or incomplete/unresolvable RSS => `INVALIDATE_NATIVE_AUTH_TREE_RSS`; otherwise failing the performance gates => `HOLD_NATIVE_AUTH_TREE_RSS`.

## Claim boundary

A green result supports packed native AuthTree state as a research in-memory sidecar on hosted Linux. It does not establish portable RSS accounting, canonical on-disk layout, allocator-independent memory behavior, proof-generation/verification speed, product ingest, or permanent libcrypto dependency.

The current candidate's temporary ctypes output arena and returned `bytes` may coexist during handoff. That peak is intentionally charged; the experiment must not hide it.
