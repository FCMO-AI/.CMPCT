# T02 — Authoritative evidence / performance / competitor matrix

- **Owner:** slot-02
- **Priority:** P0
- **State:** CLAIMED
- **Branch:** `agent/v030-coop-evidence-performance`
- **Dependencies:** benchmark harness work may proceed now; final authority must run on the exact reconciled T00 candidate and imported T01/T03 implementation.

## Objective

Turn v0.30 from promising mechanism evidence into exact release evidence without lowering any threshold or mixing independent savings.

## Immediate benchmark-semantics blocker — fix before running/crediting the new ablation

Slot-00 review of `benchmarks/v030_release_ablation_canonical.py` found that its prose and code currently disagree about what bytes are being compared.

The module says all four graph ablations consume the same staged filesystem manifest, but `_measure_row` currently does:

- accepted v0.29: `V029.build(source, ...)` on the original tree;
- Geometry-only: `G04.build(source, ...)` on the original tree;
- PrefixGraph-only: `PG.build(source, ...)` on the original tree;
- combined: `CANON.build(source, ...)`, which uses the new canonical product boundary, filesystem-manifest semantics and genuine r24 fallback.

It then asserts that canonical combined bytes equal `min(geometry_only, prefixgraph_only)`. That is not a valid complete-artifact identity because the operands do not pay the same metadata/filesystem semantics or use the same fallback boundary.

Required repair:

1. **Do not credit or preserve a green result from the current harness.** It is a measurement defect, not a candidate failure.
2. Separate two evidence questions explicitly:
   - **Frozen research-frontier causality:** preserve the historical repaired 15-workload source trees and the exact accepted v0.29 byte identity `137,501,815 B`; run v0.29 / Geometry / PrefixGraph / combined under exactly those historical content-tree semantics so the immutable threshold remains comparable.
   - **Canonical product parity:** compare released canonical v0.29/r24 product bytes against canonical v0.30 product bytes on the same original filesystem trees, including the new r25 filesystem-manifest semantics and genuine r24 fallback. This is an additional no-regression/product-worthiness gate; it must not silently redefine the 137,501,815 B historical baseline.
3. If you want a manifest-charged causal ablation, all four variants must use the **same prepared tree** and the same exact metadata charge. Label it as a new causal substrate; do not claim it reproduces historical accepted-v0.29 bytes unless it actually does.
4. Combined exact-minimum assertions may compare only complete artifacts with equivalent semantics. Do not compare `CANON.build(...)` to raw `G04.build(source)` / `PG.build(source)` artifacts.
5. Preserve the frozen >=687,783 B, >=3 improved, 0-regression and <=8x gates on their original accepted substrate. Add stricter canonical-product parity rather than moving those goalposts.
6. Add contract tests that deliberately make one variant omit the manifest/fallback charge and prove the harness rejects the semantic mismatch.

Footnote: productization is allowed to introduce a genuine new canonical r25 framing cost; benchmark honesty requires paying it. It is not allowed to retroactively rewrite the frozen historical v0.29 baseline so the new framing appears free.

## Immediate CI-topology debt — fix before final benchmark handoff

Fresh reconciled-head topology run `32105402278`, job `95613682897`, inspected every v0.30 workflow added by PR #56 and failed all 17 because they predate current-main's mandatory `# ci-lane:` declaration.

Affected files:

- `.github/workflows/geometry-v030-breakthrough.yml`
- `.github/workflows/v030-authoritative-pr-gates.yml`
- `.github/workflows/v030-authoritative-v2-pr.yml`
- `.github/workflows/v030-canonical-authority.yml`
- `.github/workflows/v030-external-competitors.yml`
- `.github/workflows/v030-g04-overlay-oracle.yml`
- `.github/workflows/v030-geometry-overlay-oracle.yml`
- `.github/workflows/v030-gir-build-rehab.yml`
- `.github/workflows/v030-gir-focused-complete.yml`
- `.github/workflows/v030-gir-hardening.yml`
- `.github/workflows/v030-hierarchical-geometry.yml`
- `.github/workflows/v030-prefixgraph-oracle.yml`
- `.github/workflows/v030-release-fuzz.yml`
- `.github/workflows/v030-release-generalization.yml`
- `.github/workflows/v030-release-performance.yml`
- `.github/workflows/v030-release-reader.yml`
- `.github/workflows/v030-shared-portfolio-rehab.yml`

