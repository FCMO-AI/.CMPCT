# v0.30 physical compression-effort attribution — mission lock

Date: 2026-09-13
Branch authority: `agent/v030-authoritative-integration`
Status: **preregistered research oracle; no product/release credit**

## Entering evidence

The accepted Office physical-economics referee holds physical membership/payload constant while replacing explicit filesystem control with implicit-v4. That substitution closes only ~0.38% of the same-run Office regret versus the exact frozen Genesis v0.29 product. The remaining Office gap therefore lives outside filesystem-control encoding.

However, the current EG05/EG07 research path deliberately caps inherited EntropyGraph compression requests at Zstd level 1 to preserve v0.30 creation speed, while the inherited v0.25 physical pack writer uses Zstd level 19. It is therefore premature to attribute the remaining physical gap specifically to pack geometry/locality.

## Falsifiable hypothesis H-EFFORT-1

A material fraction of the Office and Analytics density regret is caused by **compression effort on the already-selected physical units**, not by their membership/geometry.

Hold every raw physical pack byte, pack boundary, member-to-pack relationship, filesystem control, locality decode unit and recovery relationship fixed. Recompress those same raw physical units at:

- current v0.30 effort: Zstd level 1;
- mature inherited effort: Zstd level 19.

No relationship discovery, regrouping, selector change, locality change or new representation is allowed in this oracle.

## Required surfaces

Use the stable current15 trees for:

- `02_office_workspace` — primary high-byte deficit;
- `04_analytics_and_database` — independent high-byte transfer surface.

Execute frozen v0.29 from source `02b8b27cb2d97af7c6e0797984a898e8fa8a8e5d` through the exact Genesis product facade `experiments/entropygraph_v029_residual_strict.py` under the existing fail-closed source seal.

## Exactness law

Before any counterfactual receives credit, re-encoding every current physical unit at level 1 must reproduce its current codec decision and payload **byte-for-byte**. Any mismatch yields `PHYSICAL_EFFORT_ATTRIBUTION_INVALID`.

The level-19 oracle may change only the codec/payload bytes of an existing raw physical unit. Pack count, raw bytes, membership, decode-unit size and filesystem semantics remain fixed. PH header width is charged unchanged. Any saved bytes are therefore compression-effort headroom, not geometry headroom.

## Measurements

For each surface record:

- tree SHA and logical bytes;
- frozen-v0.29 complete bytes and source/module provenance;
- current implicit-v4 complete candidate bytes;
- current physical bytes and pack count;
- exact level-1 reproduction result;
- level-19 counterfactual physical bytes;
- complete-byte counterfactual obtained only by replacing physical payload byte cost;
- absolute and fractional regret recovered versus frozen v0.29;
- median compression-only CPU/wall for level 1 and level 19 over three same-process repetitions;
- peak RSS signal;
- current strong verify, filesystem fidelity and tail recovery;
- current max/mean selective amplification and absolute max decode unit.

The counterfactual is an oracle, not an archive and not release evidence. It must not claim recovery/integrity execution on bytes that were not materialized into a valid artifact.

## Causal classification

For each surface, using the same-run complete-candidate regret to frozen v0.29:

- `EFFORT_DOMINATES` if level-19 recompression of identical physical units recovers **>=50%** of that regret;
- `GEOMETRY_DOMINATES` if it recovers **<=20%**;
- `MIXED` otherwise.

These thresholds classify where to spend research; they are not product selector thresholds and may not be copied into admission policy.

The overall verdict is:

- `PHYSICAL_EFFORT_ATTRIBUTION_INVALID` if exact level-1 reproduction or provenance/invariants fail;
- `PHYSICAL_EFFORT_DOMINATES` if Office is `EFFORT_DOMINATES` and Analytics does not contradict with `GEOMETRY_DOMINATES`;
- `PHYSICAL_GEOMETRY_DOMINATES` if Office is `GEOMETRY_DOMINATES` and Analytics does not contradict with `EFFORT_DOMINATES`;
- `PHYSICAL_EFFORT_GEOMETRY_MIXED` otherwise.

## Disproof and next decision

If effort dominates, do **not** globally restore level 19. The next Builder hypothesis must use cheap, content-derived opportunity gating or reuse so stronger effort is spent only where expected byte value justifies CPU/RSS cost, and it must preserve v0.30's Genesis creation advantage.

If geometry dominates, stop revisiting compressor knobs and move to a representation-level locality counter-invention.

If mixed, attribute by pack/family statistics before changing either mechanism.

## Preservation

Frozen Genesis/ONE scores remain frozen. `research/cmpct1` remains an active secondary research line. No numeric version, format, reader, locality ceiling, integrity rule, recovery rule or comparator setting changes in this oracle.