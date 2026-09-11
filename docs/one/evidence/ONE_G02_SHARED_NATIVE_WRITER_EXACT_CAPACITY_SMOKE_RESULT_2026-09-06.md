# ONE-G0.2 shared native writer exact-capacity smoke result — 2026-09-06

Status: **SEMANTIC / COUNT SMOKE PASS; NOT PERFORMANCE OR RESOURCE PROMOTION**

## Mission Lock

Test the hardened metadata-only exact ONE0 wire-size oracle against the current shared native ref-fused writer before integrating exact allocation. The candidate must not widen the writer's accepted input domain merely because exact canonical bytes fit below `ONE_MAX_WIRE`; it must preserve the seed writer's conservative checked-cap rejection boundary.

## Exact-source CI evidence

The exact-source retrigger at commit `83849856406f954af7acd1ba5d735c0c0d54ea47` produced terminal GitHub Actions evidence:

- workflow: `ONE-G0.2 exact wire-size smoke`
- run: `34060247662`
- job: `101559367926`
- conclusion: **success**
- strict compilation: `cc -std=c11 -O2 -Wall -Wextra -Werror`
- terminal smoke line: `exact wire-size parity: PASS (1004 accepted plans + hostile rejection parity)`

The accepted matrix covered fixed mixed Ref/Surprise, disabled full-Surprise, all-Surprise, 1,000 deterministic pseudo-random valid partitions, and a >4,096-segment hierarchy case. Hostile rejection coverage included unknown kind, zero-length segment, and incomplete coverage.

This establishes exact canonical byte-count / Surprise-byte / hierarchy-depth / node-count parity over the exercised accepted plans plus the exercised rejection cases. It does **not** establish elapsed, requested-capacity, RSS, or peak-memory promotion.

## Hostile Reviewer hardening after the PASS

Review found that the smoke above still did not directly instantiate the exact acceptance-domain bug class that motivated the oracle hardening: a plan whose canonical ONE0 wire would fit beneath the 128 MiB wire ceiling while the seed writer's deliberately loose requested capacity exceeds the ceiling and therefore rejects.

Commit `1ff08dfe864ae55a52310b6a3c460a10d727176f` adds that explicit cap-drift hostile case to `.github/workflows/one-g02-exact-wire-size-smoke.yml`:

- source length: 64 MiB
- target length: 64 MiB
- one full-target Ref segment
- expected: both seed writer and exact-size oracle reject before payload dereference because seed checked-cap is authoritative for the current acceptance domain.

At handoff, broad Actions activity existed for `1ff08dfe...`, but no exact `ONE-G0.2 exact wire-size smoke` run was present in the commit workflow-run listing. Therefore the new cap-drift case is **committed but not yet exact-source CI-authoritative**. Do not inherit the earlier PASS onto this stronger hostile case.

## Decision

1. The original exact-size oracle semantic/count smoke is a real PASS.
2. No exact-capacity speed/resource promotion is authorized yet.
3. The strengthened acceptance-domain hostile case must obtain its own exact-source terminal run.
4. Only after that passes should the exact allocator be integrated into a frozen shared-writer A/B that charges exact-size bookkeeping inside the timed candidate and reports requested capacity, emitted/touched bytes, elapsed, and robust peak-resident memory when available.
5. Preserve the preregistered gates; do not rescue a weak result with size/density thresholds or allocator-specific classifiers.

## Causal interpretation

The experiment remains worth testing because once segments and hierarchy metadata are known, exact canonical ONE0 length is derived information. If the candidate wins, the gain comes from removing speculative allocation slack, not from adding a new Law, reader opcode, discovery mechanism, or semantic exception. If requested-capacity savings fail to translate into real memory benefit or cost more than the preregistered elapsed allowance, reject the lane cleanly.
