# ONE-G0.2 native selective Repeat bulk — result

Date: 2026-09-09  
Decision: **HOLD_NATIVE_SELECTIVE_REPEAT_BULK**

## Mission / Referee

The frozen rehabilitation question was whether the V1 selective Repeat HOLD could be repaired causally by removing its two measured cost owners without changing ONE representation or semantics:

1. eliminate full-cone source repacking for direct `Repeat(Surprise)` cones;
2. replace O(cone/period) Python terminal commands with one bounded periodic execution descriptor.

Frozen authority: `docs/one/evidence/ONE_G02_NATIVE_SELECTIVE_REPEAT_BULK_PREREG_2026-09-09.md`.

The V1 economic gates remained unchanged: median candidate/comparator CPU <= `0.75x`, every row <= `1.10x`, median modeled movement <= `1.00x`, exact semantics/authentication/cone geometry, fixed-cone root independence, bounded temporary state, and explicit physical proof that source-plan repacking disappeared.

## Exact evidence authority

- branch: `research/cmpct1`
- exact source: `fcfd4236db6e4dee5a66ca1cafd247c5ef763021`
- experimental state: `ONE-G0.2`
- workflow: `CMPCT1 ONE-G0.2 native selective Repeat bulk`
- run: `34410921999`
- job: `102664922101`
- artifact: `10127255391`
- artifact digest: `sha256:14d20aa3d55638b69352dd913be7217e742594399f18d1197c50c4e1d84a681d`
- retained JSON: `native-selective-repeat-bulk.json`
- exact-source semantic suite: **64 passed**

The prior run `34405938087` at source `08cfec6f07f087ad5adb8eab527274b4bf9c9111` is not economic evidence: two stale/invalid test contracts blocked the benchmark. One sliced-root test declared `max_output_bytes=8192` while storing a valid 16 KiB Repeat node, so global preflight correctly rejected it; one inherited test still required four Repeat commands although the preregistered rehabilitation explicitly requires one periodic descriptor. Those harness contracts were repaired without changing the candidate, matrix, comparator, thresholds, or benchmark law. Run `34410921999` is the first admissible result-bearing V2 run.

## Frozen result

The rehabilitation succeeds on its causal physical targets and on the median economics, but fails the frozen worst-row CPU gate.

| Gate | Result |
| --- | ---: |
| exact semantics / authentication | **PASS** |
| cone geometry exact | **PASS** |
| fixed-cone independence from root growth | **PASS** |
| zero full-cone source-plan packing | **PASS** |
| one periodic descriptor | **PASS** |
| temporary-state bounds | **PASS** |
| median candidate / comparator CPU <= 0.75x | **0.583286x — PASS** |
| worst candidate / comparator CPU <= 1.10x | **1.417414x — FAIL** |
| median candidate / comparator movement <= 1.00x | **1.000000x — PASS** |

Therefore the unconditional bulk backend remains a **HOLD**.

## What the rehabilitation proved

V1's identified owners were real. Removing them changed the economics dramatically:

- V1 median CPU: `2.059911x` comparator;
- V2 bulk median CPU: **`0.583286x` comparator**;
- V1 median movement: `1.329897x` comparator;
- V2 bulk median movement: **`1.000000x` comparator**;
- direct periodic positive rows now retain `packed_source_bytes = 0` and `source_plan_write_bytes = 0`;
- every positive row uses exactly **one periodic descriptor**.

So V2 is not a failed causal theory. It removes the measured duplication and turns Repeat from a median ~2.06x slowdown into a median ~1.71x speedup while preserving exact authenticated cone semantics.

## Why the unconditional backend still fails

The remaining loss is topology/economics dependent, not a correctness or locality problem.

The strongest rows are small-period repetitions, where the generic comparator repeatedly expands a tiny basis:

- 32-byte basis rows are commonly around `0.16x–0.31x` comparator CPU;
- 64-byte basis rows are commonly around `0.27x–0.49x`;
- 256-byte basis rows range roughly `0.67x–0.90x`.

At a 4096-byte basis, however, the generic Python bytes path already has essentially one period per 4 KiB authenticated cone and is extremely cheap. The native periodic call therefore becomes pure fixed overhead. The worst observed row is the 32 KiB root / first-64 request with 4096-byte basis at **`1.417414x` comparator CPU**. Other 4096-byte-basis rows remain roughly `1.18x–1.37x`.

This falsifies the idea that direct periodic Repeat should always use the native bulk backend.

## Hostile review

Do **not** weaken the `1.10x` every-row gate. The worst-row loss is real and repeatable enough to matter.

Do **not** add a reader-visible Repeat codec/opcode or encode a backend choice into ONE storage. The stored representation is already correct.

Do **not** keep optimizing the periodic kernel merely to force native execution everywhere. Python's bytes repetition/slicing path is itself optimized native code and is the right comparator for large-period/small-repeat cones.

The useful result is stronger: ONE should choose the cheapest execution backend for the same already-validated reconstruction Law. Backend selection is execution policy, not representation pluralism.

## Next decisive action

Move from an unconditional native Repeat backend to a **generic cost-based reader admission rule**.

The next experiment must be preregistered before observing its held-out matrix and should test a causal cost model rather than hand-tuning a threshold to this table. The model should compare bounded fixed native-call/planning cost against the generic work implied by the number of period fragments/repetitions inside the authenticated cone. It should:

- preserve one stored `Repeat` representation and exact semantics;
- choose native bulk only when estimated work amortizes its fixed overhead;
- preserve the generic comparator for cheap large-basis cases;
- evaluate additional unseen period sizes around the crossover, not only the four V1/V2 bases;
- require selector overhead to be negligible and every selected result to preserve the existing CPU/movement/locality/resource gates.

With the September 11 Genesis gate approaching, this adaptive execution policy should be treated as secondary to full 15-workload gate readiness. Repeat is already correct through the generic reader; the unresolved question is only which backend is cheapest for each cone.

## Campaign status

Frozen comparator authorities remain unchanged:

- v0.29: `02b8b27cb2d97af7c6e0797984a898e8fa8a8e5d`
- deferred v0.30: `f4b158a55a08b9b18b50e4e4abe4b9251048c772`

This HOLD changes no format, Law, Surprise semantics, integrity rule, recovery rule, portability rule, or Genesis gate requirement.
