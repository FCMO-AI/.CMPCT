# ONE-G0.2 native selective Repeat lowering — result

Date: 2026-09-09  
Decision: **HOLD_NATIVE_SELECTIVE_REPEAT_LOWERING**

## Mission / Referee

The frozen question was whether ordinary ONE `repeat` could lower into the existing native COPY/FILL/ADD8/XOR selective terminal schedule without a reader-visible Repeat opcode, whole-root reconstruction, or root-size-scaling work, while beating the authenticated generic `RangeEvaluator` path.

Frozen authority: `docs/one/evidence/ONE_G02_NATIVE_SELECTIVE_REPEAT_LOWERING_PREREG_2026-09-09.md`.

No threshold was changed after seeing results.

## Evidence authority

- branch: `research/cmpct1`
- exact result source: `275934cefcd70b27dcc7fb79e6aed51733c340f5`
- workflow: `CMPCT1 ONE-G0.2 native selective Repeat lowering`
- run: `34405286741`
- job: `102646681064`
- artifact: `10125066010`
- artifact digest: `sha256:586f67053f2f4970dab77b10f8a1f113b1c0aa41f35d2058426fc032a12c7b07`
- exact-source semantic suite: **61 passed**

The previous run `34397879261` at source `a60009aa44a6ff2a08bee90c824395ff809cb510` is not performance evidence: an obsolete inherited test still required Repeat to be rejected, so the benchmark never ran. The shared native-range test was repaired later, but the Repeat workflow did not watch that test path. Commit `275934cefcd70b27dcc7fb79e6aed51733c340f5` repairs that evidence-lane dependency and produces the first admissible result-bearing run.

## Frozen result

Hard semantic/locality gates all pass:

- exact candidate/comparator/reference bytes: **PASS**
- authentication against the same root commitment: **PASS**
- same authenticated cone geometry: **PASS**
- fixed 4 KiB cone source/read/write state independent of unrelated root growth 32 KiB -> 128 KiB -> 512 KiB: **PASS**
- temporary-state bound: **PASS**
- command-count bound: **PASS**
- inherited malformed/resource/authentication behavior: **PASS**

Economic gates fail:

| Metric | Frozen gate | Result |
|---|---:|---:|
| median candidate / comparator CPU | <= 0.75x | **2.059911x** |
| worst candidate / comparator CPU | <= 1.10x | **2.455025x** |
| median candidate / comparator modeled movement | <= 1.00x | **1.329897x** |

Therefore the candidate is a **HOLD**, not an invalidation: the lowering is semantically correct and genuinely cone-proportional, but it is economically worse than the already-correct generic reader.

## Causal reading

The result exposes two concrete owners rather than a vague native-overhead problem.

### 1. Repeated source packing

For a 4 KiB authenticated cone, the current candidate physically builds a 4 KiB native source plan even when the stored Repeat basis is only 32/64/256 bytes. It then writes the 4 KiB sink and later materializes the same 4 KiB authenticated proof payload. This is why candidate movement sits near 1.33x comparator movement despite perfect cone locality.

The fixed-cone rows make the distinction clear: locality versus root size is solved, but data inside the cone is still copied one stage too many.

### 2. Per-period command construction

Small bases produce many Python-side terminal commands before entering the native kernel:

- 32-byte basis / 4 KiB cone: 128 commands;
- 64-byte basis: 64 commands;
- 256-byte basis: 16 commands;
- 4 KiB basis: 1 command.

CPU improves as command count falls, but even the one-command 4 KiB-basis rows remain slower than the generic comparator. Therefore command explosion is important but not the only owner; plan construction / native-call / source-packing overhead also matters.

This is a useful falsification of the assumption that moving an operation into the existing native schedule is automatically a speed win. Python's ordinary bytes slicing/join/repetition machinery is already implemented in optimized native code beneath the interpreter and is a strong comparator for Repeat.

## Hostile reviewer

Do **not** promote the native Repeat path merely because it passes semantics or avoids root-size scaling. It loses both frozen economic gates by large margins.

Do **not** solve this by adding a reader-visible Repeat opcode. Repeat already exists as an ordinary ONE Law relation; the representation is not the problem.

Do **not** weaken the comparator or omit plan/proof movement from accounting. The current HOLD is exactly the evidence the campaign needs.

## Rehabilitation target

The next attack must remove the measured physical stages rather than tune thresholds:

1. reuse a repeated source slice instead of repacking identical basis bytes per period;
2. reduce Python command construction, ideally by lowering a periodic span as one bulk execution description rather than O(cone/basis) Python objects;
3. preserve the same authenticated cone, immutable validated Program authority, and exact failure behavior;
4. charge every source read, plan write, sink write, proof payload, and proof hash honestly.

A rehabilitation is only interesting if it can beat the already-fast generic Repeat evaluator. If the generic path remains faster after causal source/command removal, the correct reader strategy is to keep Repeat on that generic bulk path and reserve native lowering for operations where it has demonstrated a real advantage. Backend choice is an execution policy over the same ONE representation, not a new stored mechanism.
