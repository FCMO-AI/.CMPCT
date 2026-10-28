# Logs inverse-decode codec attribution — preregistration

Status: **FROZEN FORGE D2 CAUSAL ATTRIBUTION / ZERO RELEASE CREDIT**

## Why this experiment exists

Accepted `R25_LOGS_RESTORE_INNER_ATTRIBUTION_RESULT.md` localizes **28.7881%** of complete promoted Logs extraction to the exact inverse-decode boundary `LOGS.V2.BASE._decode`, across three stable inverse-decode calls per extraction. The deterministic Logs fixture offers two gzip-derived loose members and one Zstd-derived loose member; xz is discovered but is not selected by the canonical native-safe writer. Before changing decode implementation, Forge must identify which selected codec actually owns the material wall time.

This is attribution only. It changes no archive bytes, reader semantics, codec, output, integrity check, locality bound, recovery behavior, comparator or release threshold.

## Frozen target and semantic owner

- target: `neutral_hostile_v1/05_logs_and_telemetry`;
- selected representation must remain `logs-inverse`;
- exact timed semantic owner: `experiments.entropygraph_v030_logs_inverse_profile_v3.V2.BASE._decode`;
- expected selected inverse-codec call geometry per complete extraction: **gzip = 2, zstd = 1, xz = 0**;
- complete extraction must reconstruct the exact canonical user tree and pass strong verification.

The experiment may wrap `_decode` only to measure elapsed wall time by its `codec` argument, then call the inherited implementation unchanged. No output may be substituted or cached.

## Frozen method

Run **15 alternating paired rounds** of:

1. ordinary promoted Logs complete extraction control;
2. instrumented promoted Logs complete extraction with per-codec timers around the exact `_decode` owner.

Warm both arms once first. Each measured extraction uses a clean destination. Record total extraction wall, per-codec cumulative wall and per-codec call counts.

Instrumentation is valid only if:

- all 15 control and 15 instrumented extractions reconstruct the exact tree;
- selected representation is `logs-inverse`;
- strong verification passes;
- instrumented/control median wall ratio `<=1.10x`;
- per-codec call counts are stable in every measured instrumented extraction;
- stable counts equal gzip `2`, zstd `1`, xz `0`.

## Frozen materiality and terminal decision

For each selected codec, material headroom requires both:

- median cumulative codec decode time **>=0.0020 s**; and
- share of median instrumented complete extraction **>=5%**.

Terminal decision is the ordered `+` join of material codec owners using the vocabulary:

- `GZIP_INVERSE_DECODE_HEADROOM`;
- `ZSTD_INVERSE_DECODE_HEADROOM`;
- `XZ_INVERSE_DECODE_HEADROOM`.

If no codec crosses both floors: `TRACKED_INVERSE_CODECS_INSUFFICIENT`.

If custody/instrument validity fails: `INVALID_INVERSE_CODEC_ATTRIBUTION`.

No threshold may change after result-bearing execution.

## Interpretation law

A material codec becomes eligible for a later R0-R2 implementation A/B, but this attribution alone grants no product or release credit. A codec that is not material under this exact regime must not receive a tuning campaign without a reopening predicate such as changed fixture geometry, changed decoder implementation, or changed selected inverse-edge portfolio.

Correctness, logical SHA-256, authenticated pack checks, recovery, hostile corruption rejection and locality remain non-borrowable.
