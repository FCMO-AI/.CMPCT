# v0.30 R4 reversible tabular co-lift + bounded owner result

**Status:** POSITIVE RESEARCH SEED / INTEGRATED PRODUCT VALIDATION REQUIRED  
**Authority branch:** `agent/v030-authoritative-integration`  
**Feasibility source head:** `5870156e9f0a7a9cbc22dfa258676bce10f1e435`  
**Feasibility run/job:** `34635957124` / `103383817461`  
**Feasibility artifact:** `10278606276`, digest `sha256:efebd9780be5d3f3694bb55b1ae18703f9d656fe5b4d56e1b393ec727cb5162e`  
**Bounded-owner source head:** `da64f5db189305597c30869676db900d7d90f681`  
**Bounded-owner run/job:** `34636754528` / `103386443900`  
**Bounded-owner artifact:** `10278126861`, digest `sha256:e62d92124ac1b3d6d6005f3616877aa3df4e37a5ae5d577347959677dbb1cf87`  
**Shipping credit:** none

## Mission lock

The Analytics red survived global effort, selective ordinary high effort, Zstd parameter recombination and fully charged shared-dictionary attacks. Those families can recover bytes only by reintroducing enough expensive search that the v0.30 compute advantage disappears, or cannot cross the inherited v0.29 density floor at all.

The neutral Analytics workload contains two byte-distinct representations of the same 90,000 semantic rows: `events.csv` and `events.jsonl`. The new hypothesis changes representation rather than asking the same independent payload compressor to work harder:

> If two independently parsed members are byte-exact reversible views of the same semantic table, one bounded authenticated structural owner can store the shared information once and reconstruct both original member byte streams exactly, with enough fully charged headroom to justify a real product integration experiment.

Disproof was deliberately stronger than a size-only win. The pair-level oracle had to reject a row-rotation mismatch, reconstruct both source streams byte-for-byte, beat the complete fixed-L15 -> accepted-v0.29 whole-archive gap by its isolated saving, and keep charged writer work below one second. The second oracle then had to preserve that headroom while paying explicit manifest authentication, per-payload hashes, bounded row-group framing, deterministic repeated bytes, corruption refusal, measured dependency fanout and bounded failure cones.

## Exact pair-level feasibility result

Frozen Analytics identity:

- canonical tree SHA-256: `0c72d4b4d3a2f13546fe52b8b9afc7e62e1699eb284c1c56d8e8096fd77e3936`;
- CSV source bytes: `6,853,491 B`;
- JSONL source bytes: `13,693,441 B`;
- combined source bytes: `20,546,932 B`;
- rows: `90,000`;
- fields: `8`;
- independent pair Zstd-15 physical estimate: `2,150,042 B`;
- fixed-L15 complete archive: `6,569,059 B`;
- accepted v0.29 complete archive: `6,135,172 B`;
- strict complete-archive saving required: `433,888 B`.

The feasibility oracle parses CSV and JSONL independently, requires row/field equality, requires exact deterministic reserialization to both original byte streams, and rejects a one-row rotation before measuring any structural win.

Best isolated variant (column co-lift, Zstd level 9):

- stored owner bytes: **`186,578 B`**;
- saving versus independent pair Zstd-15: **`1,963,464 B`**;
- saving / strict whole-archive gap: **`4.5253x`**;
- parse/equivalence: `0.6957 s`;
- median structural encode: `0.1457 s`;
- charged writer: **`0.8414 s`**;
- median decode + reconstruction of both original members: `0.6716 s`.

This is a large representation-level signal, not a threshold effect. It says the dominant redundant information can be removed before final compression.

## Bounded authenticated owner result

The second oracle replaces the optimistic single-owner blob with a deterministic authenticated research owner:

- manifest SHA-256 authenticated in the owner prefix;
- every compressed column payload carries its own SHA-256 and checked bounds;
- corruption of a touched payload must fail authentication before decoded bytes are trusted;
- rows are split into bounded groups so one damaged group does not require treating all semantic rows as one reconstruction cone;
- dependency fanout is explicitly `2` logical members (CSV and JSONL);
- exact reconstruction of both source members is repeated twice and owner bytes must be deterministic.

| Row-group size | Owner bytes | Manifest | Groups | Max logical blast radius | Pair saving vs independent Zstd-15 | Optimistic projected complete archive | Margin vs v0.29 | Charged writer |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 2,048 | 449,182 B | 57,909 B | 44 | 467,610 B | 1,700,860 B | 4,868,199 B | **+1,266,973 B** | 0.8315 s |
| 4,096 | 375,495 B | 29,071 B | 22 | 935,212 B | 1,774,547 B | 4,794,512 B | **+1,340,660 B** | 0.8253 s |
| 8,192 | 301,905 B | 14,648 B | 11 | 1,870,254 B | 1,848,137 B | 4,720,922 B | **+1,414,250 B** | 0.8205 s |
| 16,384 | **263,680 B** | 8,117 B | 6 | 3,740,494 B | **1,886,362 B** | **4,682,697 B** | **+1,452,475 B** | **0.8201 s** |

