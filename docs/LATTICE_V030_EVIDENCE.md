# Geometry / Lattice v0.30 evidence ledger

Research branch: `agent/lattice-v030-breakthrough`

Draft PR: #45 (temporarily closed while the long Geometry measurement runs on the isolated branch trigger; it will be reopened for the full repository gate before promotion).

Status: **Geometry breakthrough gate pending independent CI**.

This file is the durable regression-debt/evidence ledger. It is separate from the design note so benchmark
conclusions are not retroactively folded into the hypothesis that preceded them.

## Frozen Geometry seed gate

The stronger Geometry compiler supersedes the initial Lattice-only gate. The active independent gate requires:

- exact same-live-tree accepted v0.29 control for every workload;
- all 15 public deterministic workloads, no dropped rows;
- candidate complete artifact <= accepted v0.29 on every row through exact fallback;
- >=256 KiB aggregate saving and >=256 KiB best-row saving;
- strong tree verification for every emitted candidate;
- dependency depth 0 and node read amplification 1.0 for the standalone Geometry seed;
- bounded ragged-transpose work in both writer nomination and reader inverse.

The threshold was raised after exact-tree local reproduction showed the initial 64/128 KiB Lattice gate was
no longer a demanding falsifier for the expanded Geometry mechanism.

## Pre-CI exact public ML mechanism evidence

The deterministic public ML workload was reproduced byte-for-byte: logical size **18,172,774 B**, tree
SHA-256 `efc09910fea8ef67d24cd8957d3d576df3a7cc7f10f14585e3a3ae269017901d`.

Complete serialized Geometry accounting on that exact tree measured:

- accepted v0.29: **13,836,439 B**;
- Geometry: **13,394,449 B**;
- saving: **441,990 B / 3.1944%**.

The standout exact payload is the 2,810,845-byte tokenizer stream: Zstd-19 stores **166,909 B**, fixed-width
lane Geometry **51,634 B**, and measured delimiter Geometry **2,782 B** while remaining byte-exactly
reversible. These are local mechanism measurements until the branch CI reproduces the complete-artifact
claim; they are not yet a promoted public-release record.

## Hostile-work resource closure

The delimiter representation is byte-bounded but a naive ragged transpose can visit a rectangular
`segment_count * max_segment_length` cell space larger than the logical node. The bounded execution facade
now caps that work at **8 * 512 KiB = 4,194,304 cell visits**:

- writer nomination removes an over-budget delimiter candidate and preserves direct/lane fallback;
- direct transform calls reject over-budget shapes;
- reader inverse checks the rectangle before allocating rows or entering the transpose loop;
- an adversarial 510,015-byte writer fixture produces a 4.8M-cell rectangle and must be rejected;
- a separate 65,536-segment authenticated-descriptor fixture attacks the reader boundary.

Footnote: resource limits are hard invariants, not performance debt. The Geometry benchmark therefore runs
through `entropygraph_v030_geometry_safe` rather than measuring an unbounded prototype and promising to fix
it later.

## Adjacent negative evidence — Multi-View HyperPack

An independently developed v0.30 HyperPack branch executed on the fixed 724-file hostile structural
aggregate before Geometry's generalization run. It produced **0 B complete-artifact saving** versus accepted
attempt #5 and therefore fell back byte-identically to v0.29 (`47,147,764 B`). Its portfolio creation path
was also very expensive (~672 s), so non-adjacent multi-view placement is rejected as the primary v0.30
compression breakthrough.

The experiment exposed a more important invariant. A weighted read-amplification score allowed an inherited
plan with a ~53.73x worst-member outlier. A member-safe variable-size plan reached ~7.66x worst-member
amplification while costing only 56 B more at the compared packing layer. Therefore future elastic packing
must use **per-member <=8x amplification** as the admission law; weighted-average locality alone is
insufficient. The 56 B storage debt means this locality repair is not silently promoted as a size win.

Footnote: this conclusion remains useful even though HyperPack's workflow ended red after its result because
an assertion read the inherited summary's worst-member value rather than the selected member-safe plan. The
compression result itself was complete and showed exact v0.29 fallback; the failing assertion does not turn
0 B into a hidden win.

## Accepted-graph Lattice oracle

PR #44 independently opens the real attempt-5 physical graph and prices lane transforms plus bounded fusion.
Its first executable run exposed two runner/oracle defects before any threshold verdict:

1. the public corpus generator dependencies were incomplete;
2. inherited v0.29 pure-direct packs may already exceed the stricter <=8x per-member law, and the oracle
   incorrectly treated such an inherited source record as an invalid Lattice candidate and aborted.

Both are repaired without changing transform choices, cost accounting or the preregistered >=64 KiB seed
threshold. Over-8x inherited source packs are now simply ineligible for Lattice replacement and remain
byte-for-byte inherited.

## Orthogonal PrefixGraph evidence

Exact public shifted-version and boundary-churn trees were locally reproduced to their historical hashes.
A separate self-contained depth-1 Zstd raw-prefix prototype round-tripped both trees exactly and measured:

- shifted: **1,699,988 B** vs v0.29 **1,723,056 B** -> **23,068 B smaller**;
- boundary churn: **75,276 B** vs v0.29 **79,876 B** -> **4,600 B smaller**.

This mechanism remains causally separate from Geometry until it receives its own durable executable oracle.
It is not included in the active Geometry gate or any release claim.

## Regression debt still open

- standalone portfolio creation builds accepted v0.29 and Geometry independently; CPU/wall-time debt is expected;
- extraction timing and peak-memory accounting are not yet complete;
- CMPNX13 remains research-only and has no canonical/native-reader portability claim;
- Geometry currently competes as a whole artifact instead of reusing Mosaic's already-proven graph/packing work.

A green seed gate therefore means **preserve and rehabilitate**, not release. Numeric v0.30 promotion remains
blocked until the ordinary direct-base size/timing gate, hostile parser/resource work, native/shared-reader
plan, release evidence, version discipline and public-site coherence all pass unchanged.
