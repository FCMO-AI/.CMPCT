# F-01 causal result

Status: **accepted Foundry causal evidence / research only / no release credit**.

## Authority

Frozen preregistration: `docs/v030-rnd/F01_CAUSAL_ABLATION_PREREG.md`.

Accepted receipt:

- source commit: `2876698d311b13f296a6f11f23d89eaab51cd09c`;
- workflow run: `33468986162`;
- artifact digest: `sha256:e910165ad51b2501f44a8531dab39ccbd697a1a1b150f9d958fb03290d33f2b6`;
- schema: `cmpct-v030-foundry-f01-causal-v1`;
- O0.1 witness seed: `c3ef298bcc3fb7f95a65245c9341f112581aa175`;
- O0.1 corpus fingerprint: `6b6438aff98e7a9e69ee834fe3f2135cc03acde0babac42100c544519e56c574`;
- decision: **`CAUSAL_SEED`**;
- conflicts: **none**.

## Causal measurements

### `discovery_mixed_lane_records`

Accepted: 1538 B vs 2090 B one-stage manual control.

- remove SPLIT -> 2090 B, exact manual control restored, **+552 B**;
- remove LANE -> 15,125 B, **+13,587 B**;
- remove DELIM -> 1551 B via `SPLIT(LANE[8]+LANE[16])`, **+13 B**.

### `discovery_mixed_lane_widths`

Accepted: 2525 B vs 3086 B one-stage manual control.

- remove SPLIT -> 3086 B, exact manual control restored, **+561 B**;
- remove LANE -> 29,842 B, **+27,317 B**.

### `transfer_postfreeze_mixed_shifted`

Accepted: 1416 B vs 1843 B one-stage manual control.

- remove SPLIT -> 1843 B, exact manual control restored, **+427 B**;
- remove LANE -> 16,541 B, **+15,125 B**;
- remove DELIM -> 1432 B via `SPLIT(LANE[8]+LANE[16])`, **+16 B**.

Every ablation reconstructed exactly.

## Scoped operator liability

Removing LANE widths 2 or 4 changed neither optimum bytes nor optimum motif on any accepted O0.1 discovery, hostile or transfer case.

Therefore, under this exact frozen regime only:

- LANE[2]: **scoped search liability**;
- LANE[4]: **scoped search liability**;
- LANE[8]: causally active;
- LANE[16]: causally active.

This does not authorize global/product deletion. Reopening widths 2/4 requires new structural evidence that they affect a materially relevant exact optimum.

## Interpretation

The O0.1 composition wins are not an accounting artifact. SPLIT is necessary for the measured composition headroom, LANE is strongly necessary, and DELIM has a small but exact unique contribution on its two witnesses.

The result advances F-01 from ORACLE to **CAUSAL_SEED**.

It does not prove the whole research compiler should become a production grammar. The most important surviving alternative is concept compression: a smaller mixed-structure segmentation primitive may capture the useful capability with much less reader/search carrying cost.

## Oracle Gift Ledger

Gifted: causal-ablation search wall time.

Never gifted: program/control bytes, terminal bytes, exact reconstruction, accepted witness bytes.

Still deferred: generic admission economics, canonical framing/index, whole-archive locality, recovery/integrity, hostile parser/fuzz, native/platform, product runtime, AOM and global mechanism carrying cost.

## Next decision

**Advance to structural transfer + AOM/carrying-cost measurement without adding operators.**

The next freeze must vary causal structure rather than merely random seeds and must explicitly measure whether scoped pruning of LANE[2]/LANE[4] preserves optima while reducing global search nominations/auditions.
