# v0.30 Office same-geometry compression-effort attribution — mission lock

Date: 2026-09-13
Status: preregistered research attribution; **not release evidence**.

## Parent result

The exact-comparator Office physical-economics referee on `efd33ff0dbf3b270ff9491f0490c1fc56da9418a` returned `OFFICE_PHYSICAL_LOCALITY_DOMINATES_REGRET`:

- frozen Genesis-v0.29 surface on the current deterministic Office tree: `5,954,929 B`;
- same physical representation + explicit filesystem control: `6,439,399 B`;
- same physical representation + implicit-v4 control: `6,437,555 B`;
- explicit -> implicit control recovery: only `1,844 B`, or `0.3806%` of B's `484,470 B` regret.

That verdict proves the filesystem control plane is not the material owner. It does **not** yet distinguish physical grouping/locality from compression-effort policy.

## Observation

The current EG01/EG05 candidate deliberately caps every inherited EntropyGraph-v0.25 Zstd request at level 1 to preserve v0.30 creation speed. The mature inherited v0.25 writer uses stronger effort on normal physical packs (level 19), cheap level 3 on cold stream slabs, and raw storage for latency-sensitive hot stream roots.

Therefore blaming pack geometry before pricing the same packs at mature effort would confound two mechanisms.

## Falsifiable hypothesis H-OFFICE-EFFORT-1

A material part of the remaining Office physical regret is **compression-effort debt on the existing physical units**, not missing relationships or wider locality.

### Fixed experiment

Build the current candidate once, decode its authenticated physical packs once, and freeze those raw pack boundaries and membership. No file relationship, stream slice, pack boundary, filesystem control, recovery layout, or locality geometry may change.

On those exact raw units, measure counterfactual payload cost at fixed Zstd effort levels `1`, `3`, `6`, `12`, and `19` under three explicitly different policies:

1. **existing-codec-only** — recompress only units already stored as Zstd; raw units remain raw. This isolates compression effort without changing codec-role policy.
2. **cold-audition** — preserve hot stream roots as raw, but allow every other raw unit to choose Zstd when `compressed + 8 < raw`, matching the inherited pack economic rule. This tests mature effort without adding a second compression layer to latency-sensitive inverse-view roots.
3. **all-audition bound** — allow every unit, including hot stream roots, to choose compressed storage by the same economic rule. This is an oracle bound only; any win here carries explicit hot-root decode-latency debt and receives no promotion credit.

The hot stream set must be derived from authenticated reconstruction recipes (`inflate_stream` dependencies), not path/file names.

The frozen v0.29 comparator must execute the exact Genesis surface `experiments/entropygraph_v029_residual_strict.py` from SHA `02b8b27cb2d97af7c6e0797984a898e8fa8a8e5d` with fail-closed `cmpct.*` import provenance.

### Verdict thresholds

Thresholds classify the causal result only; they are not product selector tuning.

Let `R` be the same-run B regret versus frozen v0.29 and let `E19` be bytes recovered by level-19 **cold-audition** while holding pack geometry fixed.

- `OFFICE_EFFORT_DOMINATES_PHYSICAL_REGRET` if `E19 >= 0.80 * R`.
- `OFFICE_EFFORT_MATERIAL_BUT_NOT_DOMINANT` if `E19 >= 0.25 * R` but `< 0.80 * R`.
- `OFFICE_GEOMETRY_RELATIONSHIPS_DOMINATE` if `E19 < 0.25 * R`.
- `OFFICE_EFFORT_ATTRIBUTION_INVALID` if pack identity, source seal, exact current level-1 accounting, or reconstruction provenance fails.

### Disproof

H-OFFICE-EFFORT-1 is rejected if level-19 cold-audition recovers less than 25% of same-run physical regret. In that case further encoder-effort tuning is the wrong lane and the next Builder may attack relationships/geometry.

## Required accounting

For every policy/level record:

- exact frozen raw-pack count and per-pack SHA-256;
- current codec and compressed bytes;
- stream-pack and hot-stream-root classification;
- counterfactual physical bytes and complete B-equivalent stored bytes;
- bytes recovered versus current B;
- remaining regret versus exact frozen v0.29;
- CPU and wall spent recompressing the frozen pack set;
- maximum raw decode unit and unchanged locality facts inherited from B.

The referee must preserve the current archive and verify it normally. Counterfactuals are attribution only and may not be presented as valid archives unless separately rebuilt and verified.

## Decision rule after attribution

If effort dominates, do **not** globally restore level 19. Use the Genesis/ONE lesson: seek cheap per-unit opportunity bounds, reuse probes, and spend high compression effort only where expected byte yield justifies CPU while preserving v0.30's large creation-speed advantage.

If geometry/relationships dominate, freeze the level-1 compute advantage and move to a representation/locality counter-invention.

If only all-audition closes the gap, the exported cost is hot-root read/decode latency; preserve that as explicit regression debt rather than silently compressing hot roots.

## Preservation

No selector threshold, locality ceiling, codec semantics, recovery rule, format revision, version number, Genesis score, ONE evidence, or release status changes in this attribution.
