# Logs gzip single-member fast-path rehabilitation — preregistration

Status: **FROZEN FORGE R1 REHABILITATION / ZERO RELEASE CREDIT**

## Why this experiment exists

Accepted `R25_LOGS_INVERSE_CODEC_ATTRIBUTION_RESULT.md` established gzip as the only material selected inverse-decode owner on `neutral_hostile_v1/05_logs_and_telemetry`: two gzip calls consume a median **0.008887544999879537 s**, **24.4394%** of complete promoted Logs extraction. Zstd and XZ fail the frozen attribution floors and are not part of this experiment.

The inherited semantic owner uses Python `gzip.decompress(raw)`. Python's documented contract supports concatenated multi-member gzip data and explicitly notes that `zlib.decompress(..., wbits=31)` is faster when input is known to contain only one member. The hypothesis is therefore not to replace gzip semantics: it is to use a direct zlib gzip decoder only when one completed gzip member consumes the entire input, and otherwise fall back to the inherited `gzip.decompress` path unchanged.

This is an implementation experiment only. It changes no archive bytes, inverse-edge selection, gzip representation, logical output, integrity/recovery/locality rule, native grammar, comparator or release threshold.

## Forge diagnosis

- strict target: reduce promoted Logs complete extraction wall time without changing selected bytes or semantics;
- causal class: **D1 local implementation overhead** inside the D2 owner identified by the predecessor attribution;
- minimum radicality: **R1**;
- saturation: no S1-S4 trigger applies to this newly isolated owner; the candidate must retire if it cannot recover material complete-extraction time;
- strongest simpler control: inherited `gzip.decompress`;
- disproof: safe single-member detection plus direct zlib does not produce >=1% complete-extraction reduction, or semantic parity cannot be established.

## Frozen candidate

For `codec == "gzip"` only:

1. construct `zlib.decompressobj(wbits=31)`;
2. decompress the complete input and flush;
3. accept the direct result only if the gzip stream reaches EOF and **no `unused_data` or `unconsumed_tail` remains**;
4. on zlib error, incomplete stream, trailing bytes, zero padding, concatenated members or any other non-exact-single-member condition, call the inherited `gzip.decompress(raw)` path on the original bytes;
5. preserve the inherited post-decode `max_output` check.

Other codecs call the inherited decoder unchanged.

The candidate may not cache output, infer eligibility from filename/corpus identity, rewrite sidecars, alter inverse-edge selection, weaken checks or assume that arbitrary gzip input is single-member.

## Frozen semantic-parity attack set

Before performance interpretation, candidate and inherited decoder must agree on success/failure and exact successful output for deterministic cases covering at least:

- ordinary single-member gzip;
- single-member gzip with optional filename/comment/header fields when constructible by the standard library/test fixture;
- two concatenated gzip members;
- valid single member followed by zero padding;
- corrupted trailer CRC;
- truncated stream;
- malformed/non-gzip bytes;
- valid member followed by non-gzip trailing garbage.

The exact promoted Logs archive must also reconstruct the same user tree and pass strong verification under both arms.

If a hostile case exposes a semantic difference, terminal decision is `INVALID_GZIP_FASTPATH_PARITY` regardless of timing.

## Frozen performance method

Run **21 alternating paired rounds** after one warmup per arm on the promoted Logs complete extraction path:

- control: inherited decoder;
- candidate: exact single-member fast path above with inherited fallback.

Each extraction uses a clean destination. Record complete extraction wall and candidate fast-path/fallback call counts.

Validity requires:

- exact hostile semantic parity;
- selected representation remains `logs-inverse`;
- strong verification and exact user-tree reconstruction;
- 21 control + 21 candidate measurements;
- stable candidate geometry of **two gzip decode calls per extraction**;
- at least one fast-path hit per measured extraction;
- no production source mutation during the experiment.

## Frozen terminal bands

Let `reduction = 1 - candidate_median / control_median`.

- `reduction >= 0.04` and `candidate_median/control_median <= 0.96` -> **`LOGS_GZIP_SINGLE_MEMBER_FASTPATH_SUPPORTED`**;
- `reduction < 0.01` -> **`LOGS_GZIP_SINGLE_MEMBER_FASTPATH_RETIRED`**;
- otherwise -> **`LOGS_GZIP_SINGLE_MEMBER_FASTPATH_AMBIGUOUS`**.

These are complete promoted-extraction bands, not gzip microbenchmark bands. No threshold may change after result-bearing execution begins.

## Carrying cost and product survival

If supported, productization must keep the fallback so arbitrary multi-member/trailing-shape gzip semantics remain inherited, add direct hostile regression coverage, and rerun full Logs/runtime/recovery/native/platform/release authorities. The optimization introduces no reader-visible grammar and should require no native format change; nevertheless Python/native semantic parity remains a release obligation.

If retired, do not repeat nearby direct-zlib variants without new evidence. The gzip owner remains real, but Forge should escalate from wrapper-level implementation tuning to a different R2 execution boundary or native hot path rather than shaving the same Python call repeatedly.

Zero release credit is granted by this experiment.
