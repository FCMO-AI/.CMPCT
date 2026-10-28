# v0.30 long-lived PR workflow fanout diagnosis — 2026-09-15

Direct observation on PR #56: the experiment-only commit `c962ce7dee8311e621f399a2bdeb5e6c2e75eae2` was associated with **248 GitHub Actions workflow runs** in the Actions run query for that head SHA. The intended G04 A/B result job remained queued while this fanout existed.

This is infrastructure/evidence-topology evidence, not a product loss.

## Causal mechanism

A representative unrelated workflow, `.github/workflows/v030-logs-inverse-edge-sidecar-pack-oracle.yml`, declares a `pull_request` `paths:` filter containing old files that are already changed somewhere in the very large long-lived PR #56. GitHub evaluates PR path filters against the pull request change set, so synchronizing a new head can wake the workflow even when the newest commit did not touch that workflow's domain.

The workflow then performs a second, correct newest-commit classifier (`git diff-tree ... HEAD`) and normally skips the expensive result job. That protects expensive execution semantics, but it does **not** prevent GitHub from creating/scheduling the workflow and its classifier job in the first place. Repeating this pattern across a large v0.30 workflow population creates a classifier-fanout storm that competes for runner capacity with the small number of result-bearing jobs actually needed.

The observed G04 commit is a clean falsifier for “PR path filters already prevent irrelevant workflow activation”: its newest commit changed only `experiments/v030_g04_delimiter_inverse_ab.py`, yet unrelated logs/R4 workflows were instantiated for the same head.

## Engineering consequence

The current two-stage topology is semantically fail-closed but operationally expensive on a giant integration PR. The next CI-topology repair should preserve newest-head classification and every evidence threshold while moving deep/release admission *before* runner allocation where possible. For the authoritative integration branch, the simplest candidate class is branch-scoped `push` + `workflow_dispatch` for deep/release evidence, with PR triggers retained only where they provide unique review value. Another acceptable design is a small central dispatcher that invokes only matched reusable workflows, provided it preserves exact-head custody and cannot silently suppress required release evidence.

Do not mass-edit workflows merely to reduce a run count without proving that required release lanes remain reachable. The migration should first inventory which workflows are historical/deep versus normative release authority, then prove that every release-lock-required evidence lane has an explicit dispatch path.

Claim boundary: the `248` figure is the direct run-count returned for this exact head at observation time. It is not a count of 248 expensive benchmark jobs; many are expected to stop after their classifier. The defect is scheduler/runner fanout and evidence latency, not fabricated product failure.
