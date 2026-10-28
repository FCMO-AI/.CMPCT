# J24B03-A — source-exact safety acceptance composition (prospective)

2026-10-27 UTC. **Preregistration before J24B03-A implementation.** This is evidence-enablement, not a new science claim.

## Baseline and prior immutability
- Released control: CMPCT v0.30.0/r24 `main@80c358f8824ec1b20d349c92ed94c898090969b0`. Isolated candidate: PR #609 `afcffd59a0ab3ac1133f1a968fcf649fd96a9eda`, Reader blob `33deb74e196f7e40aa8351b6ec426a24255d5eec`.
- Original 24-wire size-guard court passed all three hosts (Actions #40546227217). Separate H2 hostile-physical-BHDR court passed all three (Actions #40563840185).
- **Original J24B03-H preregistration was falsified** (Actions #40554574952): it incorrectly predicted unchanged historical bytes for a corrupt metadata-length field. Current original J24B03 workflow remains red (Actions #40565133857). Preserve H's immutable assertion, red run, and independent negative record; never relabel it green or weaken it.

## Problem, competing action, and falsifier
A current-head single-workflow safety witness cannot depend on H's known-false prediction. Do not edit H or mark its failure `continue-on-error`. Instead run the previously **independently preregistered and executed** original 24-wire court and H2 on **the same frozen original and same exact candidate head**; use their unchanged existing independent referees. This is a new prospective **integration gate**, not a repair of H.

For Ubuntu 24.04, macOS 14, Windows 2022, Python 3.11:
1. Pin and separately build released and candidate trees, record/verify both commits and Reader source Git blob IDs.
2. Run unchanged original size court baseline-vulnerable + candidate-repaired on the same 24 signed images, two empty controls and three independent golden codecs. Require the original stdlib referee PASS: six valid preserved, eighteen invalid size geometries rejected by candidate, two historical tail-index spills rejected.
3. Independently run unchanged H2 generator on one corpus, then execute untouched released and candidate arms, then untouched stdlib H2 referee. Require 2/2 original valid controls, 10/10 corrupt header rejections by candidate per OS, historical metadata-length shift observed and audited.
4. Persist all original wires, receipts, source IDs, and referee artifacts on failure or success. Validate CI topology on Linux.

**Kill/no admission:** any mismatch in source identity, wire identity, expected valid controls, candidate rejection, auditor result or OS transfer; any missing evidence is failure. This court does not claim generic corpus transfer, full Reader reliability, performance parity, immunity to mutable inodes, or release authority.

## Causal alternative and scope
H predicted an impossible unchanged-byte result for `rml=1`; new H2 observed the one-byte shift. Separate science from acceptance rather than ignoring the red. Reader integration owner #569 carries a measured ~27–28× cold-open regression; #610/#615 independently own hardlink alias-size; full general/native authority gates are still red or unverified. Passing this court does **not** waive any of those requirements.

**Prediction:** PR #609's exact Reader guard passes both accepted courts on every host. Any failure leaves durable contradictory evidence, not an adapted evaluator. No Builder, format, codec, canonical Reader or version change.
