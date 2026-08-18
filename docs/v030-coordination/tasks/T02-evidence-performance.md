# T02 — Authoritative evidence / performance / competitor matrix

- **Owner:** slot-02
- **Priority:** P0
- **State:** READY
- **Branch:** `agent/v030-coop-evidence-performance`
- **Dependencies:** benchmark harness work may proceed now; final authority must run on the exact reconciled T00 candidate and imported T01/T03 implementation.

## Objective

Turn v0.30 from promising mechanism evidence into exact release evidence without lowering any threshold or mixing independent savings.

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

## Failure behavior

If a gate fails, preserve the machine result and mark the task `BLOCKED` or create a narrowly scoped regression task for the owning slot. Never tune the workload, timing boundary, threshold, or comparator to turn red into green.

## Handoff

Set `REVIEW` with exact evidence files, run IDs/artifacts, environment/tool versions, raw/summary results, source SHA, topology checker output, and a concise statement of every remaining loss or unavailable comparator.
