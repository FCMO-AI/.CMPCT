# CMPCT Mosaic full-artifact attempt #4 — Placement Compiler

Status: **pre-registered research attempt; no v0.29.0 claim**  
Parent campaign: `docs/MOSAIC_V029_CAMPAIGN.md`  
Frozen full-artifact gate: **unchanged since before attempt #1**

## Why attempt #3 failed

Attempt #3 is preserved in
`benchmarks/history/2026-08-17-mosaic-v029-full-artifact-attempt3.json`.

It corrected the attempt-2 standalone-direct-cost mistake: direct leaves entered a real physical pack
marginal tournament, and a mosaic was rejected when v0.28 solid context already stored the target more
cheaply. The result remained below the frozen v2 gate:

- v1: **6,240,113 → 5,813,475 B (-6.8370%)**, 4/8 improved, 0 regressed;
- v2: **8,589,119 → 8,428,532 B (-1.8697%)**, 1/10 improved, 0 regressed;
- combined: **14,829,232 → 14,242,007 B (-3.9599%)**, 5/18 improved, 0 regressed;
- maximum descriptor-actual amplification: **4.0005x**.

The mechanism was therefore no longer promoting false archive wins, but it still had only one physical
embodiment: remove a target from ordinary root packs and store a separate mosaic record. The focused
failure diagnostic then measured where that embodiment is and is not appropriate.

Durable diagnostic summary:
`benchmarks/history/2026-08-17-mosaic-v029-failure-diagnostics-summary.json`.

## Diagnostic facts that constrain attempt #4

### Leave shifted/reordered alone

v2 `02_shifted_reordered_merge`:

- v0.28 target standalone direct cost: **252,126 B**;
- actual target marginal cost inside v0.28's 3-node solid pack: **3,802 B**;
- best two-root mosaic record: **5,592 B**;
- replacing the raw target inside that same pack with its recipe is still **853 B worse** after descriptor
  charge.

There is no measured headroom. Attempt #4 must not force a different representation here.

### Leave record-conflict alone unless a new representation changes the arithmetic

v2 `03_record_store_conflict_merge`:

- target pack marginal: **19,052 B**;
- oracle two-parent mosaic record: **91,103 B**;
- one useful parent is itself a v0.28 delta target.

Even perfect parent availability cannot make the current mosaic representation competitive with the
solid-pack marginal cost. Attempt #4 does not promote that parent merely to manufacture another win.

### Source-like has small but real **pack-local** headroom

v2 `04_source_like_merge`:

- target pack marginal: **639 B**;
- separate mosaic record: **805 B** — loses;
- baseline physical pack: **8,260 B**;
- same pack after replacing the target's raw slot with its mosaic recipe: **8,092 B**;
- conservative extra descriptor charge: **40 B**;
- net oracle saving: **128 B**;
- read amplification: **2.011x**.

The correct physical representation is not another record. It is a semantic recipe **inside the pack
that must be decoded anyway**.

### Root diversity has real bytes but the wrong root placement

v2 `09_root_diversity_pressure`:

- target marginal pack cost: **96,216 B**;
- best bounded four-root mosaic: **33,411 B**;
- oracle marginal headroom before placement cost: about **62.8 KiB**;
- current selected roots span two physical groups;
- a same-current-pack subset cannot exploit enough roots and loses **454 B**.

The missing mechanism is locality-aware co-packing of the small direct root set actually required by the
recipe, not a wider dependency graph.

### Small metadata is a bounded candidate-floor miss

v2 `10_small_metadata_control`:

- target logical size: **2,048 B**;
- inherited single delta: **725 B**;
- two-root mosaic: **210 B**.

The inherited v0.28 delta path already handles the target (`MIN_DELTA=1024`). The miss is mosaic-specific:
its `max(4096 B, target/20)` copied-information retention floor is impossible for a 2 KiB object.
Attempt #4 changes only mosaic contribution accounting, not inherited v0.28 delta policy.

## Attempt #4 hypothesis

A **Mosaic Placement Compiler** should select the physical embodiment that matches marginal archive
physics rather than forcing every multi-root target into a separate record:

1. **external mosaic record** when the target is already outside the direct root packs and the complete
   mosaic record beats its inherited delta;
2. **pack-local mosaic recipe** when roots and target already share one bounded solid pack and replacing
   the raw target slot reduces that exact compressed physical record;
3. **mosaic root co-pack + external recipe** when a bounded set of direct roots has real marginal headroom
   but current generic similarity packing scatters those roots across groups;
4. **small-target external mosaic** when a target-relative contribution floor proves multiple roots
   useful and the complete mosaic beats the inherited single delta.

Cases whose oracle economics are negative remain untouched.

## Representation design

Implementation will use a new research grammar/engine file so attempts #1–#3 remain executable.
Canonical revision 24 remains unchanged.

### Pack-local recipe node

A physical pack may contain raw direct nodes plus one or more compact mosaic recipe byte ranges. A
`pack_mosaic` node descriptor records:

