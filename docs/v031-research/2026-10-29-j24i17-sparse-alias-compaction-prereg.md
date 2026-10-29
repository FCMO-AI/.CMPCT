# J24I17 — Sparse physical-owner alias compaction resource court (preregistration)

Date: 2026-10-29 UTC
Status: **FROZEN PREDICTION BEFORE INSTRUMENT / RESULTS**
Scope: independent source-exact science on unmerged PR #735 only. No product, Reader, Builder, transactions, core version, format, benchmark comparator, release threshold, or shared Discovery state mutation.

## Authority and concurrency
- Published main: `80c358f8824ec1b20d349c92ed94c898090969b0`, v0.30.0 / revision 24.
- Exact unmerged stacked parent: PR #735, head `82e90eca58ed0580df191378947004e4061d53c3`; its integrated Reader donor is #613, blob `b2b7774c13a5c8235ff89786d171b7ea3ff20710`. Its original Builder/transactions source must remain byte-identical.
- #620 already owns sparse hardlink verification. #735 owns compaction integration; this experiment does not copy or mutate either implementation. #726 retains the independent stage-name custody promotion veto. #574 owns shared Discovery state.
- Earlier #731/#734 measured sparse regular-file-only behavior: about 279 MiB → 27 MiB RSS for 128 MiB logical sparse; #735 explicitly records the untreated alias path. Do **not** report this as a novel root-cause discovery. The missing decision-bearing observation is a source-exact, genuine *compaction* resource cost for an otherwise identical physical sparse owner with one logical hardlink alias.

## Primary falsifiable question
On the exact installed candidate #735, does adding one real physical hardlink alias to a 128 MiB predominantly-hole archive produce a material *incremental peak RSS cost during genuine journal compaction*, even though the physical payload and sparse owner are unchanged?

Prediction: one sparse K_HARDLINK alias is verified via `Reader.read()` rather than the #613 incremental sparse owner path, and triggers >=64 MiB greater fresh-process peak RSS than the owner-only control (same logical owner data, same journal replacement, same host, same build parameters). Two independent fresh child trials per condition; 2 MiB analogue as small control.

## Necessary controls and evidence
1. Source tree `a-owner.bin` is genuinely sparse (two 4 KiB physical ranges) and the optional `z-alias.bin` is a real OS hardlink to it, not a content duplicate; Builder must encode owner as `S_SPARSE` and alias as `K_HARDLINK` referencing that owner.
2. Real `append_update` on a small member ensures compaction is not a no-op.
3. Separate fresh Python processes measure compaction-only RSS/CPU/wall; collect installed module paths and exact Git source blobs; retain actual source and compacted archives and raw receipts.
4. Verify all source/target logical SHA identities, linked owner topology, UID/GID/mode/mtime indexed metadata, journal removed, source SHA unchanged, and actual physical output (not projected sizes).
5. Compare 2 MiB vs 128 MiB and alias vs owner-only. No source-identical ABBA claim across topology variants; within each condition repetitions must consume the identical physical source bytes.
6. Negative branch: if admission or compaction fails, preserve raw failure and classify correctly rather than declaring performance. If a real alias is optimized without a new memory spike, retire this risk for the measured regime.

## Simpler control, alternative explanation, and kill condition
Strongest simpler control: the same candidate #735 on the same source owner without alias. Other plausible causes are archive construction choosing a different physical storage mode, process imports/caching, journal structure or changing timestamps. Source construction locks data, source digests, mode, storage and journal generation; fresh processes bound caching; measure every actual physical source/output byte.

Predicted scientific disposition: `ALIAS_COMPACTION_RSS_DEBT_CONFIRMED` only if exact reconstruction succeeds, source and output identity hold, and both large-alias runs exceed the paired owner-only RSS by >=64 MiB. Otherwise `FALSIFIED_OR_AMBIGUOUS` with raw measurements retained; no automatic release credit either way.

## Decision and limits
A positive result establishes quantitatively that #735's 128 MiB sparse-owner memory win is not an archive-wide RSS guarantee once owner aliases are included; return decision to #735/#620 owners. No clone of #620. A negative result retires the specific claim. Linux scientific court alone cannot confer cross-platform, performance-release or security certification. Existing stage-name custody (#726) remains red.

## Counterfactual and discovery policy
This topology perturbation was prospectively recognizable directly from #735's explicit hardlink caveat; whether its quantitative result is sufficient to change integration priority is the actual test. No Discovery Engine policy change on one experiment.
