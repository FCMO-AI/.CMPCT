# J24G74 — owner-transfer acceptance and falsification matrix

**Date:** 2026-10-30 UTC. **Status: experimental integration contract, NOT authority to merge.** Original data in [result dossier](2026-10-30-j24g74-owned-decoder-result.md), [PR #820](https://github.com/FCMO-AI/.CMPCT/pull/820), and [source-bound run #41032961573](https://github.com/FCMO-AI/.CMPCT/actions/runs/41032961573). This note is a *prospective product-integration threat model* derived after seeing the result, not a replacement for the immutable preregistration or a new prediction retroactively backdated.

## The smallest ownership proof that may transfer

At inherited Reader blob `29a8be64f3acfb027750351c6a567fd82cf7dc97`:

1. `_latest_generation()` examines candidate footers and invokes `_index_from_footer()`; if unsuccessful, it may try an earlier footer. The experiment retained this selection/recovery boundary.
2. `_decode_generation_payload()` returns authenticated `(kind, payload_bytes, previous_pointer)` after footer grammar, bounds, decompression and SHA-256. **It does not persist a decoded MessagePack object.** No check of bytes alone proves operation grammar. Source is read and checked at the inherited location.
3. `msgpack.unpackb(payload, raw=False)` constructs a new checkpoint index and each one-op delta as fresh local Python objects in `_index_from_footer()`. Before the final `return index, depth`, these decoded objects are reachable only via local references constructed by the method, provided no foreign callback/cache is introduced.
4. `OwnedCMPCT` transfers that *private* graph to a bounded replay path after the exact conservative `admit()` check; this necessarily mutates the base dictionary, nested rows and delta-provided PUT rows. These are then incorporated into the returned effective index.
5. Once returned, `__init__` exposes `self.index`, `self.files`, `self.by`, `self.fsmeta` and `self.blobs`. Those are mutable Python descriptors. **No future invocation can assume unique ownership of those exposed objects.** Public-reader descriptor mutation and already-constructed caches remain separate unsafe optimization surfaces, not permissions granted by this result.

The core conditional proof is therefore `newly-decoded, unescaped, nonshared graph → in-place reconstruction → publish complete graph once`. The evidence does **not** establish `arbitrary caller dictionary → safe in-place reconstruction`. The experiment's explicit retained-caller control demonstrates the latter is false.

## Product integration gate: exact disproof first

| Threat / alternative explanation | Cheap decisive oracle before promoting source | Failure disposition |
|---|---|---|
| Decoder objects unexpectedly shared or reused | Assert nonescape/uniqueness over actual journal decode and any future cached/native bridge; add retained-caller negative that must visibly mutate only in an explicitly rejected API | Reject no-copy generalized helper; retain defensive-copy branch |
| Invalid committed opcode or malformed footer | Reuse original #795/#791 J24G56 and #795 J24G57 tests and independent no-CMPCT hostile footer/operation oracle, including rejection vs recovery distinction | Preserve fail-closed Reader/preflight and old-generation recovery; stop |
| Identity-signed xattrs/owner overrides move to wrong ordinal | Real multi-generation delete/rename/put with sparse physical POSIX xattrs and original inode identity; include delete/recreate same name | Stop; metadata fidelity and signed index are hard requirements |
| Hardlink owner operation or alias chain | Compose #241/#815/#817 hardlink fail-closed owner guard and strict preflight before Writer mutation; add hostile owner-rename/delete plus checkpoint 64 | Stop; no silent alias corruption |
| Hidden O(N) admission bottleneck at large N | Held-out 8,192/32,768/65,536-member Reader-open, realistic delta counts, CPU/wall, alloc peak, fresh process RSS and full verify/extract | Retire or narrow on nonmaterial gain or exported cost |
| Long-lived public reference may mutate after open | Separate source-exact public `index/files/by` mutation court; preserve inherited public semantics or explicitly define immutable descriptor contract before changing it | Do not infer immutable graph from private decoder ownership |
| Checkpoint and recovery under corrupt committed tail | Authentic 64th generation checkpoint, truncation, footer checksum/flags, invalid op, prev-pointer hostile and bounded reconstruction work | No release if recovery differs |
| Multiple Reader representations/native parity | Shared ABI/native Rust opening and complete same-file logical/index verification, index borrowing and memory ownership | Reject unproven alias/recovery transfer |
| Startup/cold cache vs local warm Reader-open | Same physical tree A/B/B/A fresh process and cold-open controls, splitting import/startup from Reader constructor, raw repetitions | Preserve measured scope; no marketing product speedup |
| Bytes/create/extract regression | Official source-fingerprint-bound parity and complete 0.x product gates, same-input equal semantics, 0 deterministic archive-byte regression | Preserve seed as research debt; no release |

**No product code may enter a promotion branch solely because the new helper is faster.** The currently measured 63-delete warm-open case has an additional 3.30–3.97x advantage *versus the previously experimental factored Reader*, with ~1.1 MiB less traced allocation; those are source-specific observations rather than a memory-safe public ABI specification. In the mixed family, the further observed gain is 1.84–2.20x, on much smaller final member counts. Flat Ubuntu process RSS and cross-run macOS variance reject a general RSS-dominance or deterministic-speedup claim.

## Comparison/control and minimal next authorized unit

Priority with #795/#808 integration owner: **first** a source-exact lifetime/descriptor mutation oracle over the decoded index and signed hardlink/xattr histories; **second** large held-out complete Reader-open memory/economics; **third** integrate one general state-replay architecture in a staging PR with safety/product gate verification. Maintain #818 copy-preserving implementation as control and #811 simple DELETE route only as an alternative if general carrying cost fails. Never insert a second copy of `journal_replay.py` into the product or refactor both public and private replay contracts in one unproven step.

Claim and handoff: #820 owns this bounded science only; #818 owns the earlier full Reader transfer, #808 the general helper, #795 the shipping signed-journal integration seam, #815/#817 hardlink correctness, #574 shared Discovery STATE. At this recorded boundary **no overlapping shipping mutation occurred**, no new discovery policy lesson was earned, and product/release credit remains zero.
