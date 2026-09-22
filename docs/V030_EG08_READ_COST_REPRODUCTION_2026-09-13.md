# v0.30 EG08 read-cost independent reproduction — 2026-09-13

Status: **first-run debt did not reproduce; timing remains explicit ambiguity, not promotion credit**

Original result: `docs/V030_EG08_READ_COST_RESULT_2026-09-13.md`

Reproduction head: `03bd3136f17148d5d5d52f9e2f016084ef3f152f`

Hosted run: `34765316784`

Job: `103745131770`

Artifact: `10320081683`

Artifact digest: `sha256:8d9b0b0c2e0880dd902f31d88ab9c21ba9892947cc49535f14336e581f048b54`

Scientific verdict returned by the unchanged reproduction contract: `EG08_READ_COST_SURVIVES`

## Why this reproduction exists

The first valid hostile-review run returned `EG08_READ_COST_DEBT` solely because Office strong verification crossed the inherited same-runner rule by about `+6.3% / +5.8 ms`. Before seeing another outcome, the repository requested one independent fresh-runner reproduction with **no change** to surfaces, repetition count, operation boundaries or thresholds. The two runs are not pooled, averaged or cherry-picked.

## Evidence common to both runs

Both runs preserve:

- aggregate EG08 saving versus EG07: **1,736,562 B**;
- `9/9` build-time strong verification;
- `9/9` exact extracted-tree identity;
- identical EG07↔EG08 locality geometry on all nine surfaces;
- zero confirmed full-extraction regressions;
- maximum positive reader RSS delta: **0 KiB**.

## Office reproduction

Original Office strong verification:

- CPU: `0.091774041 -> 0.097585776 s`, `1.0633266x`, `+5.811735 ms`;
- wall: `0.091802285 -> 0.097586188 s`, `1.0630039x`, `+5.783903 ms`;
- verdict under the inherited `>5% AND >3 ms` rule: confirmed regression.

Fresh-runner reproduction:

- CPU: `0.092728552 -> 0.095219825 s`, **`1.0268663x`**, `+2.491273 ms`;
- wall: `0.092725339 -> 0.095217844 s`, **`1.0268805x`**, `+2.492505 ms`;
- verdict under the unchanged rule: **not a confirmed regression**.

The reproduction's Office extraction ratios were about `1.03664x` CPU and `1.03681x` wall, also below the inherited relative threshold. No other workload produced a confirmed extraction or strong-verification regression.

## Adjudication

The defensible result is **timing ambiguity**. The first Office debt remains preserved; the second run shows it is not independently stable enough to justify invasive reader redesign or representation rollback by itself. It is equally invalid to erase the first run because the second is green or to ignore the reproduction because the first is red.

Frontier promotion remains blocked independently by EG08's creation-cost debt, so there is no reason to weaken the verification rule or force a binary timing conclusion. Re-check Office strong-verification cost on any future composition candidate; until then, focus on the more reproducible low-yield creation debt.

No Genesis score, R4 score, v0.29 comparator, locality/integrity/recovery law, format revision, numeric version or ONE status changes.
