# J24K02 — S_PACK selective geometry validation (prospective implementation test)

Date: 2026-10-27 UTC. Status: **PREREGISTERED, BEFORE PRODUCT CODE OR RESULT**.

## Authority, baseline and ownership
Published CMPCT v0.30.0, on-disk revision 24. Stack on frozen [J24K01 #598](https://github.com/FCMO-AI/.CMPCT/pull/598) at `69ce3cc18f014d76d2c4df104de192c702b0de78` rather than editing its established negative-science instrument. [J24K01 hosted result #40511702240](https://github.com/FCMO-AI/.CMPCT/actions/runs/40511702240) proves six fully reauthenticated S_PACK selective-read anomalies against the unmodified Python Reader; native ABI admission independently owns the stronger structural control in #314. Composed Reader work and performance debt are owned by #569; do not modify that branch. This child patch is a source-isolated candidate for future cherry-pick/integration, not release authority.

## Primary question and falsifier
Can an **O(1) per-selected-request** consistency check reject declared S_PACK span/owner/size contradictions **before physical blob decode or slicing**, preserving all legitimate RAW and Zstd PACK ranges exactly?

Mechanism: check storage tuple arity, exact non-boolean integer types, nonnegative blob index, offset and declared length, valid physical owner, declared packed length == logical member length, and `offset <= owner_uncompressed_size` with `length <= owner_uncompressed_size - offset`. Then use existing `_blob` and range path unchanged. Python's unbounded integers require no 64-bit arithmetic; subtract to prevent overflow assumptions in other languages.

## Strong control / alternative explanation
- Inherited J24K01 freezes six authenticated malformed RAW/Zstd wire archives; untouched baseline experiment **must continue to detect acceptance if run on its original source**, not silently invert its historical criterion.
- New J24K02 acceptance court **inverts only predicted outcomes on the candidate**: all six malformed cases rejected and both originals/ranges match independent known byte answers.
- Extend hostility with zero-length requested range and noninteger/boolean/negative tuple fields if the independent rewriter permits. Reject malformed metadata even on zero-byte requests.
- Stronger control: `preflight_archive()` already rejects these geometries, but separate preflight may scan the entire archive and introduce file-identity drift; avoid making it a `read_range` requirement.
- Alternative cause (CRC/invalid index authentication) is excluded by J24K01's fully reauthenticated primary/tail indexes and intact physical bytes.

## Kill/narrow conditions and economics
Reject candidate if any malformed selected request returns successfully, a positive READ/READ_RANGE output changes, a hostile condition crashes instead of raising controlled I/O/ValueError, or the candidate requires a full-file/all-entry preflight on each range. Measure local call-path overhead if feasible, but micro-only evidence is not whole-product performance promotion. Do not change the on-disk format or original court, loosen comparators, redefine source SHA or claim native/full-product parity.

## Evidence boundary and handoff
Research falsifier [#598](https://github.com/FCMO-AI/.CMPCT/pull/598) is the frozen inherited negative; this branch targets a candidate Python Reader correction. Product credit **PENDING** until real hosted installed-package results plus broad composition #569 and exact-head release gates. No merge/release authorization from this preregistration.
