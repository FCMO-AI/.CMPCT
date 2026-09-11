# ONE-G0.3 real block Statistical Law realization — preregistration

**Date:** 2026-09-11  
**Status:** preregistered; no result exists yet  
**Parent evidence:** `docs/one/evidence/ONE_G03_BLOCK_ADAPTIVE_STATISTICAL_LAW_RESULT_2026-09-11.md`  
**Claim boundary:** research realization of one generic ONE Law family; not Genesis evidence, not a canonical release, not a production-writer claim

## Mission lock

The hosted block-adaptive diagnostic established large causal coding opportunity under a reader-reproducible previous-byte Statistical Law, but only as ideal KT prequential codelength. The next question is narrower and harder:

> Can that opportunity survive a **real deterministic bitstream**, independently restartable blocks, exact decode, a cheap Surprise escape, and explicit block/index/integrity charges while retaining materially better density on the workloads where the Law predicted headroom?

This experiment must not modify the frozen ONE-G0.2 Genesis candidate or either frozen comparator. It is post-candidate research evidence only.

## Falsifiable hypothesis

A single generic block Statistical Law can convert enough of the modeled opportunity into real stored bytes that, after all charges defined below:

1. exact reconstruction passes on every tested byte;
2. the three preregistered opportunity targets (`04_analytics_and_database`, `05_logs_and_telemetry`, `10_large_mixed_binary`) each beat raw Surprise bytes by at least **15%** (`real_wire_ratio <= 0.85`), and at least two beat raw Surprise by **25%** (`<= 0.75`);
3. at least one target saves **>= 5 MiB** after all diagnostic wire charges;
4. neither incompressible control exceeds raw Surprise by more than **1.0%** after its block selector chooses Law vs Surprise (`real_wire_ratio <= 1.01`);
5. media and tiny-file negatives are free to choose Surprise and must remain `<= 1.01` after selector/control charges;
6. the reader performs no discovery and requires only the authenticated block descriptor, encoded payload, and bounded local predictor state.

Failure of any semantic condition is a hard reject. Density gates are evaluated only after semantic success.

## Fixed scientific inputs

Use the exact 15 Genesis workload identities and generators already frozen by the campaign. Do not alter file contents, ordering semantics, workload membership, random seeds, or logical tree identities.

This experiment is not allowed to use the frozen v0.29/v0.30 outputs to tune its thresholds or choose a different Law family.

## Fixed Law

### Block scope

- independently reconstructable block size: **65,536 bytes**;
- predictor state resets at each block boundary and each file boundary;
- empty blocks do not exist;
- first byte in each non-empty block is Surprise/raw for predictor bootstrap.

### Context and probabilities

- context = immediately previous decoded byte (`0..255`);
- symbol alphabet = next byte (`0..255`);
- each context owns 256 adaptive counts;
- symmetric KT prior `alpha = 1/2` is represented exactly for integer coding by odd weights:
  - `weight[c,s] = 2 * count[c,s] + 1`;
  - context total `W[c] = 2 * sum_s count[c,s] + 256`;
- after coding/decoding a symbol, increment only its observed count by one, therefore its integer weight by two;
- counts reset with the block.

No learned table, histogram, model, dictionary, or probability state is stored in the archive.

## Fixed real coder

The reference realization will use one deterministic integer arithmetic/range-coding algorithm, implemented in repository source and covered by an independent decoder oracle.

Required fixed properties before measurement:

- integer-only arithmetic;
- no platform floating point;
- exact encoder/decoder symmetry;
- explicit finalization rule;
- byte-exact deterministic output across repeated encodes;
- bounded state independent of source size except for output buffer;
- malformed/truncated stream fails closed rather than returning silent bytes;
- no external compression library or historical CMPCT codec may encode the Statistical Law payload.

The exact integer interval width, normalization threshold, byte-carry convention and finalization bytes must be committed in source **before the 15-workload measurement workflow is enabled**. If implementation review changes any of those details, update this preregistration in a commit that precedes result-bearing CI; never alter them after seeing the 15-workload result.

## Surprise arm

For every non-empty block there are exactly two candidates:

- `SURPRISE_RAW`: literal block bytes;
- `STAT_H1`: the real encoded Statistical Law stream described above.

The reader-visible selector is generic Law-vs-Surprise placement, not a legacy codec mode.

The winner is chosen by exact complete diagnostic wire bytes for that block. There is no workload-name, file-type, extension, corpus, threshold-by-dataset or historical-codec dispatch.

## Cheap opportunity gate

The writer may avoid full Statistical-Law encoding only through the following preregistered cheap gate:

