# CMPCT v0.29 research generalization tranche

Status: **pre-registered after attempt #5 full-artifact success; no v0.29.0 claim yet**  
Candidate: attempt #5 Mosaic Placement + Residual Program Packing  
Inherited baseline: CMPCT v0.28.0 EntropyGraph II strict portfolio  
Canonical on-disk revision: **24 unchanged**

## Why this tranche exists

Attempt #5 is the first mechanism in the multi-root campaign to clear the frozen mosaic-specific
full-artifact gate. Its exact preserved result is
`benchmarks/history/2026-08-17-mosaic-v029-full-artifact-attempt5.json`:

- v2: **8,589,119 → 8,364,515 B (-2.6150%)**, 4/10 improved, 0 regressed;
- v1+v2: **14,829,232 → 14,175,654 B (-4.4074%)**, 9/18 improved, 0 regressed;
- max mosaic read amplification: **5.1233x**;
- max additional residual-program over-read: **0.0151x**.

That proves a real multi-root/version-chain frontier. It does **not** prove that the mechanism belongs in
a scarce numeric CMPCT release. The next question is whether the candidate survives the older, broader
v0.28 frontier rather than being useful only on the corpus designed to expose its new information model.

## Fixed inherited frontier

Generalization uses the exact public deterministic generators that supported v0.28:

### `neutral_hostile_v1` — 10 workloads

1. developer repository
2. office workspace
3. media library
4. analytics and database
5. logs and telemetry
6. incremental backups
7. incompressible/encrypted-like data
8. many tiny files
9. ML artifacts
10. large mixed binary

### `resemblance_hostile_v1` — 5 workloads

1. shifted versions
2. false neighbors
3. boundary churn
4. DEFLATE family
5. incompressible data

The preserved v0.28 aggregate for those 15 workloads is **137,557,457 B**. v0.28's resemblance graph was
strictly selected on only 3/15 workloads; the other 12 retained the inherited v0.25 artifact.

Footnote: this tranche regenerates those exact deterministic workload definitions from the repository.
It does not substitute new “representative” files after seeing attempt-5 behavior.

## Generalization benchmark contract

For each workload, one attempt-5 build must expose both:

- the exact v0.28 portfolio artifact produced from the same source tree;
- the exact attempt-5 research graph and outer candidate.

The outer candidate remains `min(exact v0.28 artifact, exact attempt-5 graph)` by bytes. Therefore a
research representation may lose locally without contaminating the user-facing candidate.

Every selected artifact is strongly verified against the source tree hash before its row is accepted.

## Pre-registered acceptance gate

Generalization passes only if **all** of the following are true:

1. **0/15 per-workload size regressions** versus exact v0.28;
2. aggregate candidate bytes are **strictly smaller** than aggregate exact v0.28 bytes;
3. at least **1/15 workload** is strictly smaller than its exact v0.28 artifact;
4. every selected candidate strong-verifies to the exact source tree hash;
5. maximum descriptor-actual mosaic read amplification remains **<=8.0x**;
6. maximum additional residual-program read amplification remains **<=2.0x**;
7. all residual raw packs remain **<=256 KiB** and all dependency depth remains 1;
8. the aggregate attempt-5 portfolio creation time is **<=3.0x** the aggregate embedded v0.28 portfolio
   creation time measured inside the same builds;
9. the full repository regression suite and public-surface guard remain green.

The byte gate is intentionally “strictly smaller” rather than a post-hoc percentage. The material release
case already comes from the independently frozen 18-workload mosaic campaign; this tranche is a
**generalization and anti-overfitting test**. Requiring an arbitrary new 1% on an unrelated old frontier
after seeing neither result would conflate generalization with a second product mission.

The 3x creation ceiling is a release-quality guardrail, not a claim that 3x is free. Actual creation and
verification ratios remain reportable even when below the ceiling and may motivate optimization before
canonical promotion.

## Structural competitor tranche

If the 15-workload gate passes, the same candidate must be measured on the two complete recursive suite
aggregates using the established v0.28 competitor harness semantics:

- ZIP/Deflate-9;
- solid tar + Zstd-19 when available;
- 7z/LZMA2 when available;
- ZPAQ method 5 when available;
- DwarFS when available;
- Borg repository snapshot when available.

This comparison retains semantic mismatches instead of collapsing everything into one “compression
winner.” Solid archives, backup repositories and random-access/recovery-aware CMPCT artifacts do not
provide identical products.

### Competitor acceptance policy

Competitor availability is environmental and therefore cannot be a hard release gate. The required
properties are:

- attempt #5 aggregate bytes must be **<= the preserved v0.28 CMPCT aggregate** for each suite;
- creation and strong-verification time remain visible;
- unavailable competitors are recorded, never silently dropped;
- if a competitor is available, exact tool/version/semantics are retained in the evidence record;
- any new claim such as “smaller than 7z” or “beats solid tar+Zstd” may be made only for the measured
  aggregate where the bytes support it.

A useful promotion signal—but not a precondition—is whether attempt #5 closes or reverses v0.28's small
resemblance-aggregate gap to solid tar+Zstd/ZPAQ while preserving CMPCT's locality/recovery semantics.

## What a green result earns

A green generalization + structural-competitor tranche earns a **v0.29 release proposal**, not an automatic
merge/version bump. Canonical promotion would still require:

- a reader-visible format/revision decision for CMPNX10/CMPNX11 features;
- independent golden vectors and malformed/resource-hostile vectors;
- native reader parity for any newly canonical node descriptor;
- recovery semantics and tail-authentication parity;
- portability/ZIP/platform surfaces reconciled;
- public docs/site benchmark tables updated from durable evidence;
- no stale v0.28 claim remaining where v0.29 becomes canonical.

## What a red result means

- size regression on any old workload → fallback or selector integration is wrong;
- no strict old-frontier improvement → mechanism remains valuable but specialized; do not pretend it is a
  universal compression upgrade;
- >3x creation cost → optimize candidate discovery/compiler reuse before release proposal;
- locality/resource failure → locality wins; do not trade it for ratio headlines;
- competitor loss → record it with semantics; do not cherry-pick only favorable formats.

A red generalization result does not erase attempt #5's real mosaic-specific gains, but it blocks v0.29
promotion until the broader product case is repaired.
