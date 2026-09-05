# ONE-G0.2 — Fixed-front branch-bound proof topology negative

**Experimental line:** `ONE-G0.2`  
**Branch:** `research/cmpct1`  
**Status:** immutable negative evidence / topology retired  
**Result-bearing source:** `d10caf0a4d135c35d36d71893aa220c95d7eae2e`  
**Workflow:** `33960768366`  
**Job:** `101292150374`  
**Artifact:** `9967866972`  
**Artifact zip SHA-256:** `a62e488ad7f1d43210ae7ccd4499237a1239c6fdd680c0768c54c78faa6ff720`

## Mission lock

The preceding branch-bound gate had shown that cheap sparse one-byte coverage followed by bounded exact 64-byte proofs could distinguish the tested true shifted relations from false fragmented resemblance at very low writer cost. Its exact-proof phase, however, searched sequentially from the front of the relation and stopped after at most sixteen attempts.

The frozen hostile transfer asked whether that fixed-front proof topology generalized when the relation remained globally useful but exactly those first sixteen 64-byte proof cells were damaged.

The preregistered disproof was explicit: if the full minimizer retained positive marginal reuse while the gate produced fewer than four exact proofs, retire the fixed-front sixteen-attempt topology. The old proof count, attempt cap, comparator, corpus construction and interpretation were not to be changed after result.

## Exact result

`tests/one` remained green: **76 passed**.

The hostile writer-discovery row was:

| Metric | Result |
| --- | ---: |
| input bytes | 131,072 |
| fixed-selector opportunity | 0 B |
| full-minimizer opportunity | 64,512 B |
| marginal minimizer opportunity | 64,512 B |
| nominated shift | +1 |
| coverage hits for best shift | 1,004 |
| exact proof attempts | 16 |
| exact proofs | 0 |
| gate enabled | no |
| positive marginal opportunity | yes |

The immutable experiment decision was therefore:

> `retire_fixed_front_proof_topology`

## Causal interpretation

The cheap coverage stage still recognized the global +1 relation strongly. The failure occurred only because all exact proof budget was concentrated in one spatial phase: the damaged prefix. The remaining relation still contained 64,512 B of exact reuse available to the full minimizer.

This falsifies **proof-phase concentration**, not the broader cheap-coverage -> exact-proof branch-and-bound principle. Increasing the old sixteen-attempt cap or simply moving the same fixed front sites after seeing the result would be threshold/topology tuning and is prohibited by the freeze.

The general lesson is that an exact-proof budget intended to certify a global relation must not let one contiguous local defect own all proof opportunity. Proof placement should derive from distributed evidence/support while remaining deterministic, bounded and cheap.

## Superseding Builder

A new immutable experiment was frozen rather than mutating the failed one:

- kernel: `benchmarks/one/one_g02_shift_branch_bound_stratified_kernel.c`;
- transfer: `benchmarks/one/one_g02_shift_branch_bound_stratified_transfer.py`;
- workflow: `.github/workflows/cmpct1-one-g02-shift-branch-bound-stratified.yml`.

It preserves the successful stage-1 coverage semantics, signed shift set, strict-majority rule, four-proof admission threshold, sixteen-attempt ceiling, 64-byte exact proof size, 5% incremental-selector compute ceiling and 25% modeled read-traffic ceiling. Only proof topology changes: the relation is divided into sixteen equal strata and each stratum may contribute at most one coverage-supported exact proof.

The new disproof matrix includes the original branch-bound cases plus independent **front, middle and tail contiguous 1 KiB damage** positives. Any classification error, failure to recover those positives, compute >5% of promoted incremental selector cost, or modeled read traffic >25% retires the stratified topology. Failure would still not retire the branch-and-bound principle itself; it would show that this deterministic distributed proof ownership is insufficient.

## Claim boundary

This is encoder/writer discovery evidence only. It changes no ONE reader-visible operation, canonical CMPCT format, v0.29/v0.30 comparator, product-speed claim or release authority.
