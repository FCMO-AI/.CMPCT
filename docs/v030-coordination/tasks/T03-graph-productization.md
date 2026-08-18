# T03 — Graph integration / canonical productization

- **Owner:** slot-03
- **Priority:** P0
- **State:** READY
- **Branch:** `agent/v030-coop-graph-productization`
- **Dependencies:** may implement against bootstrap integration head; final import/evidence must be reconciled after T00.

## Objective

Turn the successful v0.30 research representations into one understandable canonical product architecture instead of shipping a pile of parallel experiment facades.

## Immediate exact-head defect — fix first

Fresh authoritative PR-gate run `32105135629`, job `95612937412`, found one focused Geometry failure before the G0–G4 oracle was allowed to run:

`tests/test_v030_geometry.py::test_regular_gap_discovery_is_content_driven`

Fixture: `(b"abcdef" + b"\x1e") * 4000`.
Expected: control separator `0x1e` must be nominated by `_delimiter_rank`.
Observed: `[100, 99, 101, 102]`.

Root cause: flat Geometry's recurrence score includes the incomplete prefix/suffix fragments as if they were complete delimiter intervals. The fixture ends on the delimiter, so the censored trailing fragment biases variance and lets ordinary periodic payload bytes outrank the true separator.

Required correction:

- compute regularity from **complete inter-occurrence intervals only** (`pos[i] - pos[i-1] - 1`);
- do not include stream-edge fragments in recurrence variance;
- retain the occurrence/segment/search bounds and deterministic tie-breaking;
- keep this heuristic nomination-only: exact transformed payload/archive pricing still decides admission;
- preserve/add a nearby footnote explaining why censored edge fragments are excluded;
- keep the existing control-byte regression test and add an edge-phase property case if useful;
- run the complete focused Geometry/G0-G4 tests before handoff.

Do **not** lower `MAX_DELIMITER_REGULARITY`, change the frozen G0–G4 oracle threshold, or introduce filename/schema semantics to make the test pass.

## Scope

- internalize PrefixGraph as a bounded depth-1 relation inside the owning v0.30 graph/compiler **or** produce a rigorously justified alternative canonical profile with equivalent accounting, locality, reader and portability guarantees;
- preserve full G0–G4 Geometry inside Mosaic/pre-fallback structure without duplicating reactor logic;
- reduce research adapters/facades from the promoted path while preserving historical evidence and rejected experiments;
- canonical API/CLI selection/read/extract behavior across r25 and exact r24 fallback;
- canonical on-disk profile/revision description and conformance semantics;
- one semantic owner per promoted mechanism;
- product-facing error/fallback behavior that is bounded and explainable.

## Owned paths

Prefer `experiments/entropygraph_v030_*` only where those modules are moving toward the promoted implementation, canonical reader/selector/API adapters, format/product tests, and `docs/FORMAT.md` / architecture docs as required. Do not alter native implementation owned by T01 or benchmark thresholds owned by T02.

## Required design properties

- complete-artifact exact pricing; no independent-savings addition;
- exact v0.29/r24 fallback on loss or unsupported cases;
- dependency depth <=1 for PrefixGraph-like references;
- <=8x selected per-member decoded-context amplification;
- bounded transform/reference search and decode units;
- no filename/MIME/schema-specific authority for Geometry nomination;
- reader simpler than encoder heuristics;
- no duplicate promoted implementation of separator nomination, generic publication, recovery, or reference semantics.

## Completion evidence

1. Clear canonical architecture document that maps every selected archive profile to one writer/reader/native responsibility.
2. Exact ablation hooks exist for v0.29, Geometry-only, PrefixGraph-only, and combined behavior without arithmetic borrowing.
3. PrefixGraph promotion debt is resolved explicitly, not left as `CMPNXP1` research scaffolding by accident.
4. Focused round-trip/recovery/locality/property tests remain green.
5. Redundant promoted facades are removed or demoted to clearly labeled historical/research helpers without deleting useful notes/evidence.
6. Format/API documentation matches actual bytes and fallback semantics.

## Handoff

Set `REVIEW` with exact source head, architecture decision record, files/commits to import, compatibility effect, tests run, and explicit list of any research modules intentionally retained only for history/ablation.