- physical record id;
- recipe offset and length within the decoded pack;
- 2–4 base node ids;
- target logical length and SHA-256.

Every base must be a direct node. Reading the target decodes the one physical pack, slices the recipe,
then reconstructs the logical target from bases already available from direct pack slices. There is no
second physical record and no dependency depth >1.

Pack-local admission requires:

- exact mosaic decode/byte-compare;
- at least two roots and at least one-third of target bytes copied;
- physical group read amplification <=8x;
- exact recompression of the whole physical group after recipe substitution;
- **>=64 B net saving after a conservative descriptor-overhead charge**.

The 64 B floor is fixed before measurement. It is above pure zero-tolerance noise while still allowing
the measured 128 B source-like oracle headroom to be tested rather than rejected by a 1% rule designed
for much larger records.

### Locality-aware root co-pack

For an external leaf mosaic whose roots span multiple current groups:

1. remove the target from the current direct-root set;
2. start from a normal v0.28 pack plan without that target;
3. remove the 2–4 selected direct bases from their generic groups;
4. place those bases together in one dedicated group, ordered deterministically;
5. recompress **all changed physical groups** and calculate the complete new pack cost;
6. add the complete external mosaic record cost;
7. accept only when total physical bytes beat the current pack state by `max(128 B, 1%)` of the measured
   marginal saving and target read amplification remains <=8x.

The dedicated co-pack may not exceed the existing **2 MiB physical context ceiling**. It does not enlarge
`MAX_PACK` or `MAX_DECODE_UNIT`.

### Target-relative small mosaic contribution floor

For mosaic candidate retention only:

- targets >=1 KiB may retain a root that copies at least `max(256 B, target_size / 8)`;
- targets >=32 KiB retain the existing stricter `max(4096 B, target_size / 20)` rule;
- candidate fanout remains bounded;
- inherited v0.28 one-base delta selection is unchanged;
- final multi-root admission still requires exact measured bytes and >=2 roots.

This rule is fixed before attempt-4 measurement. It is intentionally narrow: it removes an impossible
absolute floor for small targets without turning forests of tiny files into an unbounded delta search.

## Safety and locality invariants

Attempt #4 must preserve:

- dependency depth exactly **1**;
- at most **4** mosaic bases;
- every mosaic base is a direct node;
- <=**8x** descriptor-actual/physical read amplification;
- <=**2 MiB** dedicated co-pack context;
- <=**8 MiB** aggregate mosaic source-index bound;
- bounded candidate fanout and small-graph exhaustive correctness floor;
- exact reconstruction before admission;
- authenticated physical leaves and tail metadata recovery;
- exact v0.28 artifact fallback for every workload where the new complete graph is larger.

## Causal regression tests required before measurement

Before the full benchmark can run, tests must prove:

1. shifted/reordered is discovered but **not** forced into a losing pack-local/external representation;
2. source-like can produce an admitted `pack_mosaic` node with all bases direct and <=8x locality;
3. root-diversity can build a dedicated <=2 MiB base co-pack and a depth-1 external mosaic when the
   complete physical rearrangement saves bytes;
4. small-metadata can retain its sub-4 KiB contributing second root and upgrade the inherited single
   delta only when the complete mosaic record wins;
5. false-neighbor/incompressible controls do not manufacture mosaic nodes;
6. primary metadata recovery, payload corruption refusal and exact strong verification remain green.

## Acceptance gate — unchanged

Attempt #4 must clear **the exact full-artifact gate frozen before attempt #1**:

- v2 complete-artifact bytes **>2.0% smaller** than complete v0.28 artifacts;
- v1+v2 combined complete-artifact bytes **>3.0% smaller**;
- at least **4/10 v2 workloads** improve;
- at least **5 workloads combined** select complete mosaic artifacts;
- **0 workload regressions** under exact v0.28 fallback;
- maximum descriptor-actual mosaic read amplification **<=8x**;
- strong verification on every candidate;
- recovery/corruption grammar tests green.

No threshold is changed by this attempt.

## If attempt #4 passes

Passing still does **not** earn v0.29.0. It earns the generalization tranche across the existing 15
v0.28 neutral/resemblance workloads, where the placement compiler must prove it does not disturb the old
frontier and must expose its additional creation CPU. Structural competitor aggregates follow only after
that reconciliation.

## If attempt #4 fails

Preserve the result before another mechanism change. In particular:

- if pack-local recipes do not survive final metadata compression, abandon them rather than hand-tuning
  the descriptor around one 128 B case;
- if root co-packing loses more compression than the mosaic target saves, the locality constraint is
  telling us the reuse is not physically cheap enough;
- if the small-target path creates noisy false candidates, restore the stricter floor and treat the 2 KiB
  win as niche rather than broad policy;
- if fewer than four v2 workloads can ever beat v0.28's solid-pack marginal economics, mosaic should
  remain an optional specialized transform and the next core frontier should move elsewhere.
