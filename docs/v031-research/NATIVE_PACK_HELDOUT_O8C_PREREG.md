# O8c — same-path complete archive economics of micro-PACK admission

Date: 2026-10-24 UTC. Status: PREREGISTERED BEFORE O8c IMPLEMENTATION OR MEASUREMENT. Branch inherited PR #327 immutable product/C source 030bd50aff682592f67eba1dc5376b83bfe83fae. O8 and O8b already executed; their frozen questions, sources and results are preserved separately.

## Primary question

O8b hosted run 40066551832 found extension-dependent PACK admission and a 69-byte (4.85%) larger archive for 256 identical text files using .txt rather than .dat. This is NOT a valid same-path release-regression comparison because names differ, and other encoding policies may also depend on file suffix. Does default Builder micro-PACK actually produce more complete archived bytes than a simpler no-PACK control for **exact same paths and content**, and what price does it impose on create and native extraction work?

## Fully controlled alternative

Four immutable source families: related_256, independent_256, duplicates_256, mixed_256, from the already frozen deterministic O8 population() generator. Convert source .dat names to .txt BEFORE building BOTH variants. Mixed large .bin member remains unchanged. Build two archives per identical immutable source tree:
A: unchanged Builder(source,workers=1,reproducible=True), inherited CMPCT_MICRO_PACK_MAX_FILE normal default.
B: identical Builder but existing supported environment CMPCT_MICRO_PACK_MAX_FILE=0 (disables micro-PACK on nonempty sources).
No modifications to product code, original test data, codecs, threshold constants, comparators or release policy. Dictionary and codec selection may adapt downstream: this is intentional WHOLE-BUILDER policy economics, not an attribution to only Zstd compression bytes.

## Measurement and disproof

For each of four families use four alternating ABBA rounds of independent full Builder.build operations (16 builds per family, eight per alternative; 64 total). Preserve every build wall and process CPU observation and exact archive size/SHA. All repeated archives from the same configuration must reproduce the exact same archive hash/size, despite differing output filenames. Compare each pair on exactly the SAME paths and exact payload bytes, independently check all source hashes after each build, and verify that both archive outputs extract every expected member exactly. Use unchanged public C consumer to count actual batched/fallback members and materialize both variants (serial and grouped) with independent file hash checks; extraction timing is diagnostic only without balanced repetitions. Report total logical bytes, actual whole archive bytes, build medians, C process wall/CPU/RSS when measured. Do not infer physical disk bytes or whole-market effect.

## Prospective predictions and falsifiers

Related and mixed text: default PACK likely wins complete stored bytes and grouped extraction. Duplicates: dedup-aware separate baseline may win archive bytes despite default PACK offering some decoded-work reduction. Independent high-entropy text: may not pack under either configuration. Any surprising outcome is retained, not tuned away. A positive (normal - no-PACK) stored-byte delta on exact same-path duplicate sources demonstrates a LOCAL generic-admission loss against the stronger control, NOT an inherited release-wide regression. Any mismatched paths/bytes, nondeterministic per-config archive hash, contaminated env var, failure to reconstruct a source file, altered release benchmark/threshold, or changed Builder source invalidates the inference. Timing noise is declared ambiguous rather than forcing a positive verdict.

## Decision, alternatives, and policy constraints

The strongest simpler control is existing Builder no-PACK mode; comparing .txt against .dat cannot decide same-path byte economics. No new format, release identity, native ABI or build behavior is introduced. If duplicates lose bytes under default admission, prioritize discoverable full-cost candidate admission with a bounded fallback and held-out tests, not fixture-specific threshold tuning. If real bytes and create/extract dimensions are nondominated, preserve both. Test-only C consumer is NOT safe general filesystem extraction (path, symlink, hardlink, memory and TOCTOU obligations). Frozen O8/O8b, Bounded Drift and shared Discovery STATE remain untouched.
