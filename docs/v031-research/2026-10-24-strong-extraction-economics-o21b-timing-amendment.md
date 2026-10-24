# O21b — measurement-boundary correction, frozen before second hosted observation

Date: 2026-10-24
Status: PRE-RESULT AMENDMENT, NOT REWRITE OF O21 ORIGINAL OBSERVATIONS
Initial O21 implementation head: `ff476bcce8ea94f9146248c7f017f92e85d5f276`
Initial hosted run: `40121322679` (SUCCESS), original raw artifact ID `12571680970`, ZIP SHA-256 `2ea7cb482b07961c8fbb6145a720362d5b1f557fd3920645e64c66a4c0e6219c`.

## Measurement flaw discovered after inspection of original output

The first instrument starts CPU timing immediately before Reader open, but samples process CPU **after** calling `source_manifest(destination)`, including an independent full-output SHA-256 oracle and directory traversal. Meanwhile wall time stops immediately after `extractall()`. Therefore original `total_operation_cpu_ns` is misnamed: it measures Reader operation **plus output audit**, while `total_operation_wall_ns` measures Reader operation only.

This does not invalidate O21's output-identity judgments or paired wall-time result, and it is not a finding of a CMPCT defect. The original CPU ratio must be labeled **audit-inclusive**, not interpreted as equal-boundary Reader CPU.

## Prospective minimal correction

Capture `cpu_after_extract = time.process_time_ns()` immediately after `extractall()` returns. Keep existing post-extraction independent SHA oracle and preserve original audit-inclusive CPU as a **separate explicitly labeled diagnostic**. Compute `total_operation_cpu_ns=cpu_after_extract-before_cpu` with the *same boundary as operation wall*. Keep wall, RSS, corpus, native/Reader ownership, output hash oracle, 5 block ordering, child processes, comparator and controls unchanged. Print/report both CPU times explicitly.

## Falsification and expected observation

The correction should change reported CPU deltas/ratios but **not** output hashes, archive identities, wall ordering, physical owner selection, or integrity correctness. If it does, investigate as instrumentation drift; do not rescue by modifying fixtures. If second hosted measurements differ materially in wall beyond noise, preserve both and classify ambiguity. No product source, frozen external comparator, or release policy changes. This is an evidence-quality fix, no product performance credit.

## Independent review and negative

Original raw observations remain recoverable through the exact GitHub run/artifact above and must not be overwritten. Treat identical process RSS high-water as **uninformative about instantaneous native/Python heap difference** when package import dominates; memory has not been proven identical by O21.
