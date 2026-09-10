# ONE-G0.2 Genesis candidate adapter probe — preregistration

Date: 2026-09-10
Branch: `research/cmpct1`
Experimental version: `ONE-G0.2`
Status: preregistered before result-bearing execution

## Mission Lock / Referee

Close one remaining symmetry gap in Genesis measurement plumbing without consuming the frozen 15-workload exam. The historical v0.29/v0.30 probe has already shown that the frozen comparators can build and verify executor-owned external trees. This probe asks the same question of the current ONE general Law archive boundary.

This is **adapter-boundary evidence only**. It is not Genesis scoring, not a density promotion, and not certification that the current general Law archive is the final Genesis candidate.

## Falsifiable hypothesis

`experiments/one/general_law_archive.py` can accept one externally materialized arbitrary transfer tree, produce one complete authenticated archive using only the generic ONE reader ontology, and reconstruct whole and selective reads byte-exactly without generating or importing the Genesis workload suites.

## Frozen surface under test

- builder: `experiments.one.general_law_archive.build_general_law_archive`
- reader: `experiments.one.authenticated_archive_envelope.open_authenticated_archive`
- allowed reader-visible operations: `surprise`, `concat`, `repeat`, `fill`, `xor`, `add8`

The probe must not bypass the complete archive envelope by measuring Program bytes alone.

## Transfer fixture

Use one deterministic temporary tree containing:

- an incompressible/hash-stream file,
- an exact copy,
- an ADD8-related file,
- an XOR-related file,
- a Fill file,
- a tiny nested file,
- an empty file.

No module that builds `neutral_hostile_v1` or `resemblance_hostile_v1` may be imported.

## Disproof tests

HOLD or RETIRE the proposed adapter boundary if any of the following occurs:

1. whole reconstruction differs from the external source tree;
2. authenticated selective reconstruction differs from requested bytes;
3. the emitted Program contains an operation outside the six-operation ONE grammar;
4. the complete archive cannot be reopened by the independent existing archive reader;
5. repeated builds of the identical external tree are not byte deterministic;
6. the probe imports/generates the Genesis 15-workload corpus;
7. complete persistent archive bytes cannot be counted from the returned artifact;
8. reader discovery or a hidden legacy codec is required.

## Evidence to retain

Record at least complete stored bytes, logical bytes, root-class counts, Program node count, auth-index bytes, whole-read exactness, selective-read requested/cone/source/proof bytes, deterministic wire SHA-256, reader-visible op set, and explicit `reader_discovery=false` / `hidden_codec=false` if demonstrated by the inspected surface.

Timing/RSS is out of scope here; creation profiling has its own preregistered fresh-process lane. Synthetic measurements must never be inserted into the Genesis result matrix.

## Decision rule

- `ADVANCE_ONE_ADAPTER_BOUNDARY` only if every semantic, deterministic, ontology, external-input and no-Genesis condition passes.
- `HOLD_ONE_ADAPTER_BOUNDARY` for a clean but incomplete product seam.
- Any exactness/integrity failure blocks use of this surface as a Genesis adapter until repaired and independently re-falsified.
