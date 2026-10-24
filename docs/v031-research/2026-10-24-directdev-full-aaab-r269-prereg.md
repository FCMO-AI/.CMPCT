# v0.31 O2 — source-identical full-harness sham vs genuine canonical-development A/B

**Date:** 2026-10-24. **Status:** PREREGISTERED / NO RESULT. **Owner:** independent Phased3 scientific replication; no changes to #238, #328 or production files.

## Authority and experimental question

Canonical `agent/v031-development@4545d7d5b2a0b712b4b00f5a9c291d4a3a9e169b` (A) versus stacked Writer/salvage/evidence-infrastructure product `fb87f582918bd7ca0f16559eed2f782739977048` (B). Parent #328 is immutable for this experiment. CMPCT v0.30.0/r24 remains the released floor; this is nonpromotable research only.

Prior genuine official [run 40067337471](https://github.com/FCMO-AI/.CMPCT/actions/runs/40067337471), exact #331 source `41c36e297d738baf6656afed9a6614feaa9431f3`, recorded the sole time red `binary/library/create` 137.557→144.472ms (+5.027%, +6.915ms) while all 16 sizes matched. Existing #238 owns a different #234/#235 A/A-vs-A/B source question; its full-harness *source-identical* [run 39928521518](https://github.com/FCMO-AI/.CMPCT/actions/runs/39928521518) independently produced a red 137.795→149.484ms (+8.483%) from one candidate-labeled invocation median 163.102ms versus 135.866ms, while ZIP control moved -0.224%. The original official gate red is genuine and remains blocking; this research cannot overturn it.

**Primary question:** Under a single new hosted run with the *unchanged whole eight-corpus official benchmark schedule*, can the exact A code, used on both labels, itself yield an apparent >5%-AND->3ms binary/library/create regression? If not, does a separately source-exact A/B comparison reproduce the previously red cell? This adds a same-runner sham for the **precise** A/B pair previously tested, rather than reopening any mechanism family or tuning a threshold.

## Prediction before implementation

Expected: complete archive **size parity**, identical archive bytes across labels because Builder/codec/native sources are identical, and A/A magnitude materially capable of confusing attribution in this full-harness regime. The directional A/B result is **unresolved**: accept PASS, RED or ambiguous without changing the comparator. No scientific outcome is earned by infrastructure SUCCESS alone.

## Exact controlled design

- Use unmodified `benchmarks/zip_parity_bench.py`, `tools/aggregate_parity_runs.py`, `tools/check_performance_regression.py`, same eight frozen deterministic families, same normalized input tree, same Python 3.11 host, shared installed dependencies/native base materialization.
- Materialize A from exact canonical commit and verify A is ancestor of this branch; B is the branch's **unchanged product source**, verified via Git tree equivalence against exact parent `fb87f582918bd7ca0f16559eed2f782739977048` for `src/`, `native/`, `benchmarks/`, `pyproject.toml`, `tools/check_performance_regression.py` and aggregation module.
- Two distinct courts **in this order**, each 4 full runs, 7 repetitions per metric per invocation: (1) A0–A1–A1–A0 using **the same exact canonical A source path** for all four invocations (sham); (2) A–B–B–A using the canonical and candidate product source paths (true A/B). The A/A stage runs first to avoid a post hoc invented control after observing A/B. We do not assume the two stages have identical cache history; each verdict stays locally scoped.
- During the A/A court, the two label sets are **logical labels only**, not different engine binaries; use the same `/tmp/cmpct-performance-base/src` PYTHONPATH to eliminate source/path confounding. During A/B switch only `PYTHONPATH` in the same hosted job, identical input tree.
- Preserve stdout and complete `zip-parity.json` for **each of eight invocations**; aggregate independently per court with unchanged aggregator; invoke the unchanged comparator on **each** independent court, capture both exit statuses even on red, and always upload raw artifacts. Never equate workflow GREEN with comparator GREEN.
- Verify candidate and control Git SHA, native materializer receipt, corpus fingerprint and all 16 stored-byte results; recompute per-arm binary and ZIP negative controls in a diagnostic sidecar outside the official comparator. The benchmark saves **invocation medians, not individual seven-trial data**; do not invent per-trial variance.
- This experiment changes **no** Reader, Builder, Writer, native source, corpus, frozen benchmark, thresholds, process boundary or release policy.

## Competing explanations / falsifiers

- **H_host:** general runner-wide slowdown. Stronger control: concurrent ZIP baseline; earlier receipts show ZIP nearly flat while CMPCT varies. A same-source regression isolated to CMPCT contradicts a *uniform* host-wide multiplier, but does not identify an operation-specific kernel, scheduling, native-thread or cache cause.
- **H_code:** Writer/salvage/Reader source causes ordinary binary create slowdown. This requires repeatable genuine A/B worse than A/A under genuinely identical input and environment; same Builder/codec/native source reduces prior causal plausibility but does not logically exclude import/indirect effects.
- **H_schedule:** the full-harness chronology induces group-dependent swings. A/A >5%-AND->3ms with exact A source is a direct disproof of treating a lone full-harness red as sufficient *causal attribution*; it is **not** an exemption from release criteria.
- **Kill** claims if code ancestry/source digest, native custody, corpus identity or operation semantics drift; if either court's four JSON records are missing; if the official comparator is edited; or if a supposed size/semantics PASS is inferred solely from equality of archive lengths.

## Evidence and decision law

Truth tiers: original official A/B red is product promotion evidence (remains RED); both new A/A and A/B are hosted **diagnostic** evidence, not a promoted release gate. Positive source-identical A/A falsifies naive single-run causal attribution. Negative A/A is not proof that runtime noise is absent. A true A/B red without an A/A red narrows, but does not prove, a source-linked explanation; a true A/B PASS demonstrates nonreproducibility of the earlier timing red in this hosted regime, **not** authorization for release. A promoted v0.31 must subsequently pass the canonical unchanged release workflow against the correct direct base.

## Coordination / carrying cost

#238 already owns general A/A research; this experiment is explicitly a **source-pair-specific independent replication** of the *currently blocked* #328 O1 pair, justified by decision-changing disagreement between its real A/B red and demonstrated same-source full-harness red. No duplicate core fix, no long-lived product workflow; scientific branch/PR remains draft. Budget one hosted trial; no automatic re-run until evidence is reviewed. Publish run ID, exact HEAD, artifact identity and raw outcomes for the next zero-history operator. If the independent trial does not distinguish claims, retire the lane rather than garden thresholds or repeat arbitrary neighboring mechanisms.

**Counterfactual prospective lesson candidate:** a source-identical full-harness A/A performed alongside the first source-pair product gate could have diagnosed variance-sensitive attribution earlier. This is a hypothesis for later evaluation, not a Discovery Engine policy change.
