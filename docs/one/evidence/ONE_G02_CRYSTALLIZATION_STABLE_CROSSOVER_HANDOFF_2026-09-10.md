# ONE-G0.2 Crystallization stable-crossover handoff — 2026-09-10

## Mission Lock / Referee

Question: does the preregistered complete-wire Crystallization geometry show a stable economic crossover, or merely one or more isolated non-regressing points?

The preregistered decision in `ONE_G02_CRYSTALLIZATION_WIRE_ECONOMICS_GEOMETRY_PREREG_2026-09-10.md` is not changed here. H2 remains the registered existence test. This handoff adds a stricter *descriptive* statistic so an isolated green point cannot later be narrated as a stable product threshold.

Falsifiable hypothesis: for each measured family, there exists a first measured length after which every larger measured point remains non-regressing on complete authenticated bytes. Disproof: any larger measured point regresses after the apparent crossover; if the largest measured point regresses, no stable measured tail exists.

## Builder

Updated `benchmarks/one/one_g02_crystallization_wire_economics_geometry.py` to retain, per family:

- the preregistered `first_non_regressing_length`;
- `stable_non_regressing_length`, the first measured length for which every measured larger length is also non-regressing;
- `post_first_crossover_regression_lengths`, exposing regressions after the first green point;
- `stable_non_regressing_tail_all_families`.

The schema is now `cmpct-one-g02-crystallization-wire-economics-geometry-v2`. The claim boundary explicitly says these crossover fields are descriptive evidence, not a product threshold and not a Genesis result.

Updated the hostile tests to recompute the stable-tail summary independently from raw rows. Added synthetic falsifiers showing that a green point followed by a regression cannot be called the stable crossover, and that a regression at the largest measured point leaves the stable crossover unavailable.

Updated the hosted workflow to retain and print the new stable-tail evidence.

## Hostile review

The registered ADVANCE/HOLD/RETIRE decision remains intentionally unchanged. Rewriting H2 after observing geometry would be post-registration goalpost movement. Therefore a future run may satisfy the preregistered `ADVANCE_CRYSTALLIZATION_ECONOMICS_MODEL` while still reporting that the stricter descriptive stable tail is absent or occurs later. That would be a real research warning, not grounds to reinterpret the registered result.

If unstable crossover geometry appears, the next action should be a separately preregistered economic-admission experiment, not threshold extraction from this transfer matrix.

## Evidence truth at handoff

Exact source carrying benchmark + hostile tests + workflow hardening: `7133713e5a3718bb39842734302717d18c4639cd`.

Hosted workflow run: `34509161237`, `CMPCT1 ONE-G0.2 Crystallization wire economics geometry`.

At handoff the run was `queued` with no conclusion. No size crossover, speed, RSS, or product claim is adjudicated until exact-source hosted evidence completes.

Genesis 15-workload inputs were not executed. Genesis comparison, scoring, and winner selection remain false.

Frozen comparators remain:

- v0.29: `02b8b27cb2d97af7c6e0797984a898e8fa8a8e5d`
- v0.30: `f4b158a55a08b9b18b50e4e4abe4b9251048c772`

No ordinary v0.30 mechanism work was performed.
