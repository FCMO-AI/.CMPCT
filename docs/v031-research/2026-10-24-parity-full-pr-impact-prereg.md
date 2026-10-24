# Issue #318 — exact-source performance admission (prospective preregistration)

Date: 2026-10-24 UTC. Source base: `agent/v031-development@4545d7d5b2a0b712b4b00f5a9c291d4a3a9e169b`.
Owner surface: r24 ZIP parity **admission only**, not its frozen comparator, direct-base corpus or release thresholds. Issue: https://github.com/FCMO-AI/.CMPCT/issues/318 .

## Question
Can a multi-commit pull request end in a workflow/doc-only commit yet skip the mandated comparison despite earlier product changes? The authenticated Issue #318 reproduction says **yes** at PR #316, head `1ed92767e6438d9bb8835ddc7ae27160440c2014`; checkout's `git diff-tree -r HEAD` sees only the final commit.

## Predictions and controls (frozen before implementation)

1. Git graph `base → source-change → unrelated-workflow-change` must classify **RUN** at final HEAD. Last-commit-only classifier returns **SKIP** and is the known false-green control.
2. Net docs-only PR diff must classify **SKIP**; a code change added then reverted to base bytes must also skip when no relevant net tree delta remains.
3. Nontrivial PR merge-base divergence must use the **PR-head change set**, not changes made only on the moving base branch.
4. Push product change within `before..after` must **RUN**, push docs-only diff **SKIP**.
5. Renaming/removing a relevant source into an irrelevant path must **RUN**; rename inference must not hide deleted relevant paths.
6. Missing/unfetched base, zero-range SHA, unrelated histories, unknown events must **RUN** rather than allow a false-green skip.
7. Checkout not equal to immutable event head must fail, never produce a valid skip.
8. Manual dispatch must **RUN** regardless of diff.
9. Existing CI-topology ratchet accepts a legitimate source-scoped full-PR classifier while rejecting a declared gate lacking classifier/exact-head/full-history requirements.

## Mechanism and cheapest decisive oracle

Replace `git diff-tree -r HEAD` at the **admission** boundary with a fail-closed full PR merge-base change set (and event's `before..after` for push), bound to the exact evidence head. Use a small deterministic local Git-DAG unit court with real commits and no performance resource cost before allowing the workflow into PR CI. Keep the original path allowlist and do not touch comparator semantics, benchmark data, no-regression thresholds, or source files under `src/`.

## Rival explanations / limits

GitHub `pull_request.paths` aggregates the PR and may trigger redundant classifier work; fixing the classifier may lead to more expensive repeated receipts on long-lived product PRs. This is a known scheduling-cost debt, not license to skip unmeasured product changes. An exact-head comparison based on the current PR base can fail if history/permissions are unavailable; it must run or fail, never skip. Git graph controls only prove admission behavior, not release performance or complete GitHub event/permission compatibility. Only hosted exact-HEAD CI establishes the latter.

## Kill / narrow conditions

Reject the implementation if it classifies the two-commit product/doc control as SKIP, fails to preserve docs-only SKIP, ignores relevant rename deletion, weakens exact-head binding, accepts inaccessible source history as SKIP, or rewrites the frozen comparator/test corpus. If tests are green but Actions performance job skipped, record that truth instead of claiming product evidence.

## Concurrency

PR #306 owns the measurement comparator and has disjoint files. Branch is isolated. Re-read source and owner state before the workflow mutation; never overwrite another owner's work.
