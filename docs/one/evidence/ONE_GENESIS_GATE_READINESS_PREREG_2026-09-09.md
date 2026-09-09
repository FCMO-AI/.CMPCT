# CMPCT1 / ONE Genesis gate readiness preregistration — 2026-09-09

Experimental state: **ONE-G0.2**  
Branch authority: `research/cmpct1`  
Claim boundary: **gate-readiness infrastructure only; this document and its readiness run are not the 2026-09-11 Genesis decision and may not emit a winner.**

## Mission lock

The remaining pre-gate risk is no longer primarily an isolated Law kernel. It is evidence integrity: the 2026-09-11 decision must compare the best admissible CMPCT1 state with the frozen comparators on the exact same portable 15-workload substrate without benchmark identity drift, comparator drift, or a late harness failure.

Hypothesis: the inherited portable 15-workload substrate can be regenerated from the current CMPCT1 branch with exact historical identities, while independent comparator checkouts remain bound to the frozen Genesis SHAs. If so, the gate can begin from a reproducible input/comparator contract rather than discovering corpus or checkout problems after activation.

Disproof / HOLD readiness if any of the following occurs:

- the regenerated workload set is not exactly 15 rows (10 `neutral_hostile_v1` + 5 `resemblance_hostile_v1`);
- any workload name, file count, logical byte count, or `tree_sha256` differs from the accepted portable identity;
- any of the four repair-v5 neutral rows fails to use its accepted repaired identity;
- either comparator checkout HEAD differs from its frozen Genesis SHA;
- any required comparator benchmark/history authority is absent;
- the readiness harness performs candidate/comparator compression or emits a Genesis winner.

No readiness failure may be repaired by changing expected hashes to newly generated outputs. Identity drift requires diagnosing the producer/substrate and preserving the failure.

## Frozen comparator authority

Per `docs/CMPCT1_GENESIS.md`:

- v0.29/main pivot: `02b8b27cb2d97af7c6e0797984a898e8fa8a8e5d`;
- deferred v0.30 authoritative-integration pivot: `f4b158a55a08b9b18b50e4e4abe4b9251048c772`.

The readiness lane must independently check out those exact commits and verify `git rev-parse HEAD`; branch names or moving refs are insufficient.

## Frozen workload identity

The gate substrate is the portable 15-workload matrix already used by the accepted v0.29 generalization evidence:

- `benchmarks/neutral_hostile_corpus_v1.py`: 10 workloads;
- `benchmarks/resemblance_hostile_corpus_v1.py`: 5 workloads;
- `benchmarks/neutral_hostile_determinism_repair_v5.py`: accepted deterministic repair hooks/normalization for neutral rows;
- historical identity authority: `benchmarks/history/2026-08-16-entropygraph-v028.json`;
- repaired-row authority: `benchmarks/history/2026-08-17-neutral-hostile-determinism-repair-v5.json`;
- accepted portable frontier: `benchmarks/history/2026-08-17-mosaic-v029-generalization-v3.json`.

Exactly four neutral rows replace their older historical tree identities with repair-v5 authority:

- `02_office_workspace`;
- `03_media_library`;
- `05_logs_and_telemetry`;
- `06_incremental_backups`.

All other rows retain their historical identities. The gate must not silently regenerate a different media/office tree and compare systems on unequal bytes.

## Readiness lane scope

The pre-gate readiness program may:

1. regenerate the 15 workload trees once;
2. apply the accepted repair-v5 producer policy and normalization;
3. compute exact file count, logical bytes and repository tree hash for each workload;
4. compare them with the frozen accepted identity;
5. verify the independent v0.29 and v0.30 checkout SHAs;
6. verify required comparator authority files exist;
7. retain a machine-readable manifest of all checks, current CMPCT1 HEAD and authority-file content hashes.

It must **not**:

- run the CMPCT1 encoder on the 15 rows;
- run either frozen comparator encoder on the 15 rows;
- report bytes/CPU/wins/losses for the gate matrix;
- tune ONE using a preview of the final comparator result;
- change any comparator/corpus setting.

This preserves the uninterrupted Genesis research window while removing avoidable infrastructure uncertainty.

## 2026-09-11 decision contract (frozen now, executed later)

At or after the first qualifying activation on 2026-09-11 America/Mexico_City, the actual gate must consume the same generated input instance per row and record, for CMPCT1 and both frozen comparator authorities where the same semantic surface exists:

- exact stored bytes and representation split where available (Law / Surprise / Crystals / metadata);
- creation CPU and elapsed time;
- decode/extract CPU and throughput;
- peak memory or the strongest available directly comparable resource measure;
- selective requested bytes, touched/read bytes and amplification;
- reconstruction work/cone accounting;
- integrity/authentication behavior;
- recovery/failure-blast-radius obligations;
- portability/reader-complexity differences that make a raw size comparison semantically unequal.

The 15 rows are all required. Losses remain visible. A mechanism-level microbenchmark is supporting causal evidence, never a substitute for the full matrix.

The decision is qualitative over an evidence-complete Pareto comparison, exactly as Genesis specifies: keep CMPCT1 primary only if it demonstrates a materially stronger path and credible ability to supersede frozen v0.29 and the deferred v0.30 frontier. Otherwise reactivate v0.30 as the near-term primary line while preserving ONE evidence.

## Hostile reviewer

The most dangerous apparent success would be a smaller aggregate that silently spends more creation CPU, reconstructs unrelated data for selective reads, weakens recovery/integrity, or compares against a different generated tree. Those are failures, not tradeoffs to hide.

The readiness lane therefore intentionally produces no compression result. Its only admissible `decision` values are `READY_FOR_GENESIS_GATE` or `HOLD_GATE_READINESS`.
