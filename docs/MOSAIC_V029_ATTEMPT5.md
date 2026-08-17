# CMPCT full-artifact attempt #5 — Residual Program Packing

Status: **pre-registered research attempt; no v0.29.0 claim**  
Parent campaign: `docs/MOSAIC_V029_CAMPAIGN.md`  
Frozen full-artifact gate: **unchanged since before attempt #1**

## Mission lock

### Requested outcome

Continue the CMPCT frontier only with milestone-sized engineering. A future v0.29.0 must be supported by
material complete-artifact evidence, not by implementation churn or by weakening an already-failed gate.

### Current fact

Attempt #4's Mosaic Placement Compiler is the strongest complete-artifact candidate so far. It passes all
frozen full-artifact requirements except one:

- v1: **6,240,113 → 5,813,475 B (-6.8370%)**, 4/8 improved;
- v2: **8,589,119 → 8,365,894 B (-2.5989%)**, **3/10 improved**;
- combined: **14,829,232 → 14,179,369 B (-4.3823%)**, 7/18 improved;
- regressions: **0**;
- maximum mosaic read amplification: **5.1233x**.

The frozen v2 coverage requirement is >=4/10, so attempt #4 is **not accepted**.

## Negative evidence before this attempt

Two diagnostics close off attractive but invalid ways to manufacture the fourth win.

### Plain mosaic search space is exhausted under the locality contract

`benchmarks/mosaic_v029_locality_oracle.py` exhaustively checks the small named-root sets in the fixed v2
suite while charging physical root groups and enforcing <=8x. Only three targets have material ordinary
external-mosaic headroom: workloads 01, 09 and 10. Attempt #4 already captures 01 and 09.

### Small metadata cannot become an honest complete-artifact win

The 2 KiB workload 10 has a 210 B mosaic representation versus a 725 B inherited single delta, but the
richer CMPNX10 complete graph is **5,747 B** versus **4,637 B** for the v0.28 portfolio. Even a compact-
metadata oracle remains **540 B larger**. Lowering candidate floors or special-casing metadata would be
benchmark-shaped complexity, not a complete-artifact improvement.

Therefore attempt #5 does **not** change mosaic discovery, root count, dependency depth, small-target
policy, or the frozen acceptance thresholds.

## New observation — reconstruction programs are physical data too

Attempt #4 still stores every inherited one-base delta program in its own authenticated physical record.
This is structurally simple, but a version-heavy archive may contain many tiny reconstruction programs
that share the same direct base and instruction vocabulary. Each tiny program separately pays:

- one physical-record header;
- one compressed-frame decision;
- one Merkle leaf / record-table entry;
- metadata describing a distinct record id.

The logical dependency graph gains nothing from that physical separation.

The fixed v2 `05_compressed_stream_avalan` workload exposes this shape: attempt #4 has **12 depth-1 delta
programs** and its complete graph is only **118 B larger** than v0.28 (531,782 B vs 531,664 B).

## Pre-measurement residual-pack oracle

Durable evidence:
`benchmarks/history/2026-08-17-mosaic-v029-residual-pack-oracle.json`.

The oracle was fixed before attempt-5 implementation with these bounds:

- group only delta programs that reference the **same direct base**;
- deterministic target-id order;
- candidate residual-pack ceilings: 4, 8, 16, 32, 64, 128 and 256 KiB;
- hard maximum raw residual pack: **256 KiB**;
- maximum **additional recipe-pack** read amplification: **2.0x** per member;
- conservative descriptor charge: **16 B per packed member**;
- minimum measured group net saving after that charge: **128 B**;
- dependency depth change: **0**.

The untouched oracle projects exactly one new attempt-4 fallback becoming a complete-artifact win:
`05_compressed_stream_avalan`.

For that workload it finds two legal four-program groups under a 4 KiB ceiling:

- base 0: 2,302 B raw programs, **887 B** projected net saving, 0.00660x additional recipe over-read;
- base 1: 688 B raw programs, **260 B** projected net saving, 0.00409x additional recipe over-read.

Projected total physical saving: **1,147 B**, enough to turn attempt #4's 118 B deficit into an estimated
**1,029 B complete-artifact win**.

This is only an oracle. Exact CMPNX11 metadata, Merkle, record remapping and compressed bytes must now
prove the projection.

## Attempt #5 hypothesis

A bounded **Residual Program Pack** can co-locate several tiny depth-1 reconstruction programs that share
one direct base into one authenticated physical record, while each logical target retains an independent
slice descriptor.

This should reduce physical/header/metadata repetition without changing what any target depends on.

## Research representation

Attempt #5 must be implemented in a new engine file; attempts #1–#4 remain executable and their evidence
remains immutable.

Proposed research magic: `CMPNX11`.

### `delta_pack` node descriptor

A packed one-base target records:

