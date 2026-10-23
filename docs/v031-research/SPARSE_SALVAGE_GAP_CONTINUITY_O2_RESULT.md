# CMPCT v0.31 sparse extent continuity O2 — RETIRED BEFORE EXECUTION (2026-10-23)

**Status: SCIENTIFIC PROPOSAL WITHDRAWN; NO TEST, NO PRODUCT CODE, NO PR, NO RELEASE.**

The proposed two-guard change recorded in `SPARSE_SALVAGE_GAP_CONTINUITY_O2_PROSPECTIVE.md` was conditioned on an apparent O1 cross-extent phantom candidate. That causal precondition is false for the unchanged actual parent sparse oracle.

Exact-source [O1 original scientific run 40040863477](https://github.com/FCMO-AI/.CMPCT/actions/runs/40040863477) rejected the phantom hypothesis: bounded reference and sparse oracle each returned the same one valid candidate `[4194432]`. Re-inspection showed `carry=b""` already resets **inside** the SEEK_DATA extent loop, so the standalone reenactment that inspired O2 had inadvertently fabricated the deficiency. Follow-up source-exact hosted [O1 positive regression 40041146923](https://github.com/FCMO-AI/.CMPCT/actions/runs/40041146923) confirms parity on three deliberately gapped magic fragments.

**Decision:** do not modify `sparse_candidates` to add the originally proposed carry reset; it already has the necessary reset. Rechecking magic using already-read bytes might be reasonable *defense in depth* as future independent work, but without a distinct failure or measured advantage it does not justify another mechanism variant, product implementation or claim of fixing a vulnerability. Avoid reopening through threshold tuning or fixture-specific changes. The canonical bounded scanner still owns fallback. Parent scientific owner PR #296 remains untouched.

The O2 preregistration was committed before causal inspection was complete. This outcome document does not change that historical prediction; it prevents that unexecuted research plan from being mistaken for an active claim. No `docs/discovery/STATE.json` edit or universal policy update is justified.

**Counterfactual:** read the original `pos=start; carry=b""` indentation before creating any branch; the source itself is the lowest-cost oracle for this question. Original O1 claims, hosted evidence, and owner correction are durable in [PR #301](https://github.com/FCMO-AI/.CMPCT/pull/301).
