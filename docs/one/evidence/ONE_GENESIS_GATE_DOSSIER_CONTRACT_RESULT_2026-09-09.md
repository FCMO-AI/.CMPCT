# CMPCT1 / ONE Genesis gate dossier contract — hosted self-test

Date: 2026-09-09 America/Mexico_City  
Experimental state: **ONE-G0.2**  
Decision: **ADVANCE_FAIL_CLOSED_GENESIS_DOSSIER_CONTRACT**

## Exact authority

- exact source: `601384f086aca910a3b19a4a47465fe7804a4c94`
- workflow: `CMPCT1 ONE Genesis gate dossier contract`
- run: `34420251738`
- job: `102693889748`
- hosted result: `{"self_test": "PASS", "scoring_executed": false}`

The lane checked out the exact source, bound HEAD to `GITHUB_SHA`, and executed only the structural self-test. No corpus generation, contender encoding or Genesis scoring occurred.

## What was proven

`benchmarks/one/one_genesis_gate_result_contract.py` fails closed on intentionally incomplete or misleading future gate dossiers. Its hosted self-test proves at least the following negative cases are rejected:

- an empty/incomplete dossier;
- an `unavailable` capability represented by a numeric zero, which would incorrectly make missing work look free;
- a comparable metric that omits its semantic boundary.

The full validator additionally requires exactly 15 workload rows, exact frozen v0.29/v0.30 SHAs, an exact CMPCT1 gate SHA, the same source-tree SHA for all three contenders in each row, explicit per-contender storage/creation/whole-read/selective/integrity-resource/recovery/portability blocks, retained losses and semantic asymmetries, hostile review and a valid Genesis decision.

## Claim boundary

This is evidence about **future evidence completeness**, not evidence that ONE wins any performance or storage comparison. The validator cannot prove that a numeric measurement is physically correct; exact-source measurement code, artifacts, tests and hostile review remain required on September 11.

## Strongest caveat

A schema can become harmful if it pressures the benchmark to fabricate quantitative parity where a contender simply lacks an equivalent operation. The contract therefore explicitly permits `unavailable` and richer/different-semantics classifications. The correct response to missing equivalence is disclosure, not a fake zero or an invented proxy metric.
