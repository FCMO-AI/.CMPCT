# O34 — Frozen compact-r24 product-parity negative (2026-10-24)

**Status: DECISIVE NO-PROMOTION for the frozen PR #212/#217 candidate.** This record is research evidence, not an on-disk-format, source-code, release, or policy change.

## Exact source and court

- Frozen corrected candidate source: `b878f40a540162ab977776d7f90c3502d2749588`.
- Preregistered matrix owner: PR #217, `e235686d2a9fd4757c5478526600f410e59c6eb8`.
- Hosted workflow execution: [Actions run 40138113211](https://github.com/FCMO-AI/.CMPCT/actions/runs/40138113211), job `121003877559`, on source HEAD `17a000f150f68e724efb6cdcdd3d1dddb079c5ca` (draft PR #388).
- Artifact: `12578348560`, containing `matrix-stdout.log` and `matrix-exit-code.txt`. Workflow exit code **1**.
- Frozen gate: `benchmarks/history/2026-09-30-v030-compact-r24-full-matrix-prereg.json` requires **zero** canonical r24 product-byte regressions; it prohibits threshold, corpus, evaluator or comparator gardening.
- Source/ancestry and six frozen Git-blob custody checks, dependency setup, CI topology, and all three focused child/facade/backups tests completed successfully before the expensive run.

## Direct negative

The original unmodified matrix executed its historical computation and entered the authentic-product comparison. It terminated with:

```text
RuntimeError: canonical v0.30 product regressed genuine r24 bytes: neutral_hostile_v1/08_many_tiny_files
```

This is raised at `benchmarks/v030_release_ablation_canonical.py:309` **only after** the candidate and the genuine-r24 archives were built on the same source tree, candidate `strong_verify` passed and both logical tree SHA-256 values matched. The immediate predicate is `v030["archive_bytes"] > r24["archive_bytes"]`. It is therefore an **actual deterministic product-byte loss**, not a runner timeout, setup/permission failure, source-identification failure, invalid archive, or historical-v0.29 accounting comparison.

The full per-row size values for this failure were **not printed or committed** by the existing fail-fast evaluator; therefore the exact loss in bytes is **UNKNOWN**. The matrix raised before producing `compact-r24-full-matrix.json` or the independent success-judge `decision.json`. Thus **15/15 complete historical and product matrices were not delivered**; do not claim that all rows passed or failed. The single authentic product-byte regression nevertheless suffices to falsify promotion under the frozen zero-byte rule.

## Scientific decision and next action

**Decision: RETIRE THIS FROZEN COMPACT-R24 CANDIDATE FROM ITS PRODUCT PROMOTION LANE.** Preserve the corrected seed and completed focused positives as historical research evidence, but do **not** rerun or tune the same matrix to obtain a green. Do not weaken the zero-byte gate, silently override candidate selection, change `08_many_tiny_files`, or infer a new release credit.

Cheapest optional causal follow-up, **only if necessary for a materially different architecture**, is a single-row, same-input diagnostic that reports genuine-r24 and candidate complete archive bytes and selected physical owners while leaving the frozen matrix untouched. Such a diagnostic cannot overturn the measured gate or earn a product claim by itself. Otherwise, return execution capacity to genuinely different product/integration bottlenecks.

## Limits and adversarial self-critique

A log exception proves at least one strict size loss, **not** its magnitude or the complete 15-row result. The original run took about 45 minutes to reach the failure; it is not evidence of runtime/CPU/RSS advantage or loss against baseline. The specific candidate is frozen; this result does **not** retire unrelated r24 micro-PACK research, all compression, other portfolios or release 0.30.0.

This receipt is append-only outcome truth. Do not edit the existing preregistration, six immutable science files, benchmark generator, comparator, promotion criterion, or original GitHub artifacts. Research questions and source-time boundaries must remain distinguishable from subsequent experiments.
