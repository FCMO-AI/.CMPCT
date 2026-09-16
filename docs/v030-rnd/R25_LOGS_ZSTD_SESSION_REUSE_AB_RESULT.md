# Logs operation-scoped Zstd decompressor reuse A/B — result

Status: **ACCEPTED EXACT-HEAD FORGE NEGATIVE / SESSION REUSE RETIRED / NO RELEASE CREDIT**

This record closes the frozen experiment in `R25_LOGS_ZSTD_SESSION_REUSE_AB_PREREG.md` without changing its target, intervention, thresholds, integrity contract, locality/recovery rules, or interpretation.

## Authority

- authoritative branch: `agent/v030-authoritative-integration`
- exact result-bearing source: `94037b8b3e7a6e40d945a2a988d1690b5eca12b5`
- workflow: `CMPCT v0.30 Logs restore attribution`
- workflow run: `33697146985`
- substantive job: `100468372950` (`zstd-session-reuse`)
- artifact id: `9872264463`
- artifact: `v030-logs-zstd-session-reuse-94037b8b3e7a6e40d945a2a988d1690b5eca12b5`
- artifact ZIP digest: `sha256:e5fa4d999972e9a1b011242237857555e1dbd6fb86ba2241681b25e6ffaf78d8`
- schema: `cmpct-v030-logs-zstd-session-reuse-ab-v1`
- target: `neutral_hostile_v1/05_logs_and_telemetry`
- rounds: **21 paired alternating rounds** after one warm-up per arm
- release credit: **false**

The result-bearing A/B, frozen decision ratchet, CI-topology self-check, public-surface guard, and artifact upload all completed successfully. This is substantive evidence rather than a classifier-only green.

## Frozen intervention and exactness

Control used the exact promoted fused Logs extraction and inherited `_read_pack` behavior. Candidate reused one ordinary `zstd.ZstdDecompressor` only within one Archive/full extraction operation. It did not persist the decompressor across Archive instances or operations.

The frozen lifecycle and safety gates passed:

- candidate lifecycle valid: **true**;
- exactly one candidate decompressor construction per measured extraction: satisfied by the instrument;
- exactly two compressed-pack decompressions per measured extraction: satisfied by the instrument;
- CRC32 over complete raw packs preserved: **true**;
- SHA-256 over complete raw packs preserved: **true**;
- complete promoted strong verification: **pass**;
- cold selective-read semantics changed: **false**;
- production source changed: **false**.

Archive bytes, selected representation, canonical tree, pack framing, bounds, authentication, recovery, locality/decode-unit limits, and release thresholds were unchanged.

## Exact result

| arm | median complete extraction |
|---|---:|
| inherited fresh decompressor per compressed pack | **0.04578010500000573 s** |
| one Archive-scoped reusable decompressor | **0.045824150000001396 s** |

Derived frozen metrics:

- candidate/control wall ratio: **1.000962099147559x**;
- candidate total extraction reduction: **-0.0009620991475589591**, i.e. the candidate was about **0.09621% slower**;
- support floor: **>=4.0%** reduction and `<=0.96x` wall ratio;
- retirement band: **<1.0%** reduction.

Frozen terminal decision:

**`LOGS_ZSTD_SESSION_REUSE_RETIRED`**

## Causal interpretation

The predecessor component attribution remains valid: Zstd materialization consumes about **9.69%** of complete promoted Logs extraction under the measured warm-cache regime. This experiment shows that essentially none of that material cost is attributable to constructing two ordinary Python `ZstdDecompressor` objects. Reusing one object recovers no measurable total wall time and slightly loses instead.

Therefore the material Zstd owner is the decompression work itself, not decompressor-object lifetime/construction under this exact binding and two-pack regime.

Do not productize Archive-scoped decompressor reuse for v0.30 and do not rerun this same family hoping hosted-runner noise crosses a favorable band. Reopen only if the Zstd binding/implementation, compressed-pack count regime, or decompressor construction path changes materially.

## Forge consequence

Pack seek/read and Python remainder are already retired as material owners in `R25_LOGS_PACK_MATERIALIZATION_COMPONENT_ATTRIBUTION_RESULT.md`; decompressor session reuse is now retired as well. The remaining measured Logs pack-materialization owners are:

1. SHA-256 authentication — about **14.94%** of total extraction;
2. Zstd materialization itself — about **9.69%**;
3. CRC32 authentication — about **6.33%**.

CRC32 and SHA-256 are non-borrowable integrity facts. The next lowest-sufficient Forge question should therefore test an implementation route that reduces duplicated authenticated full-pack traversal while still establishing **both exact CRC32 and exact SHA-256 before publication**, or a materially different decompression implementation if it can preserve the same compressed bytes and bounded semantics. The intervention must measure complete extraction, not merely a microbenchmark, because the latest substantive Logs product red requires only a few percent wall-time recovery but the release gate is exact and same-runner.

No threshold, benchmark row, integrity fact, recovery condition, locality limit, archive byte, or competitor setting is changed by this negative. It grants **zero release credit**.