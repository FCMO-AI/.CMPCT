# GitHub Actions instructions

These instructions apply to `.github/**` and are subordinate to the root `AGENTS.md` quality/evidence rules.

Before editing a workflow, read `docs/CI_ARCHITECTURE.md`.

## CI is a scarce execution surface

GitHub-hosted runner capacity is part of CMPCT's engineering budget. A workflow that is individually correct but wakes on unrelated changes, duplicates another event, or lets obsolete revisions accumulate is a repository regression.

Do not weaken correctness, performance, hardening, portability, benchmark-honesty, or public-proof requirements merely to reduce queue depth. Optimize *routing and supersession*, not evidence quality.

## Mandatory lane declaration

Every new or materially edited workflow must declare one of these comments near the top:

- `# ci-lane: fast`
- `# ci-lane: deep`
- `# ci-lane: release`
- `# ci-lane: scheduled`
- `# ci-lane: publisher`

Use the definitions in `docs/CI_ARCHITECTURE.md`.

## Automatic-trigger rules

For workflows that consume GitHub-hosted runners:

1. Do not use bare feature-branch `push` plus `pull_request` for the same authority. Prefer PR validation and restrict push execution to `main`/explicit integration branches.
2. Add `paths` or `paths-ignore` when the workflow is not universally relevant.
3. Deep/release workflows must not wake for site-only/docs-only changes unless those files materially affect their evidence contract.
4. Add a concurrency group scoped to the logical PR/ref and `cancel-in-progress: true` whenever superseding an old revision is safe.
5. Never use one global concurrency group to serialize unrelated PRs or unrelated research hypotheses.
6. Historical one-shot publishers become `workflow_dispatch`-only after the durable target exists.
7. Keep GitHub Pages serving independent from heavyweight CI. `gh-pages` is the static serving branch; Actions validate source/evidence and GitHub's own Pages deployment may still consume a runner slot.

## Fast / deep / release separation

Fast CI should provide ordinary PR feedback without requiring every expensive compression experiment. Deep research runs only when its mechanism/subsystem changed, on an intentional schedule, or by explicit dispatch. Release gates remain mandatory at promotion and must stay manually dispatchable.

If a PR claim depends on a deep benchmark, the fact that the workflow is no longer universal does not waive that benchmark: run it and preserve its evidence before accepting the claim.

## Workflow edits must pass the topology ratchet

Run:

```bash
python tools/check_ci_topology.py <changed workflow paths...>
```

The PR workflow `.github/workflows/ci-topology.yml` runs the same policy against changed workflow files.

Do not bypass the checker with a vague exemption comment. If an automatic workflow genuinely cannot use cancellation/path routing, explain the exact authority/invariant next to the trigger and update the checker deliberately if the architecture truly requires it.

## Queue-health completion test

When changing CI architecture, inspect resulting workflow fan-out. The target is not a magical fixed number, but ordinary commits should wake only relevant lanes; obsolete revisions should cancel; sustained hundreds-deep queues are a CI-topology failure.

Footnote: more paid GitHub capacity is useful headroom, but it is not permission to regress routing. A larger account limit should make good CI faster, not make waste invisible.
