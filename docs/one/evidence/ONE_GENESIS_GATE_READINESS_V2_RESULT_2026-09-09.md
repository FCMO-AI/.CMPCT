# CMPCT1 / ONE Genesis gate readiness V2 — result

Date: 2026-09-09 America/Mexico_City  
Experimental state: **ONE-G0.2**  
Decision: **READY_FOR_GENESIS_GATE**  
Claim boundary: **input/comparator readiness only; no candidate or comparator encoding/scoring was performed and this is not the September 11 Genesis decision.**

## Exact hosted authority

- branch: `research/cmpct1`
- exact evidence source: `1bc001537b080853e95678ce98332650577b3974`
- workflow: `CMPCT1 ONE Genesis gate readiness V2`
- run: `34420027297`
- job: `102693207010`
- artifact: `10130610542`
- artifact name: `one-genesis-gate-readiness-v2-1bc001537b080853e95678ce98332650577b3974`
- artifact digest: `sha256:49de9d979e981ffa8aec27c10c7b5a90d69fcaa02ffd2731facf8412a131bb28`

The hosted job completed successfully after exact-source checkout, independent checkout of both frozen comparators, deterministic media dependency installation, repair-v6 corpus regeneration, exact identity comparison, explicit non-scoring assertions and artifact retention.

## Frozen result

The V2 manifest emits:

- `decision = READY_FOR_GENESIS_GATE`;
- `workloads = 15`;
- `identity_exact = true`;
- `v029_exact = true`;
- `v030_exact = true`;
- `errors = []`;
- `scoring_executed = false`;
- `candidate_encoding_executed = false`;
- `comparator_encoding_executed = false`.

Frozen comparator checkout authority remained exactly:

- v0.29: `02b8b27cb2d97af7c6e0797984a898e8fa8a8e5d`;
- v0.30: `f4b158a55a08b9b18b50e4e4abe4b9251048c772`.

The neutral substrate is bound to accepted `neutral-hostile-repair-v6`. The developer workload reproduced exact accepted tree SHA:

`d1706c497de75764b6bd0f49c5d8bdde251694eea40fc683dcbbfed5027c2f49`

No expected workload hash was changed to achieve this pass.

## Why V2 was necessary

V1 readiness exposed two independent infrastructure/substrate defects before the gate rather than allowing them to contaminate September 11:

1. initial hosted readiness lacked `ffmpeg`, so the deterministic media producer could not run;
2. after installing that dependency, V1 reproduced 14/15 workload identities but `01_developer_repository` differed in `tree_sha256` while file count and logical bytes were identical.

The second failure was traced to an internally inconsistent readiness harness. Its expected identities came from the current accepted v0.29 generalization authority, which had already moved to accepted repair-v6, while neutral generation was still explicitly bound to repair-v5. Repair-v6 exists specifically because repair-v5 retained host GCC/linker provenance inside two developer ELF fixtures.

V2 did not update the expected developer hash. It changed generation to use the same pre-existing accepted repair-v6 authority that already supplied the expected identity. This produced the exact accepted v6 tree on the hosted runner.

## Hostile review

This result must not be overinterpreted:

- it says nothing about whether ONE beats v0.29 or v0.30;
- it contains no compression ratios, creation timings, read timings or gate win/loss rows;
- it does not prove the future scored harness is complete;
- it does not remove the requirement to charge integrity, recovery, locality, memory and reader complexity in the final decision.

Its value is narrower and important: the input substrate and comparator revisions needed by the gate are now independently reproducible before any scoring begins.

## Next decisive action

Use `docs/one/evidence/ONE_GENESIS_GATE_MEASUREMENT_CONTRACT_2026-09-09.md` and the fail-closed dossier validator to finish the non-scoring measurement topology before September 11. The actual scored 15-workload same-input comparison remains reserved for the first qualifying activation on 2026-09-11 America/Mexico_City.