The result is positive even at the smallest tested group size. That matters because the mechanism does not depend on one giant solid semantic owner to create its headroom. The 2,048-row form pays substantially more manifest/framing cost yet still leaves more than `1.26 MB` of optimistic margin over the accepted v0.29 complete-archive floor.

The best-density tested owner uses 16,384-row groups and stores `263,680 B`, approximately `12.3%` of the independent pair's Zstd-15 bytes. Its max group physical payload is only `47,419 B`, although reconstructing that group can produce up to `3,740,494 B` across both logical member views. This is explicit locality debt, not hidden cost.

## What this proves

The evidence supports a **research integration prototype** for reversible tabular co-lifting.

It proves, on the frozen Analytics case:

1. the two source members are independently parseable equal semantic tables;
2. the exact lexical CSV and JSONL byte streams are reversible from one shared semantic owner;
3. a hostile row-order mismatch is rejected rather than coerced into the representation;
4. the headroom is far larger than the current complete-archive density deficit;
5. the headroom survives explicit authentication/framing and bounded row-group partitioning;
6. writer cost for the diagnostic remains below one second;
7. corrupted touched payloads fail authentication;
8. representation bytes are deterministic across repetitions.

This is qualitatively different from the retired Zstd-search families. The gain comes from removing duplicated semantic information, not from spending more compute on the same independent payloads.

## What this does **not** prove

No shipping or release credit is granted.

The complete-archive values above are projections formed by replacing the independently compressed pair's bytes inside the fixed-L15 total. A real v0.30 product owner has not yet been published and measured end-to-end. In particular:

- a generic workload-blind/content-driven admission rule is not yet implemented;
- random byte-range reads of reconstructed CSV/JSONL members are **not supported by the oracle**;
- member reads currently inherit row-group reconstruction granularity rather than current r25 member/range semantics;
- full archive index/integrity/recovery ownership has not been charged through the shipping product wrapper;
- complete create/read/open/RSS and memory traffic are not yet measured on the integrated path;
- no independent native reader/vector exists;
- Android/platform portability is untouched;
- all-15 neutral/resemblance hostile controls have not been rerun with an integrated selector;
- equivalent-looking tables with lexical differences, reordered columns, duplicate keys, floating-point spellings, embedded newlines, unusual CSV dialects or very wide/high-cardinality rows remain mandatory false-positive/adversarial surfaces.

A positive pair on a purposefully related benchmark is not permission to recognize file extensions and special-case the workload. Admission must derive from proven reversible content relations and fall back exactly when proof or economics fail.

## Hostile review / regression debt

The largest known debt is locality. The best-density 16,384-row form has a maximum measured logical failure/reconstruction cone of ~`3.74 MB` across the two views. Even the 2,048-row form exposes ~`468 KB`. This is bounded, but it is not yet equivalent to arbitrary byte-range locality. The next experiment must therefore prefer proving an owner/index design that can reconstruct only the row groups intersecting a requested member range, or expose why byte-range projection requires additional lexical offset indexes and charge those bytes.

The second debt is parser/normalization scope. The current proof intentionally supports only the exact canonical CSV/JSONL lexical forms present in the frozen workload. Broadening the parser before a generic fail-closed admission proof would create a dangerous false-positive surface. Product work should start narrow and exact, then generalize only with independent hostile vectors.

## Decision

**Preserve tabular co-lifting as the current positive R4 research seed and advance to one research-only integrated owner prototype.**

Do not change canonical r25 grammar, version, release claims or native ABI yet. The next decisive experiment is an integrated v0.30 product-wrapper candidate that:

1. discovers the relation from content, never workload identity;
2. publishes one authenticated bounded owner plus two exact logical reconstruction recipes;
3. strong-verifies/extracts the complete canonical tree;
4. measures actual complete archive bytes and creation CPU/wall/RSS;
5. measures whole-member and selected byte-range work/amplification for both reconstructed views;
6. injects owner/manifest/payload corruption and proves bounded failure;
7. includes unrelated/mismatched tabular hostile controls with exact fallback;
8. preserves the inherited representation unchanged when the structural owner loses;
9. remains research-only until native/recovery/platform/all-15 evidence exists.

If actual integration erases the >1 MB margin or produces indefensible locality/reader cost, preserve this oracle as a scoped representation-headroom result and retire the product route. Do not hide the debt by weakening range semantics.
