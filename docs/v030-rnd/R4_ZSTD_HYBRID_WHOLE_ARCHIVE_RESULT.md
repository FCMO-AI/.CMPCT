# v0.30 R4 Zstd hybrid whole-archive result

**Status:** CLOSED / NEGATIVE AS A PRODUCT ROUTE  
**Authority branch:** `agent/v030-authoritative-integration`  
**Candidate source head:** `34a288950fc4c2ee84f752df9011f04da2a5f8de`  
**Workflow run:** `34634097979`  
**Job:** `103377747611`  
**Artifact:** `10277033616` (`v030-r4-zstd-hybrid-whole-archive-34a288950fc4c2ee84f752df9011f04da2a5f8de`)  
**Artifact digest:** `sha256:c8fa56883e1dad4fe6903e7a7379b7a7c5e509701a64a0517df4b7b607549346`  
**Shipping credit:** none

## Mission lock

The parameter-decomposition diagnostic showed that a level-15 preset carrying only level-19 `strategy` and `searchLog` could *predict* about 80.7% recovery of the Analytics level-15 -> accepted-v0.29 byte gap while using less than half of level-19's measured incremental final-compression time. That call-level result was not sufficient product evidence.

This experiment therefore rebuilt complete authenticated CMPNX5 archives with four fixed policies:

1. ordinary level 15;
2. level-15 parameters plus level-19 `strategy`;
3. level-15 parameters plus level-19 `strategy` and `searchLog`;
4. ordinary level 19.

All sub-19 structural/probe behavior remained unchanged. Each policy was built twice, required deterministic archive bytes and canonical tree identity, then passed strong verification, extraction, filesystem-manifest restoration and canonical user-tree hashing. Office and Analytics were the structured targets; Developer Repository, Many Tiny Files and Incompressible/Encrypted-like were hostile/no-benefit controls. ZIP/Deflate-9 create time was measured on the same staged input.

The preregistered joint hypothesis required the Analytics `strategy+searchLog` hybrid to recover >=70% of the accepted-v0.29 gap, use <70% of level-19 incremental complete-verified creation time, remain faster than level 19, and introduce no deterministic size regression versus level 15 on the controls.

## Result

The workflow completed **green**, but the scientific hypothesis is **false**. Correctness and determinism passed; product economics did not.

| Workload | v0.29 floor | L15 | L15 + strategy19 + searchLog19 | L19 | Hybrid complete verified create | ZIP create |
|---|---:|---:|---:|---:|---:|---:|
| Office | 5,954,026 B | 6,081,780 B | 6,055,976 B | 5,955,239 B | 0.4351 s | 0.4470 s |
| Analytics | 6,135,172 B | 6,569,053 B | **6,218,880 B** | 6,135,703 B | **4.9306 s** | **1.5290 s** |
| Developer | 744,337 B | 840,066 B | 816,375 B | 812,242 B | 1.1094 s | 0.1685 s |
| Many Tiny | 420,318 B | 633,110 B | 622,599 B | 621,346 B | 1.9971 s | 0.4286 s |
| Incompressible | 10,193,958 B | **10,245,555 B** | **10,245,648 B** | 10,245,648 B | 1.0112 s | 0.3543 s |

### Analytics signal survives, but not the product contract

The complete archive reproduces the call-level mechanism closely:

- bytes recovered versus level 15: **350,173 B**;
- fraction of accepted-v0.29 gap recovered: **80.707%**;
- fraction of ordinary level-19 saving recovered: **80.806%**;
- fraction of ordinary level-19 incremental complete-verified time: **53.98%**.

That is a real causal result. But the archive remains **83,708 B larger** than accepted v0.29 and its complete verified creation is about **3.22x ZIP create time** on the same staged input. It therefore does not close either strict product dimension that matters for this red.

### Office and Developer remain representation-floor evidence

Office recovers only **25,804 B**, about **20.20%** of its v0.29 gap. Even ordinary level 19 remains `+1,213 B` above the accepted v0.29 floor in this exact whole-archive run.

Developer recovers **23,691 B**, about **24.75%** of its v0.29 gap, and remains `+72,038 B` above accepted v0.29. Its hybrid complete-verified creation is also far slower than ZIP.

### Hostile control rejects unconditional hybrid publication

Incompressible/Encrypted-like grows from `10,245,555 B` at level 15 to `10,245,648 B` under `strategy+searchLog`: a deterministic **+93 B** regression. Under the repository's zero-byte promotion rule, that is sufficient to reject an unconditional product policy even if another workload had crossed its target.

Many Tiny Files remains over `202 KiB` above its accepted v0.29 floor and gains only about 4.94% of that gap from the hybrid.

## Causal interpretation

The experiment confirms that Zstd preset decomposition is real: `strategy`/`searchLog` buy a large fraction of Analytics density for materially less work than full level 19. It simultaneously falsifies the stronger product hypothesis:

> **A fixed recombination of level-19 final-compression parameters can repair the important v0.29 density reds while retaining v0.30's compute advantage and not regressing hostile controls.**

It cannot.

The result must not be rescued by workload-name selection or by loosening the zero-byte rule. A future content-driven selector would still need evidence that the measured parameter family can cross the relevant inherited floor under an honest time budget. The companion optimistic parameter-family floor oracle exists specifically to decide that question before any more selector tuning is attempted.

## Hostile review

Reasons this family is not product-ready:

1. no tested fixed hybrid beats accepted v0.29 on Office, Analytics or Developer;
2. Analytics remains much slower than ZIP even after recovering most of the density movement;
3. Developer and Tiny Files show that the mechanism is not a general repair;
4. Incompressible has a deterministic +93 B control regression;
5. the experiment did not measure a new shipping RSS/selective-read path because no production representation changed;
6. selecting the hybrid by workload identity would be benchmark leakage, not a generic encoder policy.

## Decision

**Close the fixed Zstd-hybrid whole-archive route.** Do not add another threshold or unconditional preset mixture.

Use the exact optimistic per-payload parameter-family floor to determine whether *any* measured parameter combination with perfect foresight could cross the inherited floors. If the floor is unreachable, the corresponding red is D4 representation/physical-layout debt under the Forge rubric and further parameter tuning is retired. If reachable only at an optimistic time lower bound already above the required competitor, the same conclusion applies to the joint size+time product objective.
