# v0.30 EG09 fused final-pack Mission Lock — 2026-09-13

Status: **preregistered Builder contract; research only**

## Problem

Strict EG08 eligible-nine transfer established that density, source provenance, strong verification, recovery, unchanged locality geometry and Analytics transfer all survive. Its only failed gate is exported creation economics. EG08 currently pays a complete EG07 build whose final ordinary physical packs are encoded at capped Zstd-1, then reopens those packs, decodes them, and recompresses the same raw bytes through the fixed `3,6,12,19` effort ladder.

Tie-continuation attribution separately falsified `stop-on-tie`: 1,631 attempts could be removed only by giving back 71,520 B across 599 packs. The repair therefore must remove duplicated work rather than weaken the useful search.

## Mechanism hypothesis

V25 uses requested Zstd level 19 specifically when emitting ordinary final physical object packs, level 3 for geometry probes and cold stream slabs, and level 12 for metadata. EG05/EG07 cap all those calls to level 1. A narrow EG09 engine can preserve EG07's level-1 behavior for every request except **requested level 19 final-pack calls**. For those calls it can:

1. compute the exact EG07 level-1 incumbent;
2. if that incumbent would have been stored raw, return it unchanged so EG07 makes the same raw/compressed decision;
3. otherwise execute the exact EG08 `3,6,12,19` best-so-far ladder, including tie continuation and stop-at-first-worse;
4. return the final selected compressed bytes directly to V25 during first-pass physical construction.

This should eliminate EG08's second archive parse/decode/rewrite pass while preserving probes, pack membership, stream-root decisions, metadata compression and the final archive bytes.

## Falsifiable identity requirement

EG09 receives **zero credit** unless, on every preregistered surface, its complete archive is byte-for-byte identical to EG08 built from the same source tree. Matching only stored-byte totals is insufficient.

Any identity mismatch retires this fused implementation until the semantic difference is explained.

## Frozen evaluation surface

Use the same eligible-nine transfer set frozen before EG08 evidence:

- neutral: Office, Analytics, Logs, ML artifacts, Large mixed binary;
- hostile: shifted versions, false neighbors, boundary churn, incompressible.

## Required measurements

For EG08 and EG09 on the same generated input per row:

- complete archive SHA-256 and byte identity;
- stored bytes;
- fresh-process creation CPU and wall;
- peak RSS;
- strong verification;
- locality geometry and <=8x amplification;
- tail recovery;
- selected effort telemetry.

EG09 must not modify the numeric version, selectors, filesystem grammar, integrity/recovery contract, locality ceiling, workload set or frozen comparator settings.

## Builder success

`EG09_FUSED_FINAL_PACK_PASSES` requires:

- 9/9 complete archive byte identity to EG08;
- 9/9 strong verification and tail recovery;
- 9/9 identical locality geometry;
- zero stored-byte changes;
- strictly lower aggregate creation CPU and wall than EG08;
- no workload with a confirmed creation regression versus EG08 under the existing 5% + 3 ms timing rule.

The old EG08 low-yield gate is then rerun against EG07. Promotion remains blocked if low-yield CPU economics still fail even after exact fusion.
