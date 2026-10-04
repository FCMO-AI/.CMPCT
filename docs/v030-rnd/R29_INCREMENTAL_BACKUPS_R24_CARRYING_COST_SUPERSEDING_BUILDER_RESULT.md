# R29 — Incremental Backups r24 Carrying-Cost Superseding Builder Result

Status: **TERMINAL — PARTIAL_OWNER; VALID DIAGNOSTIC EVIDENCE; NO DIRECT PRODUCT AUTHORIZATION**

Frozen preregistration: `docs/v030-rnd/R29_INCREMENTAL_BACKUPS_R24_CARRYING_COST_SUPERSEDING_BUILDER_PREREG.md`.

Execution authority:

- workflow run: `33828955706`
- exact result-bearing head: `672c0f49d64daad1416ac997e7144588b63fd19f`
- release fingerprint at execution: `b5818373f1cdbb38758a557939a29e3020b41d33d2136318ed20e12c86991f35`
- immutable artifact: `9920994542`
- uploaded artifact ZIP SHA-256: `334bb7c3816f6727419d78c224ad7f860ae74acb19c60c47956154904458b4bc`
- frozen six-arm Builder: **PASS**
- frozen completeness guard: **PASS**

## Same-run authority

All six arms strongly verified and reconstructed the identical product tree. Selected-member locality remained **1.0x** in every arm, well below the frozen <=8.0x ceiling.

| Arm | Complete bytes | vs release-r24 | vs genuine-r24 | locality |
|---|---:|---:|---:|---:|
| genuine-r24 | 8,036,615 | — | — | 1.0x |
| release-r24 | 8,088,601 | — | +51,986 | 1.0x |
| mature Deflate threshold | 8,056,183 | **-32,418** | +19,568 | 1.0x |
| mature micro-pack target | 8,091,260 | +2,659 | +54,645 | 1.0x |
| mature micro-pack max-file | 8,110,793 | +22,192 | +74,178 | 1.0x |
| no medium `.bin` pack admission | 8,091,208 | +2,607 | +54,593 | 1.0x |

Frozen terminal decision: **`PARTIAL_OWNER`**.

The only one-factor arm that moved toward the lawful genuine-r24 floor was restoring the mature `deflate_reuse_min=65536` threshold. It removed **32,418 B / 62.3591%** of the same-run positive shipping-r24 gap while preserving exact reconstruction and 1.0x locality.

The other three frozen shipping-policy reversions did not explain the debt in isolation; each made the archive larger than release-r24 on this target.

## What R29 proves — and what it does not

R29 proves a scoped D2 fact: on this frozen Incremental Backups regime, the shipping policy that attempts Deflate reuse down to zero bytes is a **material partial carrying-cost owner** relative to mature r24.

R29 does **not** prove that the global zero-byte threshold is wrong. That shipping policy was introduced to preserve positive nested-container / exact-Deflate-reuse cases and must not be reverted globally without protecting those evidenced wins. Nor does R29 explain the remaining **19,568 B** above genuine r24.

Therefore no product code changes are authorized by R29 itself.

## Required Forge handoff

The next Builder must test a **generic content-derived conditional/elision rule** for Deflate-reuse work rather than workload-name/path dispatch or a global threshold rollback. It must include:

1. this Incremental Backups target;
2. the positive/adversarial workloads that justified zero-threshold Deflate reuse;
3. exact complete bytes and strong reconstruction;
4. fresh-process create time and peak RSS;
5. operation-derived selective-read locality <=8x;
6. explicit global carrying cost and retained positive evidence;
7. a no-regression byte law on every protected workload.

If a post-selection or cheap preflight rule can avoid unprofitable Deflate reuse while retaining profitable exact reuse, that is the preferred lowest-sufficient R1/R2 intervention. If no generic rule separates the regimes, preserve the scoped cost and move to interaction attribution for the remaining debt rather than overfitting the target.

## Strongest surviving self-critique

The exact fresh-run archive byte counts varied by tens of bytes across R27/R28/R29 even though the deterministic content-tree identity and direction/magnitude of the release-r24 carrying cost were stable. R29 correctly avoids using historical absolute archive bytes as a causal threshold, but that variability itself remains a custody question worth isolating separately. It does not invalidate the same-run paired result; it does prevent treating any one historical complete-byte count as timeless substrate identity without a pinned archive-level determinism receipt.
