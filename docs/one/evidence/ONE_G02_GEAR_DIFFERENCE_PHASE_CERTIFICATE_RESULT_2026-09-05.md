# ONE-G0.2 — Gear-difference content-local phase certificate result

Date: 2026-09-05
Experimental line: ONE-G0.2
Decision: **advance to native carrying-cost work**

## Exact evidence

- source: `ac7342ed94e47cbc74eda139ae60be26b4a22b0a`
- workflow: `33974321489`
- artifact: `9971865116`
- artifact digest: `sha256:4fb230a5729ae778973151d852401802599b9af90e5fd0aa7d227c22ca7f2443`
- pre-result ONE semantic/hostile tests: pass
- modeled writer discovery state: 280 B

## Algebraic result

For the live Gear prefix recurrence `P_i = 2 P_{i-1} + G[x_i] (mod 2^64)`, the derived 8-byte local token

`L_s = P_{s+7} - 2^8 P_{s-1} (mod 2^64)`

matched an independently recomputed direct eight-byte Gear fold on every sampled source and target window in the frozen matrix: **zero identity failures**.

This is the key mechanism result: prefix history cancels exactly, so content-local relation evidence can be obtained from already-required observer Gear state plus a few saved prefix snapshots, rather than carrying a second rolling raw-byte word or rescanning the payload.

## Frozen structural matrix

Across sizes 4, 8, 16, 64 and 256 KiB and seeds 11, 37 and 59:

- required positive misses: **0**;
- independent-random false nominations: **0**;
- Gear-difference identity failures: **0**;
- maximum sampled-position fraction: **0.1874923706**, below the frozen 0.19 ceiling;
- state: **280 B**, at the frozen ceiling.

The certificate also nominates the deliberately false `fragmented_every32` relation cases, just as a discovery certificate is allowed to do; the exact safe relation proof rejects them. This is useful evidence that nomination remains separate from Law authority.

## Hostile Reviewer

This is structural evidence, not native speed evidence. A prefix-derived local token can eliminate raw-window maintenance conceptually, but phase event handling, mixing, bottom-K maintenance and snapshot bookkeeping still cost CPU. The rejected raw-word fused path was ~2.76x baseline, so algebraic elegance alone does not rehabilitate unconditional carrying.

The next native experiment must charge total observer elapsed and actual retained state. It should compare against both the promoted observer baseline and the rejected raw-word fused certificate, with exact independent Gear-difference witnesses.

A further mechanism-level question is whether the extra `_mix64` is needed at all. `L_s` is already a 64-bit content-local weighted sum over randomized Gear table entries. Removing the mix could eliminate most of the previously measured phase-hash stage, but that changes bottom-K ordering and therefore must be structurally preregistered and falsified before timing.

No density, reader-speed, format, product, v0.29, or deferred-v0.30 claim follows.