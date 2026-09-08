# ONE-G0.2 packed authenticated-range proof transfer — preregistration

Date: 2026-09-08
Branch: `research/cmpct1`
Experimental version: `ONE-G0.2`
Frozen comparator authorities: v0.29 `02b8b27cb2d97af7c6e0797984a898e8fa8a8e5d`; deferred v0.30 `f4b158a55a08b9b18b50e4e4abe4b9251048c772`

## Mission lock

The native AuthTree creation falsifier advanced a packed digest arena under the existing generic authenticated selective-access grammar. The next risk is boundary debt: if every selective proof requires expanding that packed arena back into Python levels/objects, part of the creation win is exported into read/open work.

Hypothesis: a selective `RangeProof` can be produced directly from packed tree bytes by derived level geometry, reading only the sibling digests required by the requested range, while preserving exact proof bytes and remaining competitive with the already-materialized Python reference tree.

Disproof: any proof semantic mismatch; any need to call `NativeAuthTree.levels()` on the candidate path; proof-hash traffic larger than the reference proof itself; or material repeated proof-generation regression under the frozen timing gates.

## Fixed semantics

Reference: `build_auth_tree()` + `prove_range()`.
Candidate: `build_auth_tree_native()` once outside timing + `prove_range_packed()` directly over `packed_nodes`.

Tree creation is excluded from proof-generation timing because the preceding native-tree experiment already owns creation evidence. The question here is whether the packed sidecar remains usable for selective proof generation without full-tree object materialization.

Every row must prove:

- native and reference roots are byte-identical;
- candidate `RangeProof` equals the reference `RangeProof` exactly;
- `verify_range(candidate, root, start, length)` equals the exact requested bytes;
- candidate proof bytes touched from the tree equal `32 * len(siblings)`;
- no full-level expansion is invoked by the candidate implementation.

## Frozen matrix

Deterministic source sizes: 256 KiB and 1 MiB.
Leaf sizes: 80, 96, 112, 192 bytes.
Selective requests per tree:

- first 4 KiB;
- middle 4 KiB;
- final 4 KiB;
- middle 64 KiB.

Timing: 21 paired alternating repetitions after two warmups, with reference and candidate trees prebuilt before the clocks.

Decision scale: 1 MiB.

## Frozen gates

`ADVANCE_PACKED_AUTH_PROOF` only if:

1. the matrix is complete and all semantics are exact;
2. every 1 MiB row has candidate/reference median wall <= 1.15 and median CPU <= 1.15;
3. at least 12 of the 16 1 MiB rows have candidate/reference median wall <= 1.00 and CPU <= 1.00;
4. every 256 KiB row remains <= 1.25 on wall and CPU;
5. candidate tree-digest bytes read equal the exact sibling-hash bytes required by the proof, never the whole packed tree.

Otherwise `HOLD_PACKED_AUTH_PROOF`; semantic disagreement gives `INVALIDATE_PACKED_AUTH_PROOF`.

The no-regression threshold is intentionally modest: the architectural target is to keep the compact representation without paying a meaningful proof-generation tax. A dramatic speedup is welcome but not required because the reference already has fully materialized Python level tuples available for free at proof time.

## Claim boundary

A green result advances packed native AuthTree state as a research selective-access sidecar representation. It does not prove proof-verification acceleration, process RSS, product file placement, remote-I/O behavior, canonical on-disk layout, or portability of the current libcrypto research backend.

## Hostile-review targets before consuming a result

- empty and boundary ranges;
- odd-width tree levels;
- requests crossing many leaves;
- accidental full-level expansion;
- timer contamination from previous result destruction;
- candidate being unfairly credited for tree creation excluded from one arm but not the other;
- proof traffic accounting that gifts coordinate/metadata bytes or reads selected leaf hashes unnecessarily.