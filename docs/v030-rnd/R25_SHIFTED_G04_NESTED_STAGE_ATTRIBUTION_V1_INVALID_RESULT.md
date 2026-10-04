# r25 Shifted G0-G4 nested-stage attribution v1 — invalid result

Status: **TERMINAL / INVALID UNDER FROZEN V1 / ZERO SCIENTIFIC, PRODUCT OR RELEASE CREDIT**

Frozen preregistration: `R25_SHIFTED_G04_NESTED_STAGE_ATTRIBUTION_PREREG.md`.

## Authority

- source: `8056e513a966e834db95d492e69ecce39a9cb37a`
- workflow run: `33792738607`
- substantive job: `100774030266`
- artifact: `9908269047`
- artifact ZIP digest: `sha256:6c6ba851e26b86580d2a79266d932a5017ab41bbe758c130918c980eb974e460`
- decision emitted by the immutable v1 instrument: **`INVALID`**

## Why v1 is invalid

All three repetitions failed only the two frozen `expected_bytes` checks. Every strong-verification, common-tree, positive-time, single-stage-call and finite-stage check passed.

Observed identities were stable in all three repetitions:

- v0.28: **1,761,588 B**, SHA-256 `b483d7e1dda93b86c874eab4bf20649eedb709c42a5a8be428a8d7449786a851`;
- attempt-5: **1,723,056 B**, SHA-256 `791baff9fe09b18588f26bdc47ff1b13f160ca095dff2e47b5523241e85c91e9`;
- verified tree: `d9106dcdc8f965d45236c241d6c45f773e10b84ac204acc3c3521d889cd3a8fd`.

The v1 freeze expected 1,761,927 B and 1,723,391 B, inherited from an earlier generated Shifted filesystem instance. Those constants may not be edited after this result-bearing execution.

## Descriptive signal with zero v1 decision credit

The invalid run nevertheless retained useful non-decisive diagnostics:

- v0.28 graph / child median: **0.9518345164x**;
- v0.28 legacy / child median: **0.0483716474x**;
- attempt-5 Placement / child median: **0.9995684242x**;
- attempt-5 residual / child median: **0.0004056181x**.

These ratios would satisfy the v1 graph-dominance rule if the experiment were valid, but they receive **no v1 scientific decision credit**.

## Causal custody

`R25_SHIFTED_SERIALIZED_METADATA_CAUSAL_V2_RESULT.md` independently established `SHIFTED_MTIME_SERIALIZED_METADATA_CAUSAL_SUPPORTED`: for this deterministic Shifted content generator, nanosecond mtime is the only observed cross-generation varying Builder-consumed serialized filesystem fact, and normalizing only mtime to `1767225600000000000` ns yields a stable serialized projection and genuine-r24 identity.

Therefore this invalid result is not repaired by changing v1. It is superseded by a new v2 freeze that applies exactly that already-supported fixture normalization before either child is measured, while preserving the stage boundaries, repetitions, decision bands and zero-release-credit law.

## Decision

**`SUPERSEDE_INVALID_FIXTURE_IDENTITY`**.

No product behavior, archive grammar, release threshold, competitor, locality, recovery, integrity or runtime gate changed.
