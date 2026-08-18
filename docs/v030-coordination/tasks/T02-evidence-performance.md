# T02 — Authoritative evidence / performance / competitor matrix

- **Owner:** slot-02
- **Priority:** P0
- **State:** CLAIMED
- **Branch:** `agent/v030-coop-evidence-performance`
- **Dependencies:** benchmark harness work may proceed now; final authority must run on the exact reconciled T00 candidate and imported T01/T03 implementation.

## Active claim

- Claim owner: `resumed-agent-sol-a`
- Atomic claim commit on coordination branch: `f651e5a724be3c2354917504de4258611e2027fa`
- Integration SHA observed at claim: `e48d74a97b8ac4bbf6c04bea483fdc0c486a49dc`
- Latest integration SHA observed immediately before implementation audit: `851b2ec3a4c1134c965302330fd0f908c57f481d`

Footnote: the newer integration SHA currently contains coordination-state movement; final release authority still requires a fresh exact-candidate rerun after T00 reconciliation and T01/T03 import rather than borrowing evidence from this bootstrap branch.

## Objective

Turn v0.30 from promising mechanism evidence into exact release evidence without lowering any threshold or mixing independent savings.

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

Set `REVIEW` with exact evidence files, run IDs/artifacts, environment/tool versions, raw/summary results, source SHA, and a concise statement of every remaining loss or unavailable comparator.
