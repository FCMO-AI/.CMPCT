# ONE-G0.2 — Event-Driven Dense Selection Negative Receipt

**Experimental line:** `ONE-G0.2`  
**Primary branch:** `research/cmpct1`  
**Result-bearing source:** `4c906a13ceede4599d3052f22c3ee45058da7432`  
**Workflow:** `CMPCT1 ONE-G0.2 minimizer maintenance evidence` run `33939806976`  
**Job:** `101234876826`  
**Artifact:** `9961421301`  
**Artifact digest:** `sha256:923b6b6e0f69a9f9992c414090ca845bd181f60370f9666d205b73c8f1278aa6`

## Tested hypothesis

Keep the promoted dense prefix/suffix state and exact rightmost-minimum semantics, but avoid recomputing the selected minimum on positions where no candidate can change. The instrument tracked prefix/suffix/middle candidate changes and recomputed exact selection only on events.

The intended causal claim was that per-position selection comparison was a material owner of remaining elapsed time and could be removed without trading state or semantics.

The experiment and its decision law were frozen before the result-bearing execution. The replay above did not alter the old grammar, thresholds, cases or interpretation.

## Mechanical effect

The mechanism substantially reduced the nominal work it targeted on mature inputs:

| case | selection recomputes / windows | suffix candidate loads / windows |
|---|---:|---:|
| random 1 MiB | 1.4599% | 0.7243% |
| zlib-random ~1 MiB | 1.4703% | 0.7353% |
| exact pair ~1 MiB | 1.4547% | 0.7231% |
| shifted pair +1 B | 1.4554% | 0.7236% |
| repeated 64 KiB basis, 1 MiB | 1.3941% | 0.6521% |

This is enough work elimination that a failure cannot reasonably be explained by “the event filter did not filter enough events.”

## Elapsed result

Event-driven / regular dense-tail elapsed ratios:

| case | ratio | interpretation |
|---|---:|---|
| below enablement, 4,159 B | **1.7294x** | severe startup regression |
| at enablement, 4,160 B | 1.0037x | neutral/slower |
| random 1 MiB | 1.0275x | slower |
| zlib-random ~1 MiB | **1.0576x** | slower; crosses 1.05 boundary |
| exact pair ~1 MiB | 1.0468x | slower |
| shifted pair +1 B | 1.0305x | slower |
| repeated 64 KiB basis, 1 MiB | 0.9700x | isolated improvement |
| hostile shifted-starvation 16,385 B | 1.0160x | slower |

**Decision:** `reject_event_driven_dense_maintenance`.

## Causal interpretation

Regular dense candidate comparisons are cheap enough that replacing them with event state, event predicates and irregular control flow can cost more than the comparisons eliminated. Event count is therefore not a sufficient proxy for elapsed compute.

This negative is specifically about the tested event bookkeeping over the current dense four-segment family. It is not a universal claim that change-driven algorithms are always slower.

## Reopening predicate

Do not reopen this family merely by reducing the already-small event ratio. Reopening requires new causal evidence that materially removes or fuses the exported event-state/control cost — for example, a compiler/codegen or vectorized formulation that preserves regular execution while exploiting event sparsity — and must be tested under a new immutable gate.

## Claim boundary

This is encoder-discovery negative evidence only. It says nothing about stored bytes, wire format, reader semantics, product speed, or v0.29/v0.30 superiority.
