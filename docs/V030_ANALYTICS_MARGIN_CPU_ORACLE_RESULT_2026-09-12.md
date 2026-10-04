# v0.30 Analytics BytePlane4-margin compute oracle result — 2026-09-12

Status: **terminal negative for skip/admission tuning as the primary Analytics speed route under the currently earned BytePlane4 margin**. Research-only; no release, format, selector, locality, integrity, recovery, native or ONE/Genesis authority changes.

Source head: `ce52c04223fe73b097030bcbccaf2df069d94b77`
Hosted run: `34731164461`
Schema: `cmpct-v030-analytics-margin-cpu-oracle-v1`

## Frozen evidence

- accepted v0.29 Analytics: **6,135,172 B**
- strong BytePlane4 Analytics candidate: **6,063,752 B**
- exact spendable archive margin: **71,420 B**
- frozen admitted pack population: **45**
- total measured L15 -> L19 reward: **434,113 B**
- hosted sum of per-pack median L19 CPU: **5.780151844 s**
- hosted sum of per-pack median L15 CPU: **0.499301715 s**

The oracle was intentionally stronger than any implementable selector: it received exact post-result byte reward and exact measured L19 CPU for every admitted pack, then solved the exact 0/1 knapsack that maximized removable L19 CPU while spending no more than the full 71,420 B BytePlane4 margin. Selected pack identities are evidence only and receive no encoder-policy credit.

## Exact hosted result

The optimal oracle selected **11 packs** and gave back **67,780 B**, leaving **3,640 B** of the earned margin unused.

That impossible selector removed only **1.724148013 s** of measured L19 CPU and left **4.056003831 s**. Its CPU-removal fraction was therefore only **29.8288%**. The preregistered continuation hurdle was 70%.

The retained L15 -> L19 byte reward after spending the margin was **366,333 B**.

Verdict: **`MARGIN_INSUFFICIENT_RETIRE_SKIP_ONLY`**.

## Interpretation

This closes a family, not the whole Analytics line.

The result means another content-derived admission heuristic cannot be the primary answer while the representation has only the currently earned BytePlane4 margin. Even perfect hindsight cannot skip enough L19 work. The real implementation would necessarily do worse because it must predict without post-result knowledge and must pay observation/selection cost.

The negative compounds prior evidence:

1. the frozen coarse admission rule already rejects non-payers but still needs 45 expensive packs to cross the v0.29 byte floor;
2. reusable libzstd context/buffer state is byte-identical but recovers only about 0.6% wall time;
3. source-size-specific `searchLog - 1` gives back 48,963 B but recovers only about 7.2% CPU, far below its frozen 20% hurdle;
4. per-pack cost attribution is diffuse: the top 12 of 45 packs account for only about one third of L19 CPU;
5. scheduling-only acceleration of the same work was already retired because an impossible perfect eight-worker floor remains slower than ZIP.

Therefore the remaining credible routes are:

- **earn materially more structural margin**, enough to run a substantially cheaper global compression regime; or
- **replace/alter the high-effort engine globally** so comparable density no longer requires current L19 search work.

Do not respond to this result with another admission threshold, pack-rank heuristic, deeper `searchLog` reduction, worker-count sweep, or context-allocation micro-optimization.

## Quantitative structural target

Using the prior exact cost-attribution receipt as a planning oracle, the approximate minimum byte giveback required for omniscient CPU removal was:

- 70% CPU removal: about **176 KiB** total margin;
- 80%: about **252 KiB**;
- 82.5%: about **269 KiB**;
- 90%: about **332 KiB**.

These are planning targets, not product claims; timing varies across hosted reruns. Their purpose is to show scale: the present 71.4 KiB margin is not close to a skip-only solution.

## Next decisive test

The effort frontier already contains one unusually strong fixed candidate for the “more structural margin + cheaper global regime” branch: **level 17** stores 6,210,959 B on the frozen Analytics tree, only 75,787 B above accepted v0.29, while being materially cheaper than level 19. The already-frozen BytePlane4 mechanism saved 71,951 B at level 19. A single fixed transfer of BytePlane4 onto level 17 therefore has a pre-evidence arithmetic gap of only **3,836 B** to the v0.29 floor.

Level 17 is the justified next test because level 18 is dominated in the prior effort frontier (larger and slower), while level 16 is materially farther from the byte floor. Do not sweep levels or BytePlane widths. Freeze level 17 + width 4 and ask whether the structural transform can cross v0.29 while preserving the lower-effort creation advantage.

`research/cmpct1` and the frozen ONE Genesis result remain untouched. The only transferred ONE lesson here is to stop spending compute on work that evidence says cannot pay.
