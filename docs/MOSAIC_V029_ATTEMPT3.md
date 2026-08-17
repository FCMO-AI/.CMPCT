# CMPCT Mosaic full-artifact attempt #3 — pack-marginal admission

Status: **pre-registered research attempt; no v0.29.0 claim**  
Parent campaign: `docs/MOSAIC_V029_CAMPAIGN.md`  
Frozen full-artifact gate: **unchanged from before attempt #1**

## Why attempt #2 failed

Attempt #2 is preserved in
`benchmarks/history/2026-08-17-mosaic-v029-full-artifact-attempt2.json`.

Its complete-artifact result was:

- v1: **6,240,113 → 5,813,433 B (-6.8377%)**, 4/8 improved, 0 regressed;
- v2: **8,589,119 → 8,428,520 B (-1.8698%)**, 1/10 improved, 0 regressed;
- combined: **14,829,232 → 14,241,953 B (-3.9603%)**, 5/18 improved, 0 regressed;
- maximum descriptor-actual read amplification: **4.0005x**.

Attempt #2 therefore improved the combined result and fixed v1 reordered-target eligibility, but still
failed the frozen gate because v2 stayed below >2% and only one v2 workload improved instead of four.

The strongest diagnostic case is v2 `02_shifted_reordered_merge`. Attempt #2 now discovers and encodes a
valid depth-1 mosaic at **1.993x** amplification and estimates **246,534 B** of mosaic record savings
against standalone direct storage. Yet the complete mosaic graph is **503,958 B** versus **502,014 B**
for v0.28: **1,944 B larger**. The target is already compressed cheaply inside v0.28's similarity-ordered
solid root pack, so standalone direct cost is not its real marginal archive cost.

A second failure survives attempt #2: roots are kept as mosaic candidates only when their individual
one-root delta saves bytes. That filters out the intended pattern where root A explains one region and
root B another; either root alone can lose because the rest of the target stays literal, while A+B wins.
The primitive v2 root-diversity workload demonstrates exactly this phenomenon.

## Attempt #3 hypothesis

A full-artifact mosaic selector should make two decisions independently:

1. **information contribution:** retain a bounded root when it copies enough exact target information,
   even if its one-root representation loses;
2. **physical admission:** promote a direct leaf only when removing it from the *actual current root pack*
   saves more physical bytes than the complete mosaic record costs.

This should recover jointly useful roots without accepting the attempt-2 shifted/reordered “paper win”
that was already free inside a solid pack.

## Mechanism changes

Implementation: `experiments/entropygraph_v029_mosaic_packaware.py`  
Stable evidence entry point: `experiments/entropygraph_v029_mosaic_strict.py`

### Bounded partial-root retention

The inherited v0.28 candidate set and central-base assignment remain unchanged. The broader mosaic-only
candidate layer now retains an exact root contribution when it copies at least
`max(4096 B, target_size / 20)`, even when the one-root delta saving is <=0.

Candidate fanout remains bounded by attempt #2's discovery caps. Final mosaic admission still requires
exact encoding, byte-for-byte reconstruction, at least one-third of the target copied, <=8x locality,
and a complete stored-byte win.

### Copy-information-first ranking

Mosaic roots are ranked by exact copied bytes before one-root economics. One-root saving remains a
secondary signal, not the definition of whether a root contains useful information.

### Pack-marginal leaf tournament

Attempt #3 no longer compares a direct leaf mosaic against `_direct_cost(target)`.

For each bounded leaf candidate, it measures:

- the current v0.28-style physical root-pack cost;
- a fresh six-ceiling pack tournament with that target removed;
- the exact complete mosaic record cost including header and per-root metadata;
- descriptor-actual read amplification using the trial physical groups.

The leaf is promoted only when:

`current_pack_cost - pack_without_target_cost - complete_mosaic_record_cost`

is materially positive and locality remains <=8x.

At most **32** leaf candidates enter this tournament. Accepted promotions update the actual current pack
state before the next target is considered, so savings are not double-counted against one original pack.

### Dependency and grammar invariants

- selected v0.28 bases remain protected direct nodes;
- mosaic bases must remain direct;
- leaf targets are removed from direct packs only after a positive physical marginal tournament;
- descriptors remain compacted to roots that actually emit COPY operations;
- dependency depth remains exactly 1;
- the authenticated CMPNX9 reader/recovery grammar is unchanged from attempts #1/#2.

## Regression tests added before measurement

`tests/test_mosaic_archive.py` now requires:

1. the shifted/reordered target to enter a real pack-marginal tournament and be rejected when its solid
   pack already makes direct storage cheaper overall;
2. the root-diversity workload to retain multiple **individually unprofitable but jointly informative**
   roots and send the target into a pack-marginal tournament;
3. all emitted mosaic bases to remain direct;
4. exact reconstruction, authenticated-tail recovery, physical corruption refusal and outer v0.28
   fallback to remain green.

Footnote: the shifted/reordered test deliberately changed from attempt #2's “must promote” assertion to
attempt #3's “must discover, tournament, and reject if marginally worse” assertion. That is not moving a
benchmark goalpost; it encodes the new causal lesson from the preserved attempt-2 complete-artifact
record.

## Acceptance gate — unchanged

Attempt #3 must clear **the exact gate frozen before attempt #1**:

- v2 complete-artifact bytes **>2.0% smaller** than complete v0.28 artifacts;
- v1+v2 combined complete-artifact bytes **>3.0% smaller**;
- at least **4/10 v2 workloads** improve;
- at least **5 workloads combined** select complete mosaic artifacts;
- **0 workload regressions** under exact v0.28 fallback;
- maximum descriptor-actual mosaic read amplification **<=8x**;
- strong verification on every candidate;
- recovery/corruption grammar tests green.

No threshold has been reduced after attempts #1 or #2. If attempt #3 fails, the failure must be recorded
before another mechanism is tried.

## If attempt #3 passes

Passing still does **not** earn v0.29.0. The next tranche must generalize the strict engine across the
existing 15-workload v0.28 neutral/resemblance frontier, preserve every old workload at <= its v0.28
artifact, expose the extra creation CPU from broader discovery/pack tournaments, and then run structural
competitor aggregates on the expanded mosaic workloads.

A numeric project version can be proposed only after the old frontier, new multi-root frontier,
reliability/locality contract and practical creation cost are reconciled together.