- inspect at most the first **4,096 bytes** of a block (or the whole block if shorter);
- compute the same previous-byte KT ideal codelength on that sample;
- extrapolate only the sample ratio, not a learned table;
- if sample modeled ratio is `>= 0.97`, reject `STAT_H1` immediately and emit `SURPRISE_RAW`;
- otherwise attempt the real Statistical Law coder and then perform exact byte-cost comparison against raw Surprise.

The sample bytes are part of the single source observation; they must not be reread from storage solely for the gate. Instrument sample bytes, attempted blocks, rejected blocks, coded blocks, and total coder input bytes.

A later experiment may improve the gate, but this result may not tune `0.97` after seeing outcomes.

## Diagnostic wire accounting

Every non-empty block pays all of the following:

1. **1 byte selector/control** (`SURPRISE_RAW` or `STAT_H1`);
2. **4 bytes uncompressed length**;
3. **4 bytes payload length**;
4. payload bytes (raw block or finalized Statistical Law stream);
5. **32 bytes SHA-256 block digest** to model independently authenticated selective reconstruction;
6. **8 bytes block-offset/index entry** charged once per block.

Therefore fixed non-payload charge is **49 bytes per non-empty block**.

Additionally every non-empty file pays **16 bytes** diagnostic file/root framing. Directory/path/full-manifest costs are intentionally excluded from this focused mechanism test and MUST be called out as unpaid product debt. The same excluded costs apply to both block arms, so this experiment only asks whether Statistical Law survives a realistic local selective/integrity envelope.

`real_wire_bytes` = selected payload bytes + all charges above.

Raw comparator for ratio is the exact logical regular-file bytes of the workload. This is not a claim that a complete ONE archive can equal that baseline.

## Selective reconstruction semantics

Each block is independently decodable from its descriptor + payload.

The diagnostic must issue deterministic selective requests covering:

- first byte;
- last byte;
- 4 KiB aligned middle range when available;
- a range crossing one block boundary when available.

For every request record:

- logical bytes requested;
- encoded payload bytes touched;
- descriptor/index/digest bytes touched;
- decoded source bytes;
- reconstruction CPU/wall;
- peak RSS at process level;
- exact returned byte equality.

A request may decode at most the block(s) it intersects. Any whole-file/whole-archive discovery at read time is a hard failure.

## Compute accounting

Creation evidence must report at least:

- source bytes observed;
- sample-gate bytes;
- full Statistical-Law coder input bytes;
- blocks rejected before coding;
- blocks encoded and then rejected on exact wire cost;
- blocks selected as Law;
- creation CPU and wall time;
- process peak RSS;
- modeled predictor state bytes;
- emitted control/index/digest bytes;
- emitted payload bytes.

The implementation must not claim one fused memory pass merely because Python reads each file once: internal NumPy/Python/coder memory traffic is separate debt unless actually instrumented or implemented as a fused loop.

## Oracle and hostile review

Before the full 15-workload result is accepted:

1. independent scalar decoder/reference path must reconstruct every encoded block exactly;
2. random round trips over lengths around `0,1,2,4095,4096,65535,65536,65537` and multiple blocks;
3. all-zero, alternating, monotonic, repeated text, random and adversarial skew vectors;
4. truncation at every byte position for small encoded streams must fail or be proven unable to produce an accepted incorrect block under digest verification;
5. one-bit payload corruptions on bounded vectors must be detected by decode failure or digest mismatch;
6. deterministic re-encode must be byte-identical;
7. resource bounds must reject declared lengths outside the block contract before allocation/decode.

## Promotion / rejection

Return `ADVANCE_REAL_BLOCK_STATISTICAL_LAW` only if all semantic/hostile gates pass and every density gate in the hypothesis passes.

Otherwise return `HOLD_REAL_BLOCK_STATISTICAL_LAW` and preserve the exact failed rows/reason. Do not rescue a red result with workload-specific thresholds, larger blocks, a different coder, or omitted integrity/index charges inside the same experiment.

## What a green result would authorize

A green result authorizes only the next integration question: compile this Statistical Law into the canonical ONE reference IR/Surprise interface and compare it to Surprise-only G0.2 while charging complete archive manifest/authentication and reader complexity.

It does **not** authorize:

- changing the frozen Genesis result;
- claiming v0.29/v0.30 supersession;
- a new canonical CMPCT version;
- removing authentication or locality requirements;
- a reader-visible `OP_STAT_CODEC` special case.

The mechanism must remain a generic Statistical Law whose realized outcomes are carried by ONE Surprise.