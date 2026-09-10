# CMPCT1 / ONE Genesis gate readiness — authority reconciliation

Date: 2026-09-09  
Experimental state: **ONE-G0.2**  
Branch authority: `research/cmpct1`  
Claim boundary: **benchmark-substrate/comparator authority correction only; no Genesis scoring, encoding or winner claim.**

## Decision

The initial gate-readiness preregistration pointed at repair-v5 while the current accepted portable substrate lineage used by the later v0.29 generalization authority is repair-v6. The first readiness attempt therefore regenerated the older developer-repository identity while comparing it with the accepted repair-v6 identity.

A first reconciliation correctly changed the **shared input substrate** to repair-v6, but then over-bound the **frozen v0.29 checkout** by requiring that old commit to contain the later repair-v6 history file. Exact run `34431496719` exposed that second bookkeeping error: all 15 current substrate identities matched exactly and the v0.29 SHA itself matched exactly, but readiness remained HOLD solely because `benchmarks/history/2026-08-19-neutral-hostile-determinism-repair-v6.json` does not exist inside frozen v0.29 commit `02b8b27...`.

The correct model is two independent authorities:

1. **Shared gate input authority:** current accepted repair-v6 substrate. Every contender will consume these same exact live trees on September 11.
2. **Frozen comparator authority:** each comparator's frozen code/history at its recorded SHA. A historical comparator does not need to contain a future substrate receipt in order to encode the shared live tree fairly.

No expected workload hash, comparator SHA, scoring rule, candidate setting or semantic requirement is changed by this reconciliation.

## First HOLD: stale repair-v5 producer

Readiness source:

- `67e88ec2b0e0f9364cda9ac69be91d412882232b`
- workflow run: `34416253168`
- job: `102681679163`
- artifact: `10129267858`
- artifact digest: `sha256:3c94f79bcda2c28b4f2ba43402bca771fb077c34202158b5bb1509eadadfc883`

The lane generated all 15 workloads, checked out both frozen SHAs exactly, performed no candidate/comparator encoding or scoring, and then found one identity mismatch:

`neutral_hostile_v1/01_developer_repository`

- file count: **1266 == 1266**;
- logical bytes: **2,624,373 == 2,624,373**;
- repair-v5 generated tree: `ddcdf1ae1b61042634aae40b1b12da629feb98cb45db23c56d1da15334b74645`;
- accepted repair-v6 tree: `d1706c497de75764b6bd0f49c5d8bdde251694eea40fc683dcbbfed5027c2f49`.

Repair-v6 exists specifically because the prior developer fixture retained host compiler/linker nondeterminism. It canonicalizes the affected ELF fixtures while preserving workload meaning.

## Second HOLD: comparator checkout over-bound to future history

Reconciled readiness source:

- `6c835382d62222e5773b82bfa0ff64d2dd7bc1b6`
- workflow run: `34431496719`
- job: `102727769619`
- artifact: `10134775858`
- artifact digest: `sha256:98cc4d00d156b136316396b0a4e27a37bbd207434c0f4172d593db755fa62964`

This run establishes an important positive fact:

- observed workloads: **15**;
- all 15 exact identities: **PASS**;
- frozen v0.29 observed HEAD: exact `02b8b27cb2d97af7c6e0797984a898e8fa8a8e5d`;
- frozen v0.30 observed HEAD: exact `f4b158a55a08b9b18b50e4e4abe4b9251048c772`;
- v0.30 checkout authority: **PASS**;
- candidate encoding: **false**;
- comparator encoding: **false**;
- scoring: **false**.

The only failure was that `REQUIRED_V029` demanded the repair-v6 history file inside `02b8b27...`.

Inspection of the frozen v0.29 harness at that exact SHA proves why this requirement is invalid: its own `mosaic_v029_generalization_bench.py` explicitly references repair-v5 and `2026-08-17-neutral-hostile-determinism-repair-v5.json`. The later repair-v6 portable-substrate receipt is current gate-input authority, not historical content of that frozen comparator commit.

## Pre-existing repair-v6 input authority

Current shared substrate authority is:

- producer: `benchmarks/neutral_hostile_determinism_repair_v6.py`;
- accepted history: `benchmarks/history/2026-08-19-neutral-hostile-determinism-repair-v6.json`;
- current preserved-row consumer: `benchmarks/mosaic_v029_generalization_bench.py`.

Its acceptance record predates this readiness correction and records two independent runner authorities, exact per-file manifest equality, repeat-build equality, inherited v0.28 measurement equality, stable producer policy and no identity differences.

Repair-v6 covers five neutral rows:

1. `01_developer_repository`;
2. `02_office_workspace`;
3. `03_media_library`;
4. `05_logs_and_telemetry`;
5. `06_incremental_backups`.

The developer row's accepted identity is:

- files: `1266`;
- logical bytes: `2,624,373`;
- tree SHA-256: `d1706c497de75764b6bd0f49c5d8bdde251694eea40fc683dcbbfed5027c2f49`.

## Frozen v0.29 authority

Frozen comparator SHA remains exactly:

`02b8b27cb2d97af7c6e0797984a898e8fa8a8e5d`

Its required internal evidence should be files that actually define/check that frozen comparator, including its historical repair-v5 input receipt. The gate does **not** reuse v0.29's historical input as the shared September 11 input. Instead, the frozen engine is executed against the same current repair-v6 live trees as ONE and v0.30.

This preserves both requirements simultaneously:

- comparator implementation/history is frozen;
- gate input is identical across all contenders.

## Authority resolution

Accordingly:

- preserve `ONE_GENESIS_GATE_READINESS_PREREG_2026-09-09.md` unchanged;
- preserve both failed readiness artifacts unchanged;
- use repair-v6 producer/history as **current shared substrate authority**;
- require frozen v0.29 checkout to equal its exact SHA and contain its own historical v0.29 benchmark/evidence files, not a later repair-v6 receipt;
- keep frozen v0.30 checkout requirements unchanged;
- do **not** alter any expected per-row tree identity manually;
- continue deriving current expected rows through the already-accepted current preserved-row authority;
- re-run readiness under the same non-scoring constraints.

This remains evidence hygiene rather than benchmark rehabilitation. Any subsequent identity, SHA or required-comparator failure remains a HOLD until independently explained.

## Genesis boundary unchanged

This reconciliation does not authorize the September 11 gate early. The readiness lane remains forbidden from:

- encoding any of the 15 workloads with CMPCT1;
- encoding them with frozen v0.29 or v0.30;
- computing size/speed wins or losses;
- emitting a Genesis winner;
- changing locality, integrity, recovery, resource, portability or semantic requirements.

The only admissible readiness outcome remains `READY_FOR_GENESIS_GATE` or `HOLD_GATE_READINESS`.
