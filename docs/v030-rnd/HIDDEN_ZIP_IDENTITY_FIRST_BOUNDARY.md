# Hidden-ZIP identity-first ownership boundary

Status: **PREREGISTERED / ORACLE-FIRST / NO PRODUCT CREDIT**

## Decision being tested

The hidden-ZIP byte owner depends on exact logical-content sharing, but the current creator validates and materializes every admitted Deflate member occurrence before Builder content identity collapses duplicates. The exact-head native product attempt preserved the byte owner but failed the frozen Office create ceiling (`10793487574`: `1.341849x`; staging `52.542 ms`). Moving the same work native is retired.

Exact research receipt `10794918189` now resolves the ownership geometry: 168 Deflate occurrences expose `12,787,462 B` logical bytes but only `4,748,362 B` / 84 exact global logical objects. `8,039,100 B` (**62.87%**) is duplicate. Per-container unique material is `12,778,132 B`, so almost the entire opportunity exists only across sibling containers.

The active question is therefore: **can the creator establish exact logical identities at cohort scope before duplicate logical bytes cross the ownership/materialization boundary?**

## Strongest implementation frame

Do not reopen worker/backend/threshold tuning. The existing admission proof already inflates every relevant Deflate occurrence to validate exact logical length and CRC, but currently discards the logical identity produced by that work. A product attempt, if earned, should exploit that existing decode rather than add another identity pass:

1. During the already-required proof validation, update SHA-256 over the same logical chunks used for CRC; record `(logical_sha256, logical_length)` beside the exact physical identity.
2. Resolve the unchanged ownership fixed point at cohort scope.
3. Choose one deterministic representative for each exact logical identity needed by winning recipes.
4. During staging, materialize/decode only those representatives; duplicate occurrences reference the already-proven logical identity instead of being decoded/copied into duplicate Python objects.
5. Preserve deterministic Builder mutation and the independent final live-source stamp+digest rebind.
6. Preserve the proven Python fallback and exact r24 reconstruction semantics.

This is materially different from the retired proof/cache tweaks: the purpose is not to make proof itself faster, but to make its already-paid decode establish the ownership fact that prevents duplicate staging work later.

## Research oracle

The native identity-first oracle remains a lower-rung mechanism probe, not the required product architecture. It validates/hashes every occurrence once, byte-checks digest aliases, and exports one representative globally. The current decision-bearing revision charges:

- native kernel wall;
- ctypes input/output allocation and direct-pointer return copy;
- digest/offset conversion;
- current cohort source-buffer join.

A previous v7 receipt exposed an evaluator bug: `bytes(ctypes_array[:used])` first created millions of Python integer objects, producing a false ~106 ms bridge. v8 uses direct `ctypes.string_at(pointer, used)` and preserves all real charged work. No product decision may use the v7 list-conversion wall.

## Mature external control

Global content-identity-before-storage is a mature ownership pattern: Borg performs repository-wide strong-hash chunk deduplication across archives/hosts (`https://borgbackup.readthedocs.io/en/2.0.0b23/internals.html`), while restic uses SHA-256 content IDs for write-once repository objects (`https://restic.readthedocs.io/en/v0.15.0/design.html`). Those systems do not prove CMPCT's nested-container reconstruction economics; CMPCT still must prove exact ZIP reconstruction, bounded hostile work, transaction safety, locality and the frozen runtime gate.

## Safety invariants

- Exact tree reconstruction remains mandatory.
- CRC/length/complete-stream validation is not replaced by hash equality.
- SHA-256 identity is paired with logical length; contradictions are fatal.
- A digest alias cannot weaken exactness; research materializers byte-check aliases against the retained representative.
- Malformed provisional peers fail closed before cohort commit.
- Hardlinks, S_PACK and fallback explicit archives receive no hidden ownership credit.
- Aggregate input/output and per-job scratch bounds precede hostile allocation/decode work.
- Final live-source rebind remains after staging and before mutation/commit.
- No reader grammar, release threshold, comparator semantics or timing boundary changes.

## Kill condition

Consume v8 first. If its realistic charged cohort boundary plus the measured 62.87% duplication does not provide plausible margin against the remaining ~`12.484 ms` create debt, retire identity-first materialization. If it does, permit **one bounded product-path attempt using proof-derived logical identity and representative-only staging**. That attempt must preserve the >9.33 MB byte owner and exactness while crossing Office create `<=1.25x`; otherwise retire the family rather than tuning it.

## Counterfactual lesson

The useful earlier observable was not “native decode is faster.” It was **where identity becomes known relative to where bytes become owned**. The current pipeline pays to validate logical content before it knows which logical objects are duplicates, then pays again to materialize them before Builder deduplication. Future representation work should ask whether a fact already computed upstream can eliminate downstream ownership work before optimizing the downstream implementation.
