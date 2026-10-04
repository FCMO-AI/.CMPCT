# Logs fused extraction phase attribution — result

Status: **ACCEPTED FORGE D2 CAUSAL ATTRIBUTION / `TRACKED_PHASE_MATERIAL_HEADROOM` / NO RELEASE CREDIT**

This record closes `R25_LOGS_FUSED_PHASE_ATTRIBUTION_PREREG.md` on its frozen exact source. It does not change the promoted fused extractor, archive bytes, filesystem semantics, performance thresholds or release state.

## Authority

- authoritative branch: `agent/v030-authoritative-integration`
- exact source: `3bc650afe0483b1903794ac3b7a8797b9140d817`
- workflow: `CMPCT v0.30 Logs fused phase attribution`
- workflow run: `33681582054`
- substantive job: `100420497343`
- artifact id: `9866687979`
- artifact: `v030-logs-fused-phase-attribution-3bc650afe0483b1903794ac3b7a8797b9140d817`
- artifact digest: `sha256:88682395a87bc7e1f83bde6924ed2530e996d26385b1ea29e1586ae04ffccc7a`
- schema: `cmpct-v030-logs-fused-phase-attribution-v1`
- target: `neutral_hostile_v1/05_logs_and_telemetry`
- experiment valid: **true**
- release credit: **false**

The exact attribution, frozen overhead/decision ratchet, CI-topology self-check, public-surface guard and artifact upload all completed successfully.

## Exact result

The uninstrumented fused control median was **0.031752590 s**. The instrumented fused median was **0.031720122 s**, giving an instrumentation wall ratio of **0.998977469x**. This is well inside the frozen `<=1.10x` overhead validity ceiling, so phase shares are admissible.

| Tracked phase | Median wall | Share of instrumented total | Frozen material rule |
|---|---:|---:|---|
| authenticated graph restore (`Archive._restore_session`) | **0.026265138 s** | **82.8028%** | **material** |
| filesystem manifest decode | **0.000058178 s** | **0.1834%** | not material |
| filesystem metadata restoration | **0.000293362 s** | **0.9248%** | not material |
| explicit unattributed remainder | **0.004995832 s** | diagnostic remainder | not a gifted cost |

Frozen materiality required both `>=0.0020 s` and `>=5%` of the instrumented total. Only authenticated graph restore crosses either meaningful scale by a wide margin.

Terminal decision:

**`TRACKED_PHASE_MATERIAL_HEADROOM`**

## Causal interpretation

The remaining local Logs extraction opportunity is not in manifest parsing or final mode/time/xattr/link metadata publication under this workload. Those paths are tens or hundreds of microseconds and cannot plausibly cover the strict product row's roughly millisecond-scale deficit by themselves.

The dominant tracked owner is the authenticated logical restore path: pack reads/decompression, inverse-edge reconstruction, logical SHA-256 identity checks and cache ownership within `LOGS.Archive._restore_session`. At **26.27 ms / 82.8%** of the current fused path, it contains ample headroom to matter if a narrower causal owner can be changed without weakening integrity or locality.

The explicit ~5.0 ms remainder remains real. It includes archive/open-close and identity-map work, target/path preparation, regular-file writes, transactional temp-tree/publication and Python overhead not covered by the three wrappers. This experiment does not claim that remainder is irrelevant or additive with the tracked medians beyond these exact boundaries.

## Forge decision

**Deprioritize manifest-decode and metadata micro-optimization.** The next Logs R0-R2 intervention must first attribute or ablate work *inside the authenticated restore boundary*, preferably separating:

1. physical pack read/decompression and pack-cache misses;
2. inverse-edge decode/reconstruction;
3. per-logical-member SHA-256 identity hashing;
4. Python object/copy ownership around restored values.

Do not skip or weaken logical SHA-256, archive authentication, locality charging, recovery behavior or transactional publication to manufacture speed. A valid next A/B should preserve exact archive bytes/tree and hostile-corruption rejection while changing only the measured ownership cost.

## Relationship to product truth

`R25_LOGS_FUSED_REVALIDATION_RESULT.md` independently revalidated the one-session fused extractor at **23.3324% faster** than the mature pre-promotion comparator. The latest substantive complete-product release-performance receipt predating these local diagnostics still had Logs extraction at about **1.3003x** v0.29 versus the frozen `<=1.25x` workload ceiling, so local fused success is not release closure.

This attribution tells Forge where to spend the next intervention; only a new exact complete-product receipt can determine whether the strict Logs row is actually green after any later product change.

## Reopening law

Reopen manifest decode or filesystem metadata as primary Logs extraction hypotheses only if their implementation/corpus semantics materially change or new phase evidence shows either path has grown to the frozen millisecond-scale materiality boundary. Repeating the same wrappers with more rounds or a different reporting denominator is not a reopening predicate.