Required repair:

1. Read `.github/AGENTS.md` and `docs/CI_ARCHITECTURE.md` from reconciled main.
2. Classify mechanism/oracle experiments as `deep`; final compression/runtime/native/external evidence as `release`; use `fast` only where the job is genuinely ordinary PR feedback.
3. Do **not** call a 90-minute benchmark `fast` to evade path-scoping rules.
4. Deep/release PR-triggered workflows must have meaningful `paths`/`paths-ignore`; remove redundant automatic triggers if a branch-scoped research push or explicit dispatch is the cleaner authority.
5. Preserve concurrency cancellation and all numeric evidence thresholds.
6. Run `python tools/check_ci_topology.py <all 17 paths>` before handoff.
7. Include the exact topology checker output in the T02 handoff.

The first checker failure exposed only missing lane declarations because lane-specific PR rules cannot execute until a lane exists. After adding declarations, fix any second-order path-scope errors rather than weakening the checker.

## Scope

- repaired exact 15-workload generalization suite;
- v0.29 / Geometry-only / PrefixGraph-only / combined complete-artifact ablations;
- shared-build rehabilitation and duplicate-work accounting;
- controlled create/extract/selective-read/peak-RSS measurements;
- external competitor matrix: ZIP/Deflate, 7z/LZMA2, solid tar+Zstd-19, ZPAQ m5 where available;
- exact-tree extraction verification for every credited competitor;
- CI routing/evidence artifact harvesting for current exact candidate SHA;
- durable accepted records under `benchmarks/history/` only after gates are genuinely satisfied.

## Frozen gates

Do not weaken:

- accepted v0.29 aggregate identity;
- >=687,783 B aggregate saving;
- >=3 improved rows;
- 0 byte-regressed rows;
- <=8x selected per-member decoded-context amplification;
- shared-build >=20% and >=5 s rehabilitation hurdle where defined;
- runtime ratios/noise policy already frozen by release gate;
- symmetric benchmark semantics and exact-tree verification.

## Owned paths

Prefer `benchmarks/v030_*`, v0.30 benchmark tests, release/deep workflows, and durable evidence records after acceptance. Do not redesign G0–G4/PrefixGraph grammar or native parsers unless a benchmark defect proves an owning implementation bug; in that case create a follow-up task for the owner slot.

## Completion evidence

1. Current candidate reproduces every frozen input tree and exact v0.29 bytes.
2. Complete candidate aggregate passes frozen compression/locality gates.
3. Controlled repeated runtime/RSS gate passes or opens explicit regression debt with exact failing rows.
4. External competitor matrix verifies extraction semantics before crediting archive size and preserves every fair loss.
5. CI artifacts/runs are tied to exact reconciled candidate SHA; queued/cancelled/superseded runs are not counted.
6. Accepted results are committed durably, with raw measurements/provenance sufficient to regenerate public claims.
7. Canonical product parity is reported separately from historical research-frontier causality; neither silently substitutes for the other.

## Failure behavior

If a gate fails, preserve the machine result and mark the task `BLOCKED` or create a narrowly scoped regression task for the owning slot. Never tune the workload, timing boundary, threshold, or comparator to turn red into green.

## Handoff

Set `REVIEW` with exact evidence files, run IDs/artifacts, environment/tool versions, raw/summary results, source SHA, topology checker output, and a concise statement of every remaining loss or unavailable comparator.
