# CMPCT1 / ONE Genesis product-adapter measurement seam v0.1

Date frozen: 2026-09-10
Status: preregistered before Genesis contender execution
Experimental lineage: ONE-G0.2

## Goal

Normalize measurement boundaries without normalizing away product differences. The executor owns physical inputs and contender source identity; each adapter wraps the frozen/current product surface and emits raw evidence only.

No Genesis workload is executed by this document.

## Process boundaries

For each workload and contender:

### Creation

- five fresh-process repetitions;
- each process starts from the frozen/current contender checkout and receives exactly one executor-owned workload directory;
- CPU time is process CPU consumed by the creation worker;
- wall time is elapsed monotonic time inside the same worker;
- peak RSS is whole fresh-process peak RSS, including imports/runtime needed by that product surface;
- every persistent byte required for reconstruction/integrity is included in `stored_bytes`;
- repeated artifacts must be byte deterministic where the product contract promises determinism; a deterministic-size/wire mismatch is preserved as a semantic failure, not averaged away;
- report medians; retain individual samples.

### Whole read/extract

- use the exact artifact produced by the measured creation surface;
- five fresh-process cold-open repetitions;
- restore every promised logical object;
- independently verify output bytes/tree identity against the executor-owned source;
- include integrity verification when the product read path requires it; if verification is a distinct operation, report the separation explicitly rather than silently charging it to only one contender;
- report process CPU, wall and peak RSS medians plus individual samples.

### Selective access

Use `ONE_GENESIS_SELECTIVE_ACCESS_PLAN_v0.1_2026-09-10.md`.

- primary cross-contender request is the deterministic largest regular member for multi-file workloads;
- five fresh-process cold-open repetitions when a proven selective member surface exists;
- exact returned bytes are verified independently;
- touched/read, decoded/reconstructed, auth/proof, temporary memory and reconstruction-work fields are reported only when directly measured/returned by the frozen surface or an external process/I/O measurement that does not alter semantics;
- unknown values are explicit `unavailable`, never inferred zero;
- fallback whole extraction is not selective evidence.

## Source and authorization guard

A production adapter must refuse to run unless:

1. `CMPCT_GENESIS_SOURCE_SHA` equals its checkout HEAD;
2. the executor supplies `CMPCT_GENESIS_REAL_GATE_AUTHORIZED=1`;
3. the executor's calendar/explicit execution guard has already opened the real path;
4. `CMPCT_GENESIS_WORK_ROOT` and `CMPCT_GENESIS_OUTPUT` are explicit absolute paths.

The adapter does not choose alternate workload roots and does not generate the corpus.

## Raw evidence only

Adapters may not compute comparator deltas, row verdicts, aggregate winner scores or the Genesis campaign decision. They emit `cmpct-one-genesis-contender-raw-v1` only.

## Timing stability

The retained raw evidence includes all five samples. Median values feed the gate comparison. If obvious scheduling instability makes a timing conclusion sensitive to one sample, the first raw run remains durable and the timing cell is held/remeasured under the frozen semantics; thresholds are not changed.

## Historical asymmetry

Adapters may expose genuine historical capability differences.

- frozen v0.29 selective access remains `unavailable` unless an exact frozen reader surface is proven;
- frozen v0.30 may return exact member bytes while r24 decoded-context/amplification instrumentation is absent; resource/amplification cells remain unavailable in that case;
- ONE may retain secondary 4 KiB range evidence, but it must not replace the primary shared member request in cross-contender scoring.

## Disproof / invalidation

A production adapter is not admissible if it reads a different workload root, changes source SHA, regenerates the gate corpus itself, reports missing metrics as zero, omits required persistent bytes, uses a non-frozen comparator implementation, materializes whole archive/root and labels it selective, or performs scoring internally.
