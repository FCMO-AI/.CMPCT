# J24G06c — Cross-window in-place footer mutation: buffering confound discriminator

**PREREGISTRATION — BEFORE ANY J24G06c INSTRUMENT OR PRODUCT EDIT.**
Date: 2026-10-28 UTC. Exact source parent: scientific PR #651 at `2852dd2ebaa203a2b51b5afc92a7b050978d7b74`, Reader candidate from #650 at Git blob `bead2ea6a09a6daaadc3ec2389cfb8853e3dd172`; released Reader `e716233403dabd0966863c45635e18fa5ac6afb8` at `main@80c358f8824ec1b20d349c92ed94c898090969b0`. Branch: `agent/phased2-v031-j24g06c-cross-window-footer-refresh-20261028`. Scope: **research-only**; no Reader, Writer, Builder, validator, format, frozen benchmark, release or threshold edit.

## Why another test is decision-changing

J24G06b #651 predicted default historical Reader would revisit a modified footer after a deterministic same-inode rewrite, while negative-cache candidate would not. Its first hosted court did not show the predicted divergence. The plausible simpler explanation is CPython's ordinary buffered `open(path,'rb')` retaining a previously read footer across the second seek: on small adjacent-footer files, the historical Reader can also re-read stale bytes. A failed small-file test does not establish whether memoization is safe under **every** in-place mutation interleaving.

## Precise question / hypothesis / alternative

Does placing the mutated footer A and its referencing newer footer B in different 1 MiB scanner windows allow the **unchanged** historical Reader to observe a physically updated authenticated footer A, while the candidate's per-open `known_bad` set skips A and selects the older checkpoint?

Prediction: Both unchanged Readers choose the original Builder checkpoint when there is no mutation. With a deterministically injected same-inode A-header reparenting during the first B→A replay, original historical Reader will re-evaluate A and select A (delta depth 1) after the scanner seeks into the earlier window, whereas the candidate skips A and selects the Builder checkpoint (delta depth 0). An **adjacent-footer small-file control** is retained to confirm/characterize the earlier nonconfirmation, not rewritten as a positive result. Same physical input bytes, logical hash, signed payload SHA and replay injection boundary are required for each Reader.

Strong simpler controls: exact unmodified historical Reader, unchanged candidate Reader and the J24G06b small-file control, paired with before/after SHA-256, same inode/size, footer header and source blob identities. Competing explanations: buffered read caching still masks mutation; a valid newer B or old A is accidentally selected for unrelated reasons; the candidate cache is not populated; B or A crosses a malformed footer boundary; or another writer invariant disallows such mutation entirely.

## Cheapest decisive execution and kill conditions

Build one authentic v0.30 r24 Builder archive; append identical SHA-valid no-op payload+FTR for A (parent=0, invalid orphan) and B (parent=A). Insert only zero filler so A resides in the first 1 MiB scan block and B in the final block; set the **total archive length exactly to 2 MiB and repeat with 3 MiB** to force scan-window boundaries and avoid speculative timing races. No crafted revision/format grammar change; this is a deliberately hostile, checksum-authentic invalid tail plus synthetic in-place rewrite.

Re-use J24G06b `read_case` injection after the genuine decoder returns the old A, rewriting only A's FTR `prev` to the actual Builder checkpoint and fsyncing via a second handle; preserve same length and SHA-valid no-op payload. Count A visits, selected footer, delta depth, complete physical hashes and public `read`/`read_range`/`verify`. Assert the mutated physical file contains the new FTR and the output logical payload matches Builder, for **both** Readers. Do not interpret the old court's nonconfirmation as a failure of this distinct preregistered test. Counter-test no-mutation and small adjacent control.

**Kill/narrow:** if original and candidate select same generation under both cross-window sizes despite the real rewrite, record **NONCONFIRMING** and do not change the product; investigate buffering with an independently instrumented I/O trace, not a weakened assertion. If only one size diverges, record limited scope. If both diverge, record genuine conditional per-open temporal generation-selection inconsistency, **not** a remote exploit, release failure, broken signed data or proof of a supported mutable-source contract. Any source-identity drift, header/hash mismatch, wrong logical payload, or test injection failure invalidates the court; preserve raw failure.

## Cost, scope and next decisions

Two 2–3MiB files per Reader are small; only low-volume source-bound research CI, not a full product matrix. The branch must not modify #650/#651 owners or `docs/discovery/STATE.json`. No release credit. If divergence is real, ask the Reader owners to choose between explicit immutable-input semantics, snapshot/custody, or a reliable mutation detection invariant before promotion. If not, retire this specific interleaving and prioritize distinct Reader performance/correctness debt. Local oracle evidence cannot substitute for hosted genuine-source execution. Preserve losses, evidence and benchmark boundaries.
