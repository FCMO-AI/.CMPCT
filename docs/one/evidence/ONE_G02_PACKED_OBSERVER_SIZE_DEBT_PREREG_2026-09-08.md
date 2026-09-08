# ONE-G0.2 packed observer mid-size regression diagnostic — 2026-09-08

## Mission lock / referee

The exact packed-observer rehabilitation result at `49dce83b186505bff462f3971e81236e6a49bfe1` passed its preregistered 1 MiB gate, but its non-voting 256 KiB matrix retained two material speed regressions:

- `compressed_like`: 1.126363x wall / 1.126220x CPU;
- `long_runs`: 1.087943x wall / 1.087744x CPU.

The same 1 MiB rows were 0.918429x / 0.918535x and 0.907457x / 0.907628x respectively. This diagnostic asks whether the 256 KiB debt is a stable size-dependent cost or an isolated hosted/runtime context effect.

It does **not** authorize a size threshold or selector.

## Falsifiable hypothesis

If exact-prefix packing has a genuine mid-size exported-cost regime, a >1.05 regression should reproduce on at least one size adjacent to 256 KiB for the same family. If both neighboring sizes return to <=1.05 while only 256 KiB is red, the original row is better treated as runtime/context instability that requires repeat evidence rather than an algorithmic size cliff.

## Frozen matrix

Sizes:

- 128 KiB
- 192 KiB
- 256 KiB
- 384 KiB
- 512 KiB
- 768 KiB
- 1 MiB

Families:

- `structured`
- `compressed_like`
- `long_runs`
- `random`
- `near_repeats`

Use the exact deterministic generators, eager control, packed candidate, complete writer boundary and 15 paired alternating repetitions from `one_g02_packed_observer_rehabilitation.py`.

## Hard gates

Semantic/wire/root/observer equality remains mandatory. Any mismatch invalidates the diagnostic.

A timing row is called red only when **both** median wall and median CPU packed/eager exceed 1.05. It is called clear when both are <=1.05. Mixed wall/CPU cases are `AMBIGUOUS` and cannot establish a stable regression.

For each family, classify the 256 KiB debt as:

- `STABLE_ADJACENT_REGRESSION` if 256 KiB is red and at least one immediate neighbor (192 or 384 KiB) is also red;
- `ISOLATED_256K_RED` if 256 KiB is red while both immediate neighbors are clear;
- `NO_256K_RED_ON_REPEAT` if the new 256 KiB row itself is clear;
- `AMBIGUOUS` otherwise.

The overall diagnostic is descriptive. No category promotes a product selector.

## Hostile-review constraints

- Do not move the 1.05 red definition after seeing results.
- Do not average structured gains over a red low-opportunity row.
- Do not infer a production crossover from seven points.
- Do not label `compressed_like` opportunity-rich when its observer emits zero opportunities.
- Preserve the original 256 KiB result even if this repeat clears it.
- Keep writer, observer kernel, scratch capacity and packing algorithm unchanged.
- Report absolute medians and opportunity counts so a change in workload premise cannot masquerade as a timing change.

## Research consequence

A stable adjacent regression means exact-prefix packing still exports a real mid-size cost and needs a causally different implementation before general writer promotion. An isolated or non-reproduced red weakens the size-cliff hypothesis but still requires repeat/hostile evidence; it does not justify a hand-authored 256 KiB exception.
