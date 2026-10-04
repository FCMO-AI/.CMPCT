# v0.30 Analytics BytePlane4 strong-transfer mission lock

Status: **research-only Mission Lock / Referee**. No canonical format, selector, release, comparator, locality, integrity, recovery or ONE/Genesis authority changes.

## Causal position

The frozen Analytics selective writer can store **6,134,940 B**, only **232 B** below the accepted v0.29 floor of 6,135,172 B. Its high-effort stage remains far too expensive: 45 admitted packs consume about 4.78 s of level-19 CPU and complete verified creation is about 5.51 s versus about 0.883 s for same-runner ZIP. A perfect admission policy cannot eliminate another meaningful high-effort pack without losing the v0.29 byte floor: the next omitted positive pack would give back 5,274 B.

Reusable libzstd context/buffer state was byte-identical but only about 0.6% faster, so allocation/context churn is retired as the primary speed explanation. The remaining cost is algorithmic level-19 search. Weakening that search directly is unsafe while the representation has only 232 B of margin.

A prior fixed reversible BytePlane4 experiment at level 1 found a real, path-blind structural signal: only two payloads selected the transform and the complete candidate saved 63,255 B versus direct level 1. That mechanism was retired as a direct Analytics solution because level-1 density remained far from v0.29; it was not tested as a **margin source on the strong frontier**.

## Falsifiable hypothesis

The already-frozen width-4 byte-plane transform, gated solely by whether its fully framed level-1 audition beats the direct level-1 payload, identifies a very small set of packs where the same transform also improves level-19 output. Paying strong transformed compression only for those cheap-gate winners can create at least **8 KiB of additional stored-byte margin** versus direct level 19 while adding no more than **0.75 s** median complete verified creation on the same normalized Analytics tree.

The 8 KiB hurdle is deliberately larger than the current 232 B margin and larger than bookkeeping noise; it would create enough room to falsify one causal high-level-search reduction without instantly violating the v0.29 floor. The 0.75 s ceiling prevents buying margin with another global expensive encode.

## Referee contract

1. Use the same normalized `neutral_hostile_v1/04_analytics_and_database` tree and canonical-filesystem CMPNX5 research mechanism.
2. Freeze width=4 and the existing research frame marker. No width, level or threshold sweep.
3. For every Zstd pack request, obtain the direct level-19 payload exactly as the control does.
4. Run a cheap level-1 direct + BytePlane4 audition only to decide whether the pack is a structural candidate. The gate uses bytes only; path, extension, pack ordinal and workload identity are forbidden.
5. Only cheap-gate winners may receive an additional BytePlane4 level-19 encode. Choose it only when its fully framed bytes are strictly smaller than direct level 19.
6. Preserve exact inverse reconstruction and strong verification. Any decoded-byte drift is immediate failure.
7. Measure deterministic archive bytes, complete verified creation wall, process CPU/wall, RSS companion, number/raw bytes of cheap auditions and strong transformed auditions, selected strong transforms, and net payload saving.
8. Compare against a fresh direct-L19 control on the same normalized tree with rotated order and repeated rounds.
9. Reader/locality/auth/recovery/native claims remain unchanged/unearned; this is only a representation-margin referee.
10. Green CI means a valid receipt, not scientific victory.

## Decision

- **PASS:** candidate saves >=8,192 B versus direct L19, adds <=0.75 s median complete verified creation, exact reconstruction holds, and the gate remains path-blind. Use the earned margin for exactly one predeclared high-search ablation; do not promote BytePlane4 by itself.
- **FAIL:** retire BytePlane4 as a strong-frontier margin source. Do not sweep widths or gate thresholds. Escalate to another structural margin mechanism or a genuinely byte-preserving acceleration of high-effort search.

The frozen ONE Genesis result and `research/cmpct1` remain untouched. The only transferred lesson is cheap audition before expensive work.
