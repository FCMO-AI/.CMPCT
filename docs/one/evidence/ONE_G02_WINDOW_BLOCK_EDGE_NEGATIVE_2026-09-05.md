# ONE-G0.2 — window-block edge summary negative

**Status:** 64-position continuously maintained block-summary shape retired  
**Exact source:** `39a3e99efb5803862bdf46a69d1422a1800a436f`  
**Workflow:** `33946811533`  
**Job:** `101254293632`  
**Artifact:** `9963589166`  
**Artifact digest:** `sha256:708846ea12c417c923a18d8967f0b884579ed14b3bbe4e6750ec419defdeae6a`  
**Experiment:** `ONE-G0.2`

## Mission lock

The predecessor full-span edge replay preserved transfer but failed the small-input native gate because each edge reconstructed all 4,096 Gear states. This Builder used the already-canonical ONE `WINDOW == 64` as block granularity: continuously retain exact rightmost minima for completed 64-position blocks plus boundary bytes/checkpoints, then answer a 4,096-position edge query from full-block summaries and at most two partial boundaries.

Frozen advancement required exact edge semantics, state <=0.25x promoted, hard-row closure, and no large-input compute regression. Any large row above 1.05x promoted retired the shape.

## Result

Artifact decision: `retire_window_block_edge_summary`.

Exact edge-oracle equality held on every row. Reserved state was **8,319 B**, only **0.202626x / 20.26%** of the promoted selector's 41,056 B. Query work was indeed bounded: for example random 1 MiB performed 38 queries, reconstructed 3,248 boundary states and scanned 2,398 block summaries rather than replaying 155,648 Gear states as the full-replay edge implementation did.

But the always-paid summary maintenance dominated elapsed time:

| Case | Block / promoted | Block / full-replay edge |
|---|---:|---:|
| random 1 MiB | **2.037284x** | 2.247603x |
| zlib-random 1 MiB | **2.049123x** | 2.244548x |
| repeated 64 KiB basis 1 MiB | **2.006328x** | 2.047877x |
| shifted 512 KiB +1 | **2.051467x** | 2.314484x |
| hard 8,193 B | **1.639847x** | 1.378105x |

The hard row improved relative to promoted compared with full replay (1.640x vs 1.886x), but remained well outside the <=1.20x frozen closure threshold, while every large row catastrophically violated the 1.05x retirement boundary.

## Scoped negative constraint

**Retire continuously updating per-byte block summaries as the primary rescue shape in this tested regime.** The result falsifies the idea that a small exact hierarchy is automatically cheap enough simply because edge queries become sparse.

Do not reopen by tuning block width. The block width was inherited from canonical `WINDOW`, and the failure is ~2x large-path elapsed, not a near-boundary constant problem.

The causal lesson is stronger: the next seed must avoid both expensive extremes — full 4,096-state replay at the edge and nontrivial hierarchical bookkeeping on every byte. A minimal continuously maintained sufficient statistic is admissible only if its update is close to the already-paid fused Gear observation itself.

## Claim boundary

Native encoder-discovery negative evidence only. No reader/wire, stored-byte, product, comparator, release, access, recovery, integrity or portability authority is created.
