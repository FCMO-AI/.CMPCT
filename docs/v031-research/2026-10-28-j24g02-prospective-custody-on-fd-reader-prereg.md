# J24G02 — Prospective v0.31 custody on Linux fd-owned Reader: preregistration

**Status: PRE-IMPLEMENTATION / RESEARCH COMPOSITION / NO MERGE OR RELEASE AUTHORITY.**
Recorded 2026-10-28 UTC. This first child commit must precede any transplanted source.

## Source-locked baseline / coordination

- Recipient: CMPCT PR #636, exact commit `738e2fd8fd66d2d7e7392d5afe4b95eb71fa0f46` (Linux source-FD hardlink publication); parent PR #629 owns Win32 metadata composition.
- Donor: CMPCT PR #266, exact commit `c5ea5b97a86bf9d0bffe9dad54c5fd2a6f0b6fb1` (prospective v0.31 candidate-source identity). Donor's eight changed files will be copied by **exact existing Git blobs**, not rewritten or paraphrased. No Reader, Builder, Writer, format, release, frozen benchmark, release policy or published v0.30 evidence edit.
- Released `main@80c358f8824ec1b20d349c92ed94c898090969b0`, v0.30.0, r24. Historical release-lock Git blob must remain `988a7b05ad4e0833fac0453de74133b38f890f87`.
- Prior scientifically established baseline: issue #246 / PR #259 has four inherited CI failures in both released main and v0.31 development; #266 implements prospective rather than historical source fingerprinting. Recipient #636's original product Linux hardlink test passed but general CI inherited historical gates. Original code owner #266 remains unmodified; this is integration, not a competing implementation.

## Primary causal question

Can the unchanged #266 prospective source-identity implementation coexist with the exact #636 Reader, yielding four formerly inherited test assertions green and a genuine exact-HEAD source receipt, **without mutating historical v0.30 custody** or misrepresenting skipped full-product benchmarks?

Hypothesis: grafting the eight donor blobs onto the exact recipient and running genuine installed Linux suite will resolve the four inherited epoch-mismatch tests while keeping product Reader blob and hardlink specialized evidence unchanged. A new source identity automatically captures the changed Reader because `src/**/*.py` is fingerprinted. This is a **reusable integration prerequisite**, not evidence that all #636 functionality survives all platforms or is release-promotable.

## Alternatives / BONK filters

- Patch published `docs/V030_RELEASE_LOCK.json`: rejected; changes immutable release identity.
- Skip/delete historical tests or relabel red: rejected; weakens evidence.
- Re-implement a second fingerprinting implementation or add a second parallel CI job: rejected; owner #266 exists, additional process/runner cost unjustified.
- Graft existing donor Git blobs exactly and reuse original `tests.yml`: selected as smallest falsifiable integration route.
- Focus on another hardlink micro-variant: rejected as a saturated adjacent family without new information; custody is a distinct systemic bottleneck across many product PRs.

## Falsifiers and required evidence

1. Compare every transplanted path's current Git blob SHA to the frozen #266 donor. Reject if any differs. Confirm recipient Reader SHA is unchanged from #636; reject if Reader edited by this composition.
2. Run four original inherited test purposes on candidate. **All four must execute and pass** under the prospective authority. The new candidate fingerprint tamper controls and existing historical-lock test must execute.
3. `tests.yml` must emit an actual per-HEAD `v031-candidate-identity.json` receipt containing a SHA binding to source files, not merely an administrative workflow green.
4. Preserve original Linux J24H07 source-FD court as an additional product correctness check; historical J24H05 source-pinned tests are expected to reject modified Reader identities but must not be relabeled green.
5. Source identity must not waive the official release ABBA gate, archived benchmark parity, loss/correctness/fuzz/portability/adversarial recovery checks.
6. If any relevant actual functional test fails after graft, classify as a real integration problem and stop promotion; if CI never executes, report infrastructure limitation. Output no fictitious product performance credit.

## Decision and next step

Pass: candidate-custody integration is feasible on a modern Reader, source-preserving evidence available for cross-PR convergence. **Not** merge/release permission. Fail: isolate the collision before touching either owner or changing assertions. Report CPU/wall source fingerprint overhead if CI supplies it; otherwise unmeasured. All results remain tied to exact HEAD. Discovery policy and `STATE.json` unchanged absent decision-changing general lessons.
