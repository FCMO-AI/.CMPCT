# ONE-G0.2 — shared observer + sparse phase cold fallback result

Date: 2026-09-05
Experimental line: ONE-G0.2
Decision: **advance the cold-fallback cascade to native carrying-cost measurement**

## Exact-source receipt

- source: `5a2d79a5f258af66aaf8b7447b3e3a026ab4a54d`
- workflow: `33971914603`
- job: `101321815931`
- artifact: `9971185874`
- artifact digest: `sha256:6fdf69079459e33695561f495650135bf07a50b55ccfe3756116662d8ad20771`
- semantic/hostile ONE suite: passed before the frozen validation

## Result

The unchanged sparse phase certificate succeeds in the role it was actually designed for: a **cold complement** to already-paid shared observation.

Across 105 generator-distinct rows:

- exact-relation positives: 75;
- positives nominated by shared observation alone: **71**;
- positives missed by shared observation and recovered by cold phase fallback: **4**;
- combined positive misses: **0**;
- fallback activations: **34**;
- independent-random combined false nominations: **0**;
- maximum fallback sampled-position fraction: **0.18749237060546875**;
- transient fallback witness state: **240 bytes**.

The four recovered positives were:

- 4 KiB, seed 13, quarter damage;
- 4 KiB, seed 13, mutation every 96 bytes;
- 4 KiB, seed 67, mutation every 96 bytes;
- 8 KiB, seed 67, mutation every 96 bytes.

This is exactly the small-root blind-spot regime that shared prefix-history observation had exposed.

## False-pattern debt remains visible

All 15 `fragmented_every32` exact-relation negatives reached the cold phase nominator. All 15 independent-random negatives activated fallback but did **not** nominate.

Therefore the cascade has not yet earned efficiency. The next native experiment must include the existing sparse relation falsifier and charge every `every32` false nomination through that stage. If those rows force enough exact proofs to erase the discovery savings, the cascade fails even though structural coverage is perfect.

Fallback activations by size were:

- 4 KiB: 9 rows — 3 productive positives, 3 `every32` negatives, 3 random negatives;
- 8 KiB: 7 rows — 1 productive positive, 3 `every32` negatives, 3 random negatives;
- 16 KiB: 6 rows — 3 `every32`, 3 random;
- 64 KiB: 6 rows — 3 `every32`, 3 random;
- 256 KiB: 6 rows — 3 `every32`, 3 random.

## Causal interpretation

The earlier standalone failure does not require post-hoc witness tuning. ONE already possesses two different observation views:

- prefix/history-derived shared Gear evidence catches most useful relations;
- sparse content-local phase evidence is replayable and covers the remaining small-root blind spots.

Because the phase evidence is only computed after shared observation is silent, its 240-byte state is transient rather than continuously carried. This is materially different from the retired unconditional rolling certificate, which charged extra work on every byte of every pair.

## Next frozen question

Compare two **opportunity-equivalent rescue strategies** only on shared-silent pairs:

1. eager exact safe relation proof on every shared-silent pair;
2. cold phase certificate -> sparse relation falsifier -> exact proof only when warranted.

This comparison is honest because both strategies are attempting to recover the same relations after shared observation has already failed. The candidate must pay phase sampling, false nominations, sparse-gate work, and any exact proofs it triggers.

## Claim boundary

This is structural complementarity evidence only. No native speed, stored-byte, reader, canonical-format, v0.29/v0.30, or release claim is made.