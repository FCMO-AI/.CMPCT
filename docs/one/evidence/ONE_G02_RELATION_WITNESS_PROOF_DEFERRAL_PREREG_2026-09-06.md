# ONE-G0.2 relation witness-first proof deferral — preregistration

Date: 2026-09-06
Experimental line: `ONE-G0.2`
Authoritative branch: `research/cmpct1`
Status: frozen before result-bearing execution

## Mission Lock

The shared-observer pair nominator currently requires a successful 64-byte exact witness and then performs full left/right exact-reuse extension before a cross-object event nominates the pair for relation proof. On mature shifted/versioned inputs that extension can reread hundreds of KiB, after which the independent safe relation proof performs additional work over the same pair.

For **relation nomination specifically**, the extension may be unnecessary. The reader never trusts nomination: the existing exact safe relation proof is the sole authority for emitting a relation Law. Test whether an exact cross-object 64-byte witness can act as a cheap Opportunity Gate, deferring all relation-authority work to the downstream proof.

This experiment does not authorize deleting exact-reuse extension when exact reuse itself is being considered as a Law. It isolates marginal pair-relation discovery cost.

## Baseline

Baseline relation-discovery traffic:

1. existing local/global shared-observer lookup;
2. exact 64-byte witness verification;
3. current exact-reuse left/right extension until a cross-object exact event exists;
4. if nominated, existing safe exact relation proof.

Candidate:

1. identical lookup and exact 64-byte witness verification;
2. first qualifying cross-object exact witness nominates the pair without reuse extension;
3. existing safe exact relation proof decides the Law.

## Falsifiable hypothesis

The exact 64-byte witness already provides enough cheap pair evidence on the frozen version/resemblance family that relation proof can be deferred without losing any final relation opportunity currently recovered by shared-observer nomination. This should remove most nomination extension traffic while preserving zero false Laws because safe relation proof remains authoritative.

### Disproof

Reject the witness-first gate if it misses any pair that the current shared-observer path nominates and the safe relation proof accepts, or if negative-control witness nominations make total candidate proof traffic exceed baseline on the frozen envelope.

## Frozen envelope

Use 5 sizes (4, 8, 16, 64, 256 KiB) × seeds 7, 29, 53 × six case families:

- `shift_plus1`;
- `damage_quarter`;
- `fragmented_every96`;
- `hostile_fixed_bands`;
- `fragmented_every32`;
- `independent_random`.

Persist:

- current exact-reuse nomination yes/no;
- witness-first nomination yes/no;
- final safe relation decision;
- current witness verification bytes;
- current reuse-extension bytes;
- witness-first verification bytes;
- safe relation proof compared bytes when each arm nominates;
- total modeled relation-discovery proof bytes for baseline/candidate;
- negative-control extra proof attempts.

## Decision law

- `advance_relation_witness_proof_deferral` if every baseline-nominated safe-positive remains candidate-nominated, final relation decisions remain safe-proof exact, no false Law exists, aggregate modeled proof traffic candidate/baseline <= **0.70x**, and no negative-control row exceeds baseline by >1.10x.
- `hold_relation_witness_proof_deferral` if opportunity recall is exact and aggregate traffic <1.0x but the stronger traffic gate is missed.
- `reject_relation_witness_proof_deferral` on opportunity loss or aggregate traffic >=1.0x.

## Hostile Reviewer

A 64-byte exact witness is not a proof of a whole-file relation. It grants only permission to spend compute on the existing safe relation falsifier. The candidate may increase proof attempts; all such cost is charged. This experiment cannot weaken exact reuse semantics, cannot emit a Law from a witness, and cannot claim product writer speed from Python elapsed time.
