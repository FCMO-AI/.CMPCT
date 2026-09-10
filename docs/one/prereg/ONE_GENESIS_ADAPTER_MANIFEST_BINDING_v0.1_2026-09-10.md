# CMPCT1 / ONE Genesis adapter-manifest binding v0.1

Date frozen: 2026-09-10
Branch: `research/cmpct1`
Experimental campaign: ONE-G0.2
Status: preregistered before implementation and before Genesis contender execution

## Mission Lock / Referee

Construct the runtime adapter manifest consumed by `one_genesis_gate_measurement_executor.py` without giving the manifest authority to select a candidate, alter frozen comparator commits, generate workloads, or score results.

The manifest is plumbing only. The top-level executor remains the authority for calendar lock, explicit real-gate authorization, physical workload ownership, source binding, raw evidence retention, and the no-scoring boundary.

## Falsifiable hypothesis

Given three already-materialized checkouts and one candidate-orchestration script from the sealed CMPCT1 checkout, a small builder can verify all three checkout HEADs against the sealed sources and emit exactly one adapter entry for CMPCT1, frozen v0.29, and frozen v0.30. Each entry uses the same current-candidate raw-adapter script while setting `cwd`/checkout to the contender whose product surface will execute.

Disprove this if the builder accepts a mismatched checkout HEAD, a different v0.29/v0.30 SHA, a raw-adapter script outside the candidate checkout, an interpreter/command with shell composition, an extra or missing contender, or a manifest that can execute anything merely because the calendar gate is open.

## Frozen comparator sources

- v0.29: `02b8b27cb2d97af7c6e0797984a898e8fa8a8e5d`
- v0.30: `f4b158a55a08b9b18b50e4e4abe4b9251048c772`

The CMPCT1 SHA is supplied by the already-sealed gate candidate and must equal the candidate checkout HEAD.

## Command boundary

The builder emits argv, never a shell string. The command is the selected Python interpreter followed by the absolute path to `benchmarks/one/one_genesis_contender_raw_adapter.py` inside the candidate checkout. No contender-specific legacy module is injected into the manifest; the current orchestration layer chooses the exact frozen worker surface according to the contender identity already supplied by the executor.

The raw-adapter script itself must exist under the candidate checkout and resolve beneath it after symlink/path normalization.

## Required falsifiers

1. candidate checkout HEAD differs from sealed candidate SHA;
2. v0.29 checkout differs from frozen v0.29 SHA;
3. v0.30 checkout differs from frozen v0.30 SHA;
4. candidate raw-adapter script missing or outside candidate checkout;
5. malformed/non-40-hex candidate SHA;
6. output contains anything other than exactly the three contender entries;
7. emitted commands are not plain argv lists;
8. no authorization, workload path, score, verdict, ranking, threshold, or winner field is emitted by the builder.

## Claim boundary

Passing this preregistration establishes only `ADVANCE_ADAPTER_MANIFEST_BINDING`: the executor can be handed a source-bound runtime manifest without manual path editing. It does not execute a contender and is not evidence for size, speed, memory, access, semantics, or campaign outcome.