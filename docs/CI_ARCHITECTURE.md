# CMPCT CI architecture

This document is the normative execution model for GitHub Actions in CMPCT.

The goal is not to weaken evidence. The goal is to stop unrelated or superseded work from consuming the runner budget needed by current tests, research, release gates, and GitHub Pages.

## Mission

CMPCT CI must preserve all substantive correctness, performance, hardening, portability, benchmark-honesty, and public-proof gates while minimizing redundant executions.

A healthy repository should preferentially spend runner time on the newest relevant commit, not on obsolete revisions or unrelated subsystems.

## The three lanes

### Fast lane

Purpose: ordinary PR feedback.

Typical contents:
- unit/integration tests relevant to the changed subsystem;
- native compile/lint/smoke gates when native code changed;
- public-surface checks when site/evidence files changed;
- short parser fuzz smoke when parser/decoder code changed.

Target: useful signal within roughly 5–10 minutes under normal GitHub availability.

Fast-lane workflows may run automatically on pull requests, but must be path-scoped when practical and must cancel superseded runs for the same PR/ref.

### Deep lane

Purpose: expensive mechanism validation and research evidence.

Typical contents:
- hostile-corpus sweeps;
- category-frontier runs;
- oracle/ceiling experiments;
- long fuzzing;
- exact-tree generalization checks.

Deep work must not run merely because any file in the repository changed. It must be one of:
1. path-scoped to the mechanism/subsystem it validates;
2. scheduled when continuous exploration is intentional; or
3. explicitly launched with `workflow_dispatch` when a research or promotion decision needs it.

A deep workflow that is automatically PR-triggered must use concurrency cancellation so only the newest revision for that PR/ref remains authoritative.

### Release lane

Purpose: promotion evidence, including the zero-byte archive-size regression rule and timing/noise policy.

Release gates remain mandatory before a numeric core release. They do not need to consume runner capacity for documentation-only, site-only, or unrelated research-only edits.

Release workflows may run automatically on relevant core changes and on `main`, and must always remain manually dispatchable for deliberate promotion/re-verification.

## Trigger discipline

1. Do not use a bare `push:` trigger for expensive workflows. Restrict automatic pushes to `main` or an explicitly documented release/integration branch.
2. Prefer `pull_request` for feature-branch validation so a feature-branch push is not duplicated by both `push` and `pull_request` events.
3. Use `paths`/`paths-ignore` to prevent unrelated subsystems from waking expensive workflows.
4. Historical one-shot evidence publishers become manual-only once their durable record has landed. Do not keep spending runners to rediscover that there is nothing left to publish.
5. Site/public-proof CI is validation, not the serving critical path. The live site is the generated static `gh-pages` tree described in `docs/GH_PAGES_DEPLOYMENT.md`.

## Supersession / concurrency

Every automatically triggered workflow that consumes a GitHub-hosted runner should normally define a concurrency group and use `cancel-in-progress: true`.

The group must collapse obsolete revisions of the *same logical work item* without cancelling independent PRs or unrelated scheduled jobs. A safe pattern is:

```yaml
concurrency:
  group: cmpct-<lane>-${{ github.event_name }}-${{ github.event.pull_request.number || github.ref }}
  cancel-in-progress: true
```

Do not share one global concurrency group across unrelated benchmarks: that would serialize useful work and can hide independent failures.

## Capacity reservation

Deep research must not be allowed to consume every available standard runner during active development.

Operational target:
- keep ordinary steady-state queued work in the single digits when possible;
- avoid sustained queues above the account concurrency limit;
- keep enough capacity free for fast tests, native checks, public-proof/site verification, and the GitHub Pages deployment job;
- when many agents are pushing rapidly, obsolete runs should disappear through concurrency cancellation rather than accumulate.

If CMPCT again reaches hundreds of queued runs, treat that as a CI-topology regression even if individual jobs are correct.

## Expected demand reduction

The optimization target is architectural, not a claim that every PR has identical shape:
- ordinary changes should wake roughly 3–6 relevant workflows rather than 20+ broad workflows;
- path routing should remove about 70–85% of irrelevant automatic fan-out on typical changes;
- supersession-aware cancellation can remove >90% of obsolete work during rapid multi-commit/agent bursts;
- duplicate feature-branch `push` + `pull_request` execution should be eliminated wherever the PR event already supplies the required authority.

These percentages are engineering targets derived from the observed failure mode, not benchmark guarantees. Measure queue depth and workflow counts after rollout and revise the topology using evidence.

## Evidence must not be lost

CI optimization may change *when* a check runs. It must not silently weaken *what evidence is required for promotion*.

In particular:
- numeric releases still require the release performance gate and durable public benchmark records;
- deterministic archive-size regression remains 0 B at promotion;
- timing, hardening, portability, recovery and public-proof requirements remain in force;
- deep research evidence may be delayed/manual/path-scoped, but if a release or PR claim depends on it, that evidence must run and be durable before the claim is accepted.

## Workflow-change ratchet

Any new or materially edited workflow must declare a `# ci-lane: fast|deep|release|scheduled|publisher` comment near the top and satisfy the topology rules checked by `tools/check_ci_topology.py`.

Legacy workflows are not permission to add new broad triggers. When touching a legacy workflow, improve its routing/cancellation at the same time unless there is a concrete reason not to; document any exception next to the trigger.

## Completion rule for CI work

A CI-architecture change is complete only when:
1. the changed workflows pass the topology checker;
2. no substantive evidence gate was deleted or weakened without an explicit replacement;
3. duplicate/unrelated triggers are reduced;
4. superseded-run cancellation is present where safe;
5. the change does not make GitHub Pages depend on heavyweight benchmark workflows;
6. the repository records the rationale so future agents do not regress the topology.

Footnote: paying GitHub for additional concurrency can increase headroom, but it is a capacity multiplier, not a substitute for this topology. A 3× larger runner allowance can still be saturated by 10× redundant fan-out.
