# J24I04 — Full-matrix identical-engine A/A provenance and chronology falsifier

**2026-10-28 UTC · Preregistered before any J24I04 instrument or hosted measurement. Research only; NOT release evidence.**

## Source and inherited decision

- Authoritative comparator: unmodified `benchmarks/zip_parity_bench.py`, `tools/aggregate_parity_runs.py` and `tools/check_performance_regression.py` from the candidate harness; no changes to corpus, thresholds, timed closures or performance boundaries.
- Exact tested engine on **both** sides: J24I02/#704 commit `293aa161a4a13b4c1f4fd0f5089aa62e4dbeedef`. Two independently materialized Git worktrees at that SHA; capture imported Python/native paths and source fingerprints. Research harness owner: J24I03/#711 `6fa5bd904bd4458441fbad6675c2a0e28e72251c`.
- Released project v0.30.0 / format revision 24 unchanged. Official same-runner A/B core/ZIP gate for #704 failed twice at binary/library/create: 139.409→171.222 ms (+22.82%/+31.813ms) and 168.996→199.053 ms (+17.79%/+30.057ms). Those remain genuine release vetoes. J24I03's isolated binary and four-row-prefix A/B courts did not reproduce a comparable source effect. Older PR #238 full-matrix A/A on a **different engine** produced a false red of +8.48%/+11.689ms and is a motivation, not a #704 result.

## One primary scientific question

**Can the exact unmodified full eight-corpus, two-layer, seven-repetitions-per-invocation, four-invocation ABBA release evaluator report a material regression when both labels physically execute identical #704 source and native code on the same runner, corpus and comparator?**

Prediction H_noise: a full-matrix same-source A/A has nonzero risk of a gate-scale timing discrepancy, potentially including the specific binary/library/create cell. Prediction H_stable: same-source A/A remains inside the current gate noise envelope. The decision is about **measurement attribution** only, not the truth or validity of the prior A/B gate failures.

## Alternatives PARETOBONKed

1. Rewrite/relax the canonical 5% AND 3ms timing criterion or 0B size law: disallowed.
2. Run one more isolated binary or partial four-row test: already tested in J24I03; unlikely to decide the full-sequence question.
3. Run new candidate Builder optimizations: premature; the Builder/codec source across #699/#704 is identical.
4. Port PR #238 full-matrix identical-source result as if it were current #704 evidence: invalid source provenance.
5. **Chosen:** same-engine exact-gate full ABBA with a single deterministic corpus and source verified independently in two physical worktrees.

## Pre-result evidence contract

- Ubuntu 24.04 hosted runner; Python 3.11, same installed audio/test dependencies and native materialization as official gate, two worktrees both pointing to #704 SHA.
- **No interpreter launch or import excluded from actual canonical measurement** beyond what the existing benchmark already does: call `python benchmarks/zip_parity_bench.py` as the official four sweeps; shared `CMPCT_PARITY_REPS=7`.
- Generate exactly one public deterministic eight-category corpus with `universal_bench.reset_rng()/make_corpora()`, normalize mtime to 2026-01-01, record exact bytes/tree fingerprint and verify unchanged after all sweeps. A/B file identity is compared by `tools/aggregate_parity_runs.py`, no independent policy redefinition.
- ABBA source order A/B/B/A, where both A and B are physically separate checkouts of **the same SHA**; archive-byte mismatches, unequal native SHA, source-origin mismatches or changed corpus invalidate the court (infra/semantics), never become performance evidence.
- Preserve all four raw complete records, stdout/stderr and source/corpus/native provenance on every possible outcome, run the unchanged release checker only in diagnostic mode, and preserve its raw return code/report. An A/A red is valid negative evidence against source-causal inference; it never waives #704's official red.
- Report every significant timing/size/failed cell and exact original evidence source. Compare absolute times only within the same runner and semantic layer.

## Prospective decision

- A/A gate reports >5% and >3ms slowdown in binary/library/create (or another row): **A/A_FALSE_RED_REPRODUCED** for that cell. Narrow confidence in uncorrected A/B attribution; maintain #704 promotion veto.
- A/A remains green across all cells: **A/A_FULL_NEUTRAL**. Narrow same-source false-red prevalence for this host; original A/B remains unexplained and **not** overturned.
- Paths, full archive bytes, corpus fingerprint, native payload, or exact source differ, or CI cannot execute full matrix: **INVALID / INFRASTRUCTURE**, no source-causal conclusion.
- Any outcome only authorizes targeted follow-up measurement/runner investigation if decision-changing; not Reader/Builder modification, format revision, benchmark tuning or release promotion.

## Scope, costs and hostile review

This full product-like court is expected to consume more hosted compute than prior focused tests; it is a bounded final attempt in a saturated attribution family. Two native worktree materializations, all ZIP controls and complete eight-corpus create/extract are explicitly charged. It is a same-source **diagnostic**, not product evidence even though it uses the release machinery. Baseline labels may differ in filesystem path; the two source/native byte identities and loaded paths must be captured. Cross-host and long-run variance remain unmeasured. No `docs/discovery/STATE.json` update until a result changes the scientific decision. Keep this child isolated from #238 and #704 owners.
