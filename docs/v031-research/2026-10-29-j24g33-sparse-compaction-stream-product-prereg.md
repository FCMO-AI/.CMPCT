# J24G33 — bounded sparse verification transfer into private r24 compaction

Date: 2026-10-29 UTC  
Status: PROSPECTIVE PREREGISTRATION — written before any source edit or candidate test.

## Authority and ownership
- Published main: `80c358f8824ec1b20d349c92ed94c898090969b0`, v0.30.0, on-disk r24; untouched.
- Compaction product owner: PR #723 at exact parent `52d51b9446dc8876319f7bd1e6ca2b7f54681de8`. This child does not modify that owner's branch.
- Streaming verification donor: PR #613 at `3b2bf3c2e033fa27d77b2355821dc0087aa46873`, Reader Git blob `b2b7774c13a5c8235ff89786d171b7ea3ff20710`.
- Independent research transfer: PR #734, first source-exact court Actions #40827365924, reports 128MiB source A 279.125/279.270MiB RSS vs B 27.250/27.508MiB, identical 1809B output within cohort. These are scientific A/B observations, NOT evidence for this integrated source or official release.
- Claim boundary: this child owns ONLY the integration of #613's proven sparse verifier into the candidate #723 Reader to retire an otherwise avoidable logical-hole materialization cost. PR #726 separately owns stage-name rebind races and remains a HARD promotion veto. PRs #731/#734 own independent cost evidence; do not change or duplicate them.
- Shared discovery STATE.json remains untouched; current default cache may be stale and is not a claim or lock.

## Falsifiable primary question
Can the existing #613 Reader implementation be transferred **unchanged in semantics** into PR #723 so that compaction of authentic sparse r24 source with a signed append delta verifies source and reconstructed output without allocating logical-size zero holes, preserving exact archive bytes and metadata/table, and retaining original ordinary Reader read/read_range behavior?

Predictions: (1) source and rebuilt Reader verify accept unchanged authentic sparse archives; (2) wrong sparse hash, overlapping/overlong/missing chunk extents are rejected; (3) 128MiB sparse compaction installed process peak RSS remains <128MiB; (4) A/B independently rebuilt archive SHA agrees on the same physical tree, and source candidate does not add packed bytes, new parser semantics or native ABI; (5) non-sparse read/extract and ordinary PDF/ZIP members remain unchanged.

## Simpler control, alternative explanations and decisive rung
- Simpler control: the exact #723 candidate Reader is already correct on small inputs; the remaining hotspot is `_compaction_assert_equivalent` invoking `verify()` twice. A direct source copy cannot count as compaction, so retain source+output full physical equality checks.
- Mechanism: reuse exactly donor `_verify_sparse_streamed` and its `_blob(retain=False)` cache control; do not design a second verifier. Hash holes with bounded zero chunks and verify the complete final SHA.
- Alternative: #734's A/B improvement may be from altered child instrumentation, not the integrated product, or other temp files/native caches might dominate real compaction.
- Cheapest decisive evidence: static equivalence of donor method AST + inherited focused tests + genuine installed end-to-end compaction with source-aligned HEAD and physical SHA/metadata equality; then cross-platform and complete release gates. No product claim from pure code diff.
- Kill/narrow if any donor semantic change, source/output hash or file-metadata mismatch, corrupt extent accepted, memory >=128MiB on 128MiB sparse in controlled child, fresh non-sparse regressions, inconsistent source identity, or failed exact-head CI. No evaluator, threshold, format or release gate shall be weakened.

## Costs, incompatibilities and promotion debts
Expected extra direct time/CPU: scanning logical zero bytes for a SHA is required even when storage is sparse. Reader API adds one optional keyword arg and one helper; code complexity and frame decode costs must be charged. Long-lived cache suppression reduces memory only in verify. Hardlink aliases are NOT optimized by donor #613; alias equivalence must be separately proven under owner #610. #726 race/custody remains hard veto; hostile pathname replacement, provenance, CI legacy checks, Windows/macOS, official parity and full product benchmarks are still unmeasured until actually executed.

## Counterfactual discriminator
If the exact unmodified #613 donor can be transplanted without byte change, the earlier cheapest discriminator was #731's 128MiB sparse peak RSS followed by #734's identical output SHA A/B; both now exist. This is a prospective engineering convergence attempt, not evidence to modify global discovery policy.
