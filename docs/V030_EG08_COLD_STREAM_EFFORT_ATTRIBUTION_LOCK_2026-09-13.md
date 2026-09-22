# v0.30 EG08 cold-stream effort attribution lock — 2026-09-13

Status: **preregistered causal attribution; research evidence only**

## Question

EG09's first fused implementation can safely recognize V25 requested-level-19 calls as ordinary final object-pack emission without changing level-3 geometry probes. EG08, however, applies its post-build effort ladder to every non-hot physical pack, including any **cold stream pack** that is not an `inflate_stream` root. If those cold stream packs earn selected-byte savings, a level-19-only first-pass hook cannot be byte-identical to EG08.

## Falsifiable hypothesis

Across the same nine frozen EG07-valid transfer surfaces, EG08 earns **zero selected bytes** from packs whose telemetry says `stream_pack=true` and `hot_stream_root=false`.

One cold stream pack with `saved_bytes > 0` falsifies the hypothesis.

## Method

Use only EG08's already-emitted authenticated/verified effort telemetry after a normal build. Do not change compression, geometry, selection, locality, thresholds or files.

For each frozen surface report:

- count of cold stream packs;
- count of cold stream packs changed by EG08;
- bytes saved by cold stream packs;
- selected effort levels for those packs.

Aggregate the same values across all nine surfaces.

## Interpretation

- If the hypothesis survives, requested-level-19 final object packs are sufficient to explain EG08's selected-byte changes and the narrow EG09 fusion scope remains plausible.
- If falsified, the current EG09 implementation is expected to miss part of EG08. The next fusion must distinguish **final cold-stream emission** from level-3 probes structurally; globally changing requested-level-3 `zc` calls is forbidden because that would perturb geometry/selection.

This attribution changes no Genesis score, version, comparator, locality, integrity/recovery or ONE status.
