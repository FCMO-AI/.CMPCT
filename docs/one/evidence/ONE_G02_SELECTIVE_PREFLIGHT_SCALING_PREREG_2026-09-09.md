# ONE-G0.2 Selective Preflight Scaling — preregistration

Date: 2026-09-09
Experimental version: `ONE-G0.2`
Status: **PREREGISTERED — COST-OWNER DIAGNOSTIC, NO PROMOTION VERDICT**

## Mission lock

Determine whether the current native selective-cone planner pays CPU proportional to unrelated stored Program graph size even when the requested root interval and reconstructed cone are fixed.

This experiment does not modify the frozen `ADVANCE_AUTHENTICATED_NATIVE_SELECTIVE_CONE` thresholds and does not weaken whole-Program validation. It exists because locality accounting that reports only source/cone/authentication bytes can miss CPU spent validating unrelated graph nodes.

Current relevant boundary:

`compile_native_law_range_plan -> Program.validate_shape -> _preflight(all stored nodes) -> requested-cone lowering`

The reference `_preflight` intentionally validates every stored node so archive validity cannot depend on the requested root or cache order. That safety invariant remains binding.

## Falsifiable hypothesis

For a fixed 4 KiB request into the same 128 KiB add8/xor root, native selective-plan compilation CPU should remain approximately stable as valid, unreachable ONE nodes are added. A material monotonic increase with unrelated node count falsifies the stronger claim that selective-open planning CPU is cone-proportional.

## Frozen matrix

- root size: 128 KiB;
- requested range: first 4 KiB;
- Law families: add8 and xor;
- unrelated valid Surprise nodes added: 0, 64, 256, 1,024, 4,096;
- 11 timed CPU rounds per cell after warm-up;
- no format, Program root, requested bytes, or cone geometry changes between node-count cells.

## Accounting and interpretation

Report exact median `process_time_ns` for `compile_native_law_range_plan` and ratio to the zero-unrelated-node cell.

This is intentionally a diagnostic rather than a promotion gate. Outcomes are interpreted as follows:

- **flat/near-flat:** whole-Program preflight is not a meaningful owner at this scale; continue optimizing the measured selective-cone stage owner from the main authenticated-open falsifier;
- **material growth with unrelated nodes:** full-Program preflight is a genuine selective-open CPU owner. The next rehabilitation must preserve full validation while avoiding repeated per-request graph-wide work, most plausibly by reusing authenticated immutable validation metadata / a validated Program plan established at archive open or construction time;
- **noisy/non-monotonic:** improve measurement quality before drawing an architectural conclusion.

Skipping validation, validating only reachable nodes, or excluding preflight from the charged open boundary is not an admissible fix. The purpose is to change when safely reusable proof is established, not to delete the proof.

## Hostile-review boundary

A future cached/validated-plan design must demonstrate that malformed unreachable nodes, cycles, impossible ranges, depth bombs, output/work bombs and root-shape mismatches are still rejected before any selective bytes are trusted. Cache identity must be tied to authenticated immutable Program bytes/policy so stale validation cannot authorize modified graphs.
