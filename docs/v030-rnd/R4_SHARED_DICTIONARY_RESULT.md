# v0.30 R4 shared Zstd dictionary result

**Status:** CLOSED / NEGATIVE AS PRIMARY R4  
**Authority branch:** `agent/v030-authoritative-integration`  
**Deep-oracle source head:** `b11ff30f404a96a52457a2a070628ea75b0ddef4`  
**Workflow run:** `34635536719`  
**Job:** `103382402769`  
**Artifact:** `10278020618` (`v030-r4-shared-dictionary-b11ff30f404a96a52457a2a070628ea75b0ddef4`)  
**Artifact digest:** `sha256:d5f5f9f6da59f436e74badf67cc7d3b574265b710150333eddd08ea67b89d015`  
**Shipping credit:** none

## Mission lock

The exact parameter-family floor showed that independent per-pack Zstd search cannot jointly close the important v0.29 reds at acceptable compute cost. The next hypothesis changed mechanism rather than adding another preset: train one bounded Zstd dictionary from cheap-gated final payloads and reuse that context across many independently compressed payloads.

The oracle charged:

- dictionary bytes;
- a conservative physical owner/framing tax;
- 8 bytes per dictionary reference;
- dictionary training time;
- the eligibility scan;
- every dictionary-compression call;
- exact payload round-trip.

The first run tested dictionary compression levels 3/5/9 and was strongly negative. To remove the obvious alternative explanation that the backend was simply too weak, the hosted hostile extension added levels **15 and 19** while preserving all other charges and the same external-time budget.

## Deep hosted result

| Workload | v0.29 | Fixed L15 | Best dictionary size point | Gap to v0.29 | Charged pipeline | Best point inside ZIP budget |
|---|---:|---:|---:|---:|---:|---:|
| Office | 5,954,026 B | 6,081,882 B | **5,977,299 B** (64 KiB, L19) | +23,273 B | 0.476 s | 5,982,748 B (64 KiB, L15) |
| Analytics | 6,135,172 B | 6,569,059 B | **6,120,573 B** (64 KiB, L19) | **−14,599 B** | **5.944 s** | **6,897,530 B** (32 KiB, L9) |
| Developer | 744,337 B | 838,930 B | 830,347 B (16 KiB, L19) | +86,010 B | 0.465 s | 909,274 B (16 KiB, L9) |
| Many Tiny | 420,318 B | 639,102 B | 644,066 B (16 KiB, L19) | +223,748 B | 0.235 s | same |
| Incompressible | 10,193,958 B | 10,247,117 B | no eligible payloads | — | — | fallback |

Same-input ZIP create times were approximately:

- Office: 0.445 s
- Analytics: **1.514 s**
- Developer: 0.167 s
- Many Tiny: 0.423 s
- Incompressible: 0.353 s

## Interpretation

The hypothesis is **false** under the joint density + compute objective.

### Analytics proves the mechanism can buy bytes, but not cheaply

The strongest 64 KiB dictionary at level 19 predicts `6,120,573 B`, which is **14,599 B smaller** than accepted v0.29 and recovers 103.36% of the fixed-L15 gap. But its fully charged dictionary pipeline is **5.944 s**, roughly **3.93x** the same-input ZIP creation time before adding a real format owner, archive publication, verification, dependency accounting or selector overhead.

Inside the ZIP-time budget, the best Analytics candidate is the 32 KiB level-9 dictionary at `6,897,530 B` — **328,471 B larger than the level-15 baseline itself**. Shared dictionary context therefore does not move the speed-density frontier in the required direction.

### Office remains above the inherited density floor

Even the strongest tested dictionary point remains `+23,273 B` above accepted v0.29. The best point that fits the ZIP budget remains `+28,722 B`. There is no basis for a product selector here.

### Hostile controls reject generalization

Developer remains `+86,010 B` even at the strongest level-19 point; its budget-fitting dictionary candidate is substantially worse than L15. Many Tiny grows even at level 19 after dictionary ownership/reference tax. Incompressible correctly produces no eligible payloads.

## Decision

**Retire shared Zstd dictionaries as the primary R4 for the current reds.**

Do not rescue the family with another dictionary-size sweep, workload-name selector, or looser time budget. The result shows that cross-payload context can recover Analytics density only by reintroducing the expensive search behavior that v0.30 was reactivated to avoid.

The next R4 must exploit stronger predictable structure with cheaper reconstruction. In Analytics, a concrete candidate is reversible cross-format structural lifting: the neutral corpus contains CSV and JSONL views of the same 90,000 semantic rows. A valid experiment must accept only byte-exact reversible pairs, charge owner metadata and encode/decode work, reject mismatched-row hostile controls, and remain diagnostic until a real authenticated owner with bounded dependency/locality passes all-15 evidence.
