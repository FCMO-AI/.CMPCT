# r24 streaming-finalize RSS v1 result — measured, but invalid for productization attribution

Status: **PRESERVED LEGACY DIAGNOSTIC / INVALID FOR PRODUCTIZATION PROMOTION / NO RELEASE CREDIT**

## Authority and why this record exists

The repaired-r24 replay of the historical v1 streaming-finalize RSS oracle completed its measurement on exact source `94aaf394ddc3af5169ba0ac755e3e9a90c3e466a` in GitHub Actions run `33647754885`, substantive job `100306828709`, artifact id `9853705520` (`v030-r24-streaming-finalize-rss-94aaf394ddc3af5169ba0ac755e3e9a90c3e466a`). The measurement itself produced an internally valid exact-byte A/B under schema `cmpct-v030-r24-streaming-finalize-rss-v1`.

It **must not be interpreted as productization evidence** because post-result custody review found that `benchmarks/v030_r24_streaming_finalize_rss_oracle.py` embeds a legacy duplicate `StreamingFinalizeBuilder` rather than measuring the reusable productization class in `experiments.entropygraph_v030_r24_streaming_finalize` that the workflow separately regression-tested.

The semantic difference is material rather than cosmetic:

- reusable productization owner: `SPOOL_MEMORY_BYTES = 1 MiB`, `MAX_IN_FLIGHT_FACTOR = 1`, and raw/Deflate candidate buffers are released inside the encoding worker after codec competition;
- v1 embedded owner: `MAX_IN_FLIGHT_FACTOR = 2`, with candidate raw/Deflate release deferred until ordered parent consumption.

Therefore v1 answers a legacy-prototype memory-shape question. It does not prove the reusable implementation has the measured RSS behavior.

## Raw v1 measurement

All shipping/streaming comparisons preserved exact archive byte count, physical SHA-256 and verified logical tree identity. No selector, grammar, r24 policy, integrity, locality/decode-unit threshold or release rule changed.

| Target / operation | shipping median incremental peak RSS | v1 streaming median incremental peak RSS | streaming / shipping RSS | streaming / shipping wall |
|---|---:|---:|---:|---:|
| Shifted r24 | 117,642 KiB | 0 KiB | 0.0000x* | 0.9138x |
| Shifted full product | 248,230 KiB | 179,124 KiB | **0.721605x** | **0.932313x** |
| ML r24 | 21,866 KiB | 0 KiB | 0.0000x* | 1.0417x |
| ML full product | 86,144 KiB | 67,282 KiB | **0.781041x** | **1.003397x** |

`*` The zero is baseline-subtracted `ru_maxrss`, not proof of zero allocation. Fresh-process operation high-water remains the meaningful memory boundary; subtraction is diagnostic only.

Under v1's preregistered thresholds the artifact reported `promotion_signal = true`, because Shifted full-product incremental RSS reached 0.721605x of shipping with no >1.05x complete-product wall regression and exact bytes/tree. **That terminal label is not transferable to the reusable semantic owner.**

The workflow later failed its CI-topology self-check because its preserved-receipt concurrency group was not exact-SHA keyed. That topology failure is separate from the semantic-owner invalidity; even a topology-clean replay of v1 would still measure the wrong implementation.

## Causal interpretation

The v1 result is useful only as **mechanism-supporting headroom evidence**: bounding compressed-record/final-archive materialization and releasing candidate payload state earlier can plausibly remove a material portion of r24/full-product RSS without changing archive bytes. It is not sufficient evidence to wire the reusable finalizer into shipping.

This record intentionally preserves the attractive positive number rather than deleting it. The risk is precisely that an expiring artifact or workflow-level green could otherwise be rediscovered later and misquoted as proof for the current reusable class.

## Superseding experiment

`docs/v030-rnd/R25_R24_STREAMING_FINALIZE_RSS_V2_PREREG.md` freezes the repaired experiment before observation. V2:

- invokes the exact reusable `experiments.entropygraph_v030_r24_streaming_finalize.StreamingFinalizeBuilder` in every streaming worker;
- proves the owner module and module SHA in the receipt;
- freezes `SPOOL_MEMORY_BYTES = 1 MiB` and `MAX_IN_FLIGHT_FACTOR = 1`;
- retains the same two targets, AB/BA order, two repetitions, exact identity law and v1 decision thresholds;
- grants no release credit.

Only the v2 result may support or retire this reusable implementation as the next Forge productization candidate.

## Reopening / use law

Do not use v1 to justify a Builder change, release claim or threshold change. Reopen its exact legacy implementation only if a future question specifically concerns that old factor-2/deferred-release design; otherwise use v2 or a later explicitly superseding frozen experiment.
