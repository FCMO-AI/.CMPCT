# Genesis whole-read semantics audit

**Date:** 2026-09-11
**Status:** adjudication guardrail; no benchmark result is changed by this note
**Scope:** frozen ONE-G0.2 vs frozen v0.29/v0.30 historical worker read semantics

## Mission lock

Genesis requires same-input, same-semantics evidence. The current raw matrix contains a `whole_read` timing for each contender, but code inspection shows that the timed operations are not equivalent enough to support a supersession claim.

This note does not rerun, rescore, or weaken any contender. It records why existing whole-read timing must remain qualified until a narrow same-semantics audit is run.

## What ONE times

`benchmarks/one/one_genesis_cmpct1_product_worker.py::_whole` puts the following inside `_timed(...)`:

1. import/open the authenticated ONE archive;
2. read each regular file once through the authenticated reader;
3. hash each returned file inside the timed action.

After `_timed(...)` returns, the worker independently compares those digests to source files and checks the source semantic manifest against the authenticated archive manifest. Those independent source/tree checks are **outside** the reported `whole_read` CPU/wall timing.

## What the historical worker times

`benchmarks/one/one_genesis_historical_product_worker.py::_whole` puts all of the following inside `_timed(...)`:

1. `surface.strong_verify(archive)`;
2. `surface.extract(archive, dst)`;
3. `_assert_regular_tree_exact(root, dst)`, which re-reads source and extracted regular files to compare size+SHA-256 maps.

For v0.29 graph archives, `experiments/entropygraph_v028.py::strong_verify` itself calls `_extract_graph(...)` into a temporary directory and computes the logical tree hash. `extract(...)` then invokes reconstruction again. Thus the historical `whole_read` timing can include **two complete archive reconstructions** plus the independent source/extracted-tree digest pass.

The exact implementation path can vary when a historical archive falls back to an inherited format, but the harness contract still times `strong_verify + extract + external exact-tree check`, whereas ONE does not time its post-read independent semantic comparison.

## Consequence

The current `whole_read` medians are useful diagnostics but are not same-semantics throughput evidence.

From the authoritative partial Genesis artifact (`34573437613` / `10191000395`):

- sum of per-workload ONE whole-read CPU medians: **2.015 s**;
- sum of per-workload v0.29 whole-read CPU medians: **6.667 s**;
- raw ratio: **3.31x** in ONE's favor;
- median per-workload raw ratio: **1.71x** in ONE's favor.

Those numbers must **not** be used as evidence that ONE has superseded v0.29 read throughput, because the historical side is charged materially more work inside the clock.

## Same-semantics repair hypothesis

A fair diagnostic should separate at least two quantities rather than moving work invisibly between sides:

1. **authenticated whole reconstruction** — one logical reconstruction of the complete tree under each product's ordinary integrity checks;
2. **independent full verification** — any additional pass needed to establish the stronger archive/tree verification contract beyond ordinary authenticated reconstruction.

The benchmark should report both rather than adding verification-only work to one contender's `whole_read` clock. The source-owned exact-output oracle should have identical timing placement for all contenders (preferably outside the product throughput clock and separately accounted).

For the historical graph product, ordinary `extract` already authenticates metadata/Merkle leaves, physical-record hashes/CRC, node hashes, and file hashes while reconstructing. Whether the additional `strong_verify` tree-hash pass is a required part of the product operation or a distinct verification operation must be decided from the frozen format/product contract, not from which result makes a contender look faster.

## Disproof / hostile review

This audit is wrong if repository authority establishes that:

- ONE's ordinary whole-read operation is contractually required to perform an equivalent independent full-archive verification pass inside the clock, **or**
- v0.29/v0.30 product semantics contractually define every whole reconstruction as `strong_verify + extract` and ONE has an exactly equivalent two-pass requirement that the worker accidentally omitted.

Until one of those conditions is demonstrated, the conservative adjudication is:

> `whole_read` speed comparison = **not semantically comparable for supersession**.

Stored bytes, creation CPU/wall/RSS, exact reconstruction success/failure, and separately supported selective-access evidence remain unaffected by this qualification.
