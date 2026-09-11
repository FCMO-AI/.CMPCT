# ONE-G0.2 bulk canonical emitter — exact result

Date: 2026-09-10  
Experimental version: **ONE-G0.2**  
Decision: **RETIRE_BULK_CANONICAL_EMITTER**

## Claim boundary

This is a Python research-harness canonical-emission result only. Program construction and discovery are outside the timed region. It grants no native/product, authentication/recovery, or Genesis-comparator authority.

## Exact authority

- branch: `research/cmpct1`
- exact source: `070d4f803c7b4441f517fc5c0b90f19214f5b05f`
- workflow run: `34432051613`
- job: `102729415872`
- artifact: `10134885099`
- artifact digest: `sha256:2a77ac023a40d470c7db0fc4eded925f2a63edd0d1461874fd0893d61ac76452`
- schema: `cmpct-one-g02-bulk-canonical-emitter-v2-paired-order`
- frozen rounds: `51`
- timing order: alternating `A/B-B/A`
- exact-source ONE semantic/hostile suite before falsifier: **637 passed**

The candidate emitted byte-identical canonical ONE wire and identical statistics on every measured Program, and every decoded Program reconstructed exactly. The scientific failure is economic, not semantic.

## Frozen result

- productive median candidate/baseline emission CPU: **0.791130x**;
- productive rows <=0.90x: **16** (gate required at least 18);
- worst productive row: **1.011890x**;
- worst control size-median ratio: **1.842573x** (gate <=1.03x).

Productive size medians were:

| relation bytes | candidate/baseline median |
|---:|---:|
| 4,096 | 0.901803x |
| 8,192 | 0.844467x |
| 16,384 | 0.817988x |
| 32,768 | 0.800871x |
| 65,536 | 0.782839x |
| 131,072 | 0.774772x |
| 262,144 | 0.794083x |

So the sized single-buffer implementation is genuinely useful on many metadata-rich/productive Programs, but it cannot be promoted as the canonical general emitter because its extra sizing/write machinery exports large cost into simple Surprise-only controls at some sizes. At 65,536 and 131,072 relation-byte scales, control size medians were about **1.760x** and **1.843x** respectively.

## Mission-lock interpretation

The hypothesis under test was that a sized single-buffer writer could replace the ordinary canonical emitter generally by avoiding incremental object/bytearray construction overhead while preserving exact wire bytes.

That general-replacement hypothesis is disproved. The candidate's approximately 21% median productive improvement is not enough to justify a path that can make no-Law controls roughly 84% slower.

This is exactly the speed/efficiency law working as intended: a faster path on favorable Law Programs does not earn promotion by exporting CPU to inputs where the representation has little structural work.

## Hostile review

Do **not** rehabilitate this result by learning a size threshold from these rows or by silently routing the failing controls around the frozen falsifier. That would be post-result threshold tuning.

A future emitter experiment is admissible only if it states a new causal hypothesis before measurement. Plausible directions include eliminating the explicit sizing pass, fusing canonical-size accounting with already-required Program construction/validation, or deriving a generic pre-existing economic admission signal from work that the writer must perform anyway. Backend selection may remain an implementation policy over the same ONE representation, but it must not become benchmark-shaped dispatch.

Also do not confuse this RETIRE with a format defect. Canonical bytes, decoding, exact reconstruction, resource semantics, and reader behavior all passed.

## Next decisive action

Do not spend the remaining Genesis window polishing this micro-emitter. Gate readiness is now more valuable, and breadth/complete accounting remain the material risks. Preserve this result as a negative implementation experiment and revisit canonical-emission fusion only if profiling shows emission itself owns material end-to-end writer cost on independent workloads.
