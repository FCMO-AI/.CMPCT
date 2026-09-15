# A01 Synthetic Basis O0 preregistration

Status: **FROZEN BEFORE RESULT-BEARING EXECUTION** / Foundry O0 / research only / no release credit.

Authority: `docs/FUNDAMENTAL_RESEARCH_DOCTRINE.md`, `docs/ASSUMPTION_LEDGER.md` A01, and the exact repository head from which this freeze is committed. This experiment does not modify any v0.30 release gate, accepted product floor, frozen historical comparator, or F-01 evidence.

## Worldview delta

Current graph/resemblance mechanisms normally explain a family from one or more real members. A01 asks whether the minimum charged family description can instead use a **latent physical basis that never existed as a user object**.

If true, CMPCT gains a new relation: `family -> synthetic root + exact member residuals`, rather than only `member -> observed base(s)`.

## Capability delta

The candidate capability is to represent information shared by a family even when historical accidents make every observed member a poor root. This is distinct from ordinary pairwise resemblance, Mosaic multi-root selection, or one-stage Geometry: the explanatory root itself may be synthesized.

## Prior-art boundary

Adjacent concepts include consensus/ancestral reconstruction, median strings, dictionary learning and latent-factor models. This oracle claims none of their algorithms. Its narrow question is CMPCT-specific and accounting-first: **after charging the synthetic root itself plus every exact residual and descriptor, does allowing a non-observed root expose material family-level description-length headroom over the best observed-root control?**

## O0 gifts and charges

Gifted:
- exhaustive/offline root search;
- candidate ordering and optimization wall time;
- temporary analysis memory.

Never gifted:
- synthetic basis bytes;
- residual bytes;
- per-member reconstruction descriptors;
- exact reconstruction;
- any information required by the decoder.

Deferred product debt:
- generic discovery speed;
- admission/AOM on public real data;
- canonical framing/index;
- member/range locality;
- recovery/integrity;
- native/platform implementation;
- global reader/mechanism carrying cost;
- full release matrix.

## Frozen corpus families

The instrument generates deterministic byte families from a fixed seed and emits corpus fingerprints. It contains four classes, all unknown to the optimizer except as bytes:

1. `ancestral_sparse_edits`: members descend from an unobserved prototype with sparse independent substitutions. This is the intended positive control.
2. `biased_observed_medoid`: one observed member is deliberately near the latent prototype. This tests whether the oracle merely manufactures a root when a real root is already sufficient.
3. `two_cluster`: members come from two separated prototypes. This is a hostile control against forcing one synthetic root across multimodal data.
4. `independent_random`: no shared latent structure. This is a hostile no-headroom control.

Sizes and mutation rates are constants in the committed instrument and may not be changed after result-bearing execution. New regimes require a superseding preregistration.

## Representations compared

All candidates use the same exact residual encoding and terminal compressor so the only changed variable is root ownership.

A. **DIRECT**: independently terminal-compress every member.

B. **BEST_REAL_ROOT**: choose the cheapest observed member as root; charge terminal-compressed root plus an exact residual for every other member and all descriptors.

C. **BEST_TWO_REAL_ROOTS**: choose up to two observed roots and assign each member to its cheapest root; charge both roots, assignments, residuals and descriptors. This is the strong simpler/multi-root control.

D. **SYNTHETIC_ROOT**: synthesize one non-observed byte root using the frozen coordinate-wise candidate rule plus bounded local refinement; charge the full root, all residuals and descriptors.

E. **SYNTHETIC_OR_REAL_PORTFOLIO** is reported only as an oracle envelope and receives no independent thesis credit.

Residual encoding is exact sparse substitution: sorted changed positions encoded as positive deltas with unsigned varints, followed by replacement bytes; a raw-literal residual fallback is always available. Candidate cost includes an explicit tag, member length, root identity/assignment where needed, and terminal-compressed payload bytes. The instrument must round-trip every member byte-for-byte before a row is accepted.

## Primary falsifiable hypothesis

On `ancestral_sparse_edits`, `SYNTHETIC_ROOT` must beat `BEST_REAL_ROOT` by at least **1% of complete family bytes AND 4 KiB absolute**, and must not lose to `BEST_TWO_REAL_ROOTS` by more than 1%.

The thesis is **O0_HEADROOM** only if that condition holds and both hostile families (`two_cluster`, `independent_random`) correctly prefer a simpler control or show <1% synthetic-root gain after full charge.

## Kill / narrow rules

- If synthetic root cannot materially beat `BEST_REAL_ROOT` on the positive control after root charge, return `NO_ACTIONABLE_HEADROOM` for this oracle family.
- If `BEST_TWO_REAL_ROOTS` erases the synthetic advantage, narrow A01: the observed gain is better explained by multi-root ownership than latent-root invention.
- If synthetic root materially wins on `independent_random`, treat it as an accounting/instrument defect until disproven; no positive interpretation is allowed.
- If `two_cluster` favors two real roots, that is an expected hostile result, not a failure of accounting. If one synthetic root materially beats two real roots there, preserve the observation but do not broaden the thesis without a new causal explanation.
- Any reconstruction failure invalidates the run.

## Decision law

The instrument emits exactly one of:
- `O0_HEADROOM`;
- `MULTIROOT_EXPLAINS_GAIN`;
- `NO_ACTIONABLE_HEADROOM`;
- `INSTRUMENT_INVALID`.

No threshold, family label, comparator, candidate rule or interpretation may be moved after observing result-bearing output. The first accepted result must bind source SHA, corpus fingerprint, raw JSON and artifact digest.