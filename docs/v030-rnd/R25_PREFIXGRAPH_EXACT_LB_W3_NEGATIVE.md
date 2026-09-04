# r25 PrefixGraph exact lower-bound w3 negative constraint

Status: **HISTORICAL RESULT RECOVERED / SCOPED NEGATIVE PRESERVED / ZERO PRODUCT OR RELEASE CREDIT**

Decision: **`PREFIXGRAPH_WEAK_EXACT_LB_TERMINAL_NOT_SUPPORTED`**

This document preserves the previously executed result from the exact PrefixGraph lower-bound three-worker oracle. The workflow and instrument already existed and executed successfully on August 31, 2026, but the decisive negative was not present as a durable result document under `docs/v030-rnd/`. Repository doctrine requires failures to survive as scoped constraints so later Forge work does not rediscover the same parameter family.

## Authority

- source SHA: `62b79bb6d4fbef0c5a9bc7b760a5d7a10f916b43`;
- workflow: `.github/workflows/v030-prefixgraph-exact-lb-w3.yml`;
- run: `33360205171`;
- substantive job: `99390044771`;
- evidence artifact: `9746569143`;
- artifact digest: `sha256:bd6f1a33bb81e0f42110991f4f868b27f937352bf5ac45d96290089a8e1363fe`;
- schema: `cmpct-v030-prefixgraph-exact-lb-w3-v1`;
- target: `resemblance_hostile_v1/01_shifted_versions`;
- rounds: 2 alternating-order fresh-process A/B;
- release credit: **false**.

## Exact oracle law

The candidate reduced PrefixGraph candidate workers from four to three and added an exact strict loser terminal. For each anchor, after every decided member payload it charged:

- immutable header + footer bytes;
- every payload byte already forced by the exact historical candidate prefix, including the mandatory direct anchor payload.

It optimistically charged unseen payload bytes and both metadata copies as **zero**. A candidate could terminate only when this deliberately weak complete-artifact lower bound became **strictly greater** than the current complete incumbent. Equality was never pruned. Surviving anchors were rebuilt by the unchanged historical serializer, and exact winning archive/tree identity was mandatory.

The mechanism therefore gifted search/discovery only in the permitted sense; it did not gift representation bytes or change a tie law.

## Result

Both rounds preserved exact shipping archive identity:

- complete bytes: **1,700,242 B**;
- archive SHA-256: `8994cb83c2f62944795144ee775d9395147681bb1156892d72d4cc5d4ca417fe`;
- tree SHA-256: `d9106dcdc8f965d45236c241d6c45f773e10b84ac204acc3c3521d889cd3a8fd`.

But the proof did not fire on a single anchor:

- anchor auditions: **18**;
- terminal anchors round 1: **0/18**;
- terminal anchors round 2: **0/18**;
- fully rebuilt anchors: **18/18** in both rounds;
- probe compressions: **306** in both rounds.

Medians:

| quantity | shipping | exact-LB w3 | ratio |
|---|---:|---:|---:|
| wall | **5.257487 s** | **9.567415 s** | **1.819770x** |
| incremental peak RSS | **305,830 KiB** | **243,838 KiB** | **0.797299x** |

Frozen promotion bands were `wall <=1.05x` and `RSS <=0.75x`, with at least one exact terminal. The candidate missed all three requirements: no terminal fired, wall regressed by about **81.98%**, and RSS fell only about **20.27%**, short of the required 25% reduction.

`promotion_signal = false`.

## Causal interpretation

The strict proof was correct but too weak and too expensive in this regime. Pricing all unseen payload and metadata at zero left the lower bound below the incumbent through complete anchor audition. The extra probe compression work therefore duplicated candidate effort without eliminating construction, while the three-worker cap reduced memory somewhat but not enough to satisfy its own frozen band.

This result is especially relevant to the current Shifted post-PrefixGraph G0-G4 rehabilitation. A successor exact-futility design must not merely copy the same proof grammar into v0.28 or attempt-5 and expect early stopping. It needs at least one materially stronger source of forced cost that becomes available earlier than full construction, or it needs a shared invariant whose computation replaces rather than duplicates expensive audition work.

## Scoped negative constraint

Within the tested repaired Shifted PrefixGraph anchor regime:

- `header + footer + already-forced payload bytes`, with all unseen payload/metadata optimistically priced at zero, is **not an early-enough exact futility certificate**;
- reducing candidate workers to three while separately recompressing probe prefixes is **not a supported performance intervention**;
- exactness itself is not disproven: the mechanism preserved archive/tree identity perfectly;
- stronger lower bounds remain open if they are causally different and charge all proof work;
- this does not establish that the same weak bound must fail on every future candidate family or corpus.

## Reopening predicate

Revisit this family only with new causal evidence that supplies a materially tighter or cheaper proof, for example:

1. non-zero mandatory metadata/framing bytes known before full construction;
2. monotone forced candidate bytes already computed by the real builder, eliminating duplicate probe compression;
3. a shared lower bound that applies to multiple inherited children from state they already must compute;
4. a proof point demonstrably reached before most of the current child wall rather than after it.

A renamed version of the same zero-unseen-cost prefix probe does not satisfy the reopening predicate.

## Forge consequence

Preserve the exact-futility concept, retire this **weak duplicate-probe realization**, and require the next Shifted stopping-proof experiment to show both proof tightness and proof timing. The current shared-child attribution (`SHIFTED_G04_SHARED_MIXED_OWNERSHIP`) already says attempt-5-only work leaves a material v0.28 floor; the next useful proof should therefore seek state shared across or comparably early inside both inherited graph constructors.
