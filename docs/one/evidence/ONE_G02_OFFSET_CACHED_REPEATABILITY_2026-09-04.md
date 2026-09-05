# ONE-G0.2 — Cached suffix recurrence paired repeatability

**Branch:** `research/cmpct1`  
**Exact result-bearing source:** `a0f55d2c2ea63ccf82655a588cd27fc3bf9f3aa5`  
**Workflow run:** `33941081206`  
**Result-bearing job:** `101238515778`  
**Artifact:** `9961836739`  
**Artifact SHA-256:** `1dba2bb0188111bffc7e045d785d683fc41926336631a978c28cc58d81fe294a`  
**Experimental version:** `ONE-G0.2`

## Question

The earlier exact-head cached-recurrence A/B halved modeled suffix-build derived-state reads and reported a 6.6--15.6% improvement across all large cases, but its single-batch timing order was vulnerable to runner drift. Its immutable promotion gate was also blocked by a 4,159-byte no-suffix row. This independently frozen companion asks whether the apparent speed effect survives warm-started paired A-B-B-A measurement.

It does not rewrite any earlier result.

## Exact execution

The workflow checked out and bound exact source `a0f55d2c...`, passed **50/50 ONE tests**, reran the immutable single-batch experiment, then ran nine paired A-B-B-A rounds per case. Small inputs were batched 128 calls per timed sample; allocator/call work remained charged.

The same-run single-batch replay itself demonstrated the instability being tested: on this runner it changed from the prior result's `cached_offset_recurrence_inconclusive` to **`promote_cached_offset_recurrence`**, with median-large cached/offset `0.897500x`, worst-large `0.906660x`, worst-any `0.961593x`, and the same `0.500244x` modeled derived-read ratio.

That replay does **not** supersede the earlier immutable result. It is evidence that all-A/all-B ordering can move the promotion label for unchanged code.

## Paired result

**Enabled decision:** `timing_uncertain_enabled`  
**Below-enablement decision:** `unenabled_timing_not_repeatably_negative`

Paired cached/old-offset medians:

| case | median | p10 | p90 |
|---|---:|---:|---:|
| below enablement, 4,159 B | 0.99924x | 0.99241x | 1.01024x |
| at enablement, 4,160 B | 1.00190x | 0.99323x | 1.01445x |
| random 1 MiB | 1.00213x | 0.99761x | 1.00874x |
| zlib-random ~1 MiB | 1.00807x | 0.98599x | 1.01419x |
| exact pair ~1 MiB | 0.99675x | 0.99459x | 1.00605x |
| shifted pair +1 B | 1.00135x | 0.99923x | 1.01333x |
| repeated 64 KiB basis, 1 MiB | 1.00142x | 0.99547x | 1.00649x |
| hostile shifted 16,385 B | 1.00191x | 0.99597x | 1.00493x |

The paired large-case medians cluster around parity, roughly **0.997x--1.008x**, not around the 0.84--0.93x single-batch signal. The 4,159-byte row likewise centers at parity rather than repeating the earlier 1.19x slowdown.

## Scientific interpretation

The modeled C-level intervention is real: cached recurrence removes roughly half the explicitly counted derived-state reads while preserving exact semantics, state, lifecycle and query work. But this instrument shows that those modeled reads are **not presently supported as a material elapsed-time owner** under order-neutral paired measurement.

The correct conclusion is therefore not to promote the cached recurrence for speed and not to call the earlier large gain real. The strongest explanation is that single-batch timing order/frequency drift dominated that apparent gain, or that the compiler/cache hierarchy already makes the eliminated logical rereads effectively free enough that C-level read counts overstate physical memory cost. Static generated-code inspection can discriminate those explanations.

## Scoped negative constraint

Do not reopen **"reduce suffix elapsed by merely caching `block_values[next_argmin]` in the C recurrence"** as a primary speed strategy under the same compiler, 1,024-state segment layout, current exact selector and tested input regime without new evidence of changed generated code or physical cache/memory behavior.

This does not retire the 41,056-byte offset-only representation. Its **16.63% state saving** remains real. It only rejects the claim that the particular redundant logical reread is a proven speed owner.

## Next decisive action

Inspect same-compiler generated code for old offset-only versus cached recurrence to determine whether the extra logical reread survives optimization as a distinct machine memory operation. Then return to the post-counter residual ladder and attack an owner that is both causally present in generated work and repeatably visible in paired elapsed time. Do not choose a size dispatch threshold from noisy single-batch crossover data.

No Law, wire, reader, stored-byte, product-speed, v0.29, v0.30, release or public-superiority authority is created.
