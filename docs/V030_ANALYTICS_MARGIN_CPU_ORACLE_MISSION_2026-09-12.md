# v0.30 Analytics BytePlane4-margin compute oracle mission

Status: **research-only Mission Lock / Referee**. No canonical format, selector, release, comparator, locality, integrity, recovery or ONE/Genesis authority changes.

## Evidence entering this mission

The frozen path-blind Analytics admission writer established that direct representation needs essentially the whole positive level-15 -> level-19 reward: 45 admitted packs recover about 434 KiB, while high-effort level-19 work remains the dominant creation cost.

The fixed BytePlane4 strong transfer subsequently created real structural density headroom without weakening the workload or comparator: `6,063,752 B` versus accepted v0.29 `6,135,172 B`, an exact archive margin of **71,420 B**. The transform is fixed width 4, exact, path-blind, and selected only 2 of 50 strong-pack requests after a cheap level-1 structural audition.

Two obvious speed explanations are already retired. Reusable libzstd context/buffer state was byte-identical but recovered only about 0.6% CPU. Reducing only source-size-specific level-19 `searchLog` by one gave back 48,963 B but recovered only about 7.2% CPU, failing its preregistered 20% hurdle. Per-pack attribution also found the high-effort cost diffuse: the top 12 of 45 packs account for only about one third of measured level-19 CPU, not the preregistered 70% concentration threshold.

The next question is therefore not whether another heuristic can skip *some* level-19 work. It is whether the **entire 71,420 B of newly earned structural margin is large enough in principle** to buy back enough high-effort work to matter.

## Falsifiable hypothesis

Give an oracle impossible knowledge of every admitted pack's exact level-15 -> level-19 byte reward and measured level-19 CPU. Allow it to spend at most the full **71,420 B** BytePlane4 archive margin by reverting selected packs from level 19 to level 15. If the best exact 0/1 selection can eliminate at least **70% of measured level-19 CPU**, then a future cheap predictor/search law could still plausibly make margin-funded work elimination a primary route.

The 70% hurdle is deliberately generous. The prior Analytics creation boundary needs a substantially larger reduction to approach the approximately 0.835 s high-effort budget left after fixed build/publication/verification work. Failing even this optimistic oracle means another admission/skip heuristic cannot be the primary answer unless substantially more structural margin is first earned.

## Referee contract

1. Rebuild the exact frozen 45-pack population using the existing path-blind `raw >= 256 KiB && L15 ratio <= 0.70` rule; fail closed on population drift.
2. Reuse the existing three-round L15/L19 per-pack cost-attribution measurement with rotated order. No path, extension, workload label, pack ordinal or SHA-derived policy is allowed; SHA may only join repeated measurements.
3. Freeze accepted-v0.29 bytes at `6,135,172 B` and BytePlane4 strong candidate bytes at `6,063,752 B`; derive the spendable archive margin as exactly `71,420 B`.
4. Solve an exact 0/1 knapsack whose item weight is the deterministic bytes lost by reverting one pack from L19 to L15 and whose value is measured median L19 CPU removed. Do not tune a selector or threshold.
5. Report the oracle's selected count, byte giveback, CPU removed, remaining CPU, removal fraction, retained L15->L19 byte reward, and selected-item measurement rows. This is an impossibility/headroom oracle; selected identities receive no production-policy credit.
6. Preserve all exact-decode and fixture-validity checks inherited from the cost-attribution referee. No archive is promoted and no locality/auth/recovery/native credit is earned here.
7. Green CI means a structurally valid receipt, not that the hypothesis passed.

## Decision

- **PASS — `MARGIN_CAN_SUPPORT_SKIP_RESEARCH`:** the impossible oracle removes >=70% of measured L19 CPU while giving back <=71,420 B. Freeze the oracle result, then search for a content-derived cheap predictor on generator-distinct held-out packs before any writer change.
- **FAIL — `MARGIN_INSUFFICIENT_RETIRE_SKIP_ONLY`:** even impossible knowledge cannot remove 70% of L19 CPU under the earned margin. Retire further skip/admission tuning as the primary Analytics speed route. Preserve BytePlane4 as useful density margin and attack the high-effort engine globally or earn materially more structural margin.

This mission does not alter the frozen ONE Genesis result or `research/cmpct1`. It uses ONE's cheap-gating lesson only as a question of work elimination, not as a representation transplant.
