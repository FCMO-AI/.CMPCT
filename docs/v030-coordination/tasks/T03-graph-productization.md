# T03 — Graph integration / canonical productization

- **Owner:** v0.30 sole executor
- **Priority:** P0
- **State:** CLAIMED
- **Branch:** `agent/v030-authoritative-integration`
- **Dependencies:** final evidence must be run on the same exact reconciled candidate used by T00–T04.

## Objective

Turn the successful v0.30 research representations into one understandable canonical product architecture instead of shipping parallel experiment facades.

## Geometry exact-head invariant

A focused Geometry regression previously showed that delimiter recurrence scoring included incomplete stream-edge fragments as if they were complete intervals. Preserve the correction:

- compute regularity from **complete inter-occurrence intervals only** (`pos[i] - pos[i-1] - 1`);
- do not include censored stream-edge fragments in recurrence variance;
- retain occurrence/segment/search bounds and deterministic tie-breaking;
- keep delimiter ranking nomination-only: exact transformed payload/archive pricing decides admission;
- preserve the nearby explanatory footnote and edge/control-byte regression coverage;
- do not lower `MAX_DELIMITER_REGULARITY`, change frozen G0–G4 thresholds, or introduce filename/schema authority.

## Product-boundary review

`docs/v030-coordination/reviews/graph-productization.md` is normative until every item is either resolved in code/tests/docs or deliberately rejected with evidence.

The highest-priority invariants are:

1. genuine canonical r25 bytes compete against genuine canonical r24 bytes for the same original filesystem tree; exact ties keep r24;
2. public user-tree identity is distinct from any internal content-graph identity, and canonical strong verification proves the user-visible tree;
3. filesystem timestamps use a bounded signed domain compatible with what the writer can emit;
4. safe-symlink policy rejects escapes under both POSIX and Windows lexical semantics;
5. canonical import/dispatch is thread/import-order safe and does not mutate research-module globals process-wide;
6. metadata restoration policy distinguishes authenticated metadata from best-effort host application.

## Scope

- internalize PrefixGraph as a bounded depth-1 relation inside the owning v0.30 graph/compiler **or** use a rigorously justified canonical profile with equivalent accounting, locality, reader, and portability guarantees;
- preserve full G0–G4 Geometry inside Mosaic/pre-fallback structure without duplicating reactor logic;
- reduce research adapters/facades from the promoted path while preserving historical evidence and rejected experiments;
- canonical API/CLI selection/read/extract behavior across r25 and exact r24 fallback;
- canonical on-disk profile/revision description and conformance semantics;
- one semantic owner per promoted mechanism;
- product-facing error/fallback behavior that is bounded and explainable.

## Preferred implementation area

Prefer `experiments/entropygraph_v030_*` only where those modules are moving toward the promoted implementation, canonical reader/selector/API adapters, format/product tests, and `docs/FORMAT.md` / architecture docs as required. Because one executor owns the release, native or benchmark code may also be adjusted when a product-interface defect crosses boundaries, but release thresholds and evidence semantics remain frozen.

## Required design properties

- complete-artifact exact pricing; no independent-savings addition;
- exact genuine r24 fallback on product loss or unsupported cases;
- dependency depth <=1 for PrefixGraph-like references;
- <=8x selected per-member decoded-context amplification;
- bounded transform/reference search and decode units;
- no filename/MIME/schema-specific authority for Geometry nomination;
- reader simpler than encoder heuristics;
- no duplicate promoted implementation of separator nomination, generic publication, recovery, or reference semantics;
- import-order/thread-safe canonical profile dispatch.

## Completion evidence

1. Clear canonical architecture document maps every selected archive profile to one writer/reader/native responsibility.
2. Exact ablation hooks exist for v0.29, Geometry-only, PrefixGraph-only, and combined behavior without arithmetic borrowing.
3. PrefixGraph promotion debt is resolved explicitly, not left as research scaffolding by accident.
4. Genuine r24-vs-r25 complete-product selection floor and conservative ties are tested.
5. User/internal tree identities and strong verification semantics are explicit and tested.
6. Signed timestamp, cross-platform safe-symlink, recovery/locality/property tests remain green.
7. Canonical import/dispatch has no process-global research-module mutation hazard.
8. Redundant promoted facades are removed or demoted to clearly labeled historical/research helpers without deleting useful notes/evidence.
9. Format/API documentation matches actual bytes and fallback semantics.
10. Final `canonical-architecture` evidence is bound to the exact release fingerprint.

## Continuation rule

Work directly on the authoritative branch and fix product defects where they actually live. Earlier branch-level implementations and tests are mechanism provenance only until present on the exact candidate.

Move T03 to `DONE` only when every normative review item and the release-lock `canonical-architecture` obligation are durably closed.
