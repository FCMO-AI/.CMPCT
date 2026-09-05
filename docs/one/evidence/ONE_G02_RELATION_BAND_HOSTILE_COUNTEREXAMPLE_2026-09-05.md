# ONE-G0.2 relation-band nomination — hostile counterexample

**Status:** scoped negative / hostile-review correction  
**Experimental line:** `ONE-G0.2`  
**Mechanism affected:** fixed 16-probe / four-band relation nomination  
**Does not invalidate:** sparse pre-proof falsification, exact safe relation proof, generic ONE Law representation

## Evidence status

This counterexample was discovered during Hostile Reviewer work **after** the frozen ordinary band-nomination experiment had already advanced. It is therefore exploratory negative evidence, not a post-hoc rewrite of that immutable result and not a preregistered hostile experiment.

The ordinary result remains true in its tested regime: the band nominator reduced 276 possible pairs to four and retained the exact three productive relations across 4–256 KiB. This receipt narrows the claim boundary before the mechanism is productized.

## Counterexample construction

For each relation size in 4, 8, 16, 32, 64, 128 and 256 KiB:

1. create a deterministic random source;
2. create the normal `+1` shifted target (`b"X" + source[:-1]`), which the exact relation proof accepts;
3. compute the fixed sixteen nomination probe positions;
4. in each of the four four-byte bands, corrupt exactly one target byte at the `+1` matching position.

Only **four target bytes** are changed regardless of relation size.

An independent reimplementation of the frozen exact safe-proof rule still returns the productive `+1` relation at every tested size. The fixed band nominator returns **no candidate pair** at every tested size because each of its four `+1` bands has been deliberately broken.

Exploratory result matrix:

| relation size | exact proof | fixed-band nomination |
|---:|---|---|
| 4 KiB | accepts `+1` | misses |
| 8 KiB | accepts `+1` | misses |
| 16 KiB | accepts `+1` | misses |
| 32 KiB | accepts `+1` | misses |
| 64 KiB | accepts `+1` | misses |
| 128 KiB | accepts `+1` | misses |
| 256 KiB | accepts `+1` | misses |

## Causal interpretation

This is not a threshold problem. Any fixed finite sparse sample can be selectively damaged while leaving abundant exact relationship evidence elsewhere. Increasing the number of fixed probes only raises the attack/edit cost linearly; it does not provide structural completeness relative to the downstream proof.

The consequence is precise:

**fixed-band nomination may be a high-value fast path, but it cannot be ONE's only relation nominator if the campaign wants robust retention of exact-proof-supported relationships.**

Correctness is never threatened: missing a relation merely falls back to a less compressed generic ONE representation. The debt is density/opportunity, not byte-exact reconstruction.

## Reopening / repair predicate

Do not tune the band threshold around this counterexample. A superseding design must add a causally different evidence path. Promising directions are:

- nomination derived from the same exact-block evidence class that makes the safe proof succeed;
- content-derived/winnowed relation anchors shared with the existing fused observer rather than fixed public coordinates;
- a two-tier design where cheap fixed bands remain the common-case path and a bounded secondary path activates from independent evidence, with the complete extra compute/state bill charged.

Any repair must preserve the ordinary fast-path economics already measured while explicitly attacking deterministic probe evasion, collision-heavy false patterns, large version families, tiny-file carrying cost and bounded index state.

## Current decision

**Keep fixed bands as an opportunistic fast nominator; reject them as a complete standalone relation-discovery mechanism.**

The next scientific experiment should compare a proof-derived or independently triggered secondary nomination path against this hostile construction and ordinary controls. Success is not merely recovering these seven hand-built rows: it must show a general causal reason the secondary path sees evidence that fixed bands can miss, while retaining bounded writer cost.
