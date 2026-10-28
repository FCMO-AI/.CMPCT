# T04 — Canonical release closure

- **Owner:** v0.30 sole executor
- **Priority:** P0 after dependencies
- **State:** BLOCKED
- **Branch:** `agent/v030-authoritative-integration`
- **Dependencies:** T00, T01, T02 and T03 must reach their required completed implementation/evidence state before T04 can become `REVIEW`. The executable lock itself requires T00–T03 = `DONE`; residual research may remain only when it is explicitly outside the promoted v0.30 product path.

## Objective

Turn the reconciled, benchmark-proven implementation into the actual v0.30 release without leaving research scaffolding, stale public claims, or unverified packaging behind.

## Release-order invariant

The final release fingerprint includes canonical format/native/portability documentation, `docs/releases/v0.30.0.md`, and generated site source. Therefore **public/release source must be prepared before the final fingerprint and receipts are minted**. Otherwise a legitimate final site/release-note edit would invalidate every earlier receipt.

Required order:

1. Finish the T01/T02/T03 implementation deltas directly on the authoritative branch; no other branch is release authority.
2. Reconcile current `main` again if it moved, then complete T00 final regression/adversarial review and move T00 to `DONE` only when the integrated technical candidate is coherent.
3. Complete canonical version/format/release-note/docs/site source from already accepted durable facts. Do not publish or merge yet.
4. Set T01/T02/T03 to `DONE` only after their implementation and durable evidence obligations are genuinely closed. Move T04 from `BLOCKED` to **`REVIEW`** once the final release/public source is present and internally consistent.
5. Freeze the release-critical content fingerprint with:

   ```bash
   python -m experiments.entropygraph_v030_release_lock_strict --print-fingerprint
   ```

6. Run/re-run every final authority gate whose receipt is required on that exact fingerprinted source. Commit strict-JSON evidence and evidence-bound receipts. A pre-freeze research artifact may support diagnosis, but cannot substitute for a required final receipt.
7. Run the strict release lock. **Only `UNLOCKED` authorizes irreversible release actions.**
8. Merge the exact candidate to `main`, create the v0.30.0 tag/release, deploy/verify the public site, and run post-merge/post-tag smoke against the released bytes/code.
9. Only after those irreversible actions and post-release checks succeed may T04 move from `REVIEW` to `DONE`.

Footnote: T04 intentionally sits at `REVIEW` when the pre-release lock opens. Requiring T04 `DONE` before unlock would be circular because `DONE` includes merge/tag/live verification, which the lock exists to authorize.

## Scope

- final adversarial completion audit against `docs/V030_RELEASE_GATES.md`, `docs/V030_EXECUTION_MODEL.md`, and root `AGENTS.md`;
- canonical version/format decision and version-discipline check;
- `docs/FORMAT.md`, `docs/CURRENT_STATE.md`, `docs/HISTORY.md`, `docs/NATIVE_CORE.md`, `docs/PORTABILITY.md`, release note and benchmark-history consistency;
- public API/CLI/package smoke and upgrade/fallback behavior;
- website generated only from accepted durable benchmark records;
- public-surface guard and no unrelated internal/sensitive material;
- GitHub Pages freshness/live verification;
- merge authoritative candidate to `main` only when the strict release lock is green;
- tag/release and post-merge/post-tag verification of the exact released bytes/code.

## Pre-release REVIEW evidence

Before T04 may enter `REVIEW`:

1. T00–T03 are `DONE` on the authoritative branch according to the release manifest.
2. Canonical v0.30.0/r25 source, release note, documentation and site source exist and contain no unsupported claim.
3. Website headline numbers are derived from durable accepted benchmark records, not copied from research prose.
4. Version discipline/public-surface/site source checks are green or represented by exact required final evidence to be rerun on the frozen fingerprint.
5. No release-critical source edit is planned after the fingerprint freeze. Any such edit invalidates affected receipts and requires the lock to be satisfied again.

## Post-unlock DONE evidence

T04 becomes `DONE` only when:

1. the strict lock was `UNLOCKED` on the exact pre-merge candidate;
2. `main` contains that release candidate without unreviewed semantic changes;
3. the v0.30.0 tag/release points to the intended release commit;
4. package/archive reader smoke passes against released artifacts;
5. GitHub Pages is fresh and live-site claims match committed accepted evidence;
6. post-release version/public-surface checks are green;
7. any release-time failure is either corrected with a new fingerprint + revalidated lock or the release is explicitly not declared complete.

Footnote: presentation is part of the release artifact but never a reason to waive native, benchmark, performance, locality, recovery, Android, or competitor evidence. The order above prevents presentation changes from silently invalidating technical receipts after they have already been accepted.
