# ONE-G0.2 — local Gear certificate native carrying-cost result

Date: 2026-09-05
Experimental line: ONE-G0.2
Decision: **retire unconditional local Gear certificate maintenance**

## Exact-source receipt

- source: `f211fbd8388c5b6f637f3b0c9363eb2ccc2360cc`
- workflow: `33971465170`
- job: `101320616350`
- artifact: `9971046571`
- artifact digest: `sha256:12ae9a5a0f955bf99422943b2bca4f0c2f7772dd97f51b9a8647b865b9cff537`
- semantic/hostile suite: passed before result-bearing benchmark
- native witness mismatches versus Python reference: **0**

The workflow is red because the preregistered benchmark intentionally exits nonzero when the frozen efficiency gate fails. Artifact preservation succeeded.

## Frozen gate result

The structurally successful 32-byte rolling/bottom-8 certificate does **not** earn unconditional native carrying cost.

Median certificate/baseline ratio over the five frozen large gate controls was:

**2.2941x**

Per large case:

| case | rolling / baseline | certificate / baseline | certificate / no-reuse |
| --- | ---: | ---: | ---: |
| random 1 MiB | 1.3364x | 2.2941x | 0.9943x |
| compressed-like ~1 MiB | 1.3296x | 2.2991x | 0.9957x |
| repeated 1 MiB | 1.3335x | 2.2896x | 0.9933x |
| shifted/version 1 MiB | 1.3343x | 2.2973x | 0.9955x |
| zeros 1 MiB | 1.2557x | 1.8424x | 0.9255x |
| alternating hostile 1 MiB | 1.3381x | 2.3370x | 1.0008x |

Tiny controls were worse: 4 KiB was 2.4791x and 64 B was 3.5791x baseline elapsed.

The frozen promotion limit was <=1.20x median across the five large gate controls, <=1.25x on random/compressed controls, and <=1.35x on every 1 MiB case. The candidate misses those limits by a wide margin.

## Causal decomposition

This is not a semantic failure. Native witnesses exactly equal the Python reference everywhere, and the already-frozen structural validation remains valid.

The cost decomposition is more useful than the binary failure:

1. **Rolling content-local Gear state alone costs about +26% to +34% on the large controls.** It adds one outgoing-byte read and one extra Gear lookup for almost every input byte after the 32-byte warmup.
2. **Complete certificate maintenance raises typical large-case cost to about +129% to +134%.**
3. Heap replacement itself is rare. Across 16 internal 1 MiB repetitions, replacements were only 1,376 (random), 1,360 (compressed), 832 (repeated), and 1,696 (shifted/version). The dominant extra bill is therefore not heap rebalancing; it is asking the bottom-8 admission question for essentially every 32-byte rolling window.
4. The fused/no-reuse diagnostic is near parity on entropy-dense cases. Incoming lookup reuse is correct engineering but cannot rescue a mechanism whose dominant cost is elsewhere.

The result therefore falsifies the **unconditional every-byte rolling + every-window bottom-8 maintenance shape**, not the need for complementary content-local evidence.

## Hostile Reviewer conclusion

Do not tune the 32-byte window, eight-witness count, or timing thresholds around this failure. The structural result established that a content-local certificate covers real blind spots in prefix-history observation, but this implementation spends too much compute continuously even when useful relation evidence is absent.

The next mechanism should convert that evidence from a continuously maintained signal into an **opportunity-gated or sparse bounded-shift certificate**. In particular, the current exact relation family only tests shifts `{-2,-1,+1,+2}`. A candidate may exploit that bounded discovery fact on the writer side without changing ONE reader semantics: sparse phase-aligned short-word witnesses can cover those shifts without maintaining a rolling hash at every byte. Exact relation proof remains authoritative, so short witness collisions can only cause extra writer work, never an incorrect Law.

## Claim boundary

- no new stored-byte claim;
- no reader-speed claim;
- no v0.29 or deferred-v0.30 superiority claim;
- no reader-visible opcode or legacy fallback added;
- 136-byte state size remains a structural fact of the retired candidate, not a reason to retain it.

The useful result is negative: **content-local evidence is still needed, but it must be made sparse enough that information yield repays discovery compute.**