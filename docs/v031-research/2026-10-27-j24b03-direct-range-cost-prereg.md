# J24B03-P — Source-exact direct-range cost discriminator (prospective)

Date: 2026-10-27 UTC. Status: **preregistered before performance implementation or measurement**.
Owner: [J24B03 #609](https://github.com/FCMO-AI/.CMPCT/pull/609), isolated branch `agent/phased3-v031-j24b03-direct-blob-size-guard-20261027`.
Sources: released immutable `main@80c358f8824ec1b20d349c92ed94c898090969b0` versus the then-current J24B03 `f9e95633db832b6c2ab95de8d7aaaf80c4b3ece8`; record the *actual* candidate head / reader blob in every hosted receipt.
Existing three-host validity court has passed on J24B03's exact code, while general tests include inherited release-fingerprint and surface-revision failures; do not relabel them as this patch's defects, and do not hide them.

## Question and causal model

Does the necessary O(1) authenticated direct-owner size/BHDR guard introduce material complete-process or repeated selective-read CPU/wall/RSS cost on valid immutable revision-24 archives, beyond the shipped `read_range` fast path? The strongest simpler control is the actual released reader on the **same identical wire archive**, not an invented Python loop without the archive handler. Primary possible source of extra cost: one extra index equality plus unpacking BHDR for every RAW request. Counterhypotheses: benchmark wrapper and Python dispatch dominate; compressed blob decoding/cache dominate; fresh process startup and mmap/page-fault noise create artificial differences. Open time and per-range work must be separated.

## Frozen decision rule

A prospective **performance debt signal** is a repeated, same-host source-exact median candidate/base ratio >=1.20 in both wall and CPU for RAW 16-byte repeated range calls **and** >=0.50 microseconds absolute additional per call, after ABBA balancing. For multiple processes show individual raw observations and dispersion; if noisy or contradictory, classify inconclusive rather than positive. An excessive signal does **not** license removing a safety check; instead investigate cheaper equivalent authenticated physical custody. No-pass does **not** prove full-product no regression. A negative/zero signal requires that the instrument actually executed original/repaired distinct reader source files, the same archive SHA and the same answer hash.

## Cheapest decisive rung / test design

On Ubuntu CPython 3.11 use an independent revision-24 wire generator from the J24B03 correctness court (not the Builder): RAW, Zstd and Deflate, direct K_FILE 128-byte payload. Generator is run **once**, then byte-for-byte identical archives are consumed by the frozen and patched sources. Per independent worker record separate import/startup-excluded open wall/CPU, repeated `read_range` wall/CPU for deterministic offsets [0, 7, 31, 63, 111] at length 16, request count, measured logical bytes, answer identity, source module path, process VmHWM where available. Use repeated fresh-process A/B/B/A order rather than one unbalanced sequential A-versus-B; preserve raw observations, actual git HEAD and source blob digests. Verify answers against expected payload, not merely against each other. Confirm valid frozen direct-codec controls remain accepted in the original three-host tribunal.

Restrict the primary decision to RAW requests; compressed frames and cold-open are negative/diagnostic controls. Avoid general product credit without same-corpus archive size, creation, full extraction, security, portability and official release-parity evidence. No cache/process startup timing boundary changes after seeing results.

## Product/authority boundary

Never weaken J24B03 geometry/BHDR guards, exactness, frozen vectors or comparator semantics. Do not change core version, on-disk revision, published index, release thresholds, Discovery Engine policy or `STATE.json`. No merge or release. Keep the new instrument/workflow and receipt as a small, self-contained adjunct of PR #609. Coordinate a verified result with Reader composition owner #569; avoid duplicating their implementation.
