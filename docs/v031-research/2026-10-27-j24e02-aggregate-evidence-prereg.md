# J24E02 — prospective raw-ABBA evidence-ingestion court (before experiment)

Date: 2026-10-27 UTC. Scientific question: **Can ambiguous or nonfinite raw parity JSON escape the downstream strict J24E01 release comparator because `tools/aggregate_parity_runs.py` normalizes it first?**

## Frozen source and concurrency
- Exact parent: PR #561 HEAD `2d0461ce3fdc07bc74fd6a0f3d09990b3b377186`.
- Raw ABBA aggregator: `tools/aggregate_parity_runs.py` Git blob `6e036f75528bd892d6552b8b04f5586770ff1744`.
- Downstream strict comparator: `tools/check_performance_regression.py` blob `22172ba4465b297bba54b0120f3419abe632cbd1`.
- J24E01 PR #561 owns comparator duplicate-member guard; PR #328 owns full-PR admission. **This experiment does not edit either surface.** It tests an upstream parser boundary already passed by raw historical base/candidate job artifacts.
- No `docs/discovery/STATE.json` mutation: reconciled state is staleable and another lane owns its consolidation.

## Hypothesis, predictions and disproof
- Baseline mechanism: Python's default `json.loads` retains the last duplicate object key; the raw ABBA aggregator decodes JSON into dictionaries **before** forming median reports. The strict J24E01 downstream comparator sees only the already-collapsed output and cannot recover conflicting first values.
- Predict the original upstream aggregator accepts raw duplicate `create_s_median` (first 0.107, last 0.100), emits a unique-key candidate report, and the unchanged strict comparator returns PASS against an equivalent 0.100 baseline. Duplicate whole `corpora` and `bytes` objects are adjacent proof checks, not claims of a separate product defect.
- Predict the raw aggregator also admits non-standard JSON `NaN` in ZIP-only metrics, or finite-text overflow `1e309`, whereas the downstream strict comparator validates CMPCT fields only. At minimum this makes ZIP parity evidence untrustworthy; do not claim a hidden CMPCT timing regression from ZIP-only perturbations.
- Candidate mechanism: reject duplicate decoded JSON object names at every depth; reject non-standard numeric tokens and nonfinite parsed floating-point values **at raw input time**. Retain all accepted numeric values, median calculation, corpus paths, 0-B byte policy, >5% AND >3-ms timing thresholds, ABBA job topology and the frozen comparator source.
- Strongest simpler control: trust only the downstream comparator (#561). **Kill this research** if actual source-to-source A/B shows the downstream check already sees/rejects raw ambiguity before aggregation or if original upstream fails closed.
- Other alternatives: make producers canonicalize (cannot authenticate external artifact input); try first-wins behavior (ambiguity remains); alter comparator threshold (forbidden); add a new third JSON authority (unnecessary).
- **Disproof:** any duplicate or nonfinite raw adversary still admitted by candidate, any legitimate unique-key A/A rejected, any genuine +7%/+7-ms regression turned green, or modifications to comparator/benchmark/workflow thresholds or the format.

## Evidence tiers, accounting and decision
1. Same raw UTF-8 JSON, same source fixtures, original exact Git blob vs candidate; no alternate reimplementation of the aggregation algorithm.
2. Cases: nested duplicate CMPCT timing, duplicate corpus map, duplicate ZIP bytes, NaN, Infinity/-Infinity, exponent overflow; valid A/A and genuine real +7%/+7-ms controls.
3. Drive both aggregated outputs into actual J24E01 checker unchanged. Preserve original acceptance/false-green observations and candidate fail-closed behavior separately.
4. Run deterministic tests on independent Linux/Windows hosted sources if accessible; source/checkout identity and result artifacts are required for a hosted claim.
5. No engine, codec, format, archive size, create/extract speed or release credit from evidence-only changes. CPU overhead of strict parsing is not measured; assess when material.
6. If positive, give original owner #561 and full admission owner #328 an exact-head handoff; do not merge or promote as part of this research run.

This is a **preregistration**, not a claim that the predicted original false-green or candidate guard has been observed.
