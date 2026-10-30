# J24I59 — Prospective full-PR performance admission on the Git-custody / Windows-hardlink stack

Status: **PREREGISTERED BEFORE CODE**. Research/evidence-enablement composition only. No merge, release, format/version/ABI change, performance threshold change or product acceleration credit.

## Authority and exact baseline (2026-10-30 UTC)
- Canonical `FCMO-AI/.CMPCT`, published `main@80c358f8824ec1b20d349c92ed94c898090969b0` v0.30.0, r24; v0.31 development unreleased.
- Exact parent: PR #832 `fe7669f7f1a07720187219200e24a972fa650f6b`, stacked on #831/#828. Parent's real three-host Git HEAD source-custody workflow #41058950458 SUCCESS; General Tests #41058950509 SUCCESS; r24/ZIP #41058950391 aggregate SUCCESS but `performance` job **SKIPPED** after last-commit-only scope classification. This green is *not* performance evidence.
- Original #320 `c7e3a101836c01363d69a5507bae1f628c39be9b` has already solved the exact issue #318 with Git-DAG source-scope court (#40055813865). #822 independently reused six exact #320 Git blobs on a **different #817 stack**. Do not replace #320 or #822; this experiment is source-exact integration in the #832 Git-custody/Windows hardlink stack.

## Primary question and prediction
Can the proven full-PR tree-diff classifier from #320 be composed unchanged with #832's Git HEAD custody and physical Windows hardlink/63-signed-generation branch, without relaxing source identity or causing CI topology/general-test regressions?
H1: all six donor files copy with **identical Git blob SHA** (not reimplementation); the exact candidate HEAD runs the 12-case real-Git DAG scope court, recognizes the original source-first/workflow-last #316 witness as RUN, and passes full General Tests, CI topology and engineering evidence. The benchmark `performance` job must actually run if the entire PR tree contains a performance input, even if the latest commit is only documentation.
H0/kill: a donor blob mismatch, a false SKIP for a materially changed PR, incorrect HEAD binding, lost parent source-custody three-host pass, any newly failing General Test, modified release/historical benchmark/format/threshold, or unjustified source-model drift. Preserve all negative and ambiguous outcomes.

## Six exact donor paths (Git SHA objects expected)
1. `.github/workflows/zip-parity.yml` `f77ba07cb6ee8dfa0c8cef0be7135a536a872efb`
2. `.github/workflows/v031-zip-scope-court.yml` `4ac716423c26d565dbb847b8430da60d8b472599`
3. `tools/classify_zip_parity_scope.py` `c7107c71733077a062c424cbf3ee4b94039bff13`
4. `tools/check_ci_topology.py` `1a2143ff517608379769d46749650bf7d006d35e`
5. `tests/test_v031_zip_parity_scope.py` `74b9b43b80cd489e97cc65d27cbc27e8f8daa876`
6. `tests/test_performance_base_native_wiring.py` `b413285c3e633c6ebd4ba9dd7be9ca276171a418`

## Strong controls and alternatives
- True A/A: six existing sources unchanged, only source-exact CI files change. On a PR based directly on #832, any full r24/ZIP ABBA compares candidate against #832; identical Builder/Reader/Writer sources mean any speed ratio must be treated as timing noise, not product credit.
- More meaningful *future* release control: a genuine full-stack comparison from the canonical v0.31 development base with the unchanged candidate harness and original outputs; a narrow stacked PR cannot prove the whole #832 hardlink stack against released main.
- Alternative last-commit-only selector already falsified by #316. The #822 route is valid but has a different parent/Reader stack. Reimplementation or modifying thresholds is rejected. The outer GitHub 3,000-file path-filter limit and post-checkout source mutation/race remain unresolved.

## Test and evidence ladder
1. Git-source SHA custody before implementation: read #832 current files and #320 donor; compare exact SHA and absence of overriding owners.
2. Commit this prereg separately *before* copying donor code. Copy exact blobs in one atomic tree/commit, no local modifications.
3. Source custody self-audit: donor SHA = candidate Git blob SHA on all six files, old v0.30 release lock SHA and product source blobs preserved.
4. Trigger real GitHub Actions: scope Git-DAG court, General Tests, CI Topology, Engineering Evidence, Version Discipline, native/fuzz where triggered, r24/ZIP classification; inspect **actual performance job** and raw artifact, not aggregate SUCCESS alone. Treat checks pending as pending.
5. If a material result is blocked by CI/infra, preserve exact status and do dependency-safe adjacent work; no weakening evaluator.
6. Record a small factual outcome and exact-head/actual-run evidence only after observing; do not update the shared Discovery STATE unless decision-changing scientific truth clearly warrants it and ownership is free.

## Costs, disproof and promotion boundary
- Cost: full-depth Git fetch and potentially extra full ABBA CPU/wall on genuine material PRs, justified by eliminating false-positive release gates. No archive bytes/CPU improvement claimed.
- Safety: wrong HEAD fails; missing/ambiguous merge ancestry runs; source rename deletion runs; clean docs-only may skip. All 12 existing DAG tests remain intact. Source-custody Git HEAD rules remain intact on all three hosts.
- Verification scope: do not conflate official r24/ZIP parity, source-custody success, Reader correctness, hardlink/fidelity, and full candidate-versus-published product release eligibility.
- This composition is a **draft integration experiment**; no merge/release without independently authorized review and complete applicable product/host evidence.
