# J24M01j — syntax provenance and JUnit exact-identity repair, preregistration

Date: 2026-10-29 UTC
Status: preregistered **before correction**; experiment-only evidence enablement, no product or release promotion.
Starting HEAD: `03e3357902b5a0a5691f5dc22ea297b2045bb4f5` on PR #769.
Original hosted red: [J24M01f run #40921490475](https://github.com/FCMO-AI/.CMPCT/actions/runs/40921490475) (focused and full-suite custody jobs FAILURE); general [#40921490449](https://github.com/FCMO-AI/.CMPCT/actions/runs/40921490449) (14 failures, 797 passes, all 10 new JUnit cases failed plus four existing release/fingerprint tests).

## Question and baseline
An earlier same-basename JUnit identity check could issue a false green. The strengthened exact-module check at `tools/j24m01g_junit_custody.py` is syntactically invalid at HEAD above. Real hosted logs show `SyntaxError: unmatched ']'` (line 27). Source inspection identifies a **literal backslash-n embedded in a comment** immediately before `matches = [`; it comments out the assignment while leaving the closing `]` syntactically unmatched.

## Falsifiable hypothesis
Replacing the single literal `\\n` sequence in that comment with an actual line ending (no other decision-path change) will make the audit code parse and preserve exact `classname == 'tests.test_j24v01_sparse_verify_streamed'`, exact `name`, uniqueness, and fail-closed status semantics.

## Controls and alternatives
- Negative baseline: exact original Git blob + actual hosted traceback (do not reclassify).
- Cheap syntax gate: `python -m py_compile tools/j24m01g_junit_custody.py` must reject inherited content and admit corrected content.
- Stronger behavioral control: the ten existing hostile JUnit cases must pass, including a real positive and same-basename wrong-namespace negative. Do not change those ten expected outcomes.
- Actual full-suite JUnit should authenticate the real sparse verifier exactly once and preserve original `pytest` exit code and its four historical release/fingerprint failures. The repaired script cannot claim the suite globally green.
- Alternatives rejected: loosening classname matching reopens false green; deleting the auditor would drop a required attribution guarantee; suppressing pytest failures would defeat the scientific court.

## Kill conditions
If after this minimal syntax change any of the ten cases does not show the originally expected result, or authentic JUnit cannot be recognized, do not narrow the evaluator or relabel an error as product evidence; inspect raw exact-head XML. No change to original 256-MiB sparse workload, strict 128-MiB limit, released product code, format, release/CI gates, or Discovery state is permitted.

## Evidence and timing boundaries
No repaired exact-head CI exists at preregistration. Previous positive source-bound memory evidence is on older heads only (#40917140647) and must not be counted as a success for this pending change. Exact new HEAD and GitHub Actions run identities must be recorded afterward. Scientific outcome, product promotion, and general suite remain distinct. Concurrent owners: #738 product, #574 shared Discovery; this fix is solely inside the already-owned PR #769 audit.
