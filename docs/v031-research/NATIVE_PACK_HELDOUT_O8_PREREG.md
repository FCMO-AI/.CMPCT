# O8 prospective held-out public-C grouped reconstruction economics

**Date:** 2026-10-24 UTC. **Status:** PREREGISTERED BEFORE NEW HARNESS OR WORKFLOW. **Evidence tier:** held-out product-consumer A/B, not a shipping archive-handler or a core-release benchmark.

## Authority, baseline, independence and coordination

- Frozen starting source: PR #327 `030bd50aff682592f67eba1dc5376b83bfe83fae` (stacked on #326/#325/#322 and native hardening #316/#321/#324). New O8 code must not edit the product Reader, C header, existing O7 C client, O7 measurements, release identity, or shared Discovery state.
- O7 [hosted run 40063050649](https://github.com/FCMO-AI/.CMPCT/actions/runs/40063050649) measured 513 root-level files: serial 189.044 ms vs grouped 19.847 ms wall. Its corpus deliberately favors shared Zstd PACK and its C program is explicitly NOT a safe general extractor.
- #327 retains ownership of the grouped-consumer implementation; O8 is an **independent replication/generalization probe** with disjoint new test files and a distinct CI workflow. It tests the same public C binary against **different frozen data distributions**, not another competing implementation.
- The shared Discovery Engine state on development is stale relative to hosted #242 bounded-drift and newer native-product evidence; this study does not overwrite state or change its primary question.

## Primary question

Is the large O7 grouped-extraction win structurally robust, narrowly restricted to related-content many-member PACKs, or potentially costly on ungroupable/low-entropy-sharing workloads when the same C program must reconstruct every byte using only the public native ABI?

## Frozen held-out cohorts (all real Builder revision-24 archives, reproducible, root-level names)

1. `related_64`: 64 deterministic O7 structural source members of 768 B; medium multiplicity.
2. `related_256`: 256 deterministic O7 structural source members of 768 B; high multiplicity with different group count from original O7.
3. `independent_256`: 256 independently seeded deterministic SHA-stream ~768 B members; poor shared redundancy / high-entropy control.
4. `mixed_256`: 128 structural + 128 independent seeded ~768 B members, plus one independent 70,000 B incompressible file; realistic mixed admission/control.
5. `duplicates_256`: 256 independent paths containing exactly the same 768 B structural bytes; dedup may dominate PACK admission and should not be relabeled a batching victory.
6. `singleton`: one 70,000 B independent incompressible file; strict fallback and no grouped calls expected.

All values are measured from **actual** archives at runtime. If the Builder does not produce PACK for one of these, preserve that negative rather than modifying inputs/thresholds. The seed and source construction are fixed in the experiment code before observing outputs.

## Same-semantics method

- Build one immutable `Builder(workers=1, reproducible=True)` archive per cohort, once; capture its SHA-256 and exact stored byte count.
- Same original C11 consumer binary for BOTH arms, same native library, same archive, same host, same process-start/close and output tree creation boundary.
- Four alternating ABBA blocks per cohort (16 fresh-process extractions; eight serial/eight grouped). Record every wall, child CPU and process RSS datum, real output bytes, fallback members, batched members/count, and source SHA. Never drop losing rows or rewrite historical measurements.
- An independent Python hash oracle checks every recovered file and the exact set of file names **on each trial**. Assert `fallback + batched_members == members` for grouped mode and serial `fallback == members` (no implicit success based solely on process exit).
- Quantify per-cohort median differences, observed grouping and file-byte savings; report each cohort independently, no overall win scalar.
- No performance claim unless the run completes on a hosted exact-head CI and data actually materialize. Runtime/process inclusive comparisons are C-consumer economics only.

## Predictions, controls, kill/narrow criteria

- Related-content high-member cohorts should expose groups and faster grouped CPU/wall; `related_64` might fail to amortize grouping and is a valid negative.
- Independent/duplicate/singleton cohorts may not group, and their no-batch cases should remain near serial economics; grouping is not justified on all data. On `singleton`, batched_members and batch_count MUST equal zero.
- If grouped results are >10% AND >5ms worse on any held-out cohort, classify productization generality as **NARROW / admission debt**, even if O7 remains a large positive. A noisy few-millisecond difference alone is not a conclusive regression.
- Any byte/file mismatch, silent truncation, accepting malformed roots, false preflight success, unexpected non-zero exit or result identity mismatch invalidates the whole corresponding corpus trial. Do not weaken fixtures or correctness to obtain a green.
- Stronger simpler control is the unchanged per-entry native ABI. A format-wide pack-size/ordering change is NOT justified by this experiment.

## Exported costs and limits

Measure stored archive bytes, logical source bytes, number of grouped/fallback entries, wall, CPU and whole-process peak RSS; no SSD physical byte claim, no general speedup, no compression-gain claim, and no attribution of group scheduling vs decompression without instrumenting both. O7 has an explicit root-only test-client restriction; O8 leaves it in force. The per-file C allocation can grow with total archive logical data: this is test-only, not shipping bounded extractor. Full filesystem symlinks/hardlinks/modes, OS portability, TOCTOU and system-safe materialization remain outside O8.

## Decision unlocked

If both related controls preserve a strong benefit while independent/duplicate/singleton avoid material regressions, prioritize a **budgeted internal group scheduler** in a real native extraction handler. If independent or mixed cohorts show material negative carrying costs or physical-group count fragmentation, prioritize bounded scheduling/admission (or leave grouping optional). Any uncovered integrity/path issue takes precedence. Preserve observations and an exact-head receipt before recommending product promotion. No release or Discovery policy update from this single study.
