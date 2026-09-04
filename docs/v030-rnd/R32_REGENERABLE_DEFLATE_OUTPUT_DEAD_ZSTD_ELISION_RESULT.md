# R32 — Regenerable-Deflate Output-Dead Ordinary-Zstd Elision Result

Status: **TERMINAL — OUTPUT_DEAD_CONFIRMED_RUNTIME_DEBT_REMAINS**

Frozen preregistration: `docs/v030-rnd/R32_REGENERABLE_DEFLATE_OUTPUT_DEAD_ZSTD_ELISION_PREREG.md`.

Execution authority:

- workflow run: `33836846159`
- result-bearing checkout head: `0b1f3cd653f0e2489964b93cdd19fa8324adda2e`
- authority product substrate: `b0e7aeab92c994b4a25c5040fe3fb9f5e208b01a`
- release fingerprint at execution: `bfec299953307b9a2c32dbb9d6584279d1d091f2cbd56a403ffba9c79dff8379`
- immutable artifact: `9923664295`
- artifact ZIP SHA-256: `c7434e916ff1523b358aeb7c78e9f7e3c249fda4c4856b92f489a42973dd78fa`
- exact evidence-head binding: **PASS**
- frozen substrate binding: **PASS**
- completeness / decision-law guard: **PASS**

## Frozen terminal decision

`OUTPUT_DEAD_CONFIRMED_RUNTIME_DEBT_REMAINS`

Removing the ordinary `CODEC_ZSTD` audition for the frozen regenerable-Deflate semantic class preserved the exact R30/R31 byte-winning archive on both targets. It also recovered substantial runtime relative to `full-search`, but not enough to restore the inherited same-runner `release-all-exact` floor.

All measured archives strongly verified. Every measured virtual member remained at 1.0x decoded-context amplification, and median peak RSS remained 474,528 KiB.

### Full Incremental Backups

| Arm | Complete bytes | SHA relation | Median create | vs release |
|---|---:|---|---:|---:|
| release-all-exact | 8,088,619 | release reference | 0.489538 s | — |
| full-search | 8,056,193 | byte-winning control | 0.580627 s | +18.61% / +91.089 ms |
| no-ordinary-zstd | 8,056,193 | **byte-identical to full-search** | 0.527801 s | **+7.82% / +38.263 ms** |

The specialized no-Zstd path executed on 180 candidates / 980,226 raw bytes. Relative to full-search it recovered ~52.826 ms, about 58.0% of the measured full-search runtime debt.

### Isolated `snapshot_2.zip`

| Arm | Complete bytes | SHA relation | Median create | vs release |
|---|---:|---|---:|---:|
| release-all-exact | 2,231,160 | release reference | 0.319114 s | — |
| full-search | 2,197,414 | byte-winning control | 0.433771 s | +35.92% / +114.657 ms |
| no-ordinary-zstd | 2,197,414 | **byte-identical to full-search** | 0.374733 s | **+17.43% / +55.619 ms** |

The same 180 candidates / 980,226 raw bytes execute in the isolated projection. Relative to full-search, elision recovered ~59.038 ms, about 51.5% of the measured full-search runtime debt.

## Causal interpretation

R32 decisively confirms the R31 archive-level inference: ordinary Zstd construction is output-dead for the frozen `<64KiB`, exact-Deflate-backed, non-retained semantic class. Removing it changes neither complete archive bytes nor complete archive SHA-256 on either target.

However, the residual create-time debt remains material after that work is removed. Therefore ordinary Zstd audition is **not the sufficient runtime owner**. The remaining owner lies elsewhere in the semantic path: exact-Deflate regeneration/recipe preparation, other preserved candidate work, candidate/materialization architecture, or another build phase.

This is useful negative evidence. It prevents further Zstd-level or Zstd-elision tuning from becoming the primary rehabilitation path without new causal evidence.

## Scoped negative constraint

Within the frozen R30-R32 regime:

1. ordinary Zstd audition for the specialized 180-candidate class is output-dead;
2. removing it is insufficient to restore the inherited create-time floor;
3. further ordinary-Zstd level tuning/elision is retired as the primary runtime-rehabilitation family.

Reopening requires evidence that an ordinary Zstd output becomes selected or that a changed execution boundary makes its cost causally decisive.

## Forge decision

- diagnosis: **D2/D3 residual execution/search debt after an S5 speculative-work retirement**;
- lowest next intervention: **R0 phase attribution** before any additional removal or optimization;
- terminal decision: **`RETIRE_ZSTD_AS_SUFFICIENT_OWNER; PHASE_ATTRIBUTE_RESIDUAL_DEBT`**.

The next experiment must measure where the remaining release-vs-no-Zstd time is actually spent while preserving the exact R32 corpus, policy, bytes and reconstruction. It must not remove another codec by intuition.

## Strongest surviving self-critique

R32 proves an archive-level causal fact, not a full per-candidate winner trace. It also reports total build wall time, so it cannot distinguish whether the remaining 38–56 ms debt belongs primarily to exact Deflate regeneration, non-Zstd candidate evaluation, recipe/index work, or another phase. Any next intervention without phase attribution would risk repeating the same speculative optimization error at a different layer.
