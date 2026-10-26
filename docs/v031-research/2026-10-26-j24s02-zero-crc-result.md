# J24S02 — hosted zero-run CRC algebra falsification

**Date:** 2026-10-26 UTC. **Scope:** offline raw-DEFLATE oracle only; no CMPCT product code or format changes.

## Problem and preregistered mechanism

J24S01 #525 showed that already-known, generically admitted sparse zero runs can reuse raw-DEFLATE compressed fragments without dropping full SHA256/CRC32 accounting. This follow-up asks whether exact CRC32 polynomial composition can replace per-byte CRC scans, preserving the same logical SHA256 passes and raw-DEFLATE bytes. Preregistration precedes code: `docs/v031-research/2026-10-26-j24s02-sparse-crc-prereg.md` at commit `97e38222fbeb773c30c24f3a8c2197c259cd17b0`. The continuation threshold required >=5% whole-oracle encoder wall improvement for **both** the all-zero and mixed sparse 256MiB families (at least one compression level each), <=2% no-hole slowdown, and exact digest/bitstream equality.

## Exact-head hosted primary evidence

- PR: https://github.com/FCMO-AI/.CMPCT/pull/547
- Hosted Actions: https://github.com/FCMO-AI/.CMPCT/actions/runs/40412287839 — `SUCCESS`.
- Source-evaluated HEAD: `665e6b47816bc7cafeddb753f8baaabe0e1c6eb3`.
- Source file: `research/j24s02_zero_crc_oracle.py`, Git blob `33c359f19b19ac8c28eb52e21a4e591e71fba9c8`.
- Original raw observations: https://github.com/FCMO-AI/.CMPCT/actions/runs/40412287839/artifacts/12692099424 (includes entire interleaved repeat series, source/prereg blobs and Python/zlib identities).
- Exactly **320 independent adversarial GF2 composition checks** against literal zlib, spanning unaligned sizes, nonzero initial CRCs and nonzero suffixes. All passed.
- At least three alternating repeats per arm/case; all SHA256, CRC32, *complete* DEFLATE bytes and independent bounded raw-inflate output matched. This is a negative **performance** result, not a correctness failure.

### Measured complete offline-oracle wall time, median of three interleaved repeats

| Input | DEFLATE level | Inherited CRC scan (s) | Run-algebra (s) | Candidate/baseline speedup | Bulk zlib control (s) |
| --- | ---: | ---: | ---: | ---: | ---: |
| 256 MiB all holes | 1 | 0.213134 | 0.169621 | **1.257x** | 0.213046 |
| 256 MiB all holes | 6 | 0.213468 | 0.169721 | **1.258x** | 0.213530 |
| 256 MiB mixed sparse | 1 | 0.216097 | 0.400732 | **0.539x (regression)** | 0.216091 |
| 256 MiB mixed sparse | 6 | 0.217925 | 0.403591 | **0.540x (regression)** | 0.218333 |
| 64 MiB nonhole | 1 | 1.439698 | 1.442404 | 0.998x | 1.441439 |
| 64 MiB nonhole | 6 | 1.495106 | 1.495452 | 1.000x | 1.496634 |

The same bitstreams had lengths 1,176,066/265,474 B for all holes, 1,241,474/331,106 B for mixed sparse, and 67,129,666 B for no-hole at levels 1/6 respectively. No new compression ratio credit arises: **every CRC policy emitted identical bytes.**

**Prospective decision: `RETIRE_AS_FULL_PRODUCT_PRIORITY`.** Mixed sparse fails the whole-oracle improvement threshold badly. A favorable 256MiB single hole run is not enough to justify adoption. The strongest simple `zlib.crc32` bulk control is approximately equivalent to the inherited incremental implementation on hosted CPU, without any fragile GF2 calculations.

## Causal diagnosis and counterfactual discriminator

After early local negative screening, one local cProfile (not hosted/authoritative product evidence) on a 256MiB mixed sparse run showed **3,488 GF2 matrix-square operations and 112,048 matrix-vector applications** consuming about 0.303 s cumulative within a roughly 0.541 s measured run; the SHA256 full-byte scan consumed about 0.200 s. Repeated pure-Python recomputation of the zero-run transition operator, not raw compression, explains the observed mixed-length failure. This is a *mechanistic explanation*, not evidence that hypothetical memoization wins. A cheaper prospective control would have profiled one 16MiB repeated-run transition before purchasing the full court; Python GF2 versus vectorized C CRC asymptotics can invert depending on run fragmentation.

A different **cached per-length transition-matrix architecture** might address repeated computation, but it must independently preregister and beat the same C zlib/complete SHA controls and true product costs. No threshold gardening, post-hoc promotion, or invisible rescue in J24S02 is authorized.

## Losses, ambiguity and negative evidence

- A single contiguous 256MiB zero run wins; 16 repeated shorter structural zero runs catastrophically lose. The stronger mixed control must win at product generality; it does not.
- The `bulk` arm pays for an explicit 8MiB zero buffer; current candidate uses 1MiB seed and Python matrix state. No independent per-arm peak RSS evidence was obtained.
- Whole SHA256 was fully charged, limiting maximum theoretical wins; neither same-UID source mutation nor malformed extent geometry was tested here.
- The benchmark uses deterministic standalone J24S01-shaped spans, **not a valid CMPCT archive nor real ZIP64 Reader**. No whole-system 4GiB I/O, memory, publication, recovery, platform, security, real filesystem or release claims.
- Benchmark time includes encoder SHA/CRC/DEFLATE in the oracle but not disk I/O or Python startup. Independent compressed-byte verification is outside the timed encoder and is a correctness check, never a claimed speedup.
- Product source, format revision 24, exact-head release gates, historical comparators, and shared `docs/discovery/STATE.json` are unchanged.

## Transferable lesson and next decision

This negative should retire the current **uncached portable-Python GF2 implementation** as a product optimization. It does **not** prove all CRC-combine architectures incapable: the specific causal weakness is repeated rebuilding of a parameterized polynomial operator. If a future independently preregistered owner tests operator caching, charge matrix construction/retention, exact CRC/SHA, heterogeneous sparse run patterns and actual J24S01 ZIP64 product economics before credit. More urgent product leverage remains end-to-end O193/J24S01 ZIP64 integration and correctness/security debt.

No merge or release is authorized by this research-only falsification.