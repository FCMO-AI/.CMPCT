# O63 preregistration — exact-source one-buffer VZIP x rollback union

**Date (UTC):** 2026-10-25. **Status:** PREDICTION, before O63 product modifications or result-bearing execution.
**Canonical repository:** FCMO-AI/.CMPCT. **Scope:** single independent composite branch on O60 #415, exact base `c88a6bc29b9ec8738e23aab788b7c09ab0390e79`. Source Builder blob `bda9d7f8005e276ba891aac75ae50eabe67bd431`, codec `dc3446b0eed82edfba9380e3885a20aa45577899`.
**Independent component:** #287 at `295c7944d953901d701496a4903785a185061a70`, candidate Builder blob `745b05ded92bbf84a681a4b159ac7a3c341858c5`, owner-focused installed test court 40025216818 (7/7 PASS, no full release credit).
**Rationale for ownership:** O60 #415 owns one-capture ZIP/WHL parsing; #287 owns abandoned VZIP candidate rollback on the earlier Builder. This research integrates two *different*, already result-bearing mechanisms without editing owner branches. O62 #417 owns historical source-custody CI, not rollback. Check for new overlapping owner before late writes.

## Falsifiable primary question
Can the original #287 per-hash rollback journal be composed with O60's `original=raw` one-capture API so that an unsupported later member leaves **zero** speculative candidates, hints or Deflate variants, while all inherited O60 exact-source reconstruction and stable archive-byte parity remain intact?

**Baseline:** O60 uses `raw=p.read_bytes()` followed by `make_vzip_recipe(p, self.add_content, original=raw)`; successful ZIP/WHL remains source coherent. If a valid later Deflate stream cannot be reproduced, recipe returns `None`, but `self.add_content` already mutated `self.cands`, which `Builder.build` later encodes. #206 and #287 previously isolated this defect in the pre-O60 Builder.

**Hypothesis:** move #287 mutation journal unchanged in semantics into O60 and pass the *same original bytes* through that transaction. Success commits exactly prior candidate state; None/exception restores mutations, including existing shared-hash alias hints and Deflate counts, and ordinary opaque fallback uses the single original capture.

**Strongest simpler control:** O60 with `make_vzip_recipe` deliberately disabled for that same valid late-Z_FIXED ZIP, compared as complete deterministic r24 archive bytes. A successful VZIP (normal Deflate, STORED, WHL, mixed, 8-ZIP cohort) must remain byte-identical to O60 on same source, not merely extract equal bytes. The original #287 fixed-Huffman adversary must be *actually* irreproducible at levels 0–9, not malformed ZIP.

**Alternative explanation:** O60 or other antecedent already deduplicates unreferenced blobs; if no actual output delta or state mutation remains, do not productize a redundant mechanism. Reusing #287 may silently induce an extra full source read or change the successful canonical state; any such outcome falsifies this composition.

## Cheapest evidence and decision
1. Before changing code, execute/inspect narrow source-exact microcontrol on O60 with a true valid 2-member ZIP (first STORED, later Z_FIXED) and forced-opaque oracle: compare candidate state and complete final r24 archive bytes. If already identical, STOP/no mutation.
2. Reuse the #287 journal implementation rather than building a second parser or mark/sweep. Adapt only its entrypoint to accept captured original; do not re-open the original path. No product file except `src/cmpct/builder.py` may change.
3. Execute focused independent tests for valid-Z_FIXED rejection; pre-existing alias rollback; successful VZIP exact equality; O60 post-capture same-inode mutation reconstructing original ZIP; cohort threshold; and no extra path read. Preserve original fixed-huffman semantic adversary.
4. Run on real installed CMPCT packages in Ubuntu, macOS and Windows with exact commit/blob pin, counted passes/skips, and preserved JUnit/log artifacts. Inherited O60, O47, O50 tests need a legitimate source identity rebind, not weakened assertions. Failures do not become passes due to workflow admin status.
5. Performance: no measured speed gain claimed. Charge journal metadata, sources and memory. Any meaningful create wall/CPU/RSS slowdown remains promotion debt pending official unchanged comparison.

**Kill/narrow:** abandoned candidates still encoded, original source re-read, successful O60 r24 bytes differ, O60 adversarial mutation fails, inherited hardlink/unsupported-input semantics fail, or tests rely on a mocked codec rather than actual fixed-Huffman ZIP. Do not adjust comparator, fixture, inherited threshold or format.

## Evidence classification
- Parent #287/#415 courts: inherited evidence, **not** O63 product credit.
- New local derivation/microcontrol: lower-rung research, no product credit.
- New installed exact-head tests: scoped O63 product evidence only when result-bearing.
- Full release performance, all-platform filesystem safety and v0.31 promotion: UNMEASURED, NO MERGE, NO RELEASE until separately earned.

## Concurrency/handoff
Primary narrow claim: composing #287 explicit failed-VZIP rollback into #415 one-buffer product. Never modify #287, #415, #417 or their parent branches. Before late writes read current heads and reconcile. Store exact run/sha, negatives and next unclaimed action in this PR, not in Discovery STATE unless its decision frontier actually changes.
