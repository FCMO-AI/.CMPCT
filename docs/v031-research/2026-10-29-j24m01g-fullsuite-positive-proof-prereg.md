# J24M01g — full-suite positive execution custody (preregistered 2026-10-29 UTC)

**RESEARCH/EVIDENCE GATE ONLY; no Reader, Builder, format, benchmark, threshold, release or product change.**

## Authority and baseline

This work continues the existing J24M01f owner PR #769 at `79f010e537b1a4d10259bad9319746fbbc993e88`, stacked on #738 exact `ec112a87ea34349b63885f3f0bea4689f192bd2f`. Published main remains v0.30.0/revision-24. Full-suite source-exact [run #40908930197](https://github.com/FCMO-AI/.CMPCT/actions/runs/40908930197) completed at 16:17 UTC: `797 passed, 4 failed`; the four failures are historical release/fingerprint/attribution tests. Independent exact-head regular [CMPCT Tests #40908930158](https://github.com/FCMO-AI/.CMPCT/actions/runs/40908930158) independently reported the same `797 passed, 4 failed` and preserved its failure outcome.

J24M01f's focused court was successful (3/3). Yet its full-suite workflow currently tests only that the resource test's **FAILED** line does not appear in textual pytest output. That predicate can pass if the test is *skipped*, *not collected*, renamed or otherwise omitted while unrelated suite tests run. This is evidence admission debt, not evidence that the sparse test actually failed.

## Primary falsifiable question

Can an orthogonal structured test-report audit certify that the genuine 256-MiB sparse resource test was **collected once, executed and PASSED**, even when the full suite has unrelated inherited reds, without changing the existing test execution, its strictly less-than 128 MiB ceiling, original subprocess, source blobs or failure exit code?

## Selected lowest-cost intervention

1. Run the existing `python -m pytest -q` full suite with `--junitxml=.../full-suite.xml` only for test-execution evidence, retaining the real pytest exit code, full stdout and all independent failures.
2. Add one small standard-library XML auditor. Match exact test case name `test_real_256m_sparse_verification_does_not_materialize_holes` and basename `test_j24v01_sparse_verify_streamed` in its classname. Require exactly one matching testcase; reject an absent, skipped, error or failed testcase and malformed XML. Require report root to be `testsuites` or `testsuite`. Do not infer overall-suite PASS from this focused result.
3. Add independent fixtures that deliberately falsify the auditor on missing/skipped/failed/duplicate/malformed and accept one passing example. Preserve all raw receipts.
4. Authenticate unchanged Reader/Builder and resource test source blob in hosted workflow. Do not rewrite historical/frozen workflows or another agent's PR.

## Alternative explanations, stronger control and kill

A simple grep for absence of `FAILED` is insufficient; grepping for a `PASSED` line would require altering reporting verbosity and still be brittle. XML is an independent reporter supplied by pytest and produces explicit result semantics without changing the evaluator. If emitted XML does not contain the actual case in the expected class/name, **fail closed** and inspect the real report; do not broaden matching merely to make a workflow green. If adding XML alters suite semantics or material overhead, revert and report it.

## Decision rules

The scientific court becomes evidence-complete only if source-exact JUnit contains exactly one **passed** target, all negative-custody synthetic cases fail, the original full suite continues to report its real exit and all four unrelated failures remain visible (unless independently explained by concurrent source changes). A green evidence job is not a green product suite, benchmark, compaction security verdict, merge or release. Branch ownership remains #769; #738 owns compaction implementation. This intervention does not modify the shared staleable discovery cache.
