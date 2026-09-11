# Genesis frozen historical product worker v0.1 — preregistration

Date: 2026-09-10
Branch: `research/cmpct1`
Experimental campaign: `ONE-G0.2`
Status: preregistered before worker implementation or Genesis contender execution

## Mission Lock / Referee

Build one measurement wrapper that can invoke the exact frozen v0.29 and v0.30 release/product surfaces on an executor-owned external tree. The wrapper may normalize process boundaries and raw metric names, but must not alter either historical implementation, regenerate a workload, emulate missing capability, score contenders, or choose a winner.

Frozen implementations:

- v0.29 SHA `02b8b27cb2d97af7c6e0797984a898e8fa8a8e5d`, `experiments/entropygraph_v029_residual_strict.py`
- v0.30 SHA `f4b158a55a08b9b18b50e4e4abe4b9251048c772`, `experiments/entropygraph_v030_release_product.py`

The exact frozen surfaces already passed a transfer-only external-input probe. This work moves from API existence to measurement-boundary evidence.

## Falsifiable hypothesis

A fresh-process worker can measure complete creation and whole reconstruction for both frozen products, and selective member access for v0.30 only, while preserving exact external-tree semantics and source binding. It can do so without importing or generating the frozen Genesis workload suites and without inventing unavailable v0.29 selective evidence.

## Required modes

### build

- receive explicit external root and archive path;
- execute the exact frozen `build(root, archive)` surface;
- retain complete archive bytes reported from the actual output file;
- report fresh-process CPU, wall and peak RSS;
- retain product-returned build stats without translating them into a score.

### whole

- execute frozen `strong_verify(archive)`;
- require the product's verification result to be successful according to its own returned contract;
- extract to a worker-owned temporary directory;
- independently compare the reconstructed regular-file bytes and path universe against the supplied external root;
- report fresh-process CPU, wall, peak RSS, returned logical bytes, and exactness.

### selective

- v0.30 only: use the frozen `read_member_with_stats(archive, rel)` surface on an executor-selected regular member; independently verify returned bytes against the external input; preserve returned stats verbatim where JSON-safe;
- v0.29: fail closed / report unsupported at adapter assembly time. Do not materialize a full extraction and call it selective.

## Source / input ownership

Production mode must require:

1. exact contender selection (`v029` or `v030`);
2. an explicit contender checkout root whose Git HEAD equals the corresponding frozen SHA;
3. `CMPCT_GENESIS_REAL_GATE_AUTHORIZED=1`;
4. explicit executor-owned root/archive paths.

Transfer-fixture mode may run before the gate but remains production-ineligible and must reject any request to loosen the frozen SHA binding.

The worker must not import modules whose names indicate the frozen `neutral_hostile` or `resemblance_hostile` corpus generators.

## Independent exactness

The worker's byte comparison is not satisfied by the historical product reporting `ok`. The extracted/read bytes must be hashed/read against the external tree by the wrapper itself. Symlink/directory semantics remain governed by each product and the gate contract; the transfer falsifier should use a regular-file fixture first so wrapper correctness is separable from historical special-file differences.

## Disproof tests

HOLD/RETIRE if any occurs:

1. wrong checkout SHA is accepted;
2. Genesis workload machinery is imported or generated;
3. complete archive bytes are not measured from the actual persistent artifact;
4. whole extraction differs from source but is reported exact;
5. failed `strong_verify` is accepted;
6. v0.29 produces synthetic selective evidence;
7. v0.30 selective bytes differ from the selected source member;
8. negative resource/timing values are emitted;
9. missing metrics become numeric zero rather than explicit unavailability downstream;
10. the worker computes size deltas, comparator rankings, row verdicts, or a campaign decision.

## Transfer evidence requirement

Before use by the real gate executor, execute build + whole for both frozen SHAs and selective for v0.30 on the same deterministic synthetic/transfer tree. Require exact reconstruction and preserve complete raw outputs. No Genesis corpus may be touched.

## Decision labels

- `ADVANCE_HISTORICAL_PRODUCT_WORKER` only after exact-source hosted transfer evidence passes for both frozen products.
- `HOLD_HISTORICAL_PRODUCT_WORKER` while code/tests are local or hosted evidence is pending/incomplete.
- `RETIRE_HISTORICAL_PRODUCT_WORKER` if the wrapper must change historical semantics or fabricate missing capability to pass.

No outcome from this preregistration is a Genesis score or a claim that either comparator wins.