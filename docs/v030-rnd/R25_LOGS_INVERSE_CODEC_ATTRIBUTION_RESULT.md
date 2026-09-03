# Logs inverse-decode codec attribution — result

Status: **ACCEPTED FORGE D2 CAUSAL ATTRIBUTION / GZIP OWNER SUPPORTED / ZERO RELEASE CREDIT**

This record closes the frozen experiment in `R25_LOGS_INVERSE_CODEC_ATTRIBUTION_PREREG.md`. It changes no archive bytes, codec semantics, reader behavior, integrity/recovery/locality rule, comparator, threshold or release state.

## Authority

- authoritative branch: `agent/v030-authoritative-integration`
- exact result-bearing source: `d13d06315139ac0c6e90d76f504b7165432115e1`
- workflow: `CMPCT v0.30 Logs inverse-codec attribution`
- workflow run: `33717793259`
- substantive job: `100530516973` (`inverse-codec-attribution`)
- artifact id: `9879138268`
- artifact: `v030-logs-inverse-codec-d13d06315139ac0c6e90d76f504b7165432115e1`
- artifact ZIP digest: `sha256:0f8470a75821d2ac00a3bf5d73825c62fdec4796c5da6d51915767e87e5e0077`
- schema: `cmpct-v030-logs-inverse-codec-attribution-v1`
- runner: Ubuntu 24.04.4 / Python 3.11.16
- release credit: **false**

The exact 15-pair attribution, frozen ratchet, CI-topology self-check, public-surface guard and artifact upload all completed successfully. This is result-bearing evidence, not a classifier-only green.

## Frozen semantic owner and validity

Target: `neutral_hostile_v1 / 05_logs_and_telemetry`.

The instrument wrapped only the inherited `experiments.entropygraph_v030_logs_inverse_profile_v3.V2.BASE._decode(codec, payload)` boundary, timed the call by codec, called the inherited implementation exactly once, and returned its bytes unchanged. No decode result was substituted or cached.

All validity gates passed:

- selected representation: **`logs-inverse`**;
- exact user-tree reconstruction and strong verification: **pass**;
- rounds: **15 alternating control/instrumented pairs** after warmup;
- control median complete extraction: **0.03634871600002043 s**;
- instrumented median complete extraction: **0.0363656119998268 s**;
- instrumentation ratio: **1.0004648307x**;
- stable exact inverse call geometry: **gzip = 2, zstd = 1, xz = 0**;
- unknown codec calls: **0**.

The instrumentation overhead is about **0.0465%**, far below the frozen `1.10x` validity ceiling.

## Exact codec attribution

Frozen materiality required both median cumulative decode time `>=0.0020 s` and share of complete instrumented extraction `>=5%`.

| codec | median cumulative decode | share of complete extraction | material |
|---|---:|---:|---|
| gzip | **0.008887544999879537 s** | **24.4394209560%** | **yes** |
| zstd | **0.0015759430000343855 s** | **4.3336078052%** | no |
| xz | **0 s** | **0%** | no |

Frozen terminal decision:

**`GZIP_INVERSE_DECODE_HEADROOM`**

## Causal interpretation

The predecessor restore attribution localized about **28.7881%** of complete Logs extraction to the inverse-decode boundary. This experiment resolves that aggregate owner: under the frozen promoted Logs portfolio, almost all material inverse-decode opportunity is the two gzip-derived loose members.

The single selected Zstd inverse edge is below both frozen materiality floors, while XZ is not selected at all by the canonical native-safe writer. The result therefore sharply narrows the next engineering target from generic inverse decoding to the exact gzip implementation path.

The measured gzip share is an upper bound on what an implementation-only gzip improvement could recover from complete extraction; no R1 implementation can claim more than the work it actually removes. A candidate must therefore be judged on complete extraction, not merely a microbenchmark of the gzip call.

## Scoped negative constraints

Under this exact Logs fixture, selected inverse portfolio and Python decoder implementation:

1. **Zstd inverse decode is not a material tuning target**: median 1.576 ms and 4.33% complete-extraction share fail both frozen floors.
2. **XZ inverse decode is not an active owner**: zero selected calls.
3. A generic "optimize every inverse codec" campaign is unjustified; it would add carrying cost without measured product opportunity.

Reopen Zstd/XZ as primary inverse-decode optimization targets only if the selected inverse-edge portfolio, fixture geometry, decoder implementation, or measured call ownership materially changes.

## Forge decision

Advance only gzip to a lowest-sufficient R0–R2 implementation experiment. Preserve exact gzip semantics, including all input forms accepted by the inherited decoder, and retain archive bytes, logical output, SHA/integrity, recovery and locality unchanged.

Before any production edit, the next experiment must compare a candidate implementation at the exact semantic owner against the inherited path, include hostile gzip-shape parity (especially concatenated-member behavior if the inherited standard-library decoder accepts it), and price the effect at complete promoted Logs extraction. If an implementation shortcut changes accepted gzip semantics, it is invalid regardless of speed.

No production source changed in this attribution and v0.30 remains release-locked.
