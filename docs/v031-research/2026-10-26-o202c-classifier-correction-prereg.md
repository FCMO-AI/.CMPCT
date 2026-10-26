# O202c preregistered classifier correction — preserve decision boundary, repair erroneous reason filter (2026-10-26)

## Frozen evidence being preserved
Source-bound real hosted run [40389675515](https://github.com/FCMO-AI/.CMPCT/actions/runs/40389675515) executed O202b HEAD `d9a306fbf7269c84998915d4d1bfc2256b51a57b` successfully. The machine classifier emitted `UNEXPECTED_OR_CONTRADICTORY_DIFFERENTIAL_REQUIRES_REVIEW`, but the raw matrix shows **all four preregistered behavior-level predictions succeeded**: normalized length-4 valid control passes Python, strict preflight, native open and `CD`; normalized lengths 1/2 reproduce ordinary Python `0000` wrong late range and both strict preflight/native reject; length-5 likewise strict preflight/native reject. All original O198 wires are rejected by strict validators because their root index lacks `v`.

## Specific classifier error (not evidence failure)
The research-only predicate `normalized_preflight_geometry_rejection` tests for substring `length mismatch` **on all malformed cases**, but the existing preflight validator checks logical extent bounds before stored-byte equality: it emits `file 'sparse.bin' sparse extent 0 overlaps or exceeds file` for length 5 (> declared file size 4). Both are `ValidationError` and both reject malformed geometry. The O202b prereg expected rejection, not one exact error string. Calling this `unexpected` was therefore a false classifier negative. This explanation is independently checkable against the original untouched job log and repository validator source.

## Permitted minimal correction
Change **only the research classifier** to require typed `ValidationError` plus:
- lengths **1/2**: message contains `length mismatch`;
- length **5**: message contains `overlaps or exceeds file`.

Keep the original 4 archives, schema-normalization transformer, all native/Python calls, hashes, source checks, positive control, other decision criteria, owned code and workflow gates unchanged. Keep full original run and its incorrect-but-honest raw classification as historical evidence. Rerun on exact new HEAD to prove equivalence.

## Falsifier and completion
If a new run changes any native status, ordinary Python bytes, original missing-version negative, positive control, or strict rejection, do **not** treat the classifier fix as proof; report drift and investigate. Only if all raw results reproduce and the typed reasons are exactly scoped does the new classifier earn `EXISTING_STRICT_VALIDATORS_REJECT_GEOMETRY_ORDINARY_READER_GAP` on that HEAD. This corrects evidence-enablement, not product. No change to release, format, security threshold, comparator or evaluator used by products.

**O202a and O202b preregistrations and the prior raw run remain append-only; this supplement only corrects an over-specific research result label.**
