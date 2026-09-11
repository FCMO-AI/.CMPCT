# ONE Genesis non-circular candidate runtime binding preregistration — 2026-09-10

**Mission Lock / Referee:** repair a flaw found during hostile review of the candidate-boundary enforcement before any Genesis contender execution occurs.

## Negative found before promotion

The first enforcement draft required `certified_candidate.source_sha` inside `benchmarks/one/genesis_one_candidate_boundary_v1.json` to equal the checkout commit SHA. Because that manifest is itself content of the commit whose SHA it would name, deliberate certification would create a cryptographic self-reference: writing the SHA changes the commit SHA. A practical gate could therefore be both fail-closed and impossible to certify correctly.

Preserve this as a negative result. Do not work around it by accepting a parent SHA, abbreviated SHA, mutable branch name, or by skipping source binding.

## Revised invariant

Two independent identities must be composed:

1. **Execution source identity:** the sealed executor supplies the exact candidate commit SHA and the worker requires it to equal checkout `HEAD`.
2. **Certified runtime identity:** the candidate-boundary manifest certifies the exact ONE creator path, reader path, their Git blob identities, and the Git tree identity of `experiments/one`.

The runtime tree is outside the manifest's own path, so it can be certified without a self-reference. The exact checkout commit remains independently sealed by the executor.

## Falsifiable hypothesis

A worker that verifies both identities before importing ONE code prevents an uncertified or changed runtime from entering the gate while still allowing a later evidence-only manifest commit to certify an already-falsified runtime tree.

## Disproof tests

Reject the design if any of the following succeeds:

- a certified manifest with the wrong creator path;
- a certified manifest with the wrong reader path;
- a certified manifest with either wrong blob identity;
- a certified manifest with the wrong `experiments/one` tree identity;
- production execution when checkout HEAD differs from the executor-sealed candidate SHA;
- production import before runtime certification completes;
- transfer-fixture operation being labeled production evidence.

## Acceptance evidence

- all mismatched path/blob/tree cases fail before `_load_surface()`;
- an exact synthetic certification object for the observed runtime tree passes the certification helper;
- the current repository manifest remains HOLD until the separate product-boundary evidence is deliberately adjudicated;
- no Genesis corpus generation, measurement, comparison, scoring, or winner selection occurs in this repair.

## Claim boundary

This repair makes candidate certification *possible and source-safe*. It does not itself certify the current ONE runtime or establish that ONE wins the Genesis gate.
