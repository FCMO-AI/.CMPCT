# O188b — held-out order and phase controls: **guard family falsified as generic replacement**

Date: 2026-10-26 UTC. Prospective prediction committed *before this instrument* in `docs/v031-research/2026-10-26-o188b-heldout-order-prereg.md`, commit `9664bf5427b12e83507233c06241cec6e082ada6`. New instrument `research/o188b_heldout_order_oracle.py` committed at `5fa76221d6e01d7a87bcc6aef484e5704c952507`. The O188 original simulator and canonical O169 product source are unchanged.

**Evidence tier:** deterministic synthetic cache-policy simulation, NOT genuine Reader, RSS, wall/CPU, archive bytes or release. Local source-equivalent stdlib execution completed with all frozen assertions. Original local raw JSON SHA-256 `f52662664a5160a072cfe125556534b3de910256b4501c03c14f0a5ca1abd890`; **do not treat this hash as the hosted artifact until matched to an actual exact-head CI run**. Hosted pipeline `.github/workflows/v031-o188b-cache-heldout.yml` preserves raw JSON and independent audit.

## Decisive hostile results (cache hits only)

| Prospective control | LRU 64MiB | Fixed-pin 64MiB | Guarded 48/16 | Strongest discriminator |
|---|---:|---:|---:|---|
| Forward 96 then reverse 96, reverse-pass hits | **64** | **64** | **16** | Guard suffers 48 *more* misses than ordinary LRU on identical exact member set |
| After A96×2, shift to B48, B2 hits | **48** | **0** | **0** | LRU adapts immediately when new working set fits |
| B3 hits | **48** | **0** | **17** | Guard requires additional misses and resets |
| B4 hits | **48** | **0** | **48** | Eventually guard adapts; fixed-pin never does |
| 64-item fully fitted working set, pass2 hits | **64** | **64** | **64** | Benign control not regressed |

Detailed phase counts for A96×2 → B48×5:
- LRU: A1=0 A2=0 B1=0 B2=48 B3=48 B4=48 B5=48.
- Fixed-pin: A1=0 A2=64 B1=0 B2=0 B3=0 B4=0 B5=0.
- Guard: A1=0 A2=48 B1=0 B2=0 B3=17 B4=48 B5=48, one reset.

Reverse-scan guard causal failure: after first ascending 96, its protected 0–47 cohort has not been reused and the miss-reset counter is 96. During the reverse pass, only the most recent 16 probationary objects yield hits. Thirty-two subsequent non-protected misses reach the predeclared reset threshold (128) *before* the scan reaches the protected first 48. Those values are dropped; guard achieves only 16 reverse hits whereas ordinary LRU achieves 64.

**Decision:** `GUARD_48_16_FALSIFIED_AS_GENERIC_READER_REPLACEMENT`. The original O188 narrower existence result remains: online bounded admission can avoid O175's *forward-direction* LRU zero-hit case. But this fixed protected/probation/reset mechanism is not a product-ready win and is strictly dominated by ordinary LRU on the reverse and early phase-fit controls examined. Retire the **specific 48/16/128 policy candidate**, not the entire scan-resistant admission question. Its reset heuristic is particularly fragile and has unnecessary work under cold scans.

## Highest-value next experiment

Stop local threshold gardening (varying 48/16 or 128 cannot provide adequate generalization evidence). Before a new product algorithm, select a causally different bounded admission family with *reuse-informed priority* (e.g. historical 2Q or TinyLFU-class, with charged metadata/counter/lock work), AND require early phase-fit adaptation as an explicit acceptance criterion. Also compare to simply optimizing repeat RAW decode/no caching, given O175's +36.97ms second-pass absolute delta and modest CPU debt. Candidate must be measured on the **same actual O175 authenticated archive** under forward and reverse orders, plus separately authenticated VZIP mixed and working-set shift, using actual Reader, source custody, repeated wall/CPU/RSS and no semantic changes.

The false universal story to avoid: 96MiB scanned against 64MiB automatically causes zero reuse. **Access order changes that conclusion even for unchanged LRU.** O175's negative is valid *for its forward repeated scan*, not for every scan.

## Discovery and concurrency

One counterfactual discriminator is identifiable prospectively: after seeing directional scan thrash, reverse the SAME identifiers and demand a stronger simple LRU control before designing caching policy. One episode cannot justify an across-project discovery-policy edit. No changes to `docs/discovery/STATE.json`, release law, canonical Reader or owners #506/#509/#510/#516. Next activation should not implement this failed guard merely because it passed the first trace.
