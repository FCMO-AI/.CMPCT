# O129 preregistration — prospective v0.31 source custody × complete historical Git custody

Date: 2026-10-25
Status: PRE-IMPLEMENTATION FROZEN PREDICTION
Evidence tier: authentic exact-HEAD installed-candidate GitHub Actions regression (not product release or benchmark).

## Authority, immutable source controls, and coordination

This independent **integration court** starts at the exact PR #473 O127 head `896fada645ed9842f44b8d839c9102323a00be8d`, stacked on Builder O99's existing owner branch. PR #266 prospective fingerprint head is `c5ea5b97a86bf9d0bffe9dad54c5fd2a6f0b6fb1`. The published v0.30.0 main release and historical `docs/V030_RELEASE_LOCK.json` are immutable evidence. Neither parent owner branch will be edited; no format, Reader, Builder, codec, evaluator threshold, release or benchmark comparator may be altered here.

At the frozen baseline, PR #473's true full-depth installed candidate court [run 40241445288](https://github.com/FCMO-AI/.CMPCT/actions/runs/40241445288) reports **845 PASS / 7 SKIP / 4 FAIL**; the four failures are known published-lock/current-prospective-epoch test mismatches. Its earlier shallow parent result was **838 PASS / 7 SKIP / 11 FAIL**, seven source-object failures due only to missing Git history. PR #266's own shallow exact-head court [run 39975603659](https://github.com/FCMO-AI/.CMPCT/actions/runs/39975603659) reports **791 PASS** with the prospective source identity, but not the O99/O127 parent tests.

These are different partial successes. Neither is evidence that both repairs coexist on a single source tree.

## One question, mechanism, and strong control

**Primary question:** Can PR #266's prospective source fingerprint and four corrected epoch assertions coexist, unmodified in meaning, with PR #473's genuine complete Git-history checkout and the O99 exact-product test cohort, producing one all-green generic source-exact court without rewriting the published release lock?

Mechanism: carry PR #266's eight changed file contents onto the exact O127 parent. Merge only the overlapping `.github/workflows/tests.yml` in a conservative three-way manner: preserve O127's `fetch-depth: 0` and explicit `--is-shallow-repository=false` witness; add PR #266's pre-pytest `tools/check_v031_candidate_fingerprint.py` receipt and its retained artifact. Transfer PR #266's four bounded epoch-test changes and the actual independent candidate fingerprint tool, manifest and adversarial tests. Import the original source files, not paraphrased tests or invented receipts.

Controls: unchanged O127 parent pytest with four reds; unchanged PR #266 exact-head fingerprint test success; unchanged historical v0.30 release lock Git blob, enforced by a candidate test; installed authentic ancestor `git show` controls, not a mock; same O99 Builder code, historical sources, real corpus and release semantics on both sides.

## Prospective prediction and disproof

**Prediction:** On GitHub Actions Ubuntu, after transferring source files and combining their workflow, the exact-head `CMPCT tests` regression job will end with **zero failed tests**, no unexpected skips, and at least the inherited **845 PASS + four formerly failing tests + five new candidate identity tests** (expected **854 PASS / 7 SKIP / 0 FAIL** absent unrelated concurrent/environment variance). It must emit a candidate SHA-256 source manifest receipt tied to `EVIDENCE_HEAD`; checkout must be demonstrably non-shallow, and all inherited authenticated historical-source tests must continue passing.

**Disproof:** Any of the four original red tests still failing, any source-history test regressing, mismatch of `git rev-parse HEAD` and `EVIDENCE_HEAD`, missing/incorrect candidate source coverage, historical lock blob drift, any negative or new unexpected skip, a changed non-CI product source, or a test/threshold silently removed is a failed O129 integration. A green workflow status without actual raw pytest counts and artifact identities has no proof value.

**Stronger alternative:** A merge of owner branches without an exact-head combined pytest cannot demonstrate semantic conjunction. Creating separate parallel CI workflows would duplicate expensive runner load and could hide competing source identities; reuse one existing every-PR tests lane. If all-pass fails, first isolate the newly exported owner/epoch conflict; do not disable the failing test.

## Accounting and eventual decision

Primary outcome: regression evidence availability / source-custody continuity, **not compression ratio, create/extract speed, RSS, format capability, security guarantee, or release performance**. Runtime/network overhead of full-depth checkout is a real CI cost and may be acceptable only if it re-enables authentic historical oracles; measure where possible. No numerical version/surface bump. No merge/release. Archive-size gate, substantive ABBA, Windows/macOS and native ABI remain independent and unmeasured in this integration.

A decisive positive result should notify #266 and #473 and offer the integration branch to the existing CI-owner lane. Do not update `docs/discovery/STATE.json` unless this genuinely changes its decision-complete frontier; that cache is not a concurrency lock. Leave the frozen preregistration unchanged after results; append a separate result report with exact SHA, Actions run ID, raw counts, negatives, duration and next gate.

## Falsifiability / quality-ratchet

**disproof:** All assertions above retain their original strictness, provenance, failure visibility and timeout. **quality-ratchet:** preserve the authentic release-history proof restored by O127 and the historical-release immutability test added by #266 while adding one prospective complete candidate fingerprint receipt; green tests cannot be purchased by deleting correctness coverage.
