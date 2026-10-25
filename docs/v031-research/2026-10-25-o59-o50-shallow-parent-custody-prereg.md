# O59 — Exact frozen O47-parent source for shallow checkout O50 tests

**Date:** 2026-10-25. **Status:** preimplementation diagnostic and falsifiable plan; not product or release evidence.

## Observed source-bound failure

Unmodified O50 [PR #405](https://github.com/FCMO-AI/.CMPCT/pull/405) / head `17c96603e33b02b3f2f9e0079eec2b128f293be8` has dedicated clean-installed three-OS [O50 court #40158561118](https://github.com/FCMO-AI/.CMPCT/actions/runs/40158561118) SUCCESS, but generic [Tests #40158561054](https://github.com/FCMO-AI/.CMPCT/actions/runs/40158561054) failed 7/797 cases: four inherited release-fingerprint/surface expectations and three **new O50** `tests/test_v031_builder_parent_parity_o50.py` failures. The latter are `git show 29d9688ae6bff6d1eccc27f019893866abe5b5c3:src/cmpct/builder.py` returning exit 128 under the generic checkout. This is missing historical source custody, *not* a measured byte-parity failure.

## Single primary question and prediction

Can the **unchanged original O47 parent Builder source**, cryptographically bound to Git blob `6f60dfe63742ff4b777f959a15d6fb828ae29610`, be executed by the existing O50 parent-versus-composed byte oracle under both a full-history checkout and a shallow checkout, without skipping, weakening, or replacing any of the three original assertions?

**Prediction:** freeze a byte-exact copy of the 21,980-character parent Builder as a small executable source fixture; when the **exact parent commit** is present, prefer `git show` and fail closed on path errors; otherwise, load the frozen fixture only if its independent Git-object SHA-1 equals the historical blob above. Both paths must use the existing isolated Python module and real installed cmpct runtime. The resulting source must be identical at byte level, not merely semantically equivalent. Run the original 3 O50 A/B tests from a *clean installed* package under independent shallow/full GitHub-hosted checkouts; retain original PASS/SKIP/JUnit and output hashes. The historical upstream comparison semantics remain unchanged.

**Kill conditions:** fixture Git blob differs; full and shallow paths load different bytes; any original test fails; source import resolves to repository checkout rather than installed package; the test no longer compares complete archives and SHA; Windows/POSIX source expectations are silently changed. Preserve any such negative. A green wrapper with skipped substantive tests is failure.

## Alternatives

- Fetch full history for all generic CI: network/setup cost on every PR and fragile access to historical commits.
- Mock the original Builder or reconstruct it from a guessed delta: loses historical source authority.
- Turn the O50 source-comparison tests off in generic CI: weakens evidence.
- Frozen exact Git-blob fixture + prefer real parent when present: bounded, portable, auditable, compatible with shallow/full history.

## Scope and promotion

Independent child of O50; do not mutate #405's owner branch or source-locked historical courts. Test/evidence enablement only, zero product, format, comparator, threshold or release change. The original O50 workflow may deliberately reject a modified test blob; a new O59 workflow must bind that new blob separately rather than weakening O50's original lock. Four inherited release-custody reds remain external debt; a focused O59 PASS cannot claim full generic suite success or release promotion.
