# CMPCT1 / ONE Genesis gate readiness — authority reconciliation

Date: 2026-09-09  
Experimental state: **ONE-G0.2**  
Branch authority: `research/cmpct1`  
Claim boundary: **benchmark-substrate authority correction only; no Genesis scoring, encoding or winner claim.**

## Decision

The initial gate-readiness preregistration incorrectly named `neutral_hostile_determinism_repair_v5.py` and its repair-v5 history as the portable neutral/hostile substrate authority, while simultaneously stating that readiness must reproduce the substrate already used by the accepted v0.29 generalization evidence.

Those two statements conflict. The accepted v0.29 generalization authority predates this readiness work and explicitly consumes **repair-v6**, not repair-v5, for five neutral/hostile rows. Repair-v6 adds the developer-repository workload to the four repair-v5 rows by replacing host-GCC/linker-dependent ELF fixtures with compiler-independent deterministic ELF64 fixtures.

Therefore readiness is corrected to consume the already-accepted repair-v6 authority. No expected hash is updated from a newly observed output, no candidate/comparator setting changes, and the failed repair-v5 readiness result remains preserved.

## Evidence that exposed the stale pointer

Readiness source:

- `67e88ec2b0e0f9364cda9ac69be91d412882232b`
- workflow run: `34416253168`
- job: `102681679163`
- artifact: `10129267858`
- artifact digest: `sha256:3c94f79bcda2c28b4f2ba43402bca771fb077c34202158b5bb1509eadadfc883`

The lane successfully:

- generated all **15** required workloads;
- checked out frozen v0.29 exactly at `02b8b27cb2d97af7c6e0797984a898e8fa8a8e5d`;
- checked out frozen v0.30 exactly at `f4b158a55a08b9b18b50e4e4abe4b9251048c772`;
- installed the deterministic media dependency;
- performed **no candidate encoding, comparator encoding or gate scoring**.

It then emitted `HOLD_GATE_READINESS` because one row differed:

`neutral_hostile_v1/01_developer_repository`

- file-count equality: **PASS** (`1266`);
- logical-byte equality: **PASS** (`2,624,373`);
- generated tree under repair-v5: `ddcdf1ae1b61042634aae40b1b12da629feb98cb45db23c56d1da15334b74645`;
- expected tree supplied by the accepted v0.29 generalization authority: `d1706c497de75764b6bd0f49c5d8bdde251694eea40fc683dcbbfed5027c2f49`.

This is not evidence that the accepted substrate drifted. `ddcdf1...` is the older developer-repository identity produced before repair-v6 canonicalized its two compiler/linker-dependent ELF binaries. The readiness program was generating the wrong already-superseded producer identity while comparing it to the correct accepted v0.29 identity.

## Pre-existing repair-v6 authority

The durable authority is:

- producer: `benchmarks/neutral_hostile_determinism_repair_v6.py`;
- accepted history: `benchmarks/history/2026-08-19-neutral-hostile-determinism-repair-v6.json`;
- accepted generalization consumer: `benchmarks/mosaic_v029_generalization_bench.py`.

Repair-v6 was accepted before Genesis readiness was authored. Its history records:

- two independent GitHub-runner authorities;
- exact per-file manifest equality;
- repeat-build equality;
- exact inherited v0.28 measurement equality;
- unchanged requirements/producer policy across the independent runs;
- no cross-run identity differences;
- `accepted: true`.

Its five repaired neutral rows are:

1. `01_developer_repository`;
2. `02_office_workspace`;
3. `03_media_library`;
4. `05_logs_and_telemetry`;
5. `06_incremental_backups`.

The developer row's accepted repair-v6 identity is exactly:

- files: `1266`;
- logical bytes: `2,624,373`;
- tree SHA-256: `d1706c497de75764b6bd0f49c5d8bdde251694eea40fc683dcbbfed5027c2f49`.

## Authority resolution

The intended readiness law was always “reproduce the already-accepted portable substrate used by v0.29 generalization.” The stale repair-v5 filename in the readiness preregistration cannot override the older accepted substrate it purported to reference.

Accordingly:

- preserve `ONE_GENESIS_GATE_READINESS_PREREG_2026-09-09.md` unchanged as historical preregistration evidence;
- preserve failed run `34416253168` and its artifact unchanged;
- update the readiness implementation to use repair-v6 producer/history authority;
- require the existing v0.29 checkout to contain the repair-v6 accepted history;
- do **not** change any expected per-row identity value manually;
- derive expected rows through the same `_preserved_rows()` authority already used by `mosaic_v029_generalization_bench.py`;
- re-run readiness under the same non-scoring constraints.

This is an evidence-hygiene repair, not benchmark rehabilitation. If repair-v6 regeneration still fails any accepted identity, readiness remains HOLD and the new drift must be diagnosed independently.

## Genesis boundary unchanged

This reconciliation does not authorize the September 11 gate early. The readiness lane remains forbidden from:

- encoding any of the 15 workloads with CMPCT1;
- encoding them with frozen v0.29 or v0.30;
- computing size/speed wins or losses;
- emitting a Genesis winner;
- changing locality, integrity, recovery, resource, portability or semantic requirements.

The only admissible outcome remains `READY_FOR_GENESIS_GATE` or `HOLD_GATE_READINESS`.
