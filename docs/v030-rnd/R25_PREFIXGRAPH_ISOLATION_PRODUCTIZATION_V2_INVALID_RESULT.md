# PrefixGraph isolation Builder S6 robust-RSS receipts — invalid identity result

Status: **ACCEPTED CUSTODY INVALID / PERFORMANCE SIGNAL NON-AUTHORITATIVE / ZERO RELEASE CREDIT**

This record preserves the result-bearing attempts of the frozen Builder-level PrefixGraph process-isolation S6 contract after the whole-process-tree RSS tracker became exited-child aware. The old S6 preregistration is immutable. These attempts are invalid because the preregistered genuine-r24 product identity did not reproduce; they do not promote or retire the process-isolation mechanism.

## Authority

- authoritative branch: `agent/v030-authoritative-integration`
- exact source: `169333c9f43e05ed07590ba666da0a56535d486e`
- workflow: `CMPCT v0.30 PrefixGraph isolation Builder hostile review`
- workflow run: `33706992295`
- robust RSS authority: `benchmarks/v030_release_performance_tree_rss.py`, including descendant discovery and retention of exited-child peak contribution
- frozen preregistered r24 product identity: **29,883,732 B**
- release credit: **false**

The admission repair on this exact source caused the substantive Hostile Reviewer to execute rather than being classifier-only. Both attempts completed all four alternating control/candidate product builds and preserved internal determinism, strong verification, helper-lifecycle evidence and hostile fail-closed checks before the frozen identity ratchet rejected the receipt.

## Attempt 1

- substantive job: `100498220106`
- artifact id: `9875664201`
- observed r24 product bytes in all four measured rows: **29,883,726 B**
- threaded-control median whole-process-tree peak RSS: **360,572 KiB**
- isolated level-15 candidate median whole-process-tree peak RSS: **272,294 KiB**
- diagnostic RSS reduction: **24.48253034%**
- threaded-control median wall: **61.736766 s**
- candidate median wall: **65.578201 s**
- diagnostic wall ratio: **1.06222944x**
- selected-artifact penalty: **+63 B**

Had identity been valid, the measured RSS, wall and size values would have crossed the frozen local performance bands. They cannot be credited because the r24 identity gate failed first.

## Exact rerun / attempt 2

The same exact source and same frozen workflow were rerun specifically to determine whether `29,883,726 B` was a stable replacement product identity. It was not.

- substantive job: `100508907159`
- artifact id: `9876801999`
- artifact ZIP digest: `sha256:2f431a08589817bf6642bfa3b127fa9448d423de8f676219e0a0a521efe8d1db`
- observed r24 product bytes in all four measured rows: **29,883,728 B**
- threaded-control median whole-process-tree peak RSS: **364,702 KiB**
- isolated level-15 candidate median whole-process-tree peak RSS: **265,522 KiB**
- diagnostic RSS reduction: **27.19480562%**
- threaded-control median wall: **35.075009 s**
- candidate median wall: **35.867960 s**
- diagnostic wall ratio: **1.02260729x**
- selected-artifact penalty: **+63 B**

Again, the mechanism crossed the local performance bands but the receipt is invalid because the exact frozen r24 product identity did not reproduce.

## Decision

**`S6_PRODUCT_IDENTITY_NONDETERMINISM_BLOCKS_INTERPRETATION`**

The old S6 result remains invalid. Do not change its frozen `29,883,732 B` identity to `29,883,726 B` or `29,883,728 B`: the same exact source produced both values on independent attempts, so neither can be adopted post hoc as a replacement constant.

The robust-RSS measurements are useful only as a non-authoritative signal that the process-isolation mechanism may still own a real simultaneous-memory reduction even when exited child processes are charged. They do not grant S6, productization or release credit.

## Causal follow-up

Repository inspection identified a specific fixture-level hypothesis: the Shifted generator deterministically fixes file contents but does not normalize filesystem mtimes, while canonical r24 serializes filesystem metadata including nanosecond mtimes. The accepted historical Shifted content-tree hash does not include those mtimes. Therefore equal accepted content trees can still be different canonical product trees.

That explanation is being tested separately under `R25_SHIFTED_PRODUCT_METADATA_DETERMINISM_PREREG.md`. The old S6 grammar and thresholds remain untouched. Only a separately frozen causal result may justify a new superseding S6 fixture contract.

## Reopening / custody law

These invalid attempts may never be reinterpreted as a pass or failure of process isolation. Reopen their performance interpretation only through a new superseding S6 freeze whose product identity is deterministic for a causally justified reason while retaining the original RSS, wall, size, selection, helper lifecycle, recovery and integrity bands.
