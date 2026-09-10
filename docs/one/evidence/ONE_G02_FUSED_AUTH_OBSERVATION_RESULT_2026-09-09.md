# ONE-G0.2 fused authentication observation — result

Date: 2026-09-09 America/Mexico_City  
Experimental version: **ONE-G0.2**  
Decision: **ADVANCE_FUSED_AUTH_OBSERVATION**

## Exact hosted authority

- branch: `research/cmpct1`
- exact evidence source: `490ed9b7bb7be3a8187c63a74dff704597096481`
- workflow: `CMPCT1 ONE-G0.2 fused authentication observation`
- run: `34424913281`
- job: `102707982608`
- artifact: `10132261122`
- artifact name: `fused-auth-observation-490ed9b7bb7be3a8187c63a74dff704597096481`
- artifact digest: `sha256:3b2d4d071a624157be3149bd3b3ce88c2b6c02e21b0315cf132e6e64f9c7e9f0`
- inherited semantic suite: **76 passed**

The hosted lane checked out the exact source, bound `HEAD` to `GITHUB_SHA`, passed the inherited authenticated-archive/selective/native-range/validated-program semantics, ran the frozen falsifier, and retained the exact-source result artifact.

## Mission lock

The promoted authenticated archive seam reread every regular-file payload once after ordinary archive ingestion solely to construct its AuthTree. The frozen hypothesis was that authentication leaves can consume the exact immutable bytes already read for ordinary ONE ingestion, eliminating that second filesystem/source pass without changing wire, reader semantics, authentication, selective geometry, resource/path behavior, or representation.

Disproof was any wire or semantic divergence, any retained authentication-only source reread, candidate source traffic above one logical payload pass, median build CPU above `1.05x` baseline, any row above `1.15x`, additional archive-wide payload caching, or a new reader-visible format/integrity mode.

## Frozen result

All promotion gates passed.

- byte-identical authenticated wire on every frozen row: **PASS**;
- reopened full-file equality and path set: **PASS**;
- authenticated selective bytes/accounting/geometry unchanged: **PASS**;
- authentication-only source reread bytes: **0 on every candidate row**;
- non-empty source payload traffic: **1.0x logical bytes candidate vs 2.0x baseline**;
- source-payload read ratio candidate/baseline: **0.5x** on every non-empty row;
- additional candidate authentication payload cache: **0 B**;
- median candidate/baseline build CPU: **0.799826x**;
- worst candidate/baseline build CPU: **0.816530x**;
- decision emitted by frozen falsifier: **`ADVANCE_FUSED_AUTH_OBSERVATION`**.

The matrix covered one 32 KiB file, one ~256 KiB file, one file crossing ONE chunk boundaries, a multi-medium-file tree, and a mixed tree with empty/tiny/medium/>1 MiB files, directories and a safe symlink.

## Causal interpretation

This is a true work-elimination result rather than a threshold win. The baseline dataflow performed:

`read payload for ONE ingest -> build representation -> reread payload for AuthTree -> persist authenticated archive`

The promoted research shape performs:

`read payload once -> derive ordinary ONE representation + root digest + AuthTree from the same immutable bytes -> release per-file buffer -> persist authenticated archive`

The representation and reader do not change. Authentication still hashes the bytes in memory; the result does **not** claim zero hashing or zero memory traffic. What disappeared is the second filesystem/source payload pass.

The CPU result strengthens the causal case: despite doing the same cryptographic work and producing identical output, the candidate is about **20% faster median** on the frozen matrix while also halving payload source traffic. The primary architectural value is nevertheless the eliminated source pass, which should matter even more on slower, remote or high-latency storage.

## Why this matters for ONE

ONE's speed doctrine requires observation, integrity and discovery to share unavoidable reads rather than stacking mechanism-specific passes. This result proves one concrete instance of that doctrine at an archive boundary: authentication can be fused into ingestion without becoming a separate representation mechanism or reader capability.

It also improves the credibility of the upcoming Genesis creation-cost comparison. A candidate that saved storage but reread every payload solely to build integrity metadata would be exporting cost into ingestion. That accidental second source pass is now removed in the research archive writer.

## Hostile review / remaining debt

This ADVANCE is scoped.

1. **No filesystem snapshot claim.** The one-read path derives representation and authentication from one immutable in-process payload, which removes disagreement between two reads, but it does not provide transactional filesystem snapshot isolation around metadata enumeration and the read itself.
2. **In-memory hashing remains charged.** Source-I/O fusion is not memory-scan fusion. AuthTree hashing still consumes the payload bytes and must remain in creation CPU/memory accounting.
3. **No Genesis score preview.** This experiment does not touch or encode the 15-workload gate corpus and says nothing directly about v0.29/v0.30 superiority.
4. **Recovery/full product parity remains separate.** The research archive seam does not automatically inherit every mature CMPCT recovery, portability or filesystem guarantee.
5. **Observation fusion is not complete.** This closes one duplicated source pass. The broader writer should still converge toward one common per-file/block observation record feeding root identity, integrity and Law opportunity evidence where that can be done without inflating state or per-byte compute.

## Comparator / gate status

Frozen Genesis comparator authority remains unchanged:

- v0.29: `02b8b27cb2d97af7c6e0797984a898e8fa8a8e5d`;
- deferred v0.30: `f4b158a55a08b9b18b50e4e4abe4b9251048c772`.

This mechanism-level ADVANCE does not substitute for or pre-empt the September 11 same-input 15-workload gate.

## Next decisive action

Carry this fused source-ingest principle into the best admissible archive writer path used by the Genesis candidate, while keeping creation-stage accounting explicit. The next high-value question is whether root hashing, authentication leaf hashing and cheap Law-opportunity observation can share one bounded block traversal/observation record without increasing no-op CPU or retained state. Any such candidate should be preregistered and attacked on incompressible, compressed/media, tiny, structured and versioned controls rather than tuned on the temporal-positive rows.
