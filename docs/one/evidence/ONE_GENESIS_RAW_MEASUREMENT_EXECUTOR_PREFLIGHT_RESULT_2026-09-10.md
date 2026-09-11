# ONE Genesis raw-measurement executor preflight result — 2026-09-10

Status: **ADVANCE_PLUMBING_ONLY**  
Experimental line: **ONE-G0.2**  
Scientific claim boundary: **not Genesis compression/performance evidence**

## Mission lock

Hypothesis: the Genesis gate can use one sealed execution substrate that binds the current CMPCT1 candidate and frozen v0.29/v0.30 authorities to the exact 15-workload identity, persists raw contender outputs independently, and joins those outputs without performing comparison, scoring, or winner selection. Before the calendar gate, only a permanently synthetic fixture path may execute.

Disproof conditions included any of the following:

- real contender execution possible before 2026-09-11 America/Mexico_City;
- calendar opening alone starts execution;
- fixture inputs can smuggle real adapters/work roots;
- candidate/comparator source binding is not exact;
- raw rows can drift from the frozen workload identity;
- a required measurement family can disappear silently;
- synthetic output can claim production eligibility;
- the joined artifact performs or claims comparison/scoring/winner selection.

## Builder result

Added:

- `benchmarks/one/one_genesis_gate_measurement_executor.py`
- `tests/one/test_genesis_gate_measurement_executor.py`
- hosted coverage in `.github/workflows/cmpct1-one-genesis-gate-result-contract.yml`

The executor:

1. reuses the canonical `build_plan()` preflight rather than duplicating candidate/comparator authority;
2. fixes contenders to `cmpct1`, `v0.29`, and `v0.30`;
3. requires exactly the 15 frozen workload identities from `genesis_gate_workload_identity_v1.json`;
4. rejects real execution before 2026-09-11 local time;
5. still requires explicit `--execute-real-gate` after the calendar opens;
6. requires real adapters to bind each checkout to its sealed source SHA;
7. persists each contender raw JSON before attempting the next contender;
8. requires `stored_bytes`, `creation`, `whole_read`, `selective_access`, `semantics`, and `reader_burden` in every raw row;
9. joins raw measurements only, with `comparisons_executed=false`, `scoring_executed=false`, and `winner_selected=false`.

The synthetic fixture is permanently marked `synthetic=true` and `production_eligible=false`; its placeholder values are plumbing data only and are forbidden from scientific interpretation.

## Hosted falsifier authority

Exact source containing the executor tests and CI fixture exercise:

`c5c1b28c87134f52c8f9f62e9335bd5a8297ea61`

Hosted workflow:

- workflow: `CMPCT1 ONE Genesis gate result contract`
- run: `34454558855`
- job: `102797813941`
- conclusion: `success`
- artifact: `10142910644`
- artifact digest: `sha256:0fd9b9d8f533151e1aef0f913eed0c2eccca6acdc03f55aebe2f7895f35938b0`

The hosted job passed:

- exact-source binding;
- CI-topology validation;
- gate-result validator tests;
- executor-preflight tests;
- raw-measurement executor tests;
- the explicit pre-gate fixture-plumbing invocation;
- receipt retention/upload.

No Genesis contender encoding, comparison, scoring, or winner selection was executed by this lane.

## Hostile reviewer / remaining debt

This is **not yet the complete Genesis gate executor**.

The largest remaining blocker is the real adapter layer. Before the first qualifying 2026-09-11 activation, the implementation still needs a mechanically unambiguous path from the sealed 15 input trees into each contender's actual encode/read/selective/resource measurement surface.

Two hardening items remain especially important:

1. the executor should independently generate/recompute the physical work-root identities before invoking any real adapter, rather than relying only on an adapter to report the frozen identity back correctly;
2. raw measurement validation should be deepened so malformed nested metrics and fake zero/unavailable values fail as early as they already do in the final result validator.

Until those are closed, the correct status is `ADVANCE_PLUMBING_ONLY`, not `READY_TO_SCORE_GENESIS` and not a CMPCT1 win.

## Comparator authority

Frozen comparators remain unchanged:

- v0.29: `02b8b27cb2d97af7c6e0797984a898e8fa8a8e5d`
- v0.30: `f4b158a55a08b9b18b50e4e4abe4b9251048c772`

The 15-workload readiness authority remains:

- source: `070d4f803c7b4441f517fc5c0b90f19214f5b05f`
- artifact: `10134884441`
- digest: `sha256:a1b009dfed8deeed3a9d46ab0cc4cdaf224141c903b2c8bdcdeae32434074abd`

## Next decisive action

Close physical-input sealing and real contender adapters, using synthetic/transfer fixtures only while the calendar gate is closed. Do not run the final 15-workload contender comparison early. Once the first qualifying 2026-09-11 activation begins, seal the then-best eligible CMPCT1 SHA and use the same raw-measurement path to produce immutable raw evidence before any adjudication.
