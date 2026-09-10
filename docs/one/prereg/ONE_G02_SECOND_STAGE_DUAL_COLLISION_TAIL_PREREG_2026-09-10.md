# ONE-G0.2 second-stage dual-collision tail supplement — preregistration

Status: preregistered before any result from this supplement.

Branch authority: `research/cmpct1`.
Experimental version: `ONE-G0.2`.
Genesis separation: this supplement must not import, generate, read, encode, score, or otherwise touch any of the 15 Genesis workloads.

## Mission lock / referee

The existing second-stage relation-kernel A/B now distinguishes first-vs-last **stage-2** collisions and an early dual collision. The remaining hostile geometry is a candidate that fools both sparse stages and fails only near the end of the exact proof. That case measures the unavoidable survivor tax of the second stage rather than its easy rejection benefit.

This supplement does not alter the already-preregistered v3 kernel decision. It is a separate hostile diagnostic whose result may veto later writer integration if survivor overhead is materially worse than expected.

## Falsifiable hypothesis

For exact ADD8(+37) and XOR(0xA5) candidates whose single poison byte is the **last byte not observed by either sparse stage**, the second-stage candidate remains semantically identical to the baseline exact proof and its fixed sparse overhead is bounded enough that it does not materially worsen the late-failure path.

The expected cost model is deliberately unfavorable to the candidate:

- baseline modeled remaining bytes: `2 * N`;
- candidate modeled remaining bytes: `2 * N + 2 * second_stage_position_count`;
- both arms must reject the false relation;
- the exact proof remains the only positive authority.

No size saving is claimed. This experiment measures only false-pattern rejection cost after primary nomination/economic admission.

## Frozen matrix

Relations:
- `add8` with delta `+37`;
- `xor` with mask `0xA5`.

Lengths:
- 4,096 B;
- 16,384 B;
- 65,536 B;
- 262,144 B.

Kind:
- `dual_collision_late`: create an otherwise exact relation, then flip the **last index not contained in primary sampling or second-stage midpoint sampling**.

Input generation must be deterministic and independent of Genesis.

## Timing boundary

Primary sample positions and the nominated ADD8/XOR constant are computed before timing and shared by both arms. The timed boundary begins after nomination and the primary sampler have already passed.

Each row:
- warms both arms;
- uses 101 repetitions;
- alternates baseline/candidate order by repetition;
- records median process CPU ns and wall ns;
- retains modeled remaining bytes separately from elapsed timing.

## Gates

H1 — correctness and hostile construction:
- every row passes the existing primary sampler;
- every poison index is outside both sparse stages;
- baseline and candidate both return false;
- no sparse stage may become positive authority.

H2 — per-row survivor debt:
- for every row, candidate CPU ratio <= 1.20;
- for every row, candidate wall ratio <= 1.20.

H3 — broad survivor debt:
- median candidate/baseline CPU ratio across all rows <= 1.05;
- median candidate/baseline wall ratio across all rows <= 1.05.

H4 — accounting:
- baseline modeled remaining bytes equal `2*N`;
- candidate modeled remaining bytes equal baseline plus exactly `2*second_stage_position_count`;
- modeled candidate bytes are therefore expected to be slightly worse, and this must remain visible rather than narrated away.

Decision:
- H1 failure => `RETIRE_SECOND_STAGE_DUAL_COLLISION_TAIL`;
- H1 passes but H2/H3/H4 fails => `HOLD_SECOND_STAGE_DUAL_COLLISION_TAIL`;
- all pass => `ADVANCE_SECOND_STAGE_DUAL_COLLISION_TAIL_SAFETY_ONLY`.

An ADVANCE means only that the unavoidable late-survivor tax is bounded on this transfer matrix. It does not enable the second stage in the writer, does not modify the v3 preregistration, and grants no Genesis/product claim.

## Hostile reviewer

A second sparse filter can never eliminate an adversary deliberately placed outside both sparse sets. The correct question is therefore not whether this row wins, but whether the fixed sparse work stays a small bounded tax before the mandatory exact proof. If the Python implementation exceeds the frozen survivor envelope, preserve the negative and prefer reuse of already-paid fused/native observation state rather than tuning probe counts post hoc.
