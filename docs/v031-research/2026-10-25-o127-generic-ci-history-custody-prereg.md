# O127 — historical-source custody in general CI (preregistration)

Date: 2026-10-25 UTC. Owner: Phased2 independent CI/evidence-enablement lane. Source base: PR #455, commit `2fbdba24d0dfb29231c3710eb9b272a2aea89b9b`. The canonical `agent/v031-development` branch is still `4545d7d5b2a0b712b4b00f5a9c291d4a3a9e169b`.

## Baseline observation and question

PR #455 generic-tests GitHub Actions run [40217166617](https://github.com/FCMO-AI/.CMPCT/actions/runs/40217166617), job 121240942402, reports 838 pass / 7 skip / 11 fail. Its exact-head checkout uses `actions/checkout@v4` without `fetch-depth` (default shallow depth one). Seven failures call `git show` / `git rev-parse` for *actual immutable historical source commits* `29d9688a`, `4545d7d5`, and `7efcc511`; logs report these historical paths unavailable in the shallow checkout. Four distinct failures concern release/surface/fingerprint assertions. This is an evidence-custody gap, not evidence that the historical Builders or product outputs are wrong.

**Falsifiable hypothesis:** a full-ref checkout at the same exact candidate HEAD makes the immutable historical source objects available and cures *only* the history-dependent failures, without changing any tests, benchmark controls, source implementation, or the four independent release/surface failures.

## Alternative controls considered

- **Keep the shallow checkout and skip/history-condition the seven tests:** rejected as evaluator weakening.
- **Inject historic source text from current code:** rejected as false provenance.
- **Fetch hard-coded historical SHA objects one by one:** potentially cheaper network I/O, but couples generic CI to every new fixed-source oracle and may be blocked for unadvertised objects.
- **Use `fetch-depth: 0` on the existing exact-HEAD checkout:** one concise source-transparent correction. It costs network/time and must be priced. May not fetch orphaned commits that no advertised ref reaches.
- **Separate full-depth Git history hydration step:** higher complexity than the minimal test first; reserve only if a real cost or material portability failure appears.

## Frozen predictions / decision

1. `git rev-parse --is-shallow-repository` must report `false` after the corrected checkout.
2. `git cat-file -e <sha>:src/cmpct/builder.py` must pass for all three frozen SHA controls (not re-created source). The original logged shallow checkout fails these checks.
3. Rerunning the *unchanged* full regression suite should eliminate the seven historical-object failures; its four unrelated legacy assertion failures may remain red. A green suite is **not** a requirement for scientific validation, nor may the workflow mask a nonzero pytest exit.
4. Failure of (1) or (2) kills the proposed custody fix. If a required SHA remains unavailable with complete advertised history, use precise branch/commit provenance instead of relaxing its tests.
5. Compare checkout wall-time/cost on the same GitHub-hosted runner class against the baseline job logs. Lack of a controlled same-runner repetition forbids strong performance claims.

## Mutation boundary

Only the generic `.github/workflows/tests.yml` checkout / historical-custody assertion is in the repair surface, plus durable research/evidence records. Leave Builder/Reader, historical controls, release thresholds, branch and format authority, and performance workflows unchanged. PR #455 remains the exact experimental base; no merge to canonical is claimed or authorized by this experiment.

## Scientific outcome classification

This is CI/evidence-enablement, **not** a product correctness fix or a compression/throughput gain. Product credit 0; release credit 0 until normal promotion law is satisfied.