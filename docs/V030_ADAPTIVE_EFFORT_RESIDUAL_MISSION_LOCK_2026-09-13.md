# v0.30 adaptive-effort residual attribution mission lock — 2026-09-13

Status: **preregistered Forge experiment; no release/R4 credit**

Parent authority: `docs/V030_PHYSICAL_EFFORT_ATTRIBUTION_RESULT_2026-09-13.md`

## Mission lock

The accepted H-EFFORT-1 oracle held Office/Analytics physical geometry fixed and showed that Zstd level 19 on the exact current raw physical units recovers essentially all same-run density regret versus frozen v0.29: Office 484,719 B (100.43%) and Analytics 960,457 B (99.99%). This makes compression effort, not a representation/locality redesign, the dominant causal target until falsified.

Historical v0.30 work already contains generic adaptive-effort machinery, including the C25EG08 lower-effort policy frontier. Do **not** invent another selector, threshold family, representation or geometry rule before measuring what the existing adaptive-effort line actually captures on the current Office/Analytics physical units.

## Falsifiable hypothesis

**H-EFFORT-2:** existing generic adaptive-effort machinery captures most of the level-19 byte oracle at materially lower creation cost than globally applying level 19; the remaining density debt is concentrated in a small, causally identifiable subset of packs/effort transitions rather than requiring broader geometry changes.

Disproof: H-EFFORT-2 loses if the existing generic policy captures <80% of the fixed-geometry level-19 saving on either Office or Analytics, or if obtaining >=80% requires effort whose measured compression CPU is not materially below full level-19 compression on that surface.

The 80% boundary is a preregistered causal classifier only. It is not a product threshold and may not be tuned after seeing results.

## Referee

On the exact current stable Office and Analytics trees, freeze the same raw physical units used by H-EFFORT-1. For every pack, record effective stored payload bytes and compression CPU/wall for levels `1, 3, 6, 9, 12, 15, 19` (RAW wins remain RAW). Then evaluate, without changing geometry:

1. incumbent level-1 storage;
2. the existing generic adaptive-effort policy/policies already present in repository history, using their frozen generic inputs/rules rather than workload identity;
3. full level-19 oracle;
4. a diagnostic per-pack Pareto oracle that chooses among the frozen effort ladder only for attribution and receives no product credit.

For each surface and pack report:

- raw bytes and incumbent codec/payload;
- payload bytes at every frozen effort level;
- CPU/wall at every level;
- existing-policy selected level and payload;
- full-L19 payload;
- bytes recovered versus L1;
- residual bytes to L19;
- incremental CPU per recovered byte;
- whether size progression is monotonic across the ladder;
- whether a first-regression/early-stop rule would miss a later win;
- RAW-incumbent promotion/demotion where applicable.

Aggregate report must include policy capture fraction of the H-EFFORT-1 oracle, compression CPU/wall versus L1 and L19, pack counts by selected level, residual-byte concentration, and the top byte-weight residual packs.

## Invariants and hostile reviewer

- Same stable input trees and exact physical geometry as H-EFFORT-1.
- No pack-boundary, membership, filesystem-control, locality, integrity, recovery or reader-semantic change.
- Level 1 must reproduce current physical payloads byte-for-byte before any attribution receives credit.
- Frozen v0.29 comparison remains source-sealed through the exact Genesis facade when used.
- No workload name, path, content hash or benchmark identity may be introduced as a policy input.
- Research-time profiling/oracle knowledge is not candidate creation time and may not be hidden in a product claim.
- Preserve non-monotonic ladders and losing packs; do not smooth or threshold them away.
- No aggregate/R4/release credit from this attribution experiment.

## Decision table

- `EXISTING_EFFORT_POLICY_SUFFICIENT`: existing generic policy captures >=95% of L19 saving on both surfaces with materially lower compression CPU than full L19. Next action: materialize/composition-admit the existing mechanism and run ordinary product gates.
- `EFFORT_POLICY_RESIDUAL_LOCALIZED`: captures >=80% on both surfaces, but residual bytes are concentrated enough to motivate one preregistered cheap continuation/gating signal. Next action: attack that residual only.
- `EFFORT_POLICY_INSUFFICIENT`: <80% capture on either surface. Next action: explain the missed pack class before adding policy complexity; geometry remains frozen unless new evidence overturns H-EFFORT-1.
- `EFFORT_ATTRIBUTION_INVALID`: level-1 identity, stable-tree identity, policy provenance or measurement invariants fail.

## Preservation

Frozen Genesis scores remain ONE `275,219,901 B`, v0.29 `137,499,525 B`, frozen v0.30 `150,055,575 B`; frozen creation CPU remains ONE `3.0791 s`, v0.29 `806.5369 s`, v0.30 `33.0603 s`. `research/cmpct1` remains untouched as the active secondary line. No numeric version, tag, release, locality bound, integrity/recovery rule or comparator semantics change here.
