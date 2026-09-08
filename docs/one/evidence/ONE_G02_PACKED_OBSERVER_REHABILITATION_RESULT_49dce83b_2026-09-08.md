# ONE-G0.2 packed observer rehabilitation — exact result at `49dce83b` — 2026-09-08

Status: **`ADVANCE_PACKED_OBSERVER_REHABILITATION` within the frozen 1 MiB writer-internal claim boundary.**

## Exact evidence authority

- source branch: `research/cmpct1`
- exact source SHA: `49dce83b186505bff462f3971e81236e6a49bfe1`
- workflow run: `34219617441`
- job: `102039393228`
- artifact id: `10053294203`
- artifact name: `one-g02-packed-observer-rehabilitation-49dce83b186505bff462f3971e81236e6a49bfe1`
- artifact digest: `sha256:02219d50243a9c48c260edc793057a22ca1abcd29dcc7cf4a812256e95dda3fb`
- exact SHA binding: passed
- packed semantic proof: passed
- frozen rehabilitation falsifier: passed
- evidence upload: passed

## Frozen decision

- `semantic_gates_pass = true`
- `structured_gain_retained_1m = true`
- `all_rows_no_regression_1m = true`
- `decision = ADVANCE_PACKED_OBSERVER_REHABILITATION`

Only 1 MiB rows voted, exactly as preregistered.

## 1 MiB matrix

| family | packed/eager wall | packed/eager CPU | useful native output | packed retained | scratch capacity |
| --- | ---: | ---: | ---: | ---: | ---: |
| structured | **0.348000x** | **0.348035x** | 294,912 B | 294,912 B | 3,539,040 B |
| compressed_like | **0.918429x** | **0.918535x** | 0 B | 0 B | 3,539,040 B |
| long_runs | **0.907457x** | **0.907628x** | 5,280 B | 5,280 B | 3,539,040 B |
| random | **0.995587x** | **0.995606x** | 0 B | 0 B | 3,539,040 B |
| near_repeats | **1.004055x** | **1.004165x** | 24 B | 24 B | 3,539,040 B |

The structured family contained 1 run + 12,287 exact-reuse opportunities. Eager writer median wall was 22.323 ms; packed writer median wall was 7.768 ms. The packed path therefore retained a ~65.2% whole-writer elapsed reduction on this opportunity-heavy row while carrying only the 294,912 useful native record bytes after observation instead of the full 3,539,040-byte output arena.

The two rows that had blocked the prior arena-retaining compact candidate at 1 MiB were rehabilitated:

- `compressed_like`: 1.083153x -> 0.918429x wall;
- `random`: 1.069368x -> 0.995587x wall.

`long_runs` moved from 1.038299x to 0.907457x. `near_repeats` remained essentially parity at 1.004055x.

This is strong causal evidence that the *lifetime/export shape* of the native output arena mattered to the previous compact failure; it is not merely evidence that avoiding Python object construction helps structured data.

## Mid-size regression debt remains active

The pass is intentionally not a universal writer promotion. Non-voting 256 KiB rows contain material reds:

| family | packed/eager wall | packed/eager CPU |
| --- | ---: | ---: |
| compressed_like | **1.126363x** | **1.126220x** |
| long_runs | **1.087943x** | **1.087744x** |
| random | 1.002788x | 1.001984x |
| near_repeats | 1.011163x | 1.011102x |
| structured | 0.384833x | 0.384765x |

Do not create a 1 MiB production threshold to hide these rows. The experiment was designed to decide whether the 1 MiB `OWNER_NATIVE_OBSERVE` path was worth continuing; it did that. General writer promotion requires the 256 KiB debt to be explained and closed or bounded by a causally justified selector whose own cost is charged.

## Representation/access truth

All rows preserved identical relation classification, Program, canonical wire and decoded roots. At 1 MiB the current temporal matrix still emitted 2,097,273 canonical bytes with 2,097,152 Surprise bytes and reader work 6,291,456 B. This experiment changed writer implementation economics only.

No stored-byte, reader-complexity, selective-access, durability, recovery, portability, v0.29 or deferred-v0.30 authority is granted.

## Memory truth

Exact-size packing reduces retained native observer output state after the scan, but both arms still pay the same worst-case scratch capacity during the scan. The result is therefore **not** a peak-RSS claim. Fresh-process RSS measurement is the immediate promotion gate under `ONE_G02_PACKED_OBSERVER_RSS_PREREG_2026-09-08.md`.

## Mechanism consequence

The strongest current interpretation is:

`native observe -> used-prefix compact handoff -> release oversized scratch -> downstream writer`

is economically superior at the 1 MiB stage-owner scale to either eager Python opportunity materialization or carrying the full native scratch arena forward.

The next deeper architecture should make downstream admission/segmentation actually consume compact/native observation state instead of charging observation as dead writer work. Before that, fresh-process RSS and the 256 KiB regression debt remain mandatory.
