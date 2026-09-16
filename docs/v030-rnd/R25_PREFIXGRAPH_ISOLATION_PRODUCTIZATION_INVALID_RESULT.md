# PrefixGraph isolation Builder hostile review — invalid robust-RSS receipt

Status: **PRESERVED INVALID S6 RECEIPT / CUSTODY FAILURE / ZERO RELEASE CREDIT**

This record preserves the first result-bearing execution of `R25_PREFIXGRAPH_ISOLATION_PRODUCTIZATION_PREREG.md` after exited-child-aware whole-process-tree RSS accounting was admitted. The frozen v1 preregistration and instrument remain immutable.

## Authority

- authoritative branch: `agent/v030-authoritative-integration`
- exact source: `9d73b16c2ad55078e500d88487681a631168b488`
- workflow: `CMPCT v0.30 PrefixGraph isolation Builder hostile review`
- run: `33722652263`
- substantive job: `100544872146` (`hostile-review`)
- artifact id: `9880867780`
- artifact digest: `sha256:314f5ced2cbfb6e4910a9c1d37406e2ff75a994dad58e49b06490ea3415ee83f`
- schema: `cmpct-v030-prefixgraph-isolation-productization-v1`
- experiment valid: **false**
- release credit: **false**

The substantive Builder-versus-threaded-control measurement completed and uploaded exact evidence. The terminal ratchet correctly did not run because the v1 oracle declared the receipt invalid.

## Exact measured summaries

| arm | final r25 bytes | r24 product bytes | median whole-tree peak RSS | median wall |
|---|---:|---:|---:|---:|
| threaded control | **1,700,599 B** | **29,883,728 B** | **365,168 KiB** | **34.671370133 s** |
| process-isolated level-15 Builder | **1,700,660 B** | **29,883,728 B** | **259,774 KiB** | **38.770957360 s** |

Both arms were deterministic. The candidate size penalty was **61 B / 0.003587%**. Descriptively only, without granting terminal authority, the measured candidate reduced whole-tree peak RSS by **28.8618%** and had a **1.118241x** wall ratio.

Those descriptive deltas are not a valid S6 decision because the v1 custody gate failed first.

## Exact invalidity

The v1 oracle hard-coded:

`R24_BYTES = 29_883_732`

Every result-bearing control and candidate build on this exact generated source instead emitted:

`29_883_728 B`

The frozen v1 oracle therefore had to return **`INVALID_PRODUCTIZATION_RECEIPT`**. Because result-bearing execution had already begun, neither that literal nor the old result may be edited or reinterpreted after the fact.

## Stronger causal authority discovered before supersession

The four-byte mismatch must not be simplified into a one-off stale constant. The already accepted `R25_SHIFTED_SERIALIZED_METADATA_CAUSAL_V2_RESULT.md` established the stronger causal fact: independent fresh generations of the same accepted Shifted content tree produced genuine-r24 sizes **29,883,722 / 29,883,726 / 29,883,728 B**, and nanosecond **mtime was the only observed varying Builder-consumed serialized filesystem fact**. Normalizing only atime/mtime to `1767225600000000000` ns collapsed three independent generations to one exact genuine-r24 identity:

- **29,883,488 B**;
- SHA-256 `a3192a1462e37282e5128e50c3b20a039ca26821d5ceb2508958d6e3918bbc22`.

That accepted causal result outranks any weaker proposal to merely learn the current r24 size or compare arms opportunistically.

The repository already froze the authorized superseding experiment in `R25_PREFIXGRAPH_ISOLATION_PRODUCTIZATION_V2_PREREG.md`. V2 changes only the causally justified fixture metadata normalization and resulting exact r24 identity while preserving the original mechanism, target, rounds, robust whole-process-tree RSS accounting, wall/size gates, helper lifecycle, hostile failure law and terminal vocabulary.

## Scoped interpretation

This invalid receipt does **not** prove `PREFIXGRAPH_ISOLATION_BUILDER_SUPPORTED`, `PREFIXGRAPH_ISOLATION_EXPORTED_DEBT_REMAINS`, or `PREFIXGRAPH_ISOLATION_PRODUCTIZATION_DID_NOT_TRANSFER`.

It does provide useful non-terminal observations for hostile review:

1. exited-child-aware accounting still measured a large candidate/control RSS separation on this invalid fixture instance;
2. candidate size debt was tiny;
3. the observed wall ratio exceeded the unchanged **1.10x** promotion boundary.

V2 may reproduce or falsify any of those observations. It may not widen the wall threshold or inherit decision credit from v1.

## Supersession law

**Do not rerun or edit v1. Do not create a same-source adaptive-r24 workaround.** Execute and interpret only the already-frozen v2 experiment for the next S6 decision. Its exact normalized r24 fingerprint, thresholds and fixture intervention are immutable once result-bearing v2 execution begins.
