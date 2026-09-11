# ONE-G0.2 nomination-index probe attribution — preregistration

Date: 2026-09-06
Experimental line: `ONE-G0.2`
Authoritative branch: `research/cmpct1`
Status: frozen before result-bearing execution

## Mission Lock

The fused native nominator remains materially slower than selector-only even after removing the redundant second scan. Its two first-witness structures both use linear lookup: a 64-entry local FIFO queried every 64 input bytes and a bounded global first-witness index queried only when a new minimizer anchor is emitted.

Before inventing a new lookup structure, quantify exactly where key-comparison work occurs and which layer actually contributes cross-object exact nominations under the existing policy.

## Falsifiable hypothesis

On mature inputs, the small but frequently queried local FIFO contributes a disproportionate share of first-witness key comparisons relative to its incremental cross-object nomination yield, while the global index is larger but queried much less often.

### Disproof

The hypothesis is rejected if either:

- global lookup comparisons exceed local comparisons on a majority of mature rows; or
- the local layer provides >=50% of cross-object exact nomination events on a majority of productive mature rows.

A rejected hypothesis redirects optimization toward the global index or proof traffic rather than local lookup.

## Frozen envelope

Replay exactly the 36 mature rows used by the carrying-cost gate:

- relation sizes 64 KiB and 256 KiB;
- seeds 7, 29, 53;
- `shift_plus1`, `damage_quarter`, `fragmented_every96`, `hostile_fixed_bands`, `fragmented_every32`, `independent_random`.

Use the existing Python reference observer semantics, but replace dictionary lookups with an explicit ordered linear first-witness model that is required to reproduce the same final cross-audition/exact counts. Instrument:

- local lookup events and key comparisons;
- global lookup events and key comparisons;
- local/global cross auditions and exact nominations at the point each layer supplies the prior witness;
- input bytes;
- comparisons per input byte;
- peak local/global entries.

## Acceptance / interpretation law

The diagnostic has authority only if its externally visible total cross-audition/exact counts match `_cross_object_reuse_nominations()` on every row.

Then classify:

- `local_lookup_primary_owner_candidate` if local comparisons > global comparisons on >=75% of rows and local exact share <50% on >=75% of productive rows;
- `global_lookup_primary_owner_candidate` under the symmetric condition;
- `mixed_lookup_owner` otherwise.

This is causal attribution, not speed authority. A comparison count is not a CPU cycle.

## Hostile Reviewer

Do not remove a low-yield layer merely because it is expensive: one unique nomination can be strategically important, especially in small/hostile regimes. The next Builder should first change lookup cost while preserving semantics. Gating or removing a layer requires a separate recall/economics experiment over the hostile envelope.
