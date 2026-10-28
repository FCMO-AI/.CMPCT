# CMPCT1 / ONE Genesis gate — v0.30 reactivation authority

Date: 2026-09-11  
Decision: **`REACTIVATE_V030_NEAR_TERM`**

This is the v0.30-line handoff of the completed CMPCT1 / ONE Genesis gate. The full immutable-style analysis remains on `research/cmpct1` at `docs/one/evidence/ONE_GENESIS_GATE_RESULT_2026-09-11.md`, introduced by commit `ee14383cd6309d62fed1efba2c92f48ba54ae50f`.

## Frozen gate identities

- ONE-G0.2 candidate: `38f17f4a45686a59a853bf62f0c840e228879e17`
- v0.29: `02b8b27cb2d97af7c6e0797984a898e8fa8a8e5d`
- v0.30: `f4b158a55a08b9b18b50e4e4abe4b9251048c772`

All three have 15/15 same-input rows with exact equality of `(suite, name, files, logical_bytes, tree_sha256)`. Total logical input is `265,969,714 B` for each contender.

## Gate aggregates

| Contender | authenticated stored bytes | stored/logical | sum of per-workload median creation CPU |
|---|---:|---:|---:|
| ONE-G0.2 | 275,219,901 B | 1.034779x | 3.0791 s |
| v0.29 | 137,499,525 B | 0.516974x | 806.5369 s |
| v0.30 | 150,055,575 B | 0.564183x | 33.0603 s |

Density outcomes:

- ONE vs v0.29: ONE `0/15`, v0.29 `15/15`.
- ONE vs v0.30: ONE `0/15`, v0.30 `15/15`.
- v0.29 vs v0.30: v0.29 `6/15`, v0.30 `9/15`.

Creation CPU outcomes:

- ONE beats both mature comparators on `15/15` rows.
- v0.30 beats v0.29 on `15/15` rows.

The gate therefore rejects ONE-G0.2 as the primary near-term line while preserving its large compute-efficiency result as research input.

## Evidence provenance

ONE + v0.29 retained from real-gate run `34573437613`, artifact `10191000395`, digest `sha256:bd9d767874bddf02fcd03d67a6de7ed7a7d1378456e47da2e2f198f7992706ba`.

The original v0.30 measurement failed because the historical worker was not hermetic and then exposed a missing Python `soundfile` dependency. These were harness/environment defects, not product losses. The worker was hardened to source-seal every imported `cmpct` module under the frozen contender checkout and the diagnostic was pinned to its exact event SHA.

The successful source-sealed v0.30 recovery is run `34594599804`, job `103251512822`, artifact `10263288496`, digest `sha256:1e73f88c597bf0e16f60375b2f51c0ec0a79cf8204683adb7c00dde32b44c148`, exact harness `7e14e6867a329bc3281e9016e673c46dc3feb081`. All 15 rows complete and report frozen-source provenance.

## Required operating consequence

v0.30 is reactivated as the **primary near-term research line**. CMPCT1 / ONE remains active secondary research evidence and must not be deleted or rewritten. The frozen gate is not rerun with a newer ONE candidate to change this verdict.

The immediate v0.30 research objective is not merely to repeat v0.29 search. Preserve v0.30's large creation-compute advantage while recovering its remaining density gap through general mechanisms. The first causal map is `docs/V030_REACTIVATION_GENESIS_DEFICIT_MAP_2026-09-11.md`.

Whole-read timing from the gate is retained but not used as decisive supersession evidence because the historical comparator path performs strong verification plus a full extraction while ONE's authenticated read path is structured differently. Do not turn that accounting asymmetry into a speed claim.
