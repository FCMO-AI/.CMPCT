# Hidden-ZIP identity-first ownership boundary

Status: **PREREGISTERED / ORACLE-FIRST / NO PRODUCT CREDIT**

## Decision being tested

The hidden-ZIP byte owner depends on exact logical-content sharing, but the current creator validates and materializes every admitted Deflate member occurrence before Builder content identity collapses duplicates. The exact-head native product attempt preserved the byte owner but failed the frozen Office create ceiling (`10793487574`: `1.341849x`; staging `52.542 ms`). Moving the same validation/materialization work native is therefore retired.

The next question is narrower and materially different: **can the creator establish exact logical identities across the whole winning cohort before it exports/materializes duplicate logical occurrences across the ownership boundary?**

## Existing lower bounds

The five admitted Office winners contain 168 Deflate member occurrences. Exact compressed-stream accounting already proves 84 unique streams plus 84 exact-stream aliases. Every exact-stream alias necessarily decodes to the same logical content as its owner, so at least 84 member occurrences are known duplicate logical identities even before considering differently encoded streams that decode identically. The exact byte-weight of that logical duplication is not yet authority; the v5 native-batch receipt measures it directly.

## Cheapest discriminator

The v5 research receipt reports, on the same admitted winners:

- total logical occurrence bytes;
- exact global unique logical bytes keyed by SHA-256 plus length;
- duplicate logical bytes and exact unique logical-object count;
- per-container unique bytes, so cross-container sharing is visible rather than hidden;
- matched Python and ordinary native full-materialization controls;
- a per-container identity-first arm;
- a cohort-wide identity-first arm that validates/hashes every occurrence exactly once, byte-checks digest aliases, and exports only one representative globally.

The oracle builds only the independently reseeded Office corpus rather than regenerating unrelated media/ML/etc. workloads. `corpus_office()` owns its deterministic PRNG stream, and the same repair normalization is applied. This changes evidence setup cost, not the measured Office bytes or timed boundary.

All of this remains research evidence and receives no product credit.

## Candidate architecture if the oracle earns it

Do **not** reopen the failed native-staging design by tuning workers, codec backends or thresholds. The only authorized product frame is an ownership-boundary change:

1. validate every bounded RFC-1951 occurrence under the existing exact-consumption, declared-length and CRC contract;
2. compute strong logical identity for every occurrence;
3. retain/export logical bytes only for one deterministic representative of each exact logical identity needed by the winning cohort;
4. represent duplicate occurrences by that already-proven logical identity rather than copying the same logical bytes through the native/Python boundary again;
5. keep Python ownership fixed-point resolution, deterministic transaction commit and the independent final live-source stamp+digest rebind unless direct evidence shows one of those boundaries itself must change;
6. preserve safe fallback when optional native support is absent.

A useful implementation should avoid a second full decode of unique representatives. A two-pass `hash all -> decode owners again` design must first prove that its extra decode work is cheaper than the transfer/materialization work it removes; it is not assumed to be a win. The v5 oracle instead uses one decode per occurrence and a bounded reusable scratch buffer, copying only first-seen exact identities into caller-visible material.

## Mature external control

Global content-identity-before-storage is not a novel product principle by itself. Borg documents repository-wide deduplication by strong chunk identity across files/backups/hosts (`https://borgbackup.readthedocs.io/en/2.0.0b23/internals.html`), and restic documents SHA-256 content IDs with write-once repository objects (`https://restic.readthedocs.io/en/v0.15.0/design.html`). Those systems do **not** prove CMPCT's nested-container reconstruction economics; they are a control showing that globally resolving strong content identity before durable storage is a mature ownership pattern. CMPCT still has to prove exact ZIP reconstruction, bounded hostile work, transaction safety, locality and its frozen runtime gate.

## Safety invariants

- Exact tree reconstruction remains mandatory.
- CRC/length/complete-stream validation is not replaced by hash equality.
- SHA-256 identity is paired with logical length; any contradiction is fatal.
- A digest alias is byte-compared to its retained representative before reuse; cryptographic collision resistance is not used as permission to skip exactness.
- Malformed provisional peers fail closed before cohort commit.
- Hardlinks, S_PACK and fallback explicit archives receive no hidden ownership credit.
- Aggregate input/output limits and per-job scratch limits are checked before hostile allocation/decode work.
- The final live source rebind remains after staging and before mutation/commit.
- No reader grammar, release threshold, comparator semantics or timing boundary changes.

## Kill condition

Consume the v5 cohort identity-first receipt first. If duplicate logical bytes are too small, or if the measured cohort boundary cannot plausibly recover the remaining create debt, retire this family without product integration. If the oracle shows decision-changing headroom, permit **one bounded product-path identity-first attempt**. That attempt must preserve the >9.33 MB byte owner and exactness while crossing the unchanged Office create ceiling `<=1.25x`; otherwise retire the family rather than tuning it.

## Counterfactual lesson

The earlier native oracle timed the validation/materialization kernel and correctly showed that kernel was faster, but end-to-end product staging still lost. The wrapper subsequently converted the complete native output to Python bytes and sliced every logical occurrence into cache objects before Builder identity collapsed them. Future lower-rung execution-boundary oracles must therefore distinguish kernel time from ownership-transfer/copy/materialization cost. A faster kernel is not evidence that the product boundary is cheaper.
