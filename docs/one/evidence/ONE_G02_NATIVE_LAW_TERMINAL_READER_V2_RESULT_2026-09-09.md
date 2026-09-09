# ONE-G0.2 Native Law Terminal Reader V2 — result

Date: 2026-09-09
Experimental version: ONE-G0.2
Verdict: **ADVANCE_NATIVE_LAW_TERMINAL_READER_V2**

## Exact hosted authority

- source SHA: `48a04c660818b9a325c6b03a0ffdfd800642c35d`
- workflow: `cmpct1-one-g02-native-law-terminal-reader-v2`
- run: `34377412685`
- job: `102553602812`
- artifact: `10114660726`
- artifact digest: `sha256:a4fa19d8b7ef2aa926e3437adfd14fd3dd1fa10d7d995308156ba6f3006cbd49`
- artifact name: `one-g02-native-law-terminal-reader-v2-48a04c660818b9a325c6b03a0ffdfd800642c35d`

The hosted lane checked out the exact source SHA, bound the unchanged V1 thresholds, passed inherited fused/native semantic and hostile tests, ran the frozen V2 falsifier, and retained its JSON result.

## Mission lock and disproof test

Hypothesis: V1's native generic add8/xor terminal execution can become an admissible whole-root reader strategy if the two identified carrying costs are removed without changing representation or integrity semantics: no-Law Programs bypass native planning, and eligible roots are written directly into one fresh final immutable bytes allocation before mandatory SHA-256 verification.

Disproof: HOLD if any semantic/resource/fail-closed control diverges, if median eligible native/reference CPU exceeds 0.75x, any eligible row exceeds 1.00x, median control candidate/reference CPU exceeds 1.10x, any control exceeds 1.25x, median eligible modeled traffic/reference VM work exceeds 0.75x, or native peak temporary bytes exceed one requested root length.

## Hosted result

All frozen gates passed.

- semantic parity: **PASS on all 21 performance rows plus hostile semantics**
- median eligible native/reference CPU: **0.01165033595932275x**
- worst eligible native/reference CPU: **0.019931932834506394x**
- median control candidate/reference CPU: **1.0071253954775798x**
- worst control candidate/reference CPU: **1.0347903997559906x**
- median eligible modeled traffic/reference VM work: **0.5500324291328068x**
- peak temporary bytes: **<= one requested root length on every eligible row**

At the largest frozen scale (512 KiB per version; 1 MiB requested root):

| family | reference CPU | V2 CPU | V2/reference | modeled traffic/reference work | V2 peak temp |
|---|---:|---:|---:|---:|---:|
| add8 | 165.152 ms | 1.036 ms | 0.006274x | 0.600000x | 512 KiB |
| xor | 55.824 ms | 0.938 ms | 0.016798x | 0.600000x | 512 KiB |
| add8 + crack | 164.995 ms | 0.971 ms | 0.005887x | 0.500004x | 512 KiB |
| xor + crack | 55.907 ms | 0.849 ms | 0.015179x | 0.500004x | 512 KiB |

Largest-scale controls remained near incumbent cost:

- literal: **1.001870x CPU**
- fill: **1.001169x CPU**
- Surprise/Fill concat: **1.007125x CPU**

The worst control over all scales was the 32 KiB-per-version literal row at **1.034790x**.

Preparation remains visible rather than hidden. At the largest scale eligible rows required roughly **0.401–0.710 ms** of preparation CPU and packed **1,048,576 source-plan bytes**. The hot replay numbers above therefore do not establish zero-cost planning; they establish that the native terminal execution itself is no longer the reader bottleneck.

## Why this is an ADVANCE

V1's principle was already strong on Law cones but scientifically unacceptable as a preferred reader strategy because ordinary no-Law inputs paid candidate routing cost and eligible execution copied the whole finished root once more to freeze it. V2 changes exactly those causal costs and leaves the gates untouched.

The result is stronger than a threshold pass: eligible Law roots are approximately 50–160x faster than the Python reference evaluator in the frozen matrix while no-Law controls remain within about 0.3–3.5% of reference. The generic reader still interprets ordinary ONE Law/Surprise structure; no add8/xor-specific stored codec or reader discovery was introduced.

## Scope and limits

This promotion is **whole-root only**. It does not grant selective-range authority to the native compiler. Authenticated partial-root/range reconstruction remains on the incumbent evaluator until separately proven.

This result also does not erase preparation cost, packed source-plan memory traffic, or the cost of building the Program. Those remain charged creation/reader-front-end work and are the next places to look for marginal-efficiency gains.

The benchmark deliberately uses the V1 21-row matrix. It is mechanism-level causal evidence, not the Genesis same-input 15-workload comparison against frozen v0.29 and deferred v0.30.

## Hostile-review conclusion

The strongest remaining criticism is that the hot native execution ratios are so small that future optimization should not chase this kernel further. At the 1 MiB root scale, preparation is already of the same order as native execution, so the bottleneck has moved outward to planning/source packing, selective-range support, and generic cone scheduling.

Do not add Law-family reader shortcuts. Rehabilitate the remaining reader cost by reducing generic preparation/data movement and by proving bounded native execution for requested cones/ranges behind the same fail-closed semantics.

## Next decisive action

Preregister a **selective native Law cone/range** falsifier that reuses the same generic Program semantics and refuses unsupported topology. It should require exact range parity, authenticated-root semantics, unchanged resource rejection, bounded source amplification, and a strict CPU/traffic advantage over the incumbent range evaluator. It must not materialize a whole root simply to answer a small range.

In parallel, measure source-plan preparation as a fraction of total reader CPU across current temporal/relation Programs. If preparation dominates, attack common planning/source packing once rather than adding another operation-specific fast path.
