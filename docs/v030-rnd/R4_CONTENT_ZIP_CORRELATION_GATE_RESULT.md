# v0.30 R4 content-ZIP correlation admission result

**Status:** V1 MATRIX POSITIVE / HOSTILE FALSIFIED / V2 IN TEST  
**Primary branch:** `agent/v030-authoritative-integration`  
**Shipping credit:** none

## Context

Content-driven use of the already-existing `S_VZIP` representation recovered about 8.985 MB from the unchanged r24 Builder over the exact 15-workload matrix, almost entirely from Office. The all-valid detector was deliberately too broad: Analytics spent about 0.49 CPU seconds to save only ~0.9 KiB on one hidden NPZ.

V1 therefore preregistered a cheap opportunity hint based on central-directory `(CRC32, uncompressed-size)` signatures shared across at least two valid ZIP containers. The hint was not a correctness proof; exact recipe construction and tree/range verification remained authoritative.

## Full-matrix V1 result

Hosted run/job: `34640098466` / `103397450329`, exact head `071b4f3f70fcdba08c3236a7aaffa56157903495`.

Aggregate:

- unchanged Builder: `181,604,152 B`;
- all-valid content ZIP: `172,618,299 B`;
- V1 correlation-gated: `172,619,194 B`;
- all-valid saving: `8,985,853 B`;
- gated saving: `8,984,958 B`;
- retained saving: **99.9900%**;
- deterministic byte regressions versus baseline: **0/15**;
- exact reconstructed trees: **15/15**.

Office:

- baseline `15,445,454 B`;
- all-valid `6,460,544 B`;
- V1 gated `6,460,544 B`;
- six hidden containers admitted;
- ten repeated member signatures observed.

Analytics:

- baseline `10,392,497 B`;
- all-valid `10,391,602 B`;
- V1 gated `10,392,497 B`;
- the lone hidden NPZ had no cross-container correlation and was therefore not admitted.

The causal signal is real. But the research implementation's separate pre-scan made aggregate creation CPU worse than the all-valid detector (`11.3528 s` versus `10.3933 s`). Most of that tax came from traversing tiny-file-heavy roots twice. Any product path must fuse observation into the canonical scan/cache rather than bolt on a second walk.

## Hostile review

The first hostile workflow submission had YAML syntax/topology trouble and produced no scientific job. It was repaired without changing the hypothesis. The authoritative hostile receipt is run/job `34640453663` / `103398592018`, exact head `f92cfee21d942aa02d413d08e93c5ae2eb4486b4`, artifact `10280176240`.

V1 **fails** both preregistered attacks.

### Empty-signature false positive

Two otherwise unrelated hidden ZIPs each contained an empty member. `(CRC32=0, size=0)` therefore appeared in both and manufactured a correlation signal.

- baseline: `1,931 B`;
- V1 gated: `2,322 B`;
- V1 admitted both hidden containers;
- all three hostile expectations failed.

This proves zero-length signatures cannot carry admission evidence.

### Correlated pair with unrelated passenger

Two hidden ZIPs shared a substantial exact member and a third valid hidden ZIP was unrelated. V1 correctly found the pair but its cohort-wide admission rule also admitted the passenger.

- baseline: `1,997 B`;
- V1 gated: `2,607 B`;
- admitted: `version-a.bin`, `version-b.bin`, **and `passenger.bin`**;
- pair-detection assertions pass; passenger-exclusion assertions fail.

This proves a build-scope boolean is too coarse. Admission evidence must belong to each candidate container.

## Causal repair, preregistered before V2 results

V2 is intentionally minimal rather than threshold-tuned:

1. ignore zero-length signatures entirely;
2. compute `shared_positive_bytes` separately for each valid container from unique `(CRC32,size)` signatures also owned by another container;
3. admit a hidden container only if **its own** `shared_positive_bytes > 0`;
4. keep explicit `.zip/.whl` behavior unchanged;
5. retain exact recipe/tree/range proof.

This should remove both demonstrated V1 defects without introducing workload names, path classes or a fitted byte threshold. It does **not** yet solve economic admission for tiny-but-positive shared members; that is the next hostile question if V2 survives.

## Decision

V1 is preserved as a useful negative, not patched in place. Do not promote the cohort-wide rule. V2 must rerun the same 15-workload matrix plus both hostile controls before parser-resource, repeated CPU/RSS or shipping-integration work receives credit.
