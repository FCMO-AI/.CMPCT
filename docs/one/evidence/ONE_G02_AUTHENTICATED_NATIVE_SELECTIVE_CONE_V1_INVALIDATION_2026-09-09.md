# ONE-G0.2 Authenticated Native Selective Cone V1 — scientific invalidation

Date: 2026-09-09
Experimental version: `ONE-G0.2`
Verdict: **INVALIDATED FOR PROMOTION — ACCOUNTING DEFECT, DEBUG ONLY**

## Scope

This invalidation covers the first authenticated-native selective-cone implementation lineage through source `c9ee80dd6f8a768cd3e0db900dea7a9ccf1a9037`, including hosted run `34382432343`, regardless of any eventual workflow conclusion.

## Defect found by hostile review

The first native range-plan adapter accumulated requested source bytes in a `bytearray`, froze that buffer into a second immutable `bytes` object, and then created a third ctypes backing allocation with `from_buffer_copy` before native execution.

Its reported data-movement model charged the logical source read but did not charge those additional full-cone source-plan copies. That violates the preregistered requirement that source-plan preparation and physical/modeled data movement remain inside the selective-open bill.

Because the defect can make the candidate look artificially better on the frozen movement gate, no performance result from this lineage is admissible for `ADVANCE_AUTHENTICATED_NATIVE_SELECTIVE_CONE`.

## Correction

The corrected lineage:

1. keeps exactly one plan-owned `bytearray` backing allocation;
2. exposes that same allocation to ctypes with `from_buffer`, eliminating the extra freeze/copy chain;
3. charges both Program-source reads and source-plan writes;
4. reports proof-coordinate object count explicitly;
5. expands hostile controls to include sibling-digest corruption, proof-coordinate corruption, malformed topology, over-budget Programs, wrong commitments, source corruption, and unsupported Repeat topology.

The frozen CPU and movement thresholds are unchanged. A corrected result may therefore HOLD even if V1 would have appeared to ADVANCE.
