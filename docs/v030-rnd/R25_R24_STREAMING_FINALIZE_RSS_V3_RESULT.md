# r25/r24 streaming-finalize RSS v3 result

Status: **ACCEPTED SCOPED FORGE NEGATIVE / CANDIDATE-SHELL OWNER RETIRED / NO RELEASE CREDIT**

This record preserves the exact result of the frozen v3 follow-up to the accepted r24 streaming-finalize v2 near-win. V3 changed exactly one ownership behavior relative to the v2 control: after a candidate finished encoding, the `evict` arm removed that already-consumed `Candidate` shell from `Builder.cands`. It changed no archive grammar, selector, r24 byte policy, spool size, in-flight bound, integrity behavior, benchmark threshold, locality/decode-unit rule, or release state.

## Authority

- authoritative branch: `agent/v030-authoritative-integration`
- exact source head: `d3e95c90322bf7acec2df5cd4a67cf3970c034cf`
- workflow: `CMPCT v0.30 r24 streaming-finalize RSS v3`
- workflow run: `33660011230`
- substantive job: `100348424428` (`consumed-candidate-rss-v3`)
- artifact id: `9858817155`
- artifact: `v030-r24-streaming-finalize-rss-v3-d3e95c90322bf7acec2df5cd4a67cf3970c034cf`
- artifact digest: `sha256:87dbc59d2bc71d4d0f9888021bdb7f5cebd187e6bb3f3b34fe3a415f011d996d`
- schema: `cmpct-v030-r24-streaming-finalize-rss-v3`
- experiment valid: `true`
- rounds: 2, alternating arm order
- release credit: `false`

The result-bearing A/B, exact-contract enforcement, CI-topology self-check, and artifact upload all completed successfully. This is substantive evidence, not a classifier-only workflow green.

## Frozen semantic owner

- v2 control: `experiments.entropygraph_v030_r24_streaming_finalize.StreamingFinalizeBuilder`
- v3 evict: `experiments.entropygraph_v030_r24_streaming_finalize_v3.ConsumedCandidateEvictingStreamingFinalizeBuilder`
- spool memory: **1 MiB**
- maximum in-flight factor: **1**
- sole intervention: **evict consumed Candidate shell from `Builder.cands` after encode completion**

Every repetition required shipping, control and evict to produce exactly identical archive byte counts, physical SHA-256 and logical tree SHA-256 for the same operation/target before any RSS interpretation was allowed.

## Exact result

### Shifted versions

`resemblance_hostile_v1 / 01_shifted_versions`

| Arm | Median full peak RSS | Median diagnostic incremental RSS | Median full wall |
|---|---:|---:|---:|
| shipping | **359,574 KiB** | **240,842 KiB** | **60.0704 s** |
| v2 control | **302,536 KiB** | **183,804 KiB** | **63.7500 s** |
| v3 evict | **303,056 KiB** | **184,324 KiB** | **63.1891 s** |

Frozen diagnostic ratios:

- evict full RSS / shipping: **0.7653316282x**
- evict r24 incremental RSS / shipping: **0.0x**
- evict full wall / shipping: **1.0519163942x**
- evict full RSS / v2 control: **1.0028291006x**
- evict full wall / v2 control: **0.9912003023x**

The v3 eviction therefore made the decisive full-product incremental peak RSS about **0.283% worse than the v2 control**, while changing control-relative wall time by less than one percent. It did not recover the remaining v2 near-miss and did not satisfy the frozen Shifted promotion boundary.

### ML artifacts

`neutral_hostile_v1 / 09_ml_artifacts`

| Arm | Median full peak RSS | Median diagnostic incremental RSS | Median full wall |
|---|---:|---:|---:|
| shipping | **201,728 KiB** | **82,996 KiB** | **39.1191 s** |
| v2 control | **191,508 KiB** | **72,776 KiB** | **38.3177 s** |
| v3 evict | **191,834 KiB** | **73,102 KiB** | **37.0559 s** |

Frozen diagnostic ratios:

- evict full RSS / shipping: **0.8807894356x**
- evict r24 incremental RSS / shipping: **0.0x**
- evict full wall / shipping: **0.9472605342x**
- evict full RSS / v2 control: **1.0044794987x**
- evict full wall / v2 control: **0.9670703796x**

Again, candidate-shell eviction did not lower the residual full-product peak; it was about **0.448% worse than the v2 control** on the frozen incremental high-water metric.

## Terminal decision

The frozen terminal decision is:

**`CANDIDATE_SHELL_RETENTION_RETIRED_AS_MATERIAL_OWNER`**

`promotion_signal=false`.

The tested retained `Candidate` shells are therefore not a material owner of the remaining streaming-finalize RSS debt under this exact regime. Do not spend further v0.30 Forge effort on deleting, nulling, compacting or otherwise tuning those already-consumed shell objects without new causal evidence.

This result does **not** retire the broader v2 streaming-finalize family. V2 remains a reproducible high-value rehabilitation mechanism: it materially reduced Shifted and ML RSS while preserving exact bytes. V3 only falsifies one proposed explanation for why V2 stopped just short of its frozen Shifted promotion threshold.

## Causal interpretation and reopening predicate

The residual memory survives removal of the consumed shell object itself. The next justified ownership question must therefore move to state not removed by this intervention: encoded/spooled payload lifetime outside the shell, allocator/native retention, product-level candidate/result buffers, r25 tournament state, or another live owner demonstrably present at the high-water point.

Reopen consumed-candidate-shell retention as a primary hypothesis only if:

1. the candidate object gains materially larger retained fields in a later implementation;
2. heap/allocation evidence proves that objects reachable specifically through consumed `Builder.cands` entries own a material portion of the product high-water; or
3. a distinct exact-output ablation removes those reachable objects and materially lowers total fresh-process peak RSS under a preregistered boundary.

Runner noise, a different baseline-subtraction narrative, or repeating this same eviction with new rounds is not a reopening predicate.

## Forge implication

Preserve the v2 streaming-finalize mechanism and stop tuning candidate-shell retention. The next Shifted RSS intervention should identify the largest still-live allocation class at the streaming control's high-water and attack that owner directly. Any productization still owes the unchanged final release-performance gate; this diagnostic result itself grants no release credit.
