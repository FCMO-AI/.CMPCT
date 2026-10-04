# v0.30 R4 selective-final-effort result

**Status:** CLOSED / NEGATIVE RESULT  
**Authority branch:** `agent/v030-authoritative-integration`  
**Diagnostic source head:** `c0484b50b2f596ec626e28ff32cdb2e764a93c8e`  
**Workflow run:** `34632047761`  
**Primary job:** `103371008799`  
**Artifact:** `10275959851` (`v030-r4-selective-final-effort-*`)  
**Shipping credit:** none  

## Mission lock

The Analytics v0.29 effort frontier established a hard tradeoff: global level-19 final compression nearly reaches the inherited v0.29 byte floor, but creation time is far above ZIP and therefore destroys the main creation-compute advantage that justified the v0.30 pivot. The R4 question was whether high effort is sparse enough to gate at final physical compression units while freezing the already-measured level-1 representation/discovery decisions.

Falsifiable hypothesis:

1. for both Office and Analytics, the efficiency-ranked top quarter of positive final units captures at least 80% of all recoverable level-1 -> level-19 bytes; and
2. an oracle minimal promotion set can close the accepted v0.29 byte floor while preserving complete verified creation time below ZIP deflate9.

The diagnostic is deliberately stronger than a proposed shipping policy: it is allowed to know the realized marginal savings for every final unit. If even this oracle cannot produce a useful joint size/time point, a workload-blind cheap selector cannot rescue the same primitive.

## Contract

The experiment changed no production selector, product format, comparator, accepted v0.29 floor, canonical filesystem semantics, integrity rule, or ONE evidence. It freezes v0.25 structural/discovery decisions at the level-1 probe and varies only the final compression effort on the resulting bounded units. Every measured candidate is strong-verified and fully restored to the canonical user-tree identity. Workload identity is never available to a production policy; the workload-local oracle exists only as a falsifier and receives no release credit.

## Results

| Workload | v0.29 floor | Level-1 fixed representation | Gap | Positive units | Total possible L1->L19 saving | Efficiency-ranked top-quarter share | All-positive-high | Complete verified create | ZIP create | Result |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| Office | 5,954,026 B | 6,428,050 B | +474,024 B | 10 | 472,515 B | **84.67%** | 5,955,535 B | 0.5068 s | 0.3897 s | fails size and time |
| Analytics | 6,135,172 B | 7,096,243 B | +961,071 B | 50 | 960,462 B | **41.94%** | 6,135,781 B | 8.7477 s | 1.3637 s | diffuse; fails size and time |
| Developer control | 744,337 B | 891,809 B | +147,472 B | 17 | 81,491 B | **84.12%** | 810,318 B | 1.1973 s | 0.1735 s | insufficient and far slower |

The aggregate hypothesis is **false**.

### Office

Office does show sparse opportunity in the narrow sense: the efficiency-ranked top 3 of 10 positive units account for about 84.7% of the recoverable final-effort bytes. However, the primitive has a stronger lower-bound problem: promoting **every** positive unit recovers only 472,515 B against a 474,024 B gap. The resulting 5,955,535 B artifact remains 1,509 B above v0.29, and its complete verified creation time is already about 30% slower than ZIP. There is therefore no oracle subset of these final calls that can satisfy the joint target.

### Analytics

Analytics decisively rejects the sparse-effort hypothesis. The efficiency-ranked top 13 of 50 positive units recover only about 41.9% of possible savings. The high-effort benefit is spread broadly across the representation. Promoting all positive units gets to 6,135,781 B, still 609 B above v0.29, while complete verified creation rises to 8.75 s, about 6.4x ZIP. A cheap selector cannot turn a diffuse almost-global need for high effort into a fast path.

### Developer control

The control also rejects this primitive as a general route. Only 81,491 B are recoverable through these final calls against a 147,472 B gap, and all-positive-high creation is roughly 6.9x ZIP. This is useful because it prevents the Office concentration result from being over-generalized into a selector story.

## Causal interpretation

The result closes **selective final high effort on the frozen level-1 representation** as the primary R4 route.

The failure is not a threshold failure. Office is bounded by insufficient total recoverable bytes under the frozen representation; Analytics is additionally bounded by diffuse high-effort demand and prohibitive creation work. More effort levels, promotion percentages, or workload-specific thresholds would be tuning inside a falsified family.

This also reconciles two earlier receipts:

- canonical filesystem tax is tiny relative to the pre-tax Office/Analytics gaps, so weakening filesystem semantics cannot solve the problem;
- the exact v0.25 federated representation is already productized in the closed product-floor family, so merely reopening stream federation/derived views would repeat a retired experiment.

The accepted v0.29 floors for Office and Analytics are inherited from the exact v0.25 physical product. The remaining advantage comes primarily from the strength of its expensive final compression, not from an unproductized v0.29-only predictive mechanism. v0.30 must therefore change the **speed-density frontier itself**, not simply ask the same final encoder to work harder.

## Next decisive action

Do not add another effort sweep or selector wrapper.

The next R4 must target a different representation/execution primitive that can make the broad Analytics payload cheaper to encode **before** expensive final compression while retaining independent bounded reconstruction and the current integrity/locality contract. Candidate work must first establish causal headroom on fixed physical units and include a hostile/no-benefit control. Useful directions include cheap reversible transforms or shared predictive state only if they demonstrate net authenticated-byte savings after their own metadata and decode costs; they are not authorized by this result merely because they sound plausible.

Office may later reuse sparse-opportunity information as a secondary optimization, but it is not a primary family because the exact oracle lower bound still misses v0.29 and ZIP time.

## Negative-result preservation rule

Reopen this family only if new evidence changes one of its premises: a materially cheaper high-density backend, a representation change that alters the final-unit savings distribution, or a corrected measurement showing the fixed-representation lower bound was wrong. Do not reopen it through new effort levels, promotion fractions, workload identity, or hidden fallback to the expensive inherited product.
