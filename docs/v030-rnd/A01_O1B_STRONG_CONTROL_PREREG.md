# A01 O1b strong-control causal-transfer preregistration

Status: **FROZEN BEFORE RESULT-BEARING EXECUTION** / supersedes O1a adjudicator only / no product or release credit.

Parent truth: O0 `O0_HEADROOM` is accepted. O1a raw output is preserved but its causal adjudicator is invalid because it labeled opportunity only against `BEST_REAL_ROOT` while separately treating multi-root ownership as the correct negative for multimodal families.

## Single repair allowed by this freeze

O1b changes **only the outcome label/adjudicator and the unseen corpus**. It does not tune the predictor.

The content-derived predictor is carried forward unchanged:

- sample offset: 31;
- sample stride: 257;
- `consensus_advantage = (best_member_disagreement - mode_disagreement) / best_member_disagreement`;
- `PREDICT_LATENT` iff consensus advantage >= **0.08**.

No O1a family or seed is reused as unseen validation.

## Corrected causal target

For each family define:

`OBSERVED_PORTFOLIO = min(BEST_REAL_ROOT, BEST_TWO_REAL_ROOTS)`.

`ACTUAL_LATENT_MATERIAL = true` only if SYNTHETIC_ROOT beats `OBSERVED_PORTFOLIO` by **both >=1% and >=4 KiB** complete charged bytes.

This fixes the evaluator composition error without changing the mechanism, predictor threshold or byte materiality rule. A multimodal family where two observed roots beat one synthetic root is now correctly a negative even if synthetic beats the best single root.

## Fresh frozen corpus

Deterministic 128 KiB x 8-member families from a new seed and independently written generators:

1. `private_block_bursts` — latent center + member-private burst substitutions; expected latent-positive.
2. `private_sparse_scatter` — latent center + member-private sparse substitutions; expected latent-positive.
3. `shared_history_plus_private` — one shared historical mutation layer plus private edits; ambiguous but content-derived predictor must decide.
4. `three_cluster` — three separated latent centers; expected observed/multi-root negative (two-root may still be imperfect, so any synthetic win is preserved rather than assumed impossible).
5. `near_observed_center` — one observed member close to center; expected negative unless full charging still leaves material latent gain.
6. `independent_random` — hostile no-family negative.

Family labels are not passed to predictor or cost functions.

## Controls and accounting

Use the accepted O0 exact accounting code unchanged for DIRECT, BEST_REAL_ROOT, BEST_TWO_REAL_ROOTS, SYNTHETIC_ROOT, residual encoding, terminal compression and exact reconstruction.

All decoder-visible bytes remain charged. Search/discovery wall time for constructing the synthetic root is still O0-gifted; the predictor itself is bounded pre-result work.

## Frozen decision law

Return:

- `CAUSAL_PREDICTOR_SEED` iff every material latent-positive family is predicted LATENT, every non-material family is predicted OBSERVED/MULTIMODAL except at most one false positive, **independent random is non-material**, and all roundtrips pass;
- `PREDICTOR_FALSE_NEGATIVE` if any material latent-positive family is not predicted LATENT;
- `PREDICTOR_FALSE_POSITIVE` if more than one non-material family is predicted LATENT **or if `independent_random` itself becomes material under the synthetic representation**;
- `INSTRUMENT_INVALID` on reconstruction/accounting failure.

No positive family-specific override exists. The explicit hostile-random branch above was added by pre-execution adversarial review while the first workflow job was still queued and had executed zero steps; no result-bearing output existed. It closes an otherwise uncovered `CAUSAL_PREDICTOR_SEED` path without changing any predictor or corpus parameter.

## Disproof / quality-ratchet

Failure is preserved. Do not change 0.08, sample geometry, materiality, family parameters or labels after result.

Even a pass establishes only a same-length causal predictor seed. Full O1 remains blocked on variable-length/alignment perturbation, canonical Mosaic/resemblance controls, charged shared-context control, AOM/discovery economics and public/independent real families.