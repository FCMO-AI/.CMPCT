# J24G02/J24G02b — independently frozen signed-generation conformance against indexed ordinary Reader

**Evidence date:** 2026-10-26 UTC  
**Decision:** **SCOPED CROSS-OWNER CONFORMANCE PASS**, no product code or format change, release unearned.  
**Repository:** `FCMO-AI/.CMPCT`; isolated draft [PR #484](https://github.com/FCMO-AI/.CMPCT/pull/484).  
**Exact source parent:** indexed ordinary Reader owner [PR #358](https://github.com/FCMO-AI/.CMPCT/pull/358) at `2c5334392c57f9c0f685c3751712acf0e242efae` (base branch `agent/phased1-v031-reader-journal-shared-replay-o7-20261024`).  
**Independent producer:** fixed-byte journal oracle [PR #481](https://github.com/FCMO-AI/.CMPCT/pull/481) at `fe8dc99de2c47c42c4a7ad95f83bb3bf3c36aa81`.

## Problem and prospective hypotheses

O7 reused indexed `validation._apply_delta` inside the real ordinary Reader and previously demonstrated product performance on Writer-derived journal material. The Writer and Reader could nevertheless share a transaction interpretation bug. J24G01 already constructed small revision-24 SHA-committed checkpoint/delta archives without Builder or Writer and tested seven cases on a different Reader source; its original tests did **not** materialize output with `extractall`.

- **J24G02, preregistered** before importing the independent frozen oracle at commit `411bdbd519d7a8ebf98e7fb40f22d3be580ab4df`: indexed Reader will parse authentic latest generation, reject corrupt successors, verify content integrity, and answer exact logical/range reads without changing inherited implementation or frozen test.
- **J24G02b, preregistered** before introducing physical extraction assertions at commit `2ef9f47e467b69a950f57e1bce1fbfdf4077b790`: the same source will write the complete exact latest-valid tree for all four fixed archive variants to a real filesystem, including deleting `keep.txt` at the logical commit boundary, without creating spurious entries.

**Kill condition:** any unchanged frozen test failure, wrong extracted byte/path, accepted unauthenticated successor, or source-provenance mismatch falsifies the corresponding scoped positive result. No generator regeneration, evaluator relaxation, hidden skip or format change permitted.

## Exact source and irreversible evidence boundary

| Source | Git blob |
|---|---|
| Genuine ordinary O7 Reader | `6de2edcf5b804e224a1c651ca77361af5667dc2e` |
| Shared strict validator | `2bb3f53c918ae93efb105364e2b93ea46aeca034` |
| Original J24G01 seven-case test, **unchanged** | `63024d52c0d7a97d63adaabf13f9a0cff6499de8` |
| J24G01 fixed journal byte manifest, **unchanged** | `74a39263954a84debd7ce6992cfa71fc1ed4dd91` |

The four fixture variants (independent serialized physical bytes, not Builder output) have complete stored lengths **649, 899, 1004 and 930 bytes**. They are conformance examples and do not establish storage compression advantage. Every test checks the original archive SHA-256 against the independent manifest before Reader open.

Changes in this PR are two scientific preregistrations, the two unchanged inherited golden assets, a new physical extraction test and a dedicated exact-head three-host GitHub Actions workflow. **No code under `src/`, `native/`, Writer, Reader, validation, format, core release or release-lock changed.** The workflow checks all four source Git blobs and executes installed CMPCT under Python 3.11.

## Hosted scientific outcomes, chronologically separated

**H1/H2/H3 on exact original test-bearing commit** `44e3992040ec18a3d255682a3c5176efca25b2bb`: [run 40254137562](https://github.com/FCMO-AI/.CMPCT/actions/runs/40254137562), **Ubuntu 7 PASS, macOS 7 PASS, Windows 7 PASS; 21 effective test executions, zero failures/skips**. Original logs and source custody retained. Original artifacts: Ubuntu `12620779851` (ZIP SHA-256 `849b73dad9511f5f55d9bb98f83319d6ac2a4f6d2e318c4d899b3647b694c7f9`), macOS `12621981415` (`f2ecaf2bd095c4d20a60c4b328d42eb51d1db03f63d59ef6b49d102ce2deb825`), Windows `12621557908` (`2fe6787f6bba44585895be21255637a8b64cb30c509878652ea90a1293bb2a13`).

**H1/H2/H3 plus J24G02b H4 on code-bearing commit** `cc0b0e96afb24e5d9ca6545458a09ccf55709f82`: [run 40254622642](https://github.com/FCMO-AI/.CMPCT/actions/runs/40254622642), **Ubuntu 11 PASS in 0.10 s, macOS 11 PASS in 0.24 s, Windows 11 PASS in 0.30 s; 33 effective test executions, zero failures/skips**. Every job printed the same exact checked `EVIDENCE_HEAD` and all four expected Git blob SHA values. The four newly preregistered cases per host call actual `extractall(metadata=False,max_bytes=1048576)` and compare *all* real filesystem entries plus every stored byte/SHA-256 against the independent signed manifest. The bad fully-framed successor and incomplete tail do not resurrect `keep.txt` or invent a replacement generation.

Original raw GitHub Actions artifacts on that code-bearing head:
- Ubuntu: artifact **`12621618104`**, ZIP SHA-256 `ee6dbb778c069aea9317ec1db69e68f02d4067cfb7ee33a9e676fc9f5b836406`.
- macOS: artifact **`12621234794`**, ZIP SHA-256 `002dee12db12d36ba5664b8f86ed4d08de1c39893c0549a23a24d959e56a3bdc`.
- Windows: artifact **`12622047183`**, ZIP SHA-256 `ef6cdc8e1a7ab971fb75ff1041e6907c68ef7e0e0df084cdf7c9249f2cd2012c`.

The independently frozen original test uses `read`, `read_range`, `verify`, signed footer offsets/depth and corruption adversaries; the new physical test is separate rather than editing or expanding original assertions after observing their results.

## Engineering gates, negative evidence, and limits

At the above code-bearing HEAD `cc0b0e96`, **Engineering Evidence**, **Version Discipline**, **R36 Attribution**, **CI Topology** and **Native Core** were observed **SUCCESS**. Generic Tests, Fuzzing and substantive Performance Gate were **still in progress at this evidence checkpoint**; their later status must be looked up on exact HEAD instead of inferred. The specialized 3-host court was **3/3 SUCCESS**.

The first Engineering Evidence run on earlier `44e39920` was **FAILURE** because the initial PR body omitted required exact headings. After reading the actual unchanged `tools/check_pr_evidence.py` and reviewing the diagnostic, the PR evidence dossier was completed using the required headings and scientific falsifiability and quality-ratchet criteria; no test, policy or threshold was modified. This negative remains relevant for research tooling hygiene.

The scope is specific: archived **ordinary regular-file** signed journal generations from J24G01. It does **not** prove native C ABI journal support, transactions under concurrent writers, crash durability, hardlink/symlink extraction, malicious destination TOCTOU resistance, all malformed grammars, mmap source mutation, or general CPU/RSS/I/O economics. The inherited O7 focused 4096-generation Reader open speedup remains its **own** prior measurement, not a result of J24G02. The fixed 649–1004-byte test vectors do not measure compression ratio.

## Counterfactual and next actionable decision

The original independently frozen J24G01 could have included one tiny physical-tree oracle from the outset. It would have made logical Reader agreement and actual extraction/publication independently distinguishable before later indexed replay variants were introduced. This distinction is prospectively recognizable on any file-archive parser change: a positive logical `read` check cannot by itself prove a correct physical `extractall` tree. Preserve this as local scoped practice, not a global Discovery Engine policy change on one observation.

The resulting **conformance decision is positive** for this limited source and four fixed journal variants on all three tested hosts. Owners of #358 and #481 should integrate the original two Git blobs + separate extraction test if broader product merging is authorized, while preserving exact-head and source-custody checks and all existing release gates. **PR #484 remains DRAFT / NO MERGE / NO RELEASE**, format r24 and published v0.30.0 unchanged. Any doc-only HEAD after this report is a distinct source commit; its eventual checks are not silently projected from the original product-test bearing HEAD.