`["delta_pack", base_id, record_id, recipe_offset, recipe_length, target_length, target_sha256]`

The referenced physical record contains the concatenated raw delta programs. The physical record itself
is authenticated, checksummed and compressed exactly like other CMPCT physical records.

Decoder behavior:

1. require `base_id` to identify a **direct** node;
2. decode/authenticate the residual physical record;
3. bounds-check `recipe_offset` and `recipe_length` before slicing;
4. run the existing bounded `delta_decode` against that slice;
5. require exact expected output length and SHA-256.

There is no delta-on-delta recursion. Dependency depth remains exactly 1.

## Compiler design

Attempt #5 should be a **post-placement compiler**, not a rewrite of attempt #4:

1. build attempt #4's complete raw Placement Compiler graph unchanged;
2. inspect only ordinary `delta` nodes whose bases are direct;
3. group programs using the frozen oracle policy;
4. pack only groups that still save >=128 B under exact physical compression and conservative descriptor
   accounting;
5. remove the superseded dedicated delta records;
6. remap every surviving record id in node/file descriptors;
7. append residual records and convert their member nodes to `delta_pack` slices;
8. rebuild physical offsets, Merkle leaves/root and both authenticated metadata copies;
9. strong-verify/extract the resulting CMPNX11 graph before it can enter portfolio selection;
10. compare the exact complete CMPNX11 artifact with exact v0.28 and keep v0.28 whenever it is smaller.

Footnote: the compiler starts from attempt #4 bytes precisely so Mosaic Placement behavior is not
reimplemented, forked, or accidentally regressed while testing this independent physical optimization.

## Fixed resource/locality rules

Attempt #5 may not relax any inherited constraint. In addition it fixes:

- residual raw pack <= **256 KiB**;
- residual pack members >= **2**;
- all members in one residual pack share one direct base;
- additional residual-program over-read <= **2.0x** for every member;
- group physical saving after conservative descriptor charge >= **128 B**;
- maximum target output remains `MAX_CHUNK`;
- maximum dependency depth remains **1**;
- mosaic roots/bounds and <=8x mosaic locality remain unchanged;
- authenticated-tail metadata recovery remains mandatory;
- physical payload corruption remains fail-closed.

“Additional recipe over-read” is deliberately separate from inherited base-pack locality. Attempt #5 does
not get credit or blame for changing the direct base pack because it does not change it; it only replaces
several independent recipe records with one bounded recipe record.

## Causal tests required before complete-artifact measurement

Before the frozen benchmark may run, tests must prove:

1. `05_compressed_stream_avalan` emits at least one `delta_pack` with >=2 members;
2. every `delta_pack` base is direct and dependency depth remains 1;
3. every residual pack is <=256 KiB and every member's additional recipe over-read is <=2.0x;
4. exact extraction and strong logical-tree verification succeed;
5. malformed `recipe_offset` / `recipe_length` fail closed;
6. physical residual-record corruption fails Merkle/integrity verification;
7. primary metadata damage recovers through the authenticated tail copy;
8. a single-delta control cannot manufacture a residual pack;
9. the outer portfolio never exceeds the exact v0.28 artifact.

## Acceptance gate — unchanged

Attempt #5 must clear **the same gate frozen before attempt #1**:

- v2 complete-artifact bytes **>2.0% smaller** than complete v0.28 artifacts;
- v1+v2 combined complete-artifact bytes **>3.0% smaller**;
- at least **4/10 v2 workloads** improve;
- at least **5 workloads combined** select complete research artifacts;
- **0 workload regressions** under exact v0.28 fallback;
- maximum descriptor-actual mosaic read amplification **<=8x**;
- strong verification on every candidate;
- recovery/corruption grammar tests green.

No acceptance number is reduced because attempt #4 missed coverage by one workload.

## If attempt #5 passes

Passing does **not** authorize v0.29.0. It earns a generalization tranche across the existing 15-workload
v0.28 neutral/resemblance frontier. Residual packing must then demonstrate that it is not merely useful on
the compressed-stream stress case: old workloads stay <= exact v0.28 through portfolio fallback, creation
CPU and verification latency remain visible, residual-pack locality/resource bounds are measured, and
structural competitors are rerun on the expanded frontier.

Only after that reconciliation, plus reader/native/recovery/revision work for any promoted grammar, can a
numeric project version be proposed.

## If attempt #5 fails

Preserve the exact failure before changing the mechanism. In particular:

- if exact metadata/remapping cost consumes the projected 1,147 B, the oracle was too optimistic and the
  residual-pack idea does not earn special metadata exceptions;
- if the 2.0x additional over-read cap prevents the win, locality wins the argument;
- if residual packing helps only this synthetic workload and not the later generalization frontier, keep
  it as research/niche tooling rather than core format complexity;
- do not lower the >=4/10 frozen coverage requirement.
