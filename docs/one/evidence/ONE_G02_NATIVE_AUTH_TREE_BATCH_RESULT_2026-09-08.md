# ONE-G0.2 native authenticated-tree batch — exact-source result

Date: 2026-09-08
Experimental version: `ONE-G0.2`
Source branch: `research/cmpct1`
Exact result-bearing source: `71d09480468b5c2e3f9caaa04ec4a9bbb6010781`
Frozen comparators remain: v0.29 `02b8b27cb2d97af7c6e0797984a898e8fa8a8e5d`; deferred v0.30 `f4b158a55a08b9b18b50e4e4abe4b9251048c772`

## Mission lock

Question: can the existing generic authenticated selective-access tree grammar be built through one native batched boundary, emitting packed node digests, without changing any root, level geometry, stored-index accounting, reader semantics, or proof model?

The frozen falsifier compared the Python reference tree builder with the native libcrypto-backed builder over deterministic 64 KiB and 256 KiB roots and leaf sizes 80, 96, 112, and 192 bytes. It used 15 paired alternating repetitions after warmup.

Promotion required exact semantic equality on every row, native/reference wall and CPU ratios <= 0.50 on every 256 KiB row, and <= 0.75 on every 64 KiB row. Missing rows or semantic disagreement invalidate the experiment.

## Exact CI authority

Workflow run: `34236901417`
Job: `102096842483`
Workflow: `CMPCT1 ONE-G0.2 native auth-tree batch`
Result: `success`
Artifact: `10060393950`
Artifact name: `one-g02-native-auth-tree-batch-71d09480468b5c2e3f9caaa04ec4a9bbb6010781`
Artifact ZIP SHA-256: `ed357cc07c4f87f1cb15a9a642a84e456d1298f6166d40223a14840d1f5c0fa3`

The result-bearing executable exits zero only when `_decide()` returns `ADVANCE_NATIVE_AUTH_TREE_BATCH`. The exact-source job completed the semantic/decision-law test step, the frozen falsifier, and artifact preservation successfully.

## Decision

`ADVANCE_NATIVE_AUTH_TREE_BATCH`

Therefore the bounded claim is:

- every tested native root equals the independent Python reference root exactly;
- every tested native level set equals the reference level set exactly;
- node counts and stored-index byte accounting agree exactly;
- every 256 KiB row achieved <= 0.50x reference median wall and <= 0.50x reference median CPU time;
- every 64 KiB row achieved <= 0.75x on both median wall and CPU time.

Exact row medians remain in the retained JSON artifact. This receipt intentionally does not reconstruct unobserved point values from the green decision.

## Mechanism interpretation

The win is not a new authentication grammar. The same domain-separated SHA-256 leaf, parent, odd-node duplication, and root-commit semantics are retained. The causal change is implementation shape: one native boundary performs the existing many-hash construction and emits a packed digest arena instead of creating thousands of Python hash objects/tuples during construction.

This supports using packed native tree state as the research creation representation for authenticated selective access. It does not canonize OpenSSL/libcrypto as a permanent dependency.

## Claim boundary / debt

This experiment does not prove:

- product-level portability of the libcrypto research dependency;
- process peak-RSS improvement;
- proof-generation latency from the packed tree;
- proof-verification throughput;
- filesystem/archive placement cost;
- complete product ingest throughput;
- a new on-disk format or canonical reader change.

Those remain separate gates.

## Hostile review / next falsifier

The strongest immediate risk is re-materialization debt: a packed tree that must be expanded back into thousands of Python `bytes` objects before every selective proof would give back part of the architectural win at the next boundary.

Next experiment: generate exact `RangeProof` objects directly from the packed native sidecar using derived level geometry and direct digest slicing. Compare every proof byte-for-byte with the independent Python `prove_range()` oracle, account only the sibling digests actually touched, and benchmark proof generation without allowing full-tree materialization inside the candidate path.

A green result may advance the packed sidecar as a research selective-access representation. It still may not weaken authentication, selective-read semantics, or portability requirements.