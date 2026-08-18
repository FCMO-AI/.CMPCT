# T04 — Canonical release closure

- **Owner:** slot-00
- **Priority:** P0 after dependencies
- **State:** BLOCKED
- **Branch:** `agent/v030-authoritative-integration`
- **Dependencies:** T00, T01, T02, T03 must be DONE or have explicitly accepted residual non-release work.

## Objective

Turn the reconciled, benchmark-proven implementation into the actual v0.30 release without leaving research scaffolding, stale public claims, or unverified packaging behind.

## Scope

- final adversarial completion audit against `docs/V030_RELEASE_GATES.md` and root `AGENTS.md`;
- canonical version/format decision and version-discipline check;
- `docs/FORMAT.md`, `docs/CURRENT_STATE.md`, `docs/HISTORY.md`, `docs/NATIVE_CORE.md`, `docs/PORTABILITY.md`, release note and benchmark-history consistency;
- public API/CLI/package smoke and upgrade/fallback behavior;
- website generated only from accepted durable benchmark records;
- public-surface guard and no unrelated internal/sensitive material;
- GitHub Pages freshness/live verification;
- merge authoritative candidate to `main` only when every release lock is green;
- tag/release and post-merge/post-tag verification of the exact released bytes/code.

## Completion evidence

1. No release-critical task remains READY/CLAIMED/BLOCKED/REVIEW.
2. Normative release-gate ledger is completely green on one exact reconciled SHA.
3. Required durable benchmark/conformance records exist in-repo.
4. Numeric v0.30 version and r25 (if retained) are documented consistently across package, format, native, site, and release notes.
5. Public site claims are generated from accepted evidence, not copied from research prose.
6. `main` contains the release commit, tag/release points to it, and post-release smoke/reader/website checks pass.

Footnote: T04 is deliberately blocked until the hard engineering is complete. Presentation work must not create pressure to waive a native, benchmark, performance, locality, recovery, or competitor gate.
