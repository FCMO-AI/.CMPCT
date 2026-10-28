# J24K09 — Physical length witness for skipped Virtual ZIP streams

Date: 2026-10-28 UTC. Preregistered before implementation.
Parent: #642 at 78bc1f552fee24970228f89ac25dbf23307b0406. Draft v0.31 only; no merge, release, format or version change.

## Question and baseline
J24K07 #645 confirms that signed size inconsistencies in prior ZIP STORED, canonical Deflate mode0 and retained mode1 streams can return incorrect but correctly sized suffix bytes. Parent #642 checks selected and regenerated mode2 streams but trusts nonmode2 prior stream lengths when moving logical offsets.

## Hypothesis
A same-Reader lookup of the physical blob record header can prove a preceding stream's length without decoding its bytes. STORED and mode1 use the physical record's decoded size; canonical mode0 uses physical compressed length. Reject any mismatch with authenticated blob metadata or recipe csize. Keep prior mode2 reconstruction proof intact.

## Prediction and refutation
All six existing signed J24K07 mutations must reject wrong-coordinate suffix reads. Genuine Builder-produced ZIP variants, early/late reads and empty reads must preserve exact outputs. Malformed blob descriptors and physical header disagreements must fail closed. Prior nonmode2 size checks should not call the blob decoder. Refute or narrow if any valid input breaks, if any adversarial case still silently returns a wrong byte, or if the complexity/resource cost cannot be bounded.

## Controls and evidence
Compare against original #642 source and the simple but expensive alternative of reconstructing skipped streams. Distinguish structure/position correctness from cryptographic authentication of partial reads (#646), which cannot be established by sizes alone. Start with deterministic component and installed Reader tests; hosted multi-OS validation and measured system costs are required before product promotion. Keep original evaluators, workloads and evidence unchanged.

## Coordination
Do not modify source-owner PRs #638/#642 or scientific PRs #645/#646. Do not update discovery STATE owned by #574. This is an adjacent product repair after independently proven evidence, not a redundant implementation of mode2.
