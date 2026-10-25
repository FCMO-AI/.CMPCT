# O54 — Deferred VZIP split-read source-custody falsifier (preregistration)

Date: 2026-10-25 UTC
Status: PRE-RESULT / independent research only
Repository: FCMO-AI/.CMPCT
Frozen O50 base: 17c96603e33b02b3f2f9e0079eec2b128f293be8
Frozen Builder blob: 21a9ec696df13961c25301654feb607a7e161a4c
Frozen codec function: `src/cmpct/codec.py:make_vzip_recipe` (exact source inherited from O50).
Related owner issues: #408; research #407; product #405. No edits to these owners.

## Primary question
Can a same-path, same-inode, equal-length in-place change between the first independent `ap.read_bytes()` in `make_vzip_recipe` and its subsequent real `ZipFile(ap)` parse yield an internally inconsistent *successfully emitted* revision-24 archive?

This is NOT O52's post-stat pathname-to-symlink/FIFO pivot: no pathname redirection, no type substitution, no outside-root bytes, no source identity change. It tests multiple source-data passes of the VZIP encoder, even when the original direct-file handle and directory remain stable.

## Baseline, invariant, and predicted mechanism
The real O50 Builder defers one `.zip` to `make_vzip_recipe`. That function reads `original=ap.read_bytes()`, independently opens the same pathname as a ZipFile, then again opens it to read physical streams. The Builder later independently computes `sha(p.read_bytes())`. Under ordinary immutable source A, Builder emits a valid K_FILE/S_VZIP representation, reconstructs exact A and passes `CMPCT.verify()`.

Use valid ZIP_STORED archives A and B containing the same named and same-length inner member but different content. A and B must have identical complete byte lengths and distinct SHA-256. Instrument only the call boundary to the actual `ZipFile(ap)` inside the real codec implementation. After the first read of A completes but before the subsequent ZipFile handle opens, overwrite the same ordinary source inode with B. The wrapper immediately delegates to the unmodified zipfile implementation; Builder, codec, Reader and integrity validators remain genuine. Restore the wrapper before Reader validation.

Prediction: Builder accepts the mutated source and emits a physical archive whose VZIP skeleton/expected ZIP checksum comes from A while member bytes come from B; the emitted archive cannot satisfy its own reconstruction/integrity contract (even though the source and archive bytes are valid independent objects). Depending on Reader checks, `read()`, `verify()` or both must reject. An outright Builder refusal counts as prevention, not as the predicted silently emitted corruption. A fully verified exact archive (whether A or B) falsifies the corruption prediction. No test changes success criteria retrospectively.

## Stronger simpler controls
1. Immutable ZIP A -> built archive exact verification and extraction PASS.
2. Independent immutable ZIP B -> built archive exact verification and extraction PASS.
3. Mutation control reports A/B complete file lengths, SHA-256, unchanged physical dev/inode where OS semantics permit, mutation count exactly 1, and ZIP validity both before and after.
4. If the real Builder invokes no VZIP path (e.g., recipe rejection), evidence is INCONCLUSIVE, not PASS for the hypothesis.
5. Require actual CMPCT pip-installed in isolated environment from exact test head, and original Builder Git blob unchanged. Do not silently treat source-tree import as installed-package verification.
6. Preserve actual output archive, source SHA records, mutation timing and exception class. No weakening of existing checks, parsers, comparators, workloads, security gates or thresholds.

## Alternatives and anti-local-optimum
Compare three designs as future implications, NOT implementation authorizations: (a) same-fd source snapshot or one captured byte buffer consumed by all nested ZIP passes, (b) rooted descriptor-relative open with shared validated fd (contains path pivots but cannot alone prevent in-place changes), (c) optimistic pre/post stat/digest checking (detectable changes only, may incur re-read/ABA debt). O52 already killed final-component-only NOFOLLOW as a root-containment solution. This O54 lower-cost falsifier isolates a different source-data consistency mechanism before any cross-cutting Builder change.

## Verdict / disproof
- `EMITTED_UNVERIFIABLE_R24`: Builder returns successfully and genuine CMPCT read/verify rejects; confirms scoped inconsistency.
- `BUILDER_REJECTED`: Builder refuses split-source materialization; original hypothesis falsified, safety-positive.
- `EXACT_VERIFIED`: archive verifies and extracts identical A or B; original hypothesis falsified within tested scope.
- `INCONCLUSIVE`: no true VZIP path, no actual in-place pivot, bad control ZIP, source/CI mismatch, or infrastructure failure. Never reclassify as security-positive.

## Costs and promotion law
A scientific falsifier, not a product patch. No compression ratio, runtime speed, memory, security hardening, or release credit. Store original JUnit/JSON/logs plus source HEAD and toolchain. The result may alter architecture preference for future #408 work, but ownership and promotion remain with #405 and current repository gates. Do not mutate `docs/discovery/STATE.json` unless decision-changing evidence is confirmed and concurrent owners reconcile it.
