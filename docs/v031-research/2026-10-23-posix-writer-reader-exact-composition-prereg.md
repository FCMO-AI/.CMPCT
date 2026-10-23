# v0.31 POSIX Writer Lease × Reader Safety — Independent Composition Preregistration

**Date:** 2026-10-23 UTC. **Status:** PRE-RESULT research/integration hypothesis, NOT a release or promotion claim.

## Recovered fixed inputs
- Reader/safety/proof integration parent PR #285, exact source SHA `369255f63aaa6a9c5c5c03eae2d57f8d1776662e` (itself carries PR #277 / #271 / #266). Parent already reports 827/827 general tests and official ABBA pass, but those observations are **not** evidence about this composition.
- Cooperative POSIX multiwriter owner PR #295, source SHA `b01f9df2e056ea80fac5ae9dda89cc56cf9d4910`. Its exact-head specialized court reports 15/15 PASS. Negative discovery PR #289: two successful disjoint rename operations can lose one logical update even when physical append writes are serialized.
- PR #295 changed nine files (one product Writer, one focused test, five research notes, one micro-economics note, one dedicated workflow). PR #285 changed Reader, Reader safety test, hardening documentation; **no overlapping source paths**. Both are active independent draft owners. No owner branches will be modified.

## Question / falsifiable hypothesis
Can the **exact source files** of the cooperative POSIX transactional Writer lease coexist with the most mature composed Reader safety stack, using a single installed package, with no regression in hardlinks, Reader constructor ownership, RAW verified range access, publication/proof behavior, or the existing adversarial Writer tests?

### Simpler controls and alternatives
1. Keep the PRs separate: each provides isolated evidence only, fails to prove compatibility.
2. Rewrite merged Writer/Reader manually: unjustified duplicate implementation and potential semantic drift; reject.
3. Cherry-pick all historical commits and merge unrelated histories: introduces extra complexity without more evidence; avoid.
4. **Chosen:** create one narrow integration branch based on PR #285; transfer exact Git blobs of the nine PR #295 files; independently verify blob identity; run unchanged owner tests and current CI. This changes only what can be tested.

## Expected observable / disproof / stopping condition
- Before any composition, verify each owner blob against the exact owner source SHA. Copy by Git blob identity, not by reimplementation.
- Exact-head source custody: nine owner paths identical to the PR #295 source; Reader blob identical to parent PR #285; immutable published v0.30 release lock and format revision unchanged.
- Specialised POSIX lease court: must run **all** original 15 tests, including the adversarial path substitution, disjoint multi-process appends, hardlink/symlink identity, offset rebind, failed lock acquire and crash/recovery checks; no weakening.
- General Tests must pass all inherited tests (candidate includes prospective CI identity from PR #266). Public Proof and Reader focused courts must pass on same HEAD when actually executed; success with skipped substantive tests is **not** evidence of passing them.
- Compare official same-tree r24/ZIP ABBA where available, preserving 0-byte deterministic no-regression and unchanged timing envelope. Do not infer lack of overhead from a no-op code path; locks are active for every append mutation.
- Any lost successful mutation, modified replacement file, changed owner source blob, failed exact-head specialized court, or confirmed performance regression blocks promotion and requires diagnosis. Windows remains **NOT IMPLEMENTED** in PR #295; no cross-platform claim even with full Linux CI green.
- Distinguish SCIENTIFIC / integration evidence from RELEASE credit. No merges/version bumps; retain DRAFT until porting, adversarial resource/correctness, perf and release gates are earned.

## Coordination and next action
This is a **stacked independent compatibility court**, not a new claim of owning the Writer, Reader, CI fingerprint, or Bounded Drift. Any new insight belongs in the PR #295 and PR #285 owner discussions. Monitor active owners before late writes. Capture exact-head checks and source identities; if the court passes, identify next decisive cross-platform falsifier, not release. No edits to `docs/discovery/STATE.json` for this subordinate integration experiment.

## PARETOBONK selection
Alternatives examined: Bounded Drift productization (#242 owner, scientific positive but D5), streaming salvage (#293 product / #296 sparse oracle owner), inherited CI custody (#266 owner), and **this** cross-boundary integration. This court is chosen because it is inexpensive, source-exact, reversible, no competing implementation, and can falsify the combination of two important safety planes immediately. The competing work retains ownership. No numeric score.
