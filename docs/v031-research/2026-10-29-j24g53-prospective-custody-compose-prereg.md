# J24G53 — prospective v0.31 candidate custody on the installed J24G50 integrity union (pre-result contract)

Date: 2026-10-29 UTC
Status: preregistration before donor source transplantation; draft integration research, no merge/release.
Owner: this isolated branch only; upstream #778 and #266 remain authoritative for their own code.

## Exact baseline, question and claim

Published `main@80c358f8824ec1b20d349c92ed94c898090969b0` is v0.30.0 / revision 24 and is untouched.
Source parent is J24G50 #778 exact `47c9a4d61cd764aa4252cad741f4b22537106c60`, combining #773 journal-fsmeta and #767 zero-output Zstd defects with three-host specialized SUCCESS (run 40941257484). Its generic CMPCT Tests run 40941257274 is FAILURE, reporting 825 passed, 4 inherited release/source-attribution failures, 2 skipped.
Prospective source-custody owner is #266 exact `c5ea5b97a86bf9d0bffe9dad54c5fd2a6f0b6fb1`; its exact-head fast tests (run 39975603659) were SUCCESS. The owner isolates immutable published v0.30 release evidence from mutable v0.31 candidate identity.

**Primary hypothesis:** eight source-identical #266 files grafted onto exact #778 can close the four inherited release/fingerprint test failures *without editing the published v0.30 release lock*, weakening assertions, rewriting historical evidence or changing CMPCT engine/format. This is a source/evidence-enablement composition, not a performance or product improvement by itself.

**Strong simpler control:** run the existing full CMPCT test workflow unmodified on #778; it has four known red tests. The separate #266 fast test green cannot alone prove integrated source/metadata/codec correctness, so the composed checkout must execute all of its own tests. Historical main four-red remains a real base state, not a green claim.

**Alternative explanation:** a test/manifest assumption may only fit the older #266 development tree or existing source-checkout semantics; replacing entire files may inadvertently overwrite other parent changes, or CI source-hash scope may not cover J24G50 product mutation. If so, preserve and localize each mismatch, rather than editing frozen inputs or claiming all green.

## Mutation boundary and independent controls

- Verify each donor Git blob and each target path against current parent before transplanting.
- Transplant only the eight exact existing #266 file blobs (four existing source-attribution tests, one CI workflow, new v0.31 manifest, candidate fingerprint helper, candidate tests). Do not port any source/product bytes or re-create the mechanism.
- Before mutation, check #778 has not modified any donor target path relative to source baseline. Exact donor and parent files must be independently inspectable. No source files of Reader/Writer/codec/native, numerical version, format, benchmarks, immutable release lock, release receipts or Discovery STATE may change.
- The candidate helper must bind all presently required source files by path and SHA; mutation, rename, symlink, required-file absence and out-of-tree cases must fail closed. Existing fast CI, release tests, three-host J24G50 court and inherited benchmark semantics remain untouched.
- Preserve original complete JUnit records, process exit code and actual check conclusions; no full CI pass unless *this* exact head executes. Compare real test names and failures, not textual headline counts. The #778 three-host result does not automatically validate this new head.
- Expected worst case: source-only CI graft repairs 4 reds, but general-product performance, safety/correctness (especially hardlink xattr conflict #783), historical signed replay, same-UID publication identity #749 and external dominance remain unresolved.

## Disproof and decision

KILL/NARROW if any donor blob differs, a parent target has new overlapping mutations, a four-red test still fails, the added identity tests reject valid source or accept a mutation/missing file, source SHA does not match the installed checkout, the inherited J24G50 behavior regresses, or the original v0.30 lock blob changes. Do not waive, skip or rename tests to rescue it.
A successful exact-head full test plus specialized physical court is evidence for **integration readiness for review only**, not permission to merge/release. Any CI failure must be distinguished from infrastructure/runner starvation.
If the hypothesis survives, provide exact-head artifact/CI URLs to #266 and #778 owners; keep implementation isolated on this branch until the legitimate release owner decides full composition/promotion.

## Opportunity cost / PARETOBONK

Alternative families considered: same-UID inode publication #749 (owned and not resolved by a name-local patch); #783 hardlink metadata preflight (already owned); novel A14 PNG CRC representation (tiny lower-rung headroom); broad compression search (expensive, less immediate than a four-red correctness gate). Prospective source identity is the cheapest currently unclaimed route toward an actual integrated safe product with auditable CI. Stop after one decisive full-suite trial unless a new observation changes the decision.

## Evidence tiers

1. Existing donor/parent CI (historical source-exact but not composed).
2. Proposed exact Git-blob graft and code-level identity verification.
3. Composed exact-head full pytest + donor mutation controls.
4. Cross-platform installed physical J24G50 rerun if the branch workflow permits and results are required.
5. Release parity, portability, performance and promotion: **unmeasured** at preregistration.
