# ONE-G0.2 fused native nomination — terminal semantic/traffic result

Date: 2026-09-06
Experimental line: `ONE-G0.2`
Authoritative branch: `research/cmpct1`

## Mission Lock

Fuse the already-validated native pair-nomination event consumer into the promoted native rightmost-min Gear/minimizer observation pass, eliminating the second full byte scan and the intermediate anchor-trace dependency without changing selector or nomination semantics.

Frozen authority: `docs/one/evidence/ONE_G02_FUSED_NATIVE_NOMINATION_PREREG_2026-09-06.md`.

## Exact CI receipt

- branch head under test: `c62de836aea8ca6790316d4349264a9836ab2c6b`
- PR merge/source SHA executed by Actions: `1a0f577c256f8611fe3f72837b518633c3395b7e`
- workflow run: `34003512392`
- job: `101406473103` (`fused-native-nomination`)
- conclusion: **success**
- semantic/hostile ONE suite: **93 passed**
- artifact: `9980210229`
- artifact ZIP SHA-256: `d766b65521eae804f0c73cdd120a13773c7c6e4a13145834978f32f733975162`
- decision: **`advance_fused_native_nomination_semantics`**

## Frozen result

Across all 90 rows (5 sizes × 3 fresh seeds × 6 case families):

- `selector_mismatches = []`
- `trace_mismatches = []`
- `nomination_mismatches = []`
- `no_trace_mismatches = []`
- `false_exact_nominations = []`
- `traffic_mismatches = []`

The fused kernel reproduced the exact native selector state/anchor trace and the exact terminal two-stage nomination result while consuming nomination events at the point where the minimizer already has the selected Gear value and position.

Modeled sequential observation traffic fell from two complete passes to one on every row:

- two-stage baseline: `2 * len(previous + current)`;
- fused candidate: `len(previous + current)`;
- fused / baseline sequential observation traffic: **0.500000x** on every row.

The fused candidate's nomination path was also rerun with trace output disabled; every result field remained identical, proving that the candidate no longer requires an intermediate anchor trace for nomination.

Representative 256 KiB relation rows (combined prior+current input is 512 KiB):

- `shift_plus1`, seed 7: 294 anchors, 1/1 cross audition/exact, 524,158 extension-read bytes;
- `damage_quarter`, seed 7: 287 anchors, 2/2, 409,346 extension-read bytes;
- `fragmented_every96`, seed 7: 281 anchors, 30/30, 454,560 extension-read bytes;
- `fragmented_every96`, seed 29: 263 anchors, 28 auditions / 27 exact;
- `fragmented_every96`, seed 53: 234 anchors, 33 / 32;
- all 256 KiB `fragmented_every32` and independent-random controls: zero cross exact nominations.

## Resource debt exposed by hostile review

The semantic fusion deliberately reused the bridge's simplest bounded research indices: 64 local entries plus a fixed 8,192-entry global array. With the current native struct layout this reserves **198,144 bytes** of event-index storage irrespective of actual use.

That is not a promotable writer shape. On the frozen 256 KiB relation envelope the largest observed global peak was only **272 entries**; the fixed research allocation therefore materially over-reserves memory and pollutes the cache hierarchy simply to preserve the hard maximum.

This does not invalidate the one-pass result. It identifies the next causal owner before timing: representation/allocation of the writer-side nomination index.

## Decision / next falsifier

**ADVANCE the one-pass fusion semantics and traffic result, but do not promote the current fixed-index implementation.**

Next, preserve the exact 8,192-entry hard cap while changing the global writer-side index from fixed maximum reservation to bounded demand-grown storage. The candidate must remain byte/nomination exact, must never exceed the same cap, must report actual capacity/peak bytes, and should materially reduce resident state on ordinary/tiny inputs before any elapsed carrying-cost comparison is granted authority.

Only after that state debt is repaired should a paired native timing gate compare:

1. promoted selector/observer alone;
2. exact two-stage selector + nominator;
3. fused one-pass nominator.

That gate will decide whether removing the second scan actually survives the irregular in-loop index/proof work in elapsed time.
