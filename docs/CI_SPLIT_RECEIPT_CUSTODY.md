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
4. the classifier inspects `git diff-tree --no-commit-id --name-only -r HEAD`;
5. the expensive job depends on the classifier and runs only when current authority says the candidate requires that evidence.

Example:

```yaml
jobs:
  latest-head-impact:
    concurrency:
      group: cmpct-example-classifier-${{ github.event.pull_request.number || github.ref }}
      cancel-in-progress: true
    # exact checkout + HEAD classifier

  exact-receipt:
    needs: latest-head-impact
    if: needs.latest-head-impact.outputs.run_deep == 'true'
    concurrency:
      group: cmpct-example-receipt-${{ github.event.pull_request.head.sha || github.sha }}
      cancel-in-progress: false
    # exact checkout + result-bearing evidence
```

A newer synchronization may cancel an obsolete classifier. It cannot cancel an already-started exact receipt because that job occupies a different concurrency group. However, cancellation **before admission is safe only if the newer classifier cannot erase an unmet evidence obligation**. A measured v0.30 incident exposed the corner case: commit A changed the release fingerprint, its queued classifier had not yet admitted the expensive authority, then a non-fingerprint commit B superseded that classifier and classified only B's diff. The candidate still needed new evidence, but neither run had admitted it.

For final generalization/runtime authority, `v030-authoritative-v2-pr.yml` therefore derives impact from the same `docs/V030_RELEASE_LOCK.json` fingerprint globs that define receipt identity, rather than a narrower hand-written release surface. The regression ratchet lives in `tests/test_v030_ci_topology_split_receipts.py`, which is itself fingerprinted. This is deliberately fail-closed: an uncertain release-fingerprint mutation may spend compute, but it may not inherit stale compression/runtime authority.

Subsystem classifiers may remain narrower where they are used only for incremental feedback. **Final release acceptance is different:** every normative receipt still has to match the frozen candidate fingerprint, so a classifier-only skip never grants release credit. If a subsystem did not rerun automatically on that frozen fingerprint, its final acceptance lane must be run explicitly before its task/receipt can close.

## Evidence law is unchanged

This policy changes scheduling only. It does not permit an old receipt to authorize a new candidate. A receipt remains useful only for its exact source SHA and, when required, exact release fingerprint. Final v0.30 authority still requires all normative receipts to match the reconciled release candidate.

The policy may not:

- weaken size, timing, locality, recovery, integrity, native/platform or competitor gates;
- turn classifier-only green into substantive evidence;
- cancel an already-running exact receipt merely because a newer commit exists;
- hide preprocessing, verification, publication or recovery costs;
- use benchmark identity in product policy.

## Ratchet

`tools/check_ci_topology.py` validates `split-classifier-preserve-receipts`. `tests/test_v030_ci_topology_split_receipts.py` additionally pins the migrated high-cost authorities so they cannot silently return to workflow-level exact-SHA concurrency, and pins authoritative-v2 admission to the release-fingerprint manifest.

The ratcheted authorities are:

- `android.yml`;
- `v030-native-authority.yml`;
- `v030-final-release-authority.yml`;
- `v030-canonical-authority.yml`;
- `v030-external-competitors.yml`;
- `v030-authoritative-v2-pr.yml`;
- `v030-r25-manifest-canonical-integration.yml`;
- `v030-r25-manifest-derived-identity.yml`;
- `v030-r25-manifest-canonical-candidate.yml`;
- `v030-r25-manifest-implicit-reader-productization.yml`;
- `v030-r25-manifest-writer-admission.yml`;
- `v030-federated-generalization-admission.yml`;
- `v030-federated-candidate-productization.yml`;
- `v030-logs-sidecar-content-policy.yml`;
- `v030-logs-inverse-profile-productization.yml`.

The all-15 admission lane is included because its result-bearing proof may run for up to six hours and remains useful for its exact source, while classifier-only invocations on the long-lived integration PR are pure routing work. PR-wide non-cancelling workflow concurrency serialized those obsolete classifiers behind older receipts; split custody preserves the exact all-15 receipt without granting unrelated commits a durable queue slot.

The federated candidate productization lane uses the same policy for its up-to-three-hour Office/Analytics productization and portability receipt. The productization result is useful for its exact source once admitted; accumulated-PR classifier invocations are not. Separating them prevents unrelated integration commits from waiting behind or preserving obsolete routing work while keeping the exact result-bearing receipt non-cancellable.

The Logs D5 lanes use the same custody rule for the strict path-invariant sidecar content-policy oracle and the recoverable canonical-filesystem inverse-profile productization proof. Both receipts are useful for their exact source once admitted; neither justifies preserving obsolete accumulated-PR routing work. Their four-way ZIP/Zstd, recovery, locality, strong-verification and no-release-credit laws are unchanged by the scheduling split.

The implicit-v4 D5 chain now uses the same split custody from its derived-identity oracle through reader productization, writer admission, and the up-to-three-hour canonical-candidate gate. These jobs already carry exact reconstruction, semantic-identity, locality and fail-closed product boundaries; the migration removes only obsolete classifier queue ownership. Once any substantive job is admitted, its exact-SHA receipt remains non-cancellable and cannot be inherited by a later candidate.

Hosted Android follows the same law because its newest-head classifier is cheap routing but its emulator/JNI/conformance run is a release-critical, fingerprint-bearing platform receipt that can occupy a runner for up to one hour. Obsolete Android classifiers may now be superseded, while an admitted hosted-emulator proof remains non-cancellable for its exact source SHA. The separate physical-ARM64 workflow is deliberately not converted: it has no classifier split and intentionally grants the scarce physical device to the newest explicitly requested candidate.

Other deep/release workflows should migrate when touched if they combine exact-receipt preservation with a newest-head classifier. Retired or genuinely one-shot workflows should instead become manual-only when repository doctrine permits it.

## Reopening predicate

Revisit this model if GitHub changes concurrency/path semantics, CMPCT stops using a long-lived integration PR, or measured queue behavior shows that split custody does not reduce obsolete classifier backlog while preserving result-bearing receipts. Any replacement must satisfy all three properties simultaneously: **obsolete routing does not starve runners, admitted result-bearing evidence is not destroyed, and classifier supersession cannot erase an unmet exact-fingerprint evidence obligation.**
