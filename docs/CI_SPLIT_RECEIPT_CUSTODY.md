# Split classifier / exact-receipt custody

Status: normative supplement to `docs/CI_ARCHITECTURE.md` for long-running deep/release workflows on long-lived PRs.

## Why this exists

GitHub evaluates `pull_request.paths` against the accumulated PR diff. On a long-lived integration PR, a release workflow can therefore wake on a newest commit that did not change its subsystem. CMPCT's newest-head classifier correctly prevents the expensive job from running, but the historical exact-receipt topology placed **workflow-level** concurrency on the exact candidate SHA with `cancel-in-progress: false`.

That combination protects result-bearing receipts, but it also gives every classifier-only workflow invocation a unique, non-cancellable concurrency group. During rapid branch movement those tiny classifiers accumulate in the Actions queue. Once the queue reaches hundreds of runs, release-critical jobs can be starved even though most queued work would immediately classify out. `docs/CI_ARCHITECTURE.md` defines that state as a CI-topology regression.

## Queue-safe custody model

A workflow using the split policy declares:

```yaml
# ci-cancel-policy: split-classifier-preserve-receipts
# ci-pr-scope: latest-head-commit-gate
```

It does **not** use workflow-level concurrency. Instead:

1. `latest-head-impact` (or the equivalent cheap routing job) uses a PR/ref scheduling group and `cancel-in-progress: true`;
2. each expensive result-bearing job uses an exact-SHA job group and `cancel-in-progress: false`;
3. checkout and evidence remain bound to `EVIDENCE_HEAD`;
4. the classifier still inspects `git diff-tree --no-commit-id --name-only -r HEAD` only;
5. the expensive job still depends on the classifier and runs only when the newest exact commit can affect its evidence surface.

Example:

```yaml
jobs:
  latest-head-impact:
    concurrency:
      group: cmpct-example-classifier-${{ github.event.pull_request.number || github.ref }}
      cancel-in-progress: true
    # exact checkout + HEAD-only classifier

  exact-receipt:
    needs: latest-head-impact
    if: needs.latest-head-impact.outputs.run_deep == 'true'
    concurrency:
      group: cmpct-example-receipt-${{ github.event.pull_request.head.sha || github.sha }}
      cancel-in-progress: false
    # exact checkout + result-bearing evidence
```

A newer synchronization may cancel an obsolete classifier. It cannot cancel an already-started exact receipt because that job occupies a different concurrency group. If an older classifier has not yet admitted its expensive job, cancelling it is correct: no result-bearing work has begun and the newer exact head owns routing priority.

## Evidence law is unchanged

This policy changes scheduling only. It does not permit an old receipt to authorize a new candidate. A receipt remains useful only for its exact source SHA and, when required, exact release fingerprint. Final v0.30 authority still requires all normative receipts to match the reconciled release candidate.

The policy may not:

- weaken size, timing, locality, recovery, integrity, native/platform or competitor gates;
- turn classifier-only green into substantive evidence;
- cancel an already-running exact receipt merely because a newer commit exists;
- hide preprocessing, verification, publication or recovery costs;
- use benchmark identity in product policy.

## Ratchet

`tools/check_ci_topology.py` validates `split-classifier-preserve-receipts`. `tests/test_ci_topology_split_receipts.py` additionally pins the migrated high-cost authorities so they cannot silently return to workflow-level exact-SHA concurrency.

As of the first migration, the ratcheted authorities are:

- `v030-native-authority.yml`;
- `v030-final-release-authority.yml`;
- `v030-canonical-authority.yml`;
- `v030-external-competitors.yml`;
- `v030-authoritative-v2-pr.yml`;
- `v030-r25-manifest-canonical-integration.yml`.

Other deep/release workflows should migrate when touched if they combine exact-receipt preservation with a newest-head classifier. Retired or genuinely one-shot workflows should instead become manual-only when repository doctrine permits it.

## Reopening predicate

Revisit this model only if GitHub changes concurrency/path semantics, CMPCT stops using a long-lived integration PR, or measured queue behavior shows that split custody does not reduce obsolete classifier backlog while preserving result-bearing receipts. Any replacement must satisfy both properties simultaneously: **newest relevant work gets runner capacity, and exact result-bearing evidence is not destroyed.**
