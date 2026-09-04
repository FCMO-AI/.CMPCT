# Logs restore inner attribution result

Status: **ACCEPTED D2 CAUSAL EVIDENCE / TWO MATERIAL RESTORE OWNERS / ZERO RELEASE CREDIT**

This record preserves the completed result-bearing portion of the frozen experiment in `R25_LOGS_RESTORE_INNER_ATTRIBUTION_PREREG.md`. The workflow's measurement, exact reconstruction checks, terminal-decision ratchet, public-surface guard, and artifact upload all completed successfully. A later CI-topology self-check failed for a workflow-concurrency policy defect; that custody failure does not erase the already-uploaded scientific receipt and is tracked separately below.

## Authority

- authoritative branch: `agent/v030-authoritative-integration`
- exact result-bearing source: `b35b4c9bb6e0411201ca57662068c7e7f5b187d2`
- workflow: `CMPCT v0.30 Logs restore inner attribution`
- workflow run: `33682650426`
- substantive job: `100422611260` (`restore-inner`)
- artifact id: `9866941125`
- artifact: `v030-logs-restore-inner-b35b4c9bb6e0411201ca57662068c7e7f5b187d2`
- artifact digest: `sha256:9a42d1312f75694500688e723c767a271f1b337e94efac89babe66ec8e14f24c`
- schema: `cmpct-v030-logs-restore-inner-attribution-v1`
- target: `neutral_hostile_v1/05_logs_and_telemetry`
- rounds: **11** alternating control/instrumented pairs
- release credit: **false**

The artifact was recovered and inspected directly. The run's benchmark step and frozen contract ratchet both passed before the later topology-only failure.

## Exact identity and instrumentation validity

- selected representation: `logs-inverse`
- archive bytes: **3,550,343 B**
- archive SHA-256: `ab49befb40e4d288a9fc8ff4ce128a512988b97c955077dfb97d4bc1a29f7772`
- canonical user tree SHA-256: `f4c45f8df5ab7e5406a064194cfb71bd9c43533fd84dc09273b5df7705d32751`
- strong verification: **pass**
- canonical filesystem semantics: **verified**
- max decode unit: **7,354,596 B**
- max member read amplification: **3.002135695x**
- exact output across all measured extractions: **true**
- call counts stable: **true**
- control median: **0.046398962 s**
- instrumented median: **0.046428685 s**
- instrumentation wall ratio: **1.000640596x**
- frozen maximum instrumentation ratio: **1.10x**

Instrumentation therefore added only about **0.0641%** median wall time and is valid for the frozen causal interpretation.

## Exact inner attribution

| Restore sub-boundary | Median time | Share of total instrumented extraction | Material? |
|---|---:|---:|---|
| authenticated pack materialization | **0.014730192 s** | **31.7265%** | yes |
| inverse decode | **0.013365921 s** | **28.7881%** | yes |

The frozen materiality floor was both **>=2 ms absolute** and **>=5% of total extraction**. Both owners cross it by wide margins.

Observed stable call counts were:

- pack materialization: **7 calls** per extraction;
- inverse decode: **3 calls** per extraction.

The instrument also recorded predecessor-scale restore median **0.026265138 s** and no positive predecessor-scale unattributed restore remainder after these tracked boundaries under this exact instrument.

Frozen terminal decision:

**`PACK_MATERIALIZATION_HEADROOM+INVERSE_DECODE_HEADROOM`**

## Causal interpretation

The preceding accepted phase attribution localized roughly **82.8%** of Logs extraction wall inside authenticated restore. This experiment moves one level inward and shows that the restore cost is not a single monolithic decode bottleneck. Two distinct implementation boundaries are material in the exact promoted path:

1. authenticated pack materialization / pack access;
2. inverse transformation decode.

Neither boundary alone owns a majority of total extraction. A one-knob optimization campaign aimed only at decode would therefore leave a similarly sized pack-materialization cost behind. The lowest-sufficient next Forge work should preserve the security and exact reconstruction contract while testing whether pack materialization can be fused/reused/avoided and whether inverse decode can be accelerated independently; promotion should be judged on complete Logs extraction, not on a local microbenchmark.

This result does **not** authorize removing authentication, weakening recovery, widening locality/decode-unit bounds, changing archive bytes, changing the comparator, or treating either tracked subphase as borrowable correctness/security debt.

## Custody defect and repair requirement

The workflow terminated red only after the result-bearing steps because `tools/check_ci_topology.py` found that the automatic deep workflow lacked a top-level concurrency group and a recognized preserved-receipt exact-SHA policy. The scientific artifact remains accepted scoped evidence, but the workflow must be repaired before a later rerun can be considered globally green.

Do not rerun this experiment merely to seek different timings. A topology-only rerun is custody validation; the causal result above remains frozen unless the semantic path or instrument materially changes.

## Forge decision

Preserve both owners as active Logs rehabilitation targets. Prefer a bounded intervention that attacks pack materialization without changing authenticated semantics, then price complete-product extraction. In parallel, evaluate a locality-neutral inverse-decode acceleration only if it preserves exact bytes/tree and hostile corruption rejection. Do not collapse this scoped two-owner result into a claim that Logs overall is solved.
