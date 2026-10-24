# O6 preregistration — source-exact indexed replay × Writer/recovery/Reader union

**Date:** 2026-10-24 UTC; **scope:** CMPCT v0.31 draft, revision 24 unchanged.
**Owner / branch:** independent Phased1 child `agent/phased1-v031-writer-delta-replay-exact-union-o6-20261024`.
**Base source:** PR #345 HEAD `33c4ef777542039ab3c1b97797e5ac8ca31af96a`, `src/cmpct/validation.py` blob `015f619ebf5d775aff4858a51456669247808b21`.
**Replay source:** PR #348 HEAD `0062961be78cd4d28231a9acaf37a4d9cf43920c`, validator blob `1e085db992add64118a9488790096c574fff154d`; original optimized owner #346 `fb887d8610dced551acf5a84778ba539d08dac59`.
**Baseline historical:** `agent/v031-development` validator blob `51c2849061f99a4afeddb7666956b24566ce7de0`.

## Decision / hypothesis

PR #345 already composes Writer/recovery, signed-tree/hardlink, Win32/APFS namespace and strict MessagePack Python/Rust behavior. Its journal replay remains historical linear-list. PR #348 independently demonstrates a source-exact positional index preserving first-match `put`/`ren`, all-match `del`, and intermediate ceilings with large CPU savings and ~1 MiB post-call resident overhead. We predict the *same exact* replay block can be grafted into #345 without altering any other source byte, and while preserving installed-product signed r24 semantics and all inherited security/Reader tests.

**Mutation limit:** the `def _apply_delta_indexed` + `def _apply_delta` block and one `import heapq` line inside `src/cmpct/validation.py`; import exactly the original indexed semantic-reference test, an authentic signed journal Builder/transaction experiment, and a narrow hosted workflow. Do not modify tests/evaluators/thresholds, `_unpack`/duplicate-map rules, hardlink graph, Writer, Reader, native core, format or release law.

**Strong simpler control:** preserve PR #345 historical linear replay. Existing source-exact PR #347 same-runner ABBA showed 25.18x at 4096 operations but +42.77% traced allocation; PR #350 independent fresh-process work measured ~1 MiB extra post-call VmRSS at 16384, and intra-call memory peak remains unresolved. No inherited win silently transferred to this union HEAD.

**Alternative explanations / possible negatives:** Writer transaction delta semantics or strict MessagePack map policy may differ from the isolated parent; imported test may assume a different reader, or incremental exception semantics could differ on malformed rows. The measured CPU win may not transfer to the full union; RSS, create/extract, recovery, portability may regress. If any inherited Reader/native/Writer safety red arises, narrow or reject the transplant rather than weaken tests. If parent advances over the same region, stop and reconcile without overwrite.

## Falsifiable evidence / decision boundaries

1. **Source identity:** reconstruct expected validator by inserting the exact indexed function block from frozen PR #348 into frozen #345 and adding `import heapq`. Require byte-for-byte equality of complete source; specifically retain `object_pairs_hook=unique_map_pairs`. The CI court fails on source drift or wrong HEAD.
2. **Independent semantics:** use original PR #346 O1 10,000 deterministic mixed/duplicate/failure reference sequences; run #345's signed tree, differential hardlink, Windows/APFS/nested MessagePack inheritable suites without weakening original assertions.
3. **Product authenticity:** execute original #348 Builder+signed transaction experiment on true revision-24 archives; identical final logical index/tree against stronger checkpoint control, preserve whole archive hashes/size, per-member reads, wall/CPU and raw measurements. Capture artifacts including failures.
4. **Promotion:** exact-head general CI, Native Core, tri-platform security, substantive same-runner release parity and correct existing base/corpus fingerprint remain non-negotiable. No release or merge automatically authorized by a focused green court.
5. **Kill / narrow:** non-identical source exterior, altered results/error classes of valid/invalid signed archives, incremental state exposure, partial extraction, authenticated index ambiguity accepted, obvious or material create/extract/RSS regression, or non-executed/skipped court. Keep original owner branches intact.

**Decision value:** if exact-head focused work passes, this is a reversible product *candidate* toward one shared validator/Reader surface, not released authority. If not, identify the concrete cross-owner incompatibility and preserve the negative. The Discovery Engine's stale `STATE.json` is not modified for this scoped experiment.