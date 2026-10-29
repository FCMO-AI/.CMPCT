# J24G54b — prospective in-range *false semantic acceptance* discriminator

**Registered 2026-10-29 UTC after J24G54a's decisive false-rejection result but before J24G54b code or CI.** Keep the original J24G54 preregistration, first result and test/physical evidence immutable. This is a new bounded fork under the same research PR #786, not an attempt to rescue/alter the first result.

## Changed question and prediction
J24G54a proved that deleting an earlier row leaves a signed xattr ordinal out of range in `validation._apply_delta`, causing an obvious preflight false rejection. A simplistic future fix that merely drops/clamps invalid ordinals could miss a more dangerous case: when the stale signed ordinal stays **in range** but now refers to a different surviving file, `preflight_archive` might **accept** an effective index whose xattr ownership disagrees with the real Reader.

Prospective physical test: four sorted files `a-early.bin, b-delete.bin, c-owned.bin, z-late.bin`, only `c-owned.bin` carries a real source binary xattr at initial ordinal 2. Build first-party r24 archive; check baseline preflight and actual signed original xattr row. Append a genuine committed `del b-delete.bin`; now three files remain. **Prediction:** structural preflight accepts (`files=3`) because ordinal 2 remains within bounds, but its actual effective index binds the key to `z-late.bin`, while the Reader rekeys it to `c-owned.bin` ordinal 1 and physical strict extraction restores it only there. The direct preflight validation helper's effective index is inspected as a **read-only instrument**; do not modify its source.

## Negative controls and kill criteria
- Control `no_xattr` with same sorted files and journal delete must yield matching empty fsmeta maps; otherwise the test instrument is confused.
- If preflight refuses the in-range variant or correctly associates it with the source path, predicted false semantic acceptance is falsified.
- If both signed xattr origins are identical, index validity fails for unrelated reasons, or actual source xattr capture/restore cannot be established, mark infrastructure/ambiguous rather than science.
- Validate latest footer/delta identity with the existing separate physical referee or an independent extension, not just a source-level mock.
- No new product files, format, release laws, comparators, frozen tests, or discovery state are modified. This is a single bounded follow-up, not unbounded re-testing of the same family.

## Future decision
A positive observation would require any forthcoming owner fix to prove not only preflight acceptance of newly valid archives, but **byte/path ownership parity of the actual effective metadata** including in-range ordinal shifts. No broad release credit from this local oracle; no policy change from one additional evidence rung.