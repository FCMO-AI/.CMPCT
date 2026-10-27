# J24K05 — prospective physical projection contract (2026-10-27 UTC)

**Status at preregistration:** prediction only, no product changes, no result-bearing candidate evidence.

## Source and independent control
Canonical release `main@80c358f8824ec1b20d349c92ed94c898090969b0` is v0.30.0, physical revision 24. This candidate is based strictly on research owner #622 at `d835d3e92afbae821253e0ef8344aa1235a39231`, which preregistered and hosted the signed J24K04 S_VZIP inconsistency on two independent immutable golden sources. Do not rewrite J24K04 observational predictions. The Rust native `parse_recipe` already checks literal/skeleton and payload/source sizes for supported stored and retained-mode1 cases; it does **not** establish Python product admission or mode0/2 parity.

## Primary question / hypothesis
Can Python *strict preflight* reject the known fully signed VZIP declared-size contradictions, without decoding physical payloads, while a representation-local `range_vzip` returned-length postcondition rejects in-bounds short answers even when preflight is not explicitly called?

The projected size is `sum(skeleton literals) + sum(declared payload stream bytes)`. It must equal recipe size, and skeleton literal total must equal the authenticated skeleton blob uncompressed size. For ZIP STORED, declared payload size must equal raw content blob uncompressed size; for retained Deflate mode 1, it must equal retained stream blob logical size; for canonical Deflate mode 0, compare with the recorded physical compressed size only when the mode uses an actual `CODEC_DEFLATE` stream; for regenerated mode 2, **do not pretend** that a length check of the raw source proves the compressed output size. Reject malformed cases cheaply and retain exact fallback/readability of all legitimate modes. Never weaken SHA, CRC, frozen goldens or release gates.

## Simpler control and alternatives
One post-slice length check alone catches silence but lets strict preflight admit contradictory signed metadata. One recipe-total equality alone misses a forged skeleton and stored/retained payload byte count that sums correctly. Running whole archive preflight on each range is O(index) and may open a different inode; rejected. Rejecting mode 2 as Rust does would be an unauthorized compatibility regression, rejected. An alternate wire format is unnecessary.

## Prospective falsifiers / measurements
1. **Immutable positives:** existing Builder-independent revision-24 stored and retained exact-Deflate goldens remain accepted by preflight and exactly reconstruct/verify (bytes + SHA-256 + nested ZIP integrity).
2. **Reauthenticated adversaries:** mutate only authenticated recipe/file size +1 and -1, skeleton literal +1, and stored or retained stream-size +1; preserve *all* physical bytes and recompute both index copies. Strict preflight must reject every impossible geometry before reconstruction. Baseline previously accepted at least the +1 pair; positive result must not silently discard that historical negative.
3. **Selective contract:** for the same signed size+1 mutation, `read_range(logical_end,1)` on an ordinary Reader which does not auto-preflight must raise a typed error instead of returning `b''`. Valid ranges, including length zero, remain exact; no full-member SHA assertion for ranges.
4. **Mode semantics:** mode 0 uses blob physical Deflate stream size; mode 2 remains potentially unprovable by metadata-only checks and must at least fail closed on short returned ranges. Explicitly mark preflight limitations rather than overclaiming universal verification.
5. **Host + economics:** installed exact-head package tests on Ubuntu/macOS/Windows; source identity, historical control run / reproducible baseline, per-request overhead on legitimate VZIP ranges, cost of once-per-recipe metadata scan, no numeric benchmark/release credit without true full-system gates.

**Kill/narrow:** Any rejected legitimate fixed vector or mode0/2 compatible recipe, persistent short returned answer, unbounded new allocation, wrong identity/source, or material portability regression blocks promotion. If only strict preflight is shown, mark selective path unresolved; never call a partial success a complete fix.

## Ownership, concurrency, and scope
The new branch is an independent child of #622; #569 owns the broad composed Reader and is not edited. #609 and #615 own unrelated shared validation invariants; minimize validation diff to this VZIP representation, reconcile before future integration, never force-push or overwrite their branches. Original J24K04 scientific test is expected to become a *historical contrary oracle* on candidate source; do not alter its assertions. Discovery state #574 is not a lock and remains untouched.

**Credit boundary:** Candidate product code plus focused fixed-wire measurements only until hosted evidence; no merge, release or new format/version. Preserve every negative and observe exact-head CI before handoff.
