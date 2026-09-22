# v0.30 Analytics single SearchLog ablation mission

Status: **research-only Mission Lock / Referee**. This is the one search-cost ablation earned by the successful fixed BytePlane4 strong-transfer referee. No parameter sweep is authorized.

## Evidence entering this mission

The strong BytePlane4 transfer on the frozen Analytics strong frontier saved **71,951 B** versus direct level-19 while adding about **0.166 s** complete verified creation. The mechanism is fixed width=4, path-blind, exact, and only two of 50 pack requests won the cheap level-1 structural gate. This creates real experimental density margin that did not exist on the 232 B selective-L19 frontier.

The selective writer established that 45 level-19 pack requests are effectively required to match v0.29 under the existing direct representation, and that those requests cost about 4.78 s CPU. Reusable `ZSTD_CCtx`/buffer state was byte-identical but only ~0.6% faster, so the dominant cost is the level-19 search algorithm, not setup/allocation.

For the common 512 KiB pack scale, libzstd level 19 uses a very deep search configuration (`searchLog=7`, `targetLength=256`, `btultra2`). A one-step reduction of `searchLog` from 7 to 6 is a direct causal test of search breadth: it approximately halves the configured number of match-search attempts while leaving window/hash/chain/minMatch/targetLength/strategy otherwise at the level-19 defaults for that source size.

## Falsifiable hypothesis

On the exact frozen 45-pack Analytics admission population, **level 19 with only `searchLog` reduced by one from its source-size-specific default** can cut median compression CPU by at least **20%** while giving back no more than **48 KiB** versus ordinary level-19 output across the population.

The 48 KiB loss ceiling is deliberately below the 71,951 B structural margin earned by BytePlane4, leaving >20 KiB nominal room for integration/framing noise. The 20% speed hurdle is the same order required to move the preserved scheduling floor rather than merely polish it.

## Referee contract

1. Use exactly the same 45 raw packs selected by the frozen `>=256 KiB && L15 ratio <=0.70` rule; fail closed on population drift.
2. Baseline is current one-shot `V25.zc(raw, 19)`.
3. Candidate uses the same loaded libzstd. For each pack, obtain the exact source-size-specific level-19 parameters through `ZSTD_getCParams(19, sourceSize, 0)`, then change **only** `searchLog = max(default_searchLog - 1, 1)` before compression. All other compression parameters must equal the returned level-19 defaults.
4. No second parameter, level, threshold or content-class sweep. No path/extension/workload identity.
5. Decode every candidate frame with the normal v0.25 decoder and require byte-exact raw recovery plus CRC/SHA identity inherited from the fixture.
6. Run baseline and candidate in fresh child processes, three rounds with rotated order. Report CPU/wall, output bytes, per-size/default searchLog values, peak RSS and exact byte delta.
7. The candidate does not receive archive/locality/auth/recovery/native/release credit. It is only a causal search-cost referee.
8. Green CI means receipt validity, not a win.

## Decision

- **PASS:** candidate median CPU <=0.80x baseline, total output growth <=49,152 B, exact decode, and only SearchLog changed. Integrate this single ablation underneath the already-earned BytePlane4 strong representation and run a complete verified-creation Builder against v0.29 + same-runner ZIP.
- **FAIL:** retire SearchLog-1. Do **not** try SearchLog-2, targetLength, strategy or a parameter grid in this campaign. Use the L19 cost-attribution referee to decide whether to target hot packs structurally or change the high-effort engine itself.

This mission does not alter the frozen ONE Genesis result or `research/cmpct1`.
