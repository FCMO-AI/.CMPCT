# O219 — Same-wire index-decode and native strict-admission cost ceiling (preregistration)

Date: 2026-10-27 UTC. **Science/oracle only**. Base is O218 #577 `6372e780be99a31f5ea21b7a3c74fde92cf0bc45`, original O216 parent `6989b25640be2c82436bb77ec545dd15816f698b`. No Reader, Builder, validation, benchmark, release, format or version change.

## Question
O218 proves >=3x against an O216-like *per-reference function micro* by moving a strict S_CHUNKS loop to the CPython C API. On identical MessagePack wire bytes, can that gain survive **index decoding and message parsing** strongly enough to justify a full installed Reader implementation experiment?

## Simpler control, mechanism, alternative
Use exactly O218's immutable C source and its fixture generator, same profile matrix and raw serialized bytes. Time same-wire `msgpack.unpackb` once per evaluation and run original O218 Python strong/O216-like or O218 native check. Keep one process and identical decoded objects; do not attribute interpreter startup, index decompression, footer scans, physical records, filesystem I/O, or full Reader work to this oracle. The optimistic control credits native validation as though its binding/dispatch and packaging were free beyond direct call. If decode dominates, a large inner-loop ratio may have small total effect. If decode is small, native survives at this rung but still needs full Reader and portability evidence. The strong original `_validate_storage` may differ from the O216-like proxy and must not be called identical.

## Prospective prediction / decision
At the 262,144-reference high-repeat and high-diversity profiles, decode+native speedup relative to decode+O216-like Python is **below 2x** despite O218's >=3x micro, OR the native gain persists at >=2x. Either outcome changes experiment priority: below 2x narrows the payoff and requires cheaper full-Reader cost bound before product work; at/above 2x supports owner-coordinated authentic Reader A/B, not product adoption. Record *both* outcomes with raw repeated paired samples, CPU and wall, wire size/hash, decode fraction, bounded portability and exact source identity. No retrospective threshold tuning.

## Disproof / kill
Any changed wire semantics, input mismatch, invalid native acceptance, sample-order asymmetry without randomized pairs, missing raw repeats, or source identity drift voids the court. Host differences and GC effects must remain visible. Host Python 3.13 is an independent local observation, not a claim about GitHub Actions 3.11/3.13 or complete archive size/time.

## Ownership and concurrency
O218 #577 owns the native C function and its separate micro claim. O219 owns only the cost-composition experiment. No changes to O218 code or public release gates. Re-read #577 before late writes. If the O218 source changes, pin to exact source SHA and report scope, rather than silently reusing changed results.

## Scope and evidence classification
Lower-rung research/evidence, no full-product credit and no PARETO or discovery-policy edit without repeated transfer evidence. No fabricated CI. This document is the immutable preregistration before writing the O219 instrument.
