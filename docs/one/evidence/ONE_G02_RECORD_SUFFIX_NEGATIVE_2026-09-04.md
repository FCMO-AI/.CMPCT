# ONE-G0.2 — Record-minimum suffix change-point negative receipt

**Status:** exact-head scoped negative evidence  
**Source:** `0c204c815c4bb4179ba04fa0049a1e6ac0d3e572`  
**Workflow:** `33938622782`  
**Job:** `101231422797` (`semantic-evidence`)  
**Artifact:** `9961088338`, `one-genesis-0c204c815c4bb4179ba04fa0049a1e6ac0d3e572`  
**Artifact digest:** `sha256:edd023c6bcf81d943d9e6afc04ad1996e23d2d0c9b241c52891eec8a8cb3d7ab`  
**Instrument:** `benchmarks/one/one_g02_minimizer_record_suffix_ab.py`  
**Schema:** `cmpct-one-g02-minimizer-record-suffix-ab-v1`

## Falsifiable hypothesis

The promoted tail-aware four-segment minimizer still materializes one dense suffix-minimum `(value, offset)` entry per derived Gear state in each live completed block. The suffix-minimum function changes only when a new strict record minimum appears while scanning right-to-left. Because future suffix queries advance monotonically, a sparse change-point stream can be consumed with a monotone cursor and no source rescan.

The preregistered prediction was that removing almost all dense suffix writes would make the sparse record layout at least 15% faster than the promoted dense tail-aware layout on every large case, with no tested case more than 5% slower, no semantic difference, no source rescans, <=1.01x reserved state, and <=10% record writes relative to dense suffix entries on every large case.

Any violation retired the candidate. No threshold was mutable after result-bearing execution.

## Result

`decision = retire_record_suffix_candidate`

All 50 ONE tests passed before the A/B, and the record-suffix implementation matched the independent Python deque oracle exactly on every frozen case: emitted anchor trace, final Gear state and considered-position count were identical. There were zero source-byte rescans.

The proposed causal mechanism **did occur**: large-case record writes were only about 0.65%–0.74% of dense suffix entries, eliminating roughly 99.3% of those writes. The largest observed record set in a 1,024-state block was 17 entries. Reserved-state ratio was 1.0025x the promoted dense tail-aware model, inside the 1.01x bound.

But runtime moved in the wrong direction:

| Case | sparse record / dense tail elapsed | record writes / dense entries | max records/block |
| --- | ---: | ---: | ---: |
| below enablement 4,159 B | **1.0923x** | 0% | 0 |
| at enablement 4,160 B | **0.9387x** | 0.49% | 5 |
| random 1 MiB | **1.2535x** | 0.72% | 15 |
| zlib-random ~1 MiB | **1.2835x** | 0.74% | 17 |
| exact pair 512 KiB + 512 KiB | **1.3160x** | 0.72% | 17 |
| shifted pair +1 B insertion | **1.2683x** | 0.72% | 17 |
| repeated 64 KiB basis, 1 MiB | **1.2646x** | 0.65% | 14 |
| shifted-starvation hostile 16,385 B | **1.2107x** | 0.90% | 15 |

Thus every large case is **25.35%–31.60% slower**, despite removing about 99.3% of suffix-entry writes.

## Causal interpretation

Dense suffix write traffic is not the primary remaining compute owner in this maintenance family. The dense layout's direct offset-indexed query is extremely predictable. Replacing it with a sparse record stream introduces cursor checks, change-point advancement/control flow and extra dependency chains; those costs dominate the write savings on the tested hosted CPU.

This is useful negative evidence because it separates *amount of memory written* from *critical-path cost*. Fewer bytes touched is not automatically faster when the alternative makes the hot query loop less regular.

The successful 4,160-byte row does not rescue the family: it is a startup special case and the preregistration requires material gain on every large case plus no material regression anywhere.

## Decision and reopening predicate

Retire sparse record-minimum suffix change points as the current answer to segmented-minimum compute debt. Do not tune its thresholds, record cap or benchmark cases to manufacture a win.

Reopen only with new causal evidence that eliminates the sparse-query control/dependency cost itself—for example, a representation that preserves direct/vectorizable lookup while reducing dense construction work, or a measured hardware/vectorization result showing a different bottleneck. Merely reducing record count further is not new evidence; the tested candidate already removed about 99.3% of writes and still lost badly.

The promoted tail-aware dense four-segment maintenance remains the current encoder-discovery baseline. This receipt makes no stored-byte, wire, reader, product-speed, v0.29, v0.30 or full-CMPCT1 superiority claim.
