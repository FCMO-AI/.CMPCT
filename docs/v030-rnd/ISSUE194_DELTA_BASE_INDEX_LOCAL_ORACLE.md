# Issue #194 reusable delta-base index — local oracle

Status: **research oracle only / no product or release credit**

Authority checked: `agent/v030-authoritative-integration@496c96b40e09b6cd9a4eb81af2ec52db1caed354`.

Implementation owner: `agent/phased2-issue194-delta-index-reuse@ad74e628c4197bb1274a481d9c08daffc7a0c0fa`.
Validation branch: `agent/phased3-issue194-delta-index-validation`.

## Mechanism

Current `cmpct.resemblance.delta_encode` rebuilds the fixed-block weak-checksum index for an immutable base on every delta audition. The owner branch adds `prepare_delta_base` plus `delta_encode_prepared` so the same base index can be reused without changing the historical first-offset tie rule.

## Exact deterministic Shifted topology

Source generator blob: `335169bd6eb336b6d444cfbd34c291101262c3a9`.

On `resemblance_hostile_v1/01_shifted_versions` using the authority v0.28 CDC/sketch/LSH rules:

- files: **18**
- unique CDC nodes: **164**
- LSH candidate edges: **972**
- unique candidate bases: **80**
- maximum base fanout: **17**
- historical weak-index blocks rebuilt across edges: **2,699,424**
- weak-index blocks if each base is prepared once: **225,166**
- exact structural rebuild factor: **11.9886x**

One local lower-rung timing pass measured index construction at **9.8139 s** when rebuilt per edge versus **0.8218 s** when prepared once (**11.9414x**). This is not hosted/product timing.

Independent parity checks:
- 1,000 deterministic randomized old-vs-prepared cases, sizes 0–8,192 B, with replacement/insertion/deletion/repeated-anchor pressure: **0 mismatches**.
- 48 sampled exact Shifted candidate edges across 33 bases: **0 mismatches**.

The branch also adds a repository regression test for randomized parity, exact decoding, repeated-anchor first-offset ordering, block bounds and maximum-base-index bounds.

## Mandatory negative control: ML

Neutral generator blob: `9346995246f293fa03ea73e8782b809998588f71`.

On exact `neutral_hostile_v1/09_ml_artifacts`, authority v0.28 produced **114 unique CDC nodes and 0 LSH candidate edges**. Therefore reusable v0.28 delta-base indexing is **not** the ML v0.28 owner on this workload. Do not use this mechanism to narrate the ~22 s ML substrate gap away.

## Decision

The mechanism survives the cheapest structural/parity rung for Shifted and is worth one bounded integrated A/B if it does not displace the larger current owner. It is explicitly falsified as the v0.28 ML delta-audition explanation.

A promotion rung must preserve every delta payload/stat and final archive identity while measuring v0.28/attempt5 child wall, CPU and RSS plus complete-product wall. ML owner profiling remains a separate higher-priority architecture question.

No release threshold, comparator, format, reader or admission law changes.
