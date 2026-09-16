# R29 — Incremental Backups r24 Carrying-Cost Superseding Builder Preregistration

Status: **FROZEN BEFORE RESULT-BEARING EXECUTION**

Supersedes only the invalid cross-run exact-gap custody assumption in R28. R28 itself remains immutable and terminal `SUBSTRATE_OR_CORRECTNESS_FAILURE`.

Authority product substrate: `b0e7aeab92c994b4a25c5040fe3fb9f5e208b01a`.

## Why a superseding freeze is required

R27 established a lawful genuine-r24 floor: release-r24/current-product were ~52 KB larger at 1.0x locality. R28 then froze the historical R27 difference as exactly 52,024 B. Its later fresh execution observed a same-run +52,018 B gap and therefore correctly failed its own exact guard. The R28 arm observations are hypothesis-generation only.

R29 repairs **only** that invalid cross-run equality assumption. It does not change the target, product substrate, one-factor arms, locality ceiling, correctness law or product/release thresholds.

## Frozen question

On one freshly generated instance of the frozen Incremental Backups target, which shipping-r24 policy factor accounts for the positive complete-byte gap between release-r24 and genuine-r24?

The causal unit is the **within-run paired difference on the identical source tree**. Historical absolute archive byte counts are not used as a decision threshold.

## Frozen target and identity

Use only repaired `neutral_hostile_v1/06_incremental_backups` through the current canonical benchmark generator.

Before interpretation:

- record the generator-provided expected content-tree identity;
- require every arm to strongly verify;
- require every arm to reconstruct the same tree;
- require the release-r24 archive to be **strictly larger** than genuine-r24 in the same run;
- bind product/corpus/policy source to the unchanged authority substrate, permitting only R26-R29 diagnostic/prereg/result/workflow custody files after it.

Any failure is `SUBSTRATE_OR_CORRECTNESS_FAILURE`.

## Frozen arms

Exactly the R28 arm definitions are retained:

1. `genuine-r24` — unmodified mature canonical r24 Builder.
2. `release-r24` — current `_locality_bounded_r24_build()`.
3. `mature-deflate-threshold` — release-r24 except `deflate_reuse_min=65536`.
4. `mature-pack-target` — release-r24 except micro-pack target remains mature 256 KiB.
5. `mature-pack-max-file` — release-r24 except micro-pack max-file remains mature 32 KiB.
6. `no-medium-bin-pack` — release-r24 except `.bin` is not added to medium S_PACK admission.

All release-policy variants apply the same already-promoted dead-dictionary elision. The single-large-file fixed-8-MiB rule remains unchanged and its activation state is recorded.

## Frozen measurements

For every arm record the same R28 measurements:

- complete archive bytes and SHA-256;
- exact reconstructed tree and strong verification;
- format revision/profile;
- build wall time and fresh-process peak RSS;
- selected largest regular member;
- operation-derived decoded-context bytes and amplification;
- effective Deflate threshold, pack target, max-file, medium-binary admission and wide-single-file state.

For each experimental arm compute against the **same-run** release and genuine controls:

- `bytes_vs_release`;
- `bytes_vs_genuine`;
- `positive_gap_removed_bytes`;
- `positive_gap_removed_fraction` of that same-run positive gap.

Hard locality ceiling remains **<=8.0x**.

## Frozen interpretation law

After substrate/correctness checks:

- `SINGLE_OWNER` — exactly one experimental arm reaches `<= genuine-r24` bytes at <=8x.
- `MULTIPLE_SINGLE_OWNERS` — more than one does.
- `PARTIAL_OWNER` — no arm restores the full floor, but at least one is strictly smaller than release-r24 while remaining correct and <=8x.
- `NO_ONE_FACTOR_EXPLANATION` — none is smaller than release-r24.
- `LOCALITY_DEBT` — an otherwise floor-restoring arm exceeds 8x.
- `SUBSTRATE_OR_CORRECTNESS_FAILURE` — identity/product-substrate/correctness law fails or the same-run release-r24 gap is not positive.

If `PARTIAL_OWNER`, rank partial arms by same-run positive gap removed, but **ranking is diagnostic only**. The next Builder must test a content-derived generic conditional/elision policy and any required interactions; R29 cannot authorize changing a shipping threshold directly.

## Anti-cheating and negative evidence

No workload-name/path dispatch. No third full genuine-r24 product tournament arm. No representation invention while a lawful r24 floor remains. No adjustment of the one-factor values after execution. No use of runtime noise to excuse byte regression. Preserve an unfavorable result as a scoped D2 constraint.

After first result-bearing execution, this preregistration and its target/arms/law are immutable. A material scientific change requires another superseding freeze.
