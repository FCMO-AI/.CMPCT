# v0.30 r24 locality-derived micro-pack current15 transfer — 2026-09-12

Status: **research evidence; current-fingerprint only; not a frozen Genesis rescore**

Exact measured head: `3287447d3f267681baf5286f65db9cd2273331e8`
Hosted workflow run: `34737491578`
Receipt artifact: `v030-current15-generalizes-done15-delta-321503-wins3-fails0-exec0-f9acc42a49ad-3287447d3f267681baf5286f65db9cd2273331e8`
Corpus fingerprint: `f9acc42a49ad175d008c4e1cf7d3b88a545f6ead176d817e02947f613c574fdb`
Scientific verdict: `CURRENT15_MICROPACK_GENERALIZES`

## Why this rerun was required

The earlier transfer evidence predated the repair that restored the earned r24 micro-pack eligibility mechanism. Shared physical/membership helper changes were also not in the workflow trigger surface, so an old green could have remained visible after the mechanism itself changed. The workflow was repaired to invalidate on those helpers and this exact-head rerun is the first current15 transfer receipt after that repair.

## Result

All **15/15** current-fingerprint workloads completed without execution errors. The same-grammar independent and locality-derived arms had:

- logical bytes: **265,975,875 B**
- independent stored bytes: **182,152,701 B**
- derived stored bytes: **181,831,198 B**
- aggregate delta: **-321,503 B (-0.17650%)**
- grouped workloads with strict stored-byte wins: **3**
- zero-group exact ties: **12**
- economic failures: **0**
- invariant failures: **0**
- execution failures: **0**
- maximum member amplification: **8.0x**
- maximum physical decode unit: **41,342 B**

The transfer also observed lower in-process build cost on this measurement surface:

- independent build CPU sum: **10.542390 s**
- derived build CPU sum: **4.490022 s**
- independent build wall sum: **10.657948 s**
- derived build wall sum: **4.521609 s**

Those timing sums are supportive rather than a substitute for the dedicated alternating fresh-process economics referee. The latter separately earned fresh-process CPU/wall credit on the three grouped workloads.

## Interpretation

This result is stronger than an origin-only benchmark win: under the exact current corpus fingerprint, the mechanism is a no-op on 12 workloads and a strict byte win on all 3 workloads where it actually groups files. There are no current15 workloads where grouping is emitted and loses economically.

The result does **not** authorize a frozen Genesis rescore, release, version bump, or canonical builder change. The current transfer corpus is intentionally identified by its fingerprint and is not presented as the historical Genesis source. The research builder also still has path/extension-derived eligibility and extension bucketing that require separate causal ablation before policy promotion.

## Promotion debt

Before a canonical change, keep these gates explicit:

1. corrected hostile-transfer evidence on the repaired mechanism;
2. extension-bucket/path-dependence ablation;
3. authenticated integrity, recovery and reader parity on the exact candidate representation;
4. portability/native behavior where applicable;
5. exact whole-artifact economics with fallback on tie/loss;
6. an explicit composition measurement before changing the adjudicated R4 aggregate.
