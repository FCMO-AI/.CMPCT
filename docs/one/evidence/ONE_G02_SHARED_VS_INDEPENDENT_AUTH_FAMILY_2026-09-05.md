# ONE-G0.2 shared vs independent authenticated temporal-family carrying cost — 2026-09-05

Status: **ADVANCE (research evidence; not product/release authority)**

## Mission lock

Question: after discovery has already identified one basis plus eight exact edited roots, can ONE preserve authenticated 4 KiB selective reads while sharing the basis/AuthTree and authenticating generic Law+Surprise descriptors, instead of materializing/authenticating every version as an independent literal root?

The frozen comparator and candidate use the same selective-authentication semantics. Discovery/search is excluded symmetrically; this experiment measures representation/authentication carrying cost after the family relation is known.

Frozen gate at V=8, root sizes 64 KiB and 256 KiB, three independent families each:

- every read byte-exact and authenticated; deterministic descriptor-proof corruption rejects the candidate;
- shared persisted bytes strictly lower on every family;
- shared authentication setup median <= 0.80x independent AuthTree setup on every family;
- shared authenticated bytes touched <= 1.25x independent on every selective-read row;
- median shared/independent selective-read elapsed <= 1.25x, with no row > 1.50x.

## Exact execution

- source: `0167b39569b9dc0bd8bb092d681c9eb1b0383874`
- workflow run: `33957321982`
- result-bearing job: `101282898196`
- artifact: `9966790378`
- artifact ZIP SHA-256: `07e26011391108ce7b2c6698a79c9b45f37607df6487fa7faa1b4692d9908a17`
- semantic boundary: **76/76 `tests/one` passed**
- result schema: `cmpct-one-g02-shared-vs-independent-auth-family-v1`
- terminal decision: `advance_shared_authenticated_family_pareto`
- corruption failures: 0
- reconstruction/authentication failures: 0

The CI executor is fail-closed: the result-bearing process exits successfully only for the frozen `advance_shared_authenticated_family_pareto` decision. This corrects an evidence-control weakness found during the activation in which an earlier raw instrument could emit a negative JSON decision while still returning process success.

## Measured result

Across all six families, the shared representation persisted only about **11.18%** of the independent-authenticated representation (median ratio `0.1118420992`; worst `0.1122835345`). In concrete rows:

- 64 KiB family: independent `1,062,756 B`; shared `119,319–119,330 B`.
- 256 KiB family: independent `4,248,036 B`; shared `473,275–473,278 B`.

That is an approximately **88.8% persistent-byte reduction** for this eight-version family regime after the relationship is known.

Authentication setup also fell sharply because ONE builds one basis tree plus the compact descriptor authentication structure instead of nine whole-root trees:

- median setup ratio: **0.1112303734x**;
- worst setup ratio: **0.1130113763x**.

Representative measured medians:

- 64 KiB: independent ~`30.43–30.54 ms`; shared ~`3.43–3.45 ms`.
- 256 KiB: independent ~`123.60–125.60 ms`; shared ~`13.56–13.63 ms`.

Selective authenticated access paid a small bounded premium rather than exploding with root size:

- median authenticated-byte touch ratio: **1.0636896770x**;
- worst touch ratio: **1.0998641304x**;
- median selective-read elapsed ratio: **1.0500750347x**;
- worst selective-read elapsed ratio: **1.0659157366x**.

For 4 KiB requests, independent authenticated traffic was typically `4,352–4,688 B`; the shared candidate was typically `4,604–4,993 B`, including basis proof, descriptor control, Surprise bytes and descriptor proof. The read-time premium was therefore about **5.0% median / 6.6% worst** in this CPython/hashlib execution while eliminating roughly 88.8% of persisted family bytes and roughly 88.9% of authentication setup time.

## Causal interpretation

The previous multi-version failure was not evidence that authenticated selective access inherently requires one full AuthTree per reconstructed version. Once authentication follows the stored ONE representation rather than every logical output, temporal/version sharing survives the integrity layer:

`authenticated basis + authenticated generic Law/Surprise -> exact authenticated requested output range`.

This is materially stronger than a density-only result because it simultaneously pays persistence, setup work, proof traffic and selective reconstruction work under the same semantics. It also remains ONE-native: the reader executes the same bounded Law+Surprise reconstruction and performs no discovery.

## Hostile review / claim boundary

This is **not** yet a product-speed, native, canonical-wire, v0.29/v0.30 comparator, or release result.

The strongest surviving debt is that the timing path is CPython/hashlib and the experiment begins **after family discovery**. It therefore does not charge the writer for discovering the basis/version relationship, and Python call overhead can distort the observed ~5% read premium. It also tests the current translation-family regime rather than arbitrary deep/multi-parent Law graphs. Those costs must not be silently gifted in later claims.

The structural byte result and exact authentication semantics are nevertheless decision-changing: duplicating per-version output AuthTrees should no longer be treated as the default architecture for ONE temporal families.

## Decision and next falsifier

**Advance** the shared authenticated-family architecture. The next decisive experiment should move this same carrying-cost comparison into the native/authentication execution surface and charge marginal information yield across persisted bytes, authentication setup, selective read, memory traffic/state and reconstruction work. The goal is to determine whether the ~5% CPython selective-read premium is implementation overhead that collapses under fused native execution or a real cost exported by descriptor+Surprise authentication.

Do not reopen the independent-per-output AuthTree architecture without new causal evidence that the shared representation breaks a required integrity/recovery/locality invariant.
