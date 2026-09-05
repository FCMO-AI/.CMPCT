# ONE-G0.2 sparse relation opportunity gate — result receipt

**Status:** ADVANCE as a writer-side pre-proof falsifier; no product/release authority  
**Experiment:** `ONE-G0.2` sparse relation gate integration  
**Branch:** `research/cmpct1`  
**Frozen experiment source:** `5e3e48429726d75e5102aae74709eae6b7f796f2`  
**First dispatch source:** `c76590233f3880d6e91fbd76c04217c6cc78d3a9`  
**Result-bearing source after preflight-only repair:** `4759c8e7b727e8e6bf117ff3ed53f7f2bb984db5`

## Mission Lock

The overlap-safe generalized shift-relation writer can exploit useful ±1/±2 byte relationships, but full exact proof is wasteful for already-nominated pairs that contain no useful relation. The hypothesis was that a tiny content-only sample can reject obvious negatives before full proof while preserving every productive relation and reducing total proof-path elapsed time.

The frozen gate samples 16 evenly spaced positions and the four shifts already owned by the downstream exact proof (`-2`, `-1`, `+1`, `+2`). Two supporting samples admit full proof. Every gate comparison is charged. The exact safe dispatcher remains the only authority that can establish a usable relation.

The five-case relation-transfer corpus is replayed at 4, 8, 16, 32, 64, 128 and 256 KiB. Frozen promotion requires at every size:

- identical enabled/disabled classification versus the ungated safe dispatcher;
- identical best shift for every enabled relation;
- 100% retention of productive baseline relations;
- at least one pair rejected before full proof;
- gate compared bytes <= 1.0% of logical relation bytes;
- gated/baseline elapsed <= 1.03x.

Across all seven sizes, median gated/baseline elapsed must be <= 0.95x. A miss retires this exact gate shape; thresholds are not retuned after seeing results.

## Preflight incident and repair

The first dedicated workflow run, `33965168847`, job `101303891835`, on exact source `c76590233f3880d6e91fbd76c04217c6cc78d3a9`, did **not** execute the frozen benchmark. `tests/one` failed during preflight, the result-bearing step was skipped, and artifact preservation consequently failed.

This was not scientific negative evidence. The workflow used a different test environment from the repository's authoritative test lane: Python 3.12 with only `pytest` installed, instead of an installed project test environment. No benchmark outcome existed to interpret.

Commit `4759c8e7b727e8e6bf117ff3ed53f7f2bb984db5` changes only the workflow preflight environment: Python 3.11 with pip cache and `pip install -e '.[test]'`. It does not alter the frozen corpus, sparse-gate code, exact proof kernel, thresholds, repetitions, batch shape or interpretation.

## Exact result-bearing evidence

The repaired exact-head workflow executed the previously frozen experiment unchanged:

- source: `4759c8e7b727e8e6bf117ff3ed53f7f2bb984db5`;
- workflow run: `33968154451`;
- result-bearing job: `101311827047`;
- ONE semantic/hostile preflight: **PASS**;
- frozen sparse relation integration: **PASS**;
- artifact: `9970091362`;
- artifact name: `one-g02-sparse-relation-gate-4759c8e7b727e8e6bf117ff3ed53f7f2bb984db5`;
- artifact digest: `sha256:7fcab879fed0800fd903235033c25529bf56ed5ab066653b545af8cc643f7d3a`.

The benchmark process exits non-zero unless its immutable decision is `advance_sparse_relation_gate`; therefore the successful result-bearing step establishes that **all frozen per-row correctness/opportunity/read-budget/timing gates and the <=0.95x cross-size median timing gate passed**.

The exact JSON row values remain the artifact authority. Do not substitute threshold bounds for exact measurements when quoting row-level performance. The durable conclusion from workflow truth is that the gate achieved at least the preregistered 5% median proof-path improvement bound across the seven size rows, retained all productive baseline opportunities, cheaply rejected at least one pair at every size, kept sparse comparison traffic within 1% of logical relation bytes, and introduced no row slower than the frozen 1.03x ceiling.

## Decision

**ADVANCE `sparse_relation_gate` as a writer-side pre-proof falsifier.**

This result does not promote a new ONE reader operation and does not change stored representation semantics. It validates a content-derived way to kill some exact-proof work early after a relation pair has already been nominated.

## Strongest hostile review / remaining debt

The experiment still gifts **pair identity**: the frozen batch supplies the candidate source/target relation pairs. That is the largest remaining scientific debt. A cheap proof gate can look excellent while pair enumeration or nomination dominates the actual writer.

Therefore this result is **not** evidence of end-to-end ONE creation-speed improvement, and it grants no stored-byte, reader-speed, selective-access, v0.29/v0.30 or release claim.

Naive arbitrary relation discovery has already produced multiple negative/failing experiments on this branch. The next test must not reopen an all-pairs search. It should derive relation nominations from evidence already produced by, or cheaply fused into, the ONE observation pass, then charge nomination + sparse gate + exact proof together.

## Next decisive experiment

Build a content-derived, bounded relation nomination stage that can share the existing fused observation pass. Measure the complete chain:

`observation / nomination -> sparse falsifier -> exact safe proof -> generic ONE Law`

against the current writer-side baseline on generator-distinct positive and negative cases.

Promotion requires exact opportunity retention, explicit candidate counts/false positives, complete source/read traffic, retained state and total elapsed cost. A nomination design that saves proof work but merely exports more CPU/memory traffic into candidate discovery is a rejection.
