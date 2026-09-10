# CMPCT1 / ONE Genesis executor preflight handoff — 2026-09-10

Status: **pre-gate infrastructure only; no Genesis contender encoding or scoring executed**

Experimental lineage: `ONE-G0.2`

## Mission lock

Before the September 11 Genesis gate, remove execution-time degrees of freedom without observing the gate result.

Falsifiable hypothesis:

> A small fail-closed preflight can bind the exact CMPCT1 candidate to the checked-out commit, verify the frozen 15-workload and v0.29/v0.30 authorities, preserve the preregistered execution order, and remain incapable of performing contender encoding/scoring merely because the calendar boundary opens.

Disproof conditions include any of:

- a non-hex or mismatched candidate SHA is accepted;
- the frozen 15-workload authority is missing/substituted yet preflight reports ready;
- either frozen comparator SHA or its admissibility rules drift without a HOLD;
- September 11 clock opening itself causes contender execution/scoring;
- a result/winner claim is emitted by preflight.

## Implementation

`benchmarks/one/one_genesis_gate_executor_preflight.py` now:

- requires the exact frozen v0.29 SHA `02b8b27cb2d97af7c6e0797984a898e8fa8a8e5d`;
- requires the exact frozen v0.30 SHA `f4b158a55a08b9b18b50e4e4abe4b9251048c772`;
- binds readiness to source `070d4f803c7b4441f517fc5c0b90f19214f5b05f` and artifact digest `sha256:a1b009dfed8deeed3a9d46ab0cc4cdaf224141c903b2c8bdcdeae32434074abd`;
- checks the frozen workload identity manifest is exactly 15 rows with the 10/5 suite split;
- checks the frozen comparator authority and its anti-posthoc/admissibility rules;
- hashes all required gate authority files into the plan;
- requires the candidate SHA to equal the actual checkout HEAD;
- records the preregistered execution order;
- records the America/Mexico_City gate clock state;
- always reports contender/comparator encoding, scoring and winner selection as false because this program has no execution path for them.

The clock is deliberately informational permission state only. A 2026-09-11 timestamp does not transform this preflight into the gate executor.

## Hostile tests

`tests/one/test_genesis_gate_executor_preflight.py` attacks:

1. exact current-HEAD binding before the gate;
2. the date boundary itself, proving it changes `gate_open` but executes nothing;
3. a valid-looking 40-hex SHA that differs from checked-out HEAD;
4. a malformed/non-hex candidate identity.

The existing Genesis result-contract lane now covers these tests together with the final-result structural validator and runs the CI-topology ratchet for its own workflow.

## Claim boundary / remaining debt

This work does **not** establish that a complete three-contender measurement executor exists.

Still required before/at the qualifying September 11 activation:

1. a single execution path that consumes the sealed candidate + exact shared workload trees;
2. measurement adapters for CMPCT1, frozen v0.29 and frozen v0.30 under the same boundaries;
3. creation CPU/wall/RSS, stored bytes, whole-read, selective/access/resource and semantic evidence collectors;
4. raw-output persistence before interpretation;
5. assembly into `cmpct-one-genesis-gate-result-v1`;
6. final fail-closed validation and hostile adjudication.

Do not call the preflight an end-to-end gate executor. Its value is narrower: it prevents candidate/authority drift and accidental pre-gate result observation while making the eventual executor consume an explicit sealed plan.

## Evidence status

The source-bearing workflow run for the new preflight contract was queued when this handoff was written. A queued/pending/source-mismatched run is not a passing receipt. Only an exact-source completed run may be cited as hosted validation.
