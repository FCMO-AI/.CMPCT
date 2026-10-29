# J24M01i — prevent foreign-namespace JUnit target impersonation (prospective 2026-10-29 UTC)

**No product, core, release, threshold or format modification authorized.** Owner PR #769, specific source HEAD `2b76dcb800c5a1dc98e13ed74a018d0af715613e`. This preregistration predates any code edit for this hypothesis.

## Existing result and new source-derived concern

The genuine [full-suite exact-head artifact #12917515918](https://github.com/FCMO-AI/.CMPCT/actions/runs/40917140647/artifacts/12917515918) records one authentic target `classname=tests.test_j24v01_sparse_verify_streamed`, `name=test_real_256m_sparse_verification_does_not_materialize_holes`; original head `8c99a162`, 806 pass / 4 inherited fail. Existing independent helper `tools/j24m01g_junit_custody.py` blob `e7abc6cd21f2d39a78a8dd88bb0e18391c07062f` accepts a classname if **only its last dot-separated basename** matches `test_j24v01_sparse_verify_streamed`. This is too broad for a proof of exact module identity. A fixture with `classname=decoy.test_j24v01_sparse_verify_streamed` and identical case name could impersonate the missing real test. This is a **derived synthetic-receipt concern**, not a claim of malicious GitHub-provider artifact compromise.

## Primary prediction and cheapest decisive negative

Create an independent synthetic JUnit fixture that retains the exact test name and changes only classname to an alternative prefix ending in the expected basename. Existing helper incorrectly returns success; stronger exact-classname comparison must reject it. The genuine actual provider artifact with `tests.test_j24v01_sparse_verify_streamed` must still pass, as must all existing 9 hostile/positive fixtures. Add a direct `wrong_namespace` fixture. This is a targeted semantic strengthening of the JUnit evidence validator, not a change to product resource verification.

## Controls, kill and debt

- Require `classname == 'tests.test_j24v01_sparse_verify_streamed'` **exactly**, observed from authentic provider XML; reject similarly suffixed alternate namespaces. Preserve duplicate/missing/notrun/skipped/failure/error/malformed detection and no test-exit laundering.
- If authentic current provider XML uses a different legitimate exact classname on a supported context, stop and preserve a red instead of broadening matching to convenience.
- Re-pin the validator and synthetic fixture *Git blob* in the existing hosted source-custody workflow; do not remove other source pins. Any stale workflow preflight is RED until reconciled.
- Require a hosted current-head focused + genuine full-order result; from a locally proven condition alone credit only research-instrument evidence, not new product behavior.
- Avoid redundant parallel implementation or changes to `docs/discovery/STATE.json` (#574 authority), v0.30 historical release files, Reader/Builder, original strict 128MiB resource ceiling, benchmark comparators, or #749 same-UID publication-security blocker.

## Alternatives/self-critique

Keeping basename matching is simpler but cannot support a full module identity claim. Requiring broad XML suite-wide signatures/cryptographic provenance is unnecessary complexity when exact-class binding plus original provider ZIP hashes/head identity resolve this narrow false-green. This proof hardens a research receipt, not the completeness of all other CI outcomes or against a malicious privileged actor rewriting both artifact and source. Simpler strong control is the authentic existing provider XML itself.
