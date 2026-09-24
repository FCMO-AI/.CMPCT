# Hidden-ZIP identity-first ownership boundary

Status: **PREREGISTERED / ORACLE-FIRST / NO PRODUCT CREDIT**

## Decision being tested

The hidden-ZIP byte owner depends on exact logical-content sharing, but the current creator validates and materializes every admitted Deflate member occurrence before Builder content identity collapses duplicates. The exact-head native product attempt preserved the byte owner but failed the frozen Office create ceiling (`10793487574`: `1.341849x`; staging `52.542 ms`). Moving the same validation/materialization work native is therefore retired.

The next question is narrower and materially different: **can the creator establish exact logical identities before it exports/materializes duplicate logical occurrences across the ownership boundary?**

## Existing lower bounds

The five admitted Office winners contain 168 Deflate member occurrences. Exact compressed-stream accounting already proves 84 unique streams plus 84 exact-stream aliases. Every exact-stream alias necessarily decodes to the same logical content as its owner, so at least 84 member occurrences are known duplicate logical identities even before considering differently encoded streams that decode identically. The exact byte-weight of that logical duplication is not yet authority; the v3 native-batch receipt measures it directly.

## Cheapest discriminator

The v3 native-batch research receipt reports, on the same admitted winners:

- total logical occurrence bytes;
- exact unique logical bytes keyed by SHA-256 plus length;
- duplicate logical bytes;
- exact unique logical-object count.

This accounting is untimed and receives no product credit. It exists only to decide whether an implementation can plausibly delete enough transfer/materialization work to matter.

## Candidate architecture if the oracle earns it

Do **not** reopen the failed native-staging design by tuning workers, codec backends or thresholds. The only authorized implementation frame is an ownership-boundary change:

1. validate every bounded RFC-1951 occurrence under the existing exact-consumption, declared-length and CRC contract;
2. compute strong logical identity for every occurrence;
3. retain/export logical bytes only for one deterministic representative of each exact logical identity needed by the winning cohort;
4. represent duplicate occurrences by that already-proven logical identity rather than copying the same logical bytes through the native/Python boundary again;
5. keep Python ownership fixed-point resolution, deterministic transaction commit and the independent final live-source stamp+digest rebind unless direct evidence shows one of those boundaries itself must change;
6. preserve safe fallback when optional native support is absent.

A useful implementation should avoid a second full decode of unique representatives. A two-pass `hash all -> decode owners again` design must first prove that its extra decode work is cheaper than the transfer/materialization work it removes; it is not assumed to be a win.

## Safety invariants

- Exact tree reconstruction remains mandatory.
- CRC/length/complete-stream validation is not replaced by hash equality.
- SHA-256 identity is paired with logical length; any contradiction is fatal.
- Malformed provisional peers fail closed before cohort commit.
- Hardlinks, S_PACK and fallback explicit archives receive no hidden ownership credit.
- Aggregate memory/work bounds remain enforced before hostile decode work.
- The final live source rebind remains after staging and before mutation/commit.
- No reader grammar, release threshold, comparator semantics or timing boundary changes.

## Kill condition

First consume the v3 logical-uniqueness receipt. If duplicate logical bytes are too small to plausibly recover the remaining create debt, retire this family without implementation. If the oracle shows material duplication, permit **one bounded product-path identity-first attempt**. That attempt must preserve the >9.33 MB byte owner and exactness while crossing the unchanged Office create ceiling `<=1.25x`; otherwise retire the family rather than tuning it.

## Counterfactual lesson

The earlier native oracle timed the validation/materialization kernel and correctly showed that kernel was faster, but end-to-end product staging still lost. Future lower-rung execution-boundary oracles must distinguish kernel time from ownership-transfer/copy/materialization cost. A faster kernel is not evidence that the product boundary is cheaper.
