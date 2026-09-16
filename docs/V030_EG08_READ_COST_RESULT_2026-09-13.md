# v0.30 EG08 exported read-cost result — 2026-09-13

Status: **hostile-review DEBT; density evidence preserved, frontier promotion blocked**

Exact measured head: `56d02a4e9d00180c5e0c1f67c1d6b53158d47141`

Hosted run: `34765042618`

Job: `103744400130`

Artifact: `10320381078`

Artifact digest: `sha256:1af9e6ca8345081f2dd3d58c82085b393ceaa90d7c98277706cea35671546476`

Scientific verdict: `EG08_READ_COST_DEBT`

## Contract

The hostile reviewer executed the already-preregistered eligible-nine surface from `docs/V030_EG08_READ_COST_MISSION_LOCK_2026-09-13.md`. It changed no compression decision. For each frozen surface it fresh-process built EG07 and EG08 from the same deterministic source, required build-time strong verification and identical locality geometry, then measured three fresh-process repetitions each of full extraction and strong verification. The inherited same-runner timing rule was unchanged: a regression is confirmed only when EG08 is both more than 5% and more than 3 ms slower than EG07.

## What survived

Across all nine surfaces:

- aggregate EG08 stored-byte saving versus EG07: **1,736,562 B**;
- `9/9` build-time strong verification PASS;
- `9/9` exact extracted-tree identity for both contenders;
- `9/9` identical member count / max decode unit / max amplification geometry;
- **zero confirmed extraction CPU regressions**;
- **zero confirmed extraction wall regressions**;
- maximum positive reader RSS delta: **0 KiB**.

Worst extraction ratios were only:

- CPU: `1.0403505258x`;
- wall: `1.0408329207x`.

Those remain below the inherited relative threshold and therefore are not confirmed regressions.

## Exact blocker

Only Office crossed the strong-verification timing rule:

| Metric | EG07 | EG08 | Ratio | Absolute delta |
| --- | ---: | ---: | ---: | ---: |
| verify CPU | `0.091774041 s` | `0.097585776 s` | **1.0633266x** | **+0.005811735 s** |
| verify wall | `0.091802285 s` | `0.097586188 s` | **1.0630039x** | **+0.005783903 s** |

Office simultaneously preserves a **483,585 B** stored-byte saving versus EG07. Its full extraction did **not** regress under the same rule:

- extraction CPU ratio: `1.0403505x`;
- extraction wall ratio: `1.0408329x`.

No other surface produced a confirmed strong-verification regression. The global worst verify ratios are therefore the Office values above.

## Interpretation

EG08's higher-effort physical frames do not create a general extraction or reader-memory debt on the frozen eligible-nine domain. The exported reader debt is much narrower: Office strong verification is measurably slower by about **5.8 ms / 6.3%** under the preregistered rule.

That debt is small in absolute time but is real under repository policy and is not waived because the density saving is large. `EG08_READ_COST_SURVIVES` therefore does not earn.

EG11 does not change this adjudication. EG11 proved that the exact EG08 bytes can be created with less duplicate encoder work; because the complete artifacts are byte-identical, their read/verify behavior is the same representation-level behavior measured here.

## Remaining creation debt

Separately, `docs/V030_EG08_ELIGIBLE9_TRANSFER_RESULT_2026-09-13.md` already established that EG08's post-build implementation fails only the preregistered low-yield creation-cost gate. EG11 improves aggregate EG08 creation by about 1.32%, but it does not plausibly close the known low-yield rows such as Large Mixed (`56 B` saving) and hostile incompressible (`0 B` saving), which historically paid multi-x creation CPU versus EG07.

Thus two different exported-cost debts remain and must not be conflated:

1. **creation:** redundant/high-effort work on low- or zero-yield physical packs;
2. **reader:** Office strong verification only, approximately +5.8 ms / +6.3%.

## Score custody

This result does not alter Genesis, the composed R4 score, v0.29 release identity, locality limits, integrity/recovery semantics, numeric version, format revision or ONE's preserved secondary status. EG08's `1,736,562 B` eligible-nine saving remains mechanism evidence, not an aggregate product score change.

## Next decisive work

Do not tune Office thresholds or weaken strong verification. First attribute the low-yield creation work into **selected-frame work versus rejected ladder work** on the frozen low-yield surfaces. If most cost is rejected work, a general exact branch-and-bound/opportunity gate can attack creation without changing EG08 bytes. If selected winners themselves dominate cost, exact-EG08 creation has a real floor and the next representation must explicitly trade density against creation/read cost under a new preregistered Pareto referee.

In parallel, the Office verify delta should be independently reproduced before invasive reader work because the absolute effect is only ~5.8 ms. A second same-semantics reproduction can distinguish stable frame-level decode cost from a near-threshold hosted-run effect without weakening the frozen rule.
