# O12 — Native authenticated logical digest export for bounded-streaming verification (preregistration)

Date: 2026-10-24 UTC. Status: PREDICTION FROZEN BEFORE PRODUCT/TEST IMPLEMENTATION. No release or product benefit is assumed.

## Authority and non-overlap

Canonical development is `agent/v031-development` (orientation HEAD `4545d7d5b2a0b712b4b00f5a9c291d4a3a9e169b`), released v0.30.0/r24. This isolated draft starts on exact independent native safety/batching owner PR #326 HEAD `43ba79f9b9395af22a0f408de565704c268a4758`. PR #337 owns research-only C batch/stream extraction; PRs #338/#339 own Python signed-tree preflight; this experiment changes neither surface. No Concurrency Protocol was present on the development branch when checked. `docs/discovery/STATE.json` is a staleable cache, not a lock.

## Question

Can a native consumer performing fixed-memory ranged reconstruction verify its final logical output against the **authenticated r24 index** without exposing Rust internals, allocating a full-file output, or silently trusting mutable RAW payloads?

The current public C ABI exposes kind/path/size/ranges but **not** the per-entry SHA-256 already parsed into `Entry.logical_hash`. For RAW direct or RAW PACK, range reads do not by themselves attest the reconstructed whole file. Existing O10/O11 results rely on *independent external original-source comparison*, which an ordinary consumer cannot always perform.

## Prediction / mechanism

Introduce one ABI query `cmpct_entry_logical_sha256(archive, entry_index, uint8_t out_digest[32])`. It copies only an authenticated-index logical digest for an ordinary file. Non-files and entries **lacking** an authenticated logical hash return UNSUPPORTED; invalid index RANGE; null archive/pointer NULL. Valid output is zeroed on failure and never borrows Rust storage. This call is metadata-only: no physical read, no format/codec/Writer mutation, no clock-dependent state.

A representative bounded-stream consumer will compute SHA-256 on the bytes it actually writes; equality with the returned authenticated index digest proves those bytes match the index commitment under SHA-256 assumptions, even when individual RAW range calls do not authenticate their source. On a modified RAW physical source the consumer should obtain a **mismatch**, not falsely claim exact output. The query itself is not a signature of archive-file freshness or filesystem transactionality.

## Strong controls and falsifiers

- Build real r24 archives with the inherited Builder: incompressible direct RAW (>=1 MiB), small packed text Zstd, and multiple kinds. Use native `cmpct_open`, `cmpct_entry_path`, `cmpct_entry_read_range` via ctypes, and Python stdlib `hashlib.sha256` on returned logical bytes. A separate Python Reader or source-file SHA is a differently rooted control.
- Test digest equals source hash for ordinary Builder-produced files; read 64 KiB chunks and hash streamed output; mutate one RAW payload byte **after native open** without changing the signed index, assert consumer-level digest mismatch. Existing ABI read semantics remain unchanged.
- Test invalid index, non-file, null archive, null output, and fail-zero digest behavior. Test optional-hash absence with independently signed index mutation if cheap; otherwise explicitly leave it unmeasured and make the implementation fail closed.
- Negative: if real r24 Builder omits row SHA for common RAW data, the API is only a scoped capability; no all-archive claim. If authentic index hash is not actually committed or if streaming a real RAW file cannot detect byte mutation, retire/narrow. If ABI adds more cost to cold open, format bytes, or old symbols change, reject.
- Hosted exact-head native court plus existing native/fuzz/general CI; do not award release/performance credit from a few file/ABI tests.

## Alternatives, economics and debt

Full-file verification inside every selective native read exports physical I/O and defeats RAW range locality. Exposing raw physical-header SHA is weaker than exposing authenticated logical index identity and fails for composed/sparse representations. A caller-supplied SHA-256 implementation or existing platform crypto is a portable *consumer* responsibility; no new third-party runtime dependency is introduced in the library. Hashing the completed output adds ~1 hash-pass worth of CPU and has no claimed free performance gain. Whole-tree publication, path safety, hardlinks, symlinks, crash recovery, and mutable-source snapshot semantics remain independent product debt.

## Decision

Only a source-exact real-Builder + independent-digest + post-open mutation court can earn a narrow positive. This is an optional ABI building block for O11 productization, not a complete extractor and not a release milestone. Preserve all negatives.
