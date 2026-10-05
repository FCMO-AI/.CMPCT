# Preserve primary CI diagnostics and repair PR #221 validation

## Problem and baseline

When correctness failed before benchmarking, CI tried to summarize or upload measurements that did not exist. Commit `cccf38da` preserves the primary failure and its stream and separates cancellable classifiers from admitted exact-head receipts. Its own validation exposed four test failures: a truncated release fingerprint, an attribution test pinned to an obsolete surface, and an incomplete PR dossier. The public-proof job also failed because its evidence envelope took project identity from the historical v0.29 frontier while the serving project was v0.30.

## Insight and hypothesis

Evidence admission policy and evidence ownership are separate invariants: a rolling pre-1.0 checkpoint still fingerprints its historical-engine helper, conformance/platform sources, disclosure rules and workflows. Likewise, serving identity and measured identity must remain separate. The quality-ratchet improves diagnostic custody and provenance without changing engine bytes or performance thresholds. Disproof: a missing/corrupt benchmark must retain its primary failure, and a future serving version must not relabel historical candidate rows or hide losses. A receipt present in the DOM is insufficient: its geometry must fit the visible card.

## Alternatives considered

Retaining the narrower fingerprint would leave release-critical mutations outside candidate identity. Restoring the old strict receipt/admission policy would reverse the current rolling-release decision. Both are rejected; restore the inherited fingerprint surface while preserving current admission policy. Pinning attribution to another literal would repeat the next-release failure; assert the active core line and the historical campaign floor instead. Relabeling old benchmark records as v0.30 would fabricate evidence; preserve their measured identity and values. The coherent attribution and proof-surface work advances the surface once from `0.30.a` to `0.30.b`; core remains `0.30.0`, with existing format/ABI contracts.

## Evidence

Pre-change reproduction: four failures and nine passes in the attribution/fingerprint/topology custody tests; generated-site release evidence fails on its project-version equality. Focused repair checks: 15 passes, including enhancement of real committed frontier data under a synthetic future serving identity. `tests/test_ci_failure_diagnostics.py` exercises the real workflow scripts with absent, valid and corrupt evidence and preserves a subprocess exit status of 23 through pipefail.

Full regression suite: **791 passed in 531.67 s**, Python **3.11.17**, with test/audio extras installed. Four corpus-sensitive cases separately pass under that same interpreter. Public-proof and release-evidence contracts, JavaScript syntax, Browser Lab writer plus canonical r24 reader, and all **16 physical viewport classes** pass. Desktop 1440×1000 and mobile 390×844 were rendered and inspected with reduced motion. Inspection reproduced an additional mobile receipt defect (1302 px of content in a 351 px card); bounded tracks and wrapping repair it, and the viewport gate now checks the card, body and grid.

Local raw evidence is retained in the sibling `PS3-EVIDENCE/` directory: `cmpct-round2-pytest-final.log`, `cmpct-round2-site-final.log`, `cmpct-round2-viewports-final/`, `cmpct-round2-manual-anchors/` and `cmpct-round2-receipt-baseline.log`. ABBA results are recorded below after the unchanged performance checker completes.

Reproduce with `python -m pytest -q`; run all six workflow-invoked `tools/check_*` programs. Topology uses the changed workflows, as `ci-topology.yml` requires. Validate this body with `tools/check_pr_evidence.py --base-sha origin/main --event <synthetic-event.json>`, where `pull_request.body` is this file and `draft` is false. Public-proof validation follows `.github/workflows/site-proof-contract.yml`, including the physical viewport matrix.

## Losses, ambiguity and negative evidence

No compression or speed improvement is claimed. Existing competitor losses and historical benchmark records remain intact. The full v0.30 product-selector, hosted Android and other platform authorities are separate from the local r24 parity comparison. The earlier Python 3.13.5 run produced 787 passes and four errors/failures at the frozen corpus hash boundary; its gzip header differs from Python 3.11, and the generator cannot reproduce the accepted log tree under that interpreter. Preserve that negative evidence in `cmpct-round2-pytest.log`; do not rewrite historical hashes. Final validation uses CI's Python 3.11 line and does not claim a GitHub-hosted receipt. This is maintenance, not a breakthrough seed or release promotion.

## Safety, integrity and resource accounting

No archive parser, resource bound, recovery or path behavior changes. Missing measurements suppress the performance claim; corrupt measurements still fail. Pipefail preserves the originating error. Upload remains strict when an executed correctness suite owes its diagnostic stream. Fingerprint patterns cover source inputs and exclude Cargo target output, Android build output and generated JNI libraries.

## Compatibility and portability

Core remains `0.30.0`; the coherent surface milestone advances from `0.30.a` to `0.30.b`. Attribution still requires the campaign's `0.29.k` floor on the historical line, and follows the normal reset on later core lines. No new on-disk grammar, native ABI or optional dependency is introduced. The stable public-evidence schema remains v1 with additive measured-version/format provenance and legacy renderer fallback. Browser Lab retains its reviewed revision-24 writer and canonical-reader smoke test.

## Performance accounting

Archive bytes, create/extract/read behavior, selective decoded work, peak memory and reconstruction dependencies are unchanged by source inspection: `src/`, native engine and parity harness match the direct base. Execute the unchanged workflow's same-tree seven-repetition ABBA comparison before final attestation. The checker retains zero-byte size tolerance and the 5% plus 3 ms timing envelope. It measures the canonical r24 core, not the v0.30 product selector. No synthetic or copied measurements receive benchmark credit.

## Public-surface check

The disclosure guard checks the tracked public text. The renderer displays current project identity separately from the historical measured frontier and retains measured candidate labels, raw record references and losses. Existing committed benchmark records are unchanged; no hand-copied performance headline or private provenance is added. Generated static output is locally validated; publication is outside this local, no-push repair.

## Completion gates

- [ ] Full pytest suite and all workflow-invoked checker programs passed for the repaired candidate.
- [x] The missing/corrupt-evidence and future-version disproof cases attack the surviving assumptions.
- [x] Existing design footnotes and benchmark semantics are preserved.
- [x] Non-obvious identity and diagnostic invariants have nearby why comments.
- [x] No workload, fair competitor loss, timing boundary or threshold was weakened.
- [x] Breakthrough rehabilitation is N/A: no research gain or numeric release is promoted.
- [x] Version discipline retains core 0.30.0 and advances the coherent surface milestone once to 0.30.b.
- [ ] Same-tree r24 ABBA comparison passed its unchanged release-performance checker.
- [x] Public-proof, Browser Lab and all physical viewport checks passed locally; changed receipt geometry was rendered and inspected.
- [x] This dossier and repository regression tests explain the mechanisms and their limits.

## Future leverage

Later core releases can reuse historical evidence without corrupting serving identity or relabeling measurements. Restored custody inputs prevent release classifiers from accepting changes outside the candidate fingerprint. CI failures retain useful diagnostics without manufacturing secondary measurement failures. Remote PR-body installation, hosted checks, merge and static publication remain for the normal authorized review path; this task performs no remote writes.
