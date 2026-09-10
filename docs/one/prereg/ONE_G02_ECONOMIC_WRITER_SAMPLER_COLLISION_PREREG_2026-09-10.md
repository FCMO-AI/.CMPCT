# ONE-G0.2 economic writer sampler-collision preregistration — 2026-09-10

## Mission lock

Test a hostile failure mode in the current ONE-G0.2 general Law writer without touching Genesis inputs: a false ADD8/XOR relation that is deliberately constructed to agree at every frozen discovery sample position while disagreeing at an unsampled byte.

This is a selection-safety experiment, not a density benchmark and not a Genesis evaluation.

## Falsifiable hypothesis

For each frozen hostile transfer row, the sampled nomination may pass, but the bounded exact proof must reject the false relation. With economic admission enabled, the emitted reader-visible target must remain Surprise, reconstruction must be exact, the wire must be deterministic, and complete persisted bytes must not exceed the ungated writer on the same input.

For candidate lengths already economically admissible under the frozen marginal-cost model, economic admission is not expected to reduce exact-proof work. The point of those rows is to prove that cheap sampling cannot bypass exact proof. Any claim of CPU improvement from these rows is prohibited.

## Frozen hostile matrix

Relations:
- ADD8(+37) near-miss
- XOR(0xA5) near-miss

Lengths:
- 17 bytes
- 32 bytes
- 256 bytes
- 4096 bytes

For each row:
1. Generate a deterministic high-entropy source that remains Surprise.
2. Generate the exact relation over the full target.
3. Compute the frozen 16-point sample positions independently from the writer implementation.
4. Select the first byte position not in that sample set.
5. Corrupt exactly that unsampled target byte.
6. Assert that every sampled byte still satisfies the nominated relation and the poison byte does not.

The experiment must additionally assert that the writer's `_sample_positions()` output equals the independently re-derived frozen positions for every row. A sampler-definition drift is HOLD, not permission to silently construct a different attack.

## Gates

H1 — sampler collision is real:
- all frozen sample positions satisfy the intended ADD8/XOR relation;
- exactly one chosen unsampled poison byte violates it;
- writer sample positions equal the independent frozen oracle.

H2 — false-pattern safety:
- economic writer target structure is Surprise for every row;
- ungated writer target structure is also Surprise;
- no false ADD8/XOR Law survives exact proof.

H3 — semantic and representation safety:
- both archives reconstruct the exact source tree independently;
- economic wire is deterministic across repeated builds;
- reader-visible ops remain within the existing generic ONE ontology;
- economic complete persisted bytes are <= ungated complete persisted bytes.

H4 — proof-accounting causality:
- because all frozen lengths are >= 17 and ADD8/XOR K=11, the economic model predicts admission;
- exact-proof bytes must therefore be non-zero for the hostile nomination;
- economic and ungated exact-proof accounting must agree row-for-row. This experiment must not manufacture a proof-work win where the model says none exists.

## Decisions

- Any H1 or H3 failure: `RETIRE_OR_REPAIR_SAMPLER_COLLISION_SAFETY`.
- H1/H3 pass but any false relation survives: `HOLD_SAMPLER_COLLISION_SAFETY`.
- All H1–H4 pass: `ADVANCE_SAMPLER_COLLISION_SAFETY_ONLY`.

`ADVANCE_SAMPLER_COLLISION_SAFETY_ONLY` means only that the current sampled nomination + exact-proof seam rejects this specific adversarial family. It does not promote the general candidate boundary, set a product threshold, prove broad false-positive rates, or score Genesis.

## Forbidden reinterpretations

Do not:
- use Genesis 15-workload inputs;
- weaken exactness, integrity, recovery, portability or selective-read requirements;
- count a failed exact proof as a compression win;
- claim CPU/RSS benefit from these rows;
- alter SAMPLE_POINTS, the marginal-cost constants, or relation encoding after seeing this result;
- introduce a fallback codec or reader-visible special opcode.

## Genesis flags

Every result artifact must state:
- `genesis_inputs_executed = false`
- `genesis_comparison_executed = false`
- `genesis_scoring_executed = false`
- `genesis_winner_selected = false`
