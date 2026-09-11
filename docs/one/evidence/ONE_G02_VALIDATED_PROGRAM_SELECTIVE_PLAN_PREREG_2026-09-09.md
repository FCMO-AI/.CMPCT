# ONE-G0.2 — reusable validated Program selective-plan preregistration

Date: 2026-09-09  
Branch: `research/cmpct1`  
Experimental version: `ONE-G0.2`  
Status: preregistered before result-bearing implementation

## Mission Lock / Referee

### Observed cost owner

The fixed-cone preflight-scaling diagnostic keeps a 128 KiB root and first 4 KiB selective request unchanged while adding unrelated but valid ONE nodes. Exact hosted evidence at source `56d1d6af8791a87a8d1e62cde3ff2ab68f5382be` shows per-request `compile_native_law_range_plan()` CPU growing from tens of microseconds to several milliseconds as unrelated graph size reaches 4,096 nodes.

The requested data cone is fixed. The exported cost is therefore control-plane work: every selective compile repeats `Program.validate_shape()` plus full `_preflight(program)`, and `_preflight` intentionally validates every stored node.

### Hard invariant

Full stored-Program validation may not be weakened or made request-dependent. Unreachable malformed nodes, cycles, invalid ranges, declared-length violations, depth bombs and whole-Program work-budget violations must still fail closed.

The experiment is allowed to move that validation cost to an explicit immutable Program-open boundary and reuse its result. It is not allowed to skip validation.

### Hypothesis

If ONE validates and snapshots an immutable Program once, subsequent selective-plan compilation can remain proportional to the requested reconstruction cone rather than total unrelated graph size while preserving the exact existing validation semantics.

### Disproof

HOLD if any of the following occurs:

- a malformed Program can obtain validated authority;
- mutating caller-owned root mappings after validation changes the validated snapshot;
- selective outputs diverge from the ordinary range evaluator;
- repeated validated-plan CPU still scales materially with unrelated graph size;
- the apparent gain depends on excluding the one-time validation/open cost from disclosed accounting;
- resource bounds or unsupported-topology behavior are weakened.

## Candidate design

Introduce a research-only `ValidatedProgram` authority created by one constructor that:

1. snapshots the Program into immutable/frozen Python objects, including a copied read-only root mapping;
2. runs ordinary `Program.validate_shape()`;
3. runs the exact existing full `_preflight()` once;
4. retains the preflight certificate together with the exact snapshot.

A separate selective-plan compiler accepts only this authority. The existing raw-Program API retains its current full validation behavior.

This changes no ONE opcode, wire byte, root identity, authentication rule or reader-visible semantic.

## Frozen diagnostic matrix

Root: 128 KiB.  
Request: first 4 KiB.  
Law families: `add8`, `xor`.  
Unrelated valid nodes: `0, 64, 256, 1024, 4096`.  
Repeated CPU samples: 11 per cell after warm-up.

Measure separately:

- one-time validated-Program construction CPU;
- incumbent raw selective-plan compile CPU;
- validated selective-plan compile CPU;
- validated/incumbent ratio;
- candidate growth relative to its own zero-unrelated cell;
- exact output parity.

## Frozen interpretation gates

This is a cost-owner rehabilitation experiment, not a product-release gate.

Required for `ADVANCE_VALIDATED_PROGRAM_SELECTIVE_PLAN`:

- exact semantic parity on every row;
- malformed/stale/mutation hostile tests pass;
- maximum candidate CPU growth from 0 to 4096 unrelated nodes <= 2.0x for each Law family;
- at 1024 and 4096 unrelated nodes, candidate/incumbent selective-plan CPU <= 0.20x on every row;
- one-time validation/open CPU is reported for every row and remains outside per-request timing only because the experiment explicitly models repeated requests after a completed archive-open validation boundary;
- no format, opcode, integrity, resource-limit or unsupported-topology weakening.

If the candidate misses the CPU gates while preserving semantics, retain the result as `HOLD` and localize the remaining cone-planning owner rather than weakening thresholds.

## Hostile-review focus

The most dangerous false win is stale authority. A wrapper around a caller-mutable Program object is not sufficient. The validated object must own a snapshot whose roots cannot be mutated through the original mapping, and later selective compilation must consume only that validated snapshot.
