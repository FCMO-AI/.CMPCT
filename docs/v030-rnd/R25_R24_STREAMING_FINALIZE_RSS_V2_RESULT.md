# r24 streaming-finalize RSS v2 result

Status: **accepted exact-head Forge diagnostic / strong near-miss / `ITERATE_SAME_FAMILY` / no production or release credit**.

This record preserves the superseding semantic-owner result for `docs/v030-rnd/R25_R24_STREAMING_FINALIZE_RSS_V2_PREREG.md`. It supersedes only the productization interpretation of the invalid legacy v1 streaming-finalize experiment; the old raw measurements remain historical evidence and are not rewritten.

No selector, canonical r24 policy, archive grammar, integrity/recovery rule, locality/decode-unit bound, benchmark threshold, corpus identity, or release state changed.

## Authority

- authoritative branch: `agent/v030-authoritative-integration`;
- exact source: `e673a5d051ed40e476cae0f5f82d52a143736c43`;
- workflow: `CMPCT v0.30 r24 streaming-finalize RSS v2`;
- workflow run: `33648728669`;
- substantive job: `100310560685` (`semantic-owner-rss-v2`);
- artifact id: `9854311819`;
- artifact: `v030-r24-streaming-finalize-rss-v2-e673a5d051ed40e476cae0f5f82d52a143736c43`;
- artifact ZIP digest: `sha256:b4add93144e7b87681cd2a1ea843bbc49f541f5c1fc5b58416daa55a6d57aaea`;
- schema: `cmpct-v030-r24-streaming-finalize-rss-v2`;
- semantic owner: `experiments.entropygraph_v030_r24_streaming_finalize.StreamingFinalizeBuilder`;
- semantic-owner module SHA-256: `609e6b881db6cd5b265d9217ca6e351ae5abab05fa0f6be77a5bc59f8fc02d48`;
- spool memory: `1,048,576 B`;
- maximum in-flight factor: `1`;
- experiment valid: **true**;
- release credit: **false**.

The substantive fresh-process A/B completed successfully. Every repetition proved exact archive bytes, physical archive SHA-256, and logical tree SHA-256 equality between shipping and streaming arms for both the genuine-r24 operation and the complete promoted-product operation.

## Frozen decision contract

The preregistration required all of the following for `promotion_signal=true`:

1. exact output identity for every arm and repetition;
2. complete-product wall-time ratio `<=1.05x` on every target;
3. Shifted complete-product incremental-RSS ratio `<=0.75x`;
4. Shifted genuine-r24-only incremental-RSS ratio `<=0.50x`.

The bands are immutable after result-bearing execution. A near miss is not rounded into a pass.

## Exact result

| Target | Streaming / shipping complete-product RSS | Streaming / shipping r24-only RSS | Streaming / shipping complete-product wall time |
|---|---:|---:|---:|
| `resemblance_hostile_v1/01_shifted_versions` | **0.7546867932x** | **0.0000000000x** | **0.9173766299x** |
| `neutral_hostile_v1/09_ml_artifacts` | **0.7939298965x** | **0.0000000000x** | **0.9854863116x** |

Derived complete-product effects:

- Shifted peak-RSS reduction: **24.5313%**;
- Shifted wall-time improvement: **8.2623%**;
- ML peak-RSS reduction: **20.6070%**;
- ML wall-time improvement: **1.4514%**.

The Shifted r24-only frozen memory condition passed decisively under the oracle's baseline-subtracted high-water metric. That `0.0x` value is not a claim that r24 construction uses zero memory; it means the streaming r24 operation did not raise the measured high-water mark above the matched fresh-process baseline in this instrument.

### Terminal decision

**`promotion_signal = false`**.

The decisive miss is Shifted complete-product RSS: `0.7546867932x` is above the frozen `<=0.75x` boundary by **0.0046867932 ratio points**. Wall time improved rather than regressed, output identity remained exact, and the r24-only condition passed, but the complete frozen conjunction did not pass.

## Causal interpretation

This is strong positive evidence for the **execution/lifetime architecture**, but not enough evidence to productize this exact implementation under the frozen v2 contract.

The reusable semantic owner removes the mature `encoded + records + joined-data + whole-archive concatenation` residency stack, bounds in-flight encode results, releases raw/Deflate candidate material inside the worker once codec competition has completed, spools compressed records, and streams final publication. On the exact Shifted product path that architecture removed about one quarter of peak RSS while also making the complete operation faster.

That is materially stronger than the blunt one-worker control, which recovered only 12.7817% RSS while costing 1.594x wall time. The evidence therefore supports **lifetime/ownership repair rather than globally discarding useful worker concurrency**.

However, the remaining Shifted full-product high-water still belongs somewhere outside the r24-only streaming finalizer's now-collapsed incremental peak. The result does not prove which retained product/candidate state owns the residual, and it does not authorize tuning the 0.75 threshold or rerunning until runner noise happens to cross it.

## Scoped negative constraint

Do not promote this exact semantic-owner implementation as the Shifted RSS repair under the v2 preregistration. It missed the frozen complete-product RSS boundary.

Do not infer from that miss that streaming finalization is futile. The measured mechanism is large, byte-identical, and wall-time-positive. What is falsified is the narrower claim that **this exact bounded-spool/in-flight implementation alone is sufficient to satisfy the frozen v2 promotion conjunction**.

## Strongest surviving self-critique

The margin to the frozen Shifted boundary is small enough that ordinary hosted-runner variance could plausibly move the observed ratio around, but post-result appeals to noise are not release evidence. The correct response is not threshold reinterpretation. A successor experiment must change a measured ownership fact and preregister that change before execution.

The `r24_rss_ratio=0.0` diagnostic also means the next intervention should not blindly optimize r24 finalization further: the decisive remaining debt appears in the complete product composition, where other retained state can coexist with the r24 result.

## Forge decision

**`ITERATE_SAME_FAMILY`**, narrowly.

Streaming/lifetime ownership remains the highest-supported Shifted memory mechanism because it achieved a material ~24.5% complete-product RSS reduction with exact bytes and better wall time. The next step is to identify the residual complete-product allocation/lifetime owner and remove or shorten that lifetime while retaining this semantic owner unchanged as the strong control.

A successor may advance only if it changes a causal ownership boundary and preserves:

- exact selected archive bytes/SHA/tree;
- canonical r24 policy and r25 selector semantics;
- current locality/decode-unit, recovery and integrity contracts;
- the frozen runtime/RSS release thresholds;
- the wall-time gain/no-regression behavior.

## Reopening / supersession predicate

Do not simply rerun v2 or vary its threshold. Supersede it only after a material implementation/ownership change with evidence capable of explaining and closing the remaining complete-product RSS gap—for example a specifically measured retained candidate/product buffer, bounded in-flight state outside the r24 owner, or another exact lifetime whose removal is large enough to move the product ratio below the existing boundary.

The next product claim still requires the full exact-fingerprint release-performance and release-authority chain. This diagnostic grants none of that credit.
