# J24G78 — Writer 63-delete copy-elision and stage-ownership preregistration (FROZEN BEFORE IMPLEMENTATION)

Date: 2026-10-30 UTC. Source parent: [#822](https://github.com/FCMO-AI/.CMPCT/pull/822) exact `6b68197c64b8de0654dd2f854a5185b45a00d2b9`; this is a research-only instrument, no shipping changes. Primary question is issue [#824](https://github.com/FCMO-AI/.CMPCT/issues/824).

## Baseline and question
J24G76 on physical public Writer archives recorded 63 one-op deletes of 8,192 initial files in Ubuntu/macOS/Windows 7.306/6.448/9.571 seconds and 32,768 files in 37.255/33.526/42.869 seconds. This exceeds the last-generation Reader-open cost. In inherited `src/cmpct/transactions.py` each `append_delete` (and `append_rename`) opens `CMPCT`, scans surviving hardlink owners, makes a full MessagePack serialize+unserialize clone of `ar.index`, and appends a one-op signed delta; only depth 63 requires the mutated checkpoint copy. The stage whose cost dominates is **not yet directly measured**. PR #795 owns shipping journal behavior; #815/#817 own hardlink/signed-xattr composition.

## Competing mechanisms / BONK
- H1 copy-elision: deferring the full index clone until the 64th checkpoint meaningfully reduces complete 63-delete Writer time without changing any committed byte or recovery contract. This is a bounded D1/D2 research mechanism.
- H2 Reader replay dominates the total; avoiding the copy saves relatively little and does not solve Writer economics. The J24G76 end-depth Reader linear model predicts 77–95%+ of total on some hosts, so H2 is a strong control and may win.
- H3 fsync/create/metadata or instrumentation process history dominates; false attribution possible. Another frame is a per-session owned state/cache with explicit interprocess visibility proof; do NOT implement it until H1/H2 are decided.
- No threshold tuning, removal of fsync, looser journal admission, split-consistency or reward for changing timing boundaries. This is not a new archive representation.

## Frozen experimental design
Use ONE physically created Builder revision-24 base per N, clone the same archive bytes into isolated copies, and execute the same 63 distinct public `append_delete` names. Two families N=8192/middle and N=32768/tail, both measured on Ubuntu 24.04 / Python 3.11. Variants:
A — inherited public `tx.append_delete` unchanged;
S — literal source-equivalent phase-instrumented clone including full index clone on **every** generation (sham control);
B — same phase-instrumented clone but full-index clone **only at depth >=63**.
Keep hardlink owner guard, Reader, checkpoint, signed delta encoding, two phase fsync, source files and benchmark policy identical. Do not measure a different archive between A/B. Source attest exact parent `transactions.py` blob `71bbc8a989d1da79d0f0dbe44f7f5c39f3304854`; abort if it changed. Preserve raw per-append wall/CPU stage times: CMPCT context and by lookup; hardlink guard; MessagePack copy; checkpoint application; append/footer/fsync. Keep instrumentation itself outside the A path, to avoid bias, and S sham control.

Warm up and run A/B/B/A (at least one block per N, preferably 2 if bounded) on independent source-exact file copies, with at least one S run for causal attribution. Total Writer median per family, per-stage percent, RSS/peak where available, final archive bytes/digests, effective Reader index, all live member bytes and strict structural preflight. At the 64th mutation require a checkpoint (depth resets), exact byte identity to A's outcome, owner metadata semantics, and corrupt-last-footer recovery to preceding generation. Zero test changes to release gates. Preserve stdout/log and JSON artifact with actual host, source SHA, branch, head, corpus, timing arrays and failures.

## Decision / kill rules
1. Reject any byte/index/preflight/read/64th-checkpoint/corrupt-tail mismatch, a missing source identity attestation or a missing A path. Never count performance before semantics.
2. H1 materiality requires **>=10% lower complete 63-delete wall median on BOTH N families** and **at least 5% absolute total Writer time measured directly as copy work** under S. If either fails, mark narrow H1 `NOT_MATERIAL`, even if an isolated clone microbenchmark is favorable; preserve it as bounded microdebt only.
3. A vs S sham must differ <=10% per family in end-to-end wall median; otherwise phase attribution is ambiguous and cannot earn H1 credit. Run A/B in balanced chronological order; note cold/warm asymmetry. A/A raw process-history noise is not proof of algorithmic change.
4. Verify source identity, equal corpus bytes, integrity and restore for both. H2 wins if Reader-open dominates stage attribution (>50% of complete Writer wall), especially when B cannot satisfy H1. Compare full product costs separately; oracle not promotable. New evidence should change whether to spend another activation implementing safe clone elision vs Reader/session ownership, not open endless nearby variants.
5. One Ubuntu hosted result cannot establish macOS/Windows portability, cross-process concurrency, production RSS, arbitrary filesystem correctness, general performance, release parity or security #749; no shipping credit until whole product evidence.
6. Stop work after decisive result; retire copy-elision as primary family if materially bounded. Preserve original raw receipts and negative controls.

## Coordination and invariants
Research path only. No modification to `src/`, `native/`, `docs/discovery/STATE.json`, format revision, historical test fixtures, published main, PR #795/#817 branches, or frozen policies. PR #822 gives full-PR benchmark admission for any future material branch, but does not require a redundant official benchmark on a research-only path. Do not promote without signed xattrs/hardlinks, recovery, hostile grammar, concurrency, format and exact-head CI gates. Repository truth + #824 win over this prose if concurrent ownership appears.
