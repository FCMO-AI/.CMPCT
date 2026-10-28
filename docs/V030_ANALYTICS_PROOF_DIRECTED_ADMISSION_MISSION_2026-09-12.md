# v0.30 Analytics proof-directed admission mission — 2026-09-12

Status: **MISSION LOCK / REFEREE SPEC — research only, no release credit**

T0: `2026-09-12T17:10:08-06:00`

Authority at mission lock: `agent/v030-authoritative-integration @ 615cfa51b2b9477e13e815a8a2dc3fd7869f18a0`.

## Pivot custody

The frozen CMPCT1 / ONE Genesis gate remains unchanged: ONE `275,219,901 B`, v0.29 `137,499,525 B`, v0.30 `150,055,575 B`; ONE creation CPU `3.0791 s`, v0.29 `806.5369 s`, v0.30 `33.0603 s`. v0.30 remains the primary near-term line. `research/cmpct1` remains durable secondary evidence. This mission does not alter the Genesis score.

## Observed opportunity

The accepted Analytics effort referee showed that globally increasing effort is not economical. The L15->L19 attribution then showed the byte reward is sparse: only 11/52 ordinary physical packs have positive L19 savings and the full `433,350 B` L15->L19 pack delta is carried by ordinary packs. Historical C25EG02 evidence separately establishes a density existence proof at `6,134,723 B`, `449 B` below the frozen v0.29 Analytics control `6,135,172 B`, but with too much creation work.

The remaining problem is therefore admission economics, not a missing density existence proof.

## Falsifiable hypothesis

A **content-derived, path-blind cheap gate** computed from bytes already available before expensive repack can reject most non-paying packs while retaining enough high-effort winners to keep the complete Analytics archive `<= 6,135,172 B`. The gate must reduce expensive-stage work sufficiently that the same semantics have a credible route to beat the frozen ZIP creation control (`~1.359 s` in the accepted C25 evidence).

This is deliberately stronger than asking for correlation. A gate that predicts winners but does not pay for itself is a negative result.

## Disproof tests

The hypothesis is false for this mechanism if any of the following is required:

1. path, extension, corpus/workload identity, pack ordinal, or benchmark-specific labels;
2. weakening losslessness, filesystem fidelity, authentication/recovery semantics, locality, source sealing, or comparator settings;
3. moving the frozen v0.29 density target;
4. admitting so much expensive work that the measured/derived creation budget cannot plausibly cross the ZIP control;
5. missing required high-effort packs such that complete stored bytes exceed `6,135,172 B`;
6. tuning a threshold on Analytics without a held-out hostile control that exercises false-positive and false-negative behavior.

## Builder constraints

The first Builder must instrument the existing pack economics before inventing a codec. For each physical ordinary pack it should retain at minimum:

- raw bytes (`usize`);
- cheap compressed bytes and ratio from an already-required cheap candidate;
- exact expensive-candidate saving in bytes;
- expensive-candidate CPU/wall cost measured independently where practical;
- content-only cheap observables whose total observation cost is measured (for example bounded prefix statistics, byte entropy/run structure, or cheap-candidate ratio).

The Builder may use branch-and-bound / opportunity gating, but must not use filename-derived labels. Existing diagnostic labels may appear only in post-hoc reporting.

No threshold sweep receives product credit. If a small family of thresholds is used to understand a mechanism, one must be frozen before held-out evaluation and the exploration must remain explicitly research-only.

## Acceptance referee

A promotable research receipt must report, on same-input same-semantics measurements:

- complete authenticated/stored archive bytes or the exact repository-equivalent charged size;
- complete verified creation CPU and wall;
- peak RSS;
- number of ordinary packs, admitted packs, true paying packs retained, false positives, and false negatives;
- total expensive-stage CPU/wall and total cheap-observation CPU/wall;
- strong reconstruction verification;
- selective-read/locality result and reader/decode work when the representation changes;
- frozen v0.29 and ZIP controls executed hermetically or referenced only where the repository already has an accepted frozen receipt with identical semantics.

Primary density acceptance: `candidate_bytes <= 6,135,172 B`.

Primary economic target: preserve that density while driving expensive-stage work toward the historical C25-derived budget of approximately `<= 0.835 s`; final product promotion still requires complete verified creation to beat the relevant frozen comparator under the repository benchmark contract.

## Hostile reviewer questions

Before credit, answer all of these:

- Is the gate learning content structure, or merely rediscovering file type by proxy?
- Does observation cost erase the compute saved by rejection?
- Are the largest winners retained because of a general physical signal, or because Analytics happens to contain a few giant packs?
- What happens on large incompressible, adversarially structured, and deceptively cheap-ratio packs?
- Does the gate remain useful if pack ordering and paths are randomized?
- Can the same observation be reused by later selector/proof work rather than creating redundant discovery traffic?

## Negative-result policy

If cheap observables cannot separate the economic winners under held-out hostile controls, preserve the negative and escalate to a mechanism that reduces the cost of the expensive candidate itself (native bulk execution, reusable compression state/caches, or a cheaper proof audition). Do not respond by raising global effort or by adding path/type exceptions.

## ONE lesson absorbed without representation transplant

This mission intentionally imports only ONE's compute-economy lesson: fused observation, cheap opportunity gating, branch-and-bound, reusable evidence and elimination of redundant discovery. It does **not** import ONE's representation and does not change ONE's secondary status.
