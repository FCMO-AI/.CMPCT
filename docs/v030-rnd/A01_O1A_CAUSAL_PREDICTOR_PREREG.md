# A01 O1a latent-root causal-predictor preregistration

Status: **FROZEN BEFORE RESULT-BEARING EXECUTION** / Foundry causal-transfer instrument / no product or release credit.

Parent evidence: `docs/v030-rnd/A01_SYNTHETIC_BASIS_O0_RESULT.md` (`O0_HEADROOM`). Prior-negative constraints: `docs/v030-rnd/A01_PRIOR_NEGATIVE_RECONCILIATION.md` and `docs/v030-rnd/A01_EXTERNAL_PRIOR_ART_BOUNDARY.md`.

## Question

The O0 result proves that a charged non-observed root can beat observed-root ownership on a friendly sparse-substitution family. It does not explain **when** this should happen from pre-result content.

O1a tests one narrow causal predictor before attempting broader variable-length or real-data admission:

> When same-length family members contain dispersed independent disagreement around a common latent center, a sampled coordinate-consensus deficit should predict whether a synthetic coordinate-wise medoid can beat the best observed root. Correlated/clustered disagreement should weaken or reverse that advantage.

This is not yet full O1 product admission. It is a causal-transfer gate whose purpose is to prevent the project from jumping directly from friendly O0 bytes to expensive real-data machinery without a predictive account.

## Frozen predictor

For deterministic sample coordinates chosen from content-independent stride/offset constants, compute:

- `mode_disagreement`: total sampled member bytes that differ from the coordinate-wise mode;
- for each observed member, `member_disagreement`: total sampled disagreement between that member and all family members;
- `best_member_disagreement`: minimum of those values;
- `consensus_advantage = (best_member_disagreement - mode_disagreement) / max(1, best_member_disagreement)`.

No compression candidate is built to compute this statistic.

Frozen prediction:

- `PREDICT_LATENT` iff `consensus_advantage >= 0.08`;
- otherwise `PREDICT_OBSERVED_OR_MULTIMODAL`.

The 0.08 threshold is frozen before result execution and may not move afterward.

## Frozen transfer families

All are deterministic 128 KiB x 8-member families generated independently from the O0 seed and family code.

1. `independent_bursts`: unobserved prototype; each member receives several disjoint local substitution bursts. Expected latent-positive.
2. `independent_scatter`: unobserved prototype; sparse substitutions drawn from a different RNG/distribution than O0. Expected latent-positive.
3. `shared_correlated_patch`: all members share one large historical patch plus smaller private edits; expected weak/ambiguous latent advantage because an observed member already carries the shared patch.
4. `two_cluster`: two distinct latent centers; expected observed/multi-root.
5. `near_medoid`: one observed member is very close to the latent center; expected weak latent-positive or observed-root.
6. `independent_random`: hostile no-family control; expected no profitable latent representation.

Family labels are interpretation only and are never passed to the predictor or cost functions.

## Exact representation controls

Use the same charged root/residual/descriptor/terminal accounting as accepted O0 for:

- DIRECT;
- BEST_REAL_ROOT;
- BEST_TWO_REAL_ROOTS;
- SYNTHETIC_ROOT.

Every synthetic row must round-trip exactly. The instrument also reports whether synthetic root actually beats best real by >=1% and >=4 KiB (`ACTUAL_LATENT_MATERIAL`).

## Primary decision law

Across the six frozen families:

- every `ACTUAL_LATENT_MATERIAL` family must be predicted `PREDICT_LATENT`;
- `independent_random` must not be `ACTUAL_LATENT_MATERIAL`;
- `two_cluster` must prefer BEST_TWO_REAL_ROOTS over SYNTHETIC_ROOT or else be treated as a causal surprise;
- false-positive rate for `PREDICT_LATENT` among non-material families must be <= 1/3.

Return exactly one of:

- `CAUSAL_PREDICTOR_SEED` — all conditions pass;
- `PREDICTOR_FALSE_NEGATIVE` — any material latent family is missed;
- `PREDICTOR_FALSE_POSITIVE` — false-positive law fails;
- `MULTIMODAL_CAUSAL_SURPRISE` — one synthetic root materially beats two-root control on frozen two-cluster family;
- `INSTRUMENT_INVALID` — any reconstruction/accounting invariant fails.

## Disproof / quality ratchet

A failed predictor is not rescued by changing threshold, sample stride, family labels, mutation rates, or synthesis rule. Preserve the negative and either derive a different pre-result observable in a superseding freeze or narrow A01.

Even `CAUSAL_PREDICTOR_SEED` is not O1 completion. The next quality-ratchet would require generator-distinct variable-length/alignment perturbation, strongest canonical Mosaic/resemblance controls, charged shared-context control, AOM, bounded discovery cost and public/independent real families.