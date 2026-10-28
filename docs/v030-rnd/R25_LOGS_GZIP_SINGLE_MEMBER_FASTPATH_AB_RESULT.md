# Logs gzip single-member fast-path rehabilitation — result

Status: **CLOSED FORGE R1 NEGATIVE / FAST-PATH FAMILY RETIRED / ZERO RELEASE CREDIT**

This record closes the frozen experiment in `R25_LOGS_GZIP_SINGLE_MEMBER_FASTPATH_AB_PREREG.md`. It changes no production source, archive bytes, selected inverse edge, gzip semantics, logical output, integrity/recovery/locality rule, comparator, threshold or release state.

## Authority

- authoritative branch: `agent/v030-authoritative-integration`
- exact result-bearing source: `ae2e96e4c743734a67ff903b697c17f1cfe1e4c2`
- workflow: `CMPCT v0.30 Logs gzip single-member fast-path A/B`
- workflow run: `33718119732`
- substantive job: `100531479879` (`gzip-fastpath-ab`)
- artifact id: `9879244417`
- artifact: `v030-logs-gzip-fastpath-ae2e96e4c743734a67ff903b697c17f1cfe1e4c2`
- artifact ZIP digest: `sha256:389050d59ee9b2896078ac7642c044b8032c3214756e0fc29dc56dec7773f814`
- schema: `cmpct-v030-logs-gzip-single-member-fastpath-ab-v1`
- runner: Ubuntu 24.04.4 / Python 3.11.16
- release credit: **false**

The exact 21-pair complete-extraction A/B, semantic-parity attack set, frozen decision ratchet, CI-topology self-check, public-surface guard and artifact upload all completed successfully. This is substantive result-bearing evidence.

## Frozen semantic intervention

The candidate changed only the gzip implementation boundary in the isolated experiment:

1. attempt an exact one-member decode through `zlib.decompressobj(wbits=31)`;
2. accept that result only if the decoder reaches EOF with no `unused_data` and no `unconsumed_tail`;
3. otherwise fall back to the inherited `gzip.decompress(raw)` on the original bytes;
4. preserve the inherited post-decode `max_output` check;
5. leave Zstd/XZ and all archive/selection semantics unchanged.

This deliberately preserves Python gzip's broader accepted-shape semantics rather than assuming every gzip payload is a single member.

## Semantic parity

The frozen attack set passed exactly between inherited and candidate success/failure/output behavior for:

- ordinary single-member gzip;
- named/header gzip;
- concatenated members;
- valid member plus zero padding;
- corrupt trailer CRC;
- truncated input;
- malformed input;
- valid member plus trailing garbage.

The fallback-shape guard passed. On the promoted Logs fixture every measured candidate extraction observed exactly **2 gzip calls**, both safely qualifying for the single-member fast path (`fast_hits=[2]`, `fallback_calls=[0]`). Strong verification and exact user-tree reconstruction passed.

## Exact performance result

Target: `neutral_hostile_v1 / 05_logs_and_telemetry`.

| arm | median complete extraction |
|---|---:|
| inherited `gzip.decompress` control | **0.042709097999996004 s** |
| semantic-preserving single-member fast path | **0.042681086000001756 s** |

Frozen metrics:

- candidate/control wall ratio: **0.9993441210115407x**;
- complete-extraction reduction: **0.000655878988459313 / 0.06559%**.

Frozen retirement band: complete-extraction reduction `<1%`.

Terminal decision:

**`LOGS_GZIP_SINGLE_MEMBER_FASTPATH_RETIRED`**

## Causal interpretation

The predecessor D2 attribution remains valid: gzip owns roughly **24.44%** of complete promoted Logs extraction under that exact attribution run. This negative does not make gzip unimportant. It says the obvious Python-level wrapper substitution does essentially nothing to the product wall clock even when both selected gzip edges take the direct path.

Therefore the useful gzip opportunity is not recoverable by replacing `gzip.decompress` with an exact-single-member `zlib.decompressobj` wrapper under this regime. Any tiny per-call implementation difference is swallowed by surrounding decode/materialization costs and is far below the product threshold.

The result also falsifies the tempting inference that Python's documented single-member `zlib` speed note automatically translates into meaningful promoted-product speed. Product timing, not isolated API folklore, remains authoritative.

## Scoped negative constraint and reopening predicate

Do not spend further v0.30 Forge activations on nearby Python direct-zlib variants (`zlib.decompress`, alternate `decompressobj` wrapper shape, minor header prechecks, or equivalent wrapper tuning) merely to shave the same two selected calls.

Reopen this R1 family only if:

1. the Python gzip/zlib implementation materially changes;
2. the selected gzip payload geometry grows enough that wrapper overhead becomes a measured product owner;
3. new profiling shows a distinct Python wrapper cost rather than decompression/materialization itself; or
4. a new implementation eliminates a materially different layer of work and therefore constitutes a separate R2 hypothesis.

## Forge decision

Preserve gzip as the only currently supported inverse-codec owner, but escalate away from Python wrapper tuning. The next justified lane is an **R2 execution-boundary/native hot-path question** that can eliminate a larger fraction of the measured gzip work while preserving full inherited gzip semantics, exact output, bounds, recovery and integrity.

Before building such a candidate, measure/price the exact boundary it would replace so native-call overhead and buffer-copy cost are explicit. A native path must not be promoted on a gzip microbenchmark alone; complete promoted Logs extraction remains the decisive product boundary.

v0.30 remains release-locked.
