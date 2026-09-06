# ONE-G0.2 native nomination event consumer — terminal result

Date: 2026-09-06
Experimental line: `ONE-G0.2`
Authoritative branch: `research/cmpct1`

## Mission Lock

Remove Python event/index consumption from the semantic handoff between the already-proven native rightmost-min selector and pair nomination, without yet claiming fused-observer speed.

Frozen authority: `docs/one/evidence/ONE_G02_NATIVE_NOMINATION_EVENT_CONSUMER_PREREG_2026-09-06.md`.

## Exact CI receipt

- branch head under test: `7b0b099ed81d6e209be3668aa9cb647f38ca909a`
- PR merge/source SHA executed by Actions: `0f696dfcd49b55c29d5b959d6628bac54484671c`
- workflow run: `34003344581`
- job: `101406034015` (`native-nomination-event-consumer`)
- conclusion: **success**
- semantic/hostile ONE suite: **93 passed**
- artifact: `9980159721`
- artifact ZIP SHA-256: `7bbdb3da7920bce6e70aac976c72198fb96aa66b9b1c20bee6e3cebb86ad5dd9`
- decision: **`advance_native_nomination_event_consumer`**

## Result

Across the frozen 90-row envelope (5 sizes × 3 fresh seeds × 6 case families):

- `trace_mismatches = []`
- `audition_mismatches = []`
- `exact_mismatches = []`
- `false_exact_nominations = []`

The native event consumer exactly reproduced the existing reference pair-nomination policy from the proven native anchor trace. Local fixed-window auditions, global minimizer-witness consumption, run-dominance suppression, `covered_until`, exact 64-byte witness verification, left/right exact extension, and cross-object classification all agreed at the externally visible nomination-count boundary.

Representative hostile/large rows demonstrate that this is not agreement only on trivial positives:

- 256 KiB `shift_plus1`, seed 7: 294 anchors consumed, 1/1 cross audition/exact, 524,158 extension bytes charged;
- 256 KiB `damage_quarter`, seed 7: 287 anchors, 2/2, 409,346 extension bytes;
- 256 KiB `fragmented_every96`, seed 7: 281 anchors, 30/30, 454,560 extension bytes;
- 256 KiB `fragmented_every96`, seed 29: 263 anchors, 28 auditions / 27 exact, matching reference exactly;
- 256 KiB `fragmented_every96`, seed 53: 234 anchors, 33 / 32, matching reference exactly;
- every 256 KiB `fragmented_every32` and independent-random control: zero cross exact nominations.

The local index reached its frozen 64-entry bound as expected. The global index remained far below its 8,192-entry cap on this envelope (hundreds of entries at 256 KiB, not thousands).

## Causal interpretation

There is no longer a semantic reason to keep pair-nomination event consumption in Python. The same nomination policy can be represented natively without a new discovery concept or reader-visible operation.

However, this implementation still scans the combined source+target bytes **after** the selector has already scanned them to produce the anchor trace. Therefore it deliberately preserves one redundant full observation pass and an intermediate anchor trace. It is an oracle/bridge, not the desired writer shape.

## Hostile Reviewer

Do not compare this two-stage implementation's elapsed time to the promoted fused observer and call the result a native nomination regression. The extra scan is known construction debt introduced solely to separate semantic migration from fusion.

Likewise, successful nomination is not complete arbitrary-relation recall. Reference misses remain misses; exact relation proof remains authoritative after nomination.

## Decision / next falsifier

**ADVANCE native event consumption semantics.**

The next Builder should fuse this exact event/index logic into the promoted native observation/minimizer pass so Gear state, run state and selected anchors are consumed where they are already produced. The fused implementation must match this terminal two-stage oracle on every frozen row, remove the second full byte scan and intermediate anchor-trace dependency from the candidate path, expose exact source-traffic/state accounting, and only then become eligible for a native writer-discovery performance claim or the integrated safe-relation-dispatch A/B.
