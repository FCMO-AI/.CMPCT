# R25 G0-G4 ML native in-process FFI v1 — invalid instrument result

Status: **CANDIDATE_INVALID — zero scientific decision credit**

## Immutable execution receipt

- workflow: `.github/workflows/v030-g04-ml-native-ffi-reader.yml`
- run: `33755189758`
- substantive job: `100647820757`
- source commit: `9fe545ef0b4887be5ad3e98d5d3d6ec873304115`
- target: `neutral_hostile_v1/09_ml_artifacts`
- intended rounds: 5 alternating Python/native in-process FFI measurements
- intended scientific bands: at least 20% median verify improvement **and** at least 20% median extract improvement
- release credit: none

The job reached deterministic dependency setup but failed before candidate construction and before any paired
measurement. `git apply --check benchmarks/patches/v030_g04_shared_record_cache_candidate.patch` terminated with:

`error: patch with only garbage at line 5`

The committed v1 candidate transport used bare `@@` hunk markers and is not a valid unified diff. Therefore no
candidate source existed, no Rust FFI library containing the candidate was built, and no verify/extract timing
sample can be interpreted.

## Causal interpretation

This is a D0 measurement/instrument failure, not evidence for or against shared physical-record reuse. The
scientific worldview remains untested: repeated canonical ML full-archive verification/extraction may or may not
recover material wall time when already-decoded G0-G4 physical records are reused inside one operation.

A second custody defect was found in the v1 workflow: preserved-result concurrency was grouped by `github.ref`.
`tools/check_ci_topology.py` requires preserved deep/release receipts to include the exact evidence SHA in the
pending/running concurrency key. That topology flaw did not cause the malformed-patch failure, but it prevents v1
from being a valid long-lived exact-receipt instrument.

## Preservation and reopening predicate

The v1 workflow, malformed patch, run, and this result remain preserved. They must not be edited to manufacture a
retroactive result.

A superseding instrument may rerun the same scientific question only if it changes the mechanical transport needed
to construct the intended temporary candidate, binds preserved execution to exact `github.sha`, and leaves all
scientific variables unchanged: corpus, Python comparator, five-round alternating A/B, timed FFI boundary, archive
bytes/grammar/selector, integrity and corruption rejection, caller output-budget preflight, 8x locality,
8 MiB decode unit, memory law, and the 20% verify + 20% extract decision bands.
