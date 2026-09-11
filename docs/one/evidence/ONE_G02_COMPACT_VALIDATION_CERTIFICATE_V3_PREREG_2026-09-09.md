# ONE-G0.2 compact validation certificate V3 — preregistration

Date: 2026-09-09

## Mission lock

V1 proved large-graph retained-state value but HOLDed on one tiny hot-path CPU row. V2 attempted lower-overhead scalar lookup but was rejected before its falsifier because the added read-only memory-view metadata made a tiny compact certificate larger than the ordinary proof.

V3 changes only **admission of the in-memory validated-length representation**. Full ordinary validation remains mandatory and authoritative.

## Falsifiable hypothesis

If compact proof state is installed only when its honestly measured retained Python state is strictly smaller than the already-valid ordinary proof state, tiny Programs will keep the ordinary certificate (therefore avoiding compact lookup/memory tax), while large Programs retain the dense-table memory win. This should satisfy the original V1 CPU and memory gates without a benchmark-specific graph-size threshold.

Disproof: semantic mismatch, >uint64 semantic narrowing, failure of any original V1 memory/CPU gate, or compact admission for a case where its measured retained proof state is not smaller.

## Frozen matrix and gates

Exactly V1:
- families: add8 and XOR;
- 128 KiB root, first 4 KiB request;
- unrelated valid nodes: 0, 64, 256, 1,024, 4,096;
- 15 warmed CPU measurements per cell;
- ordinary validated certificate comparator.

Promotion requires:
- exact semantic parity every row;
- at 4,096 unrelated nodes, candidate retained Python preflight bytes <= 0.40x ordinary;
- candidate retained state <= 12 B/node + 256 B;
- median repeated-read CPU <= 1.15x ordinary;
- every repeated-read row <= 1.30x ordinary;
- median one-time open CPU <= 1.25x ordinary.

## Admission law

No hand-tuned node-count threshold is allowed. After complete validation and uint64-domain eligibility, construct the compact proof and compare the same retained-state accounting used by `ValidatedProgram.python_preflight_bytes`. Install compact lengths iff the compact proof representation is strictly smaller; otherwise retain ordinary lengths.

The admission decision is therefore representation-economic and portable, not workload-name or benchmark-size specific.
