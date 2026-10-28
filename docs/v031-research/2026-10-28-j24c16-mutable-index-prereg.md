# J24C16 — independent installed Reader falsifier of mutable in-memory S_CHUNKS prefix hints

Date: 2026-10-28 UTC. **Prospective research preregistration, before implementing instrument or workflow.**

## Authority and ownership

- Base: frozen owner PR #662 HEAD `a66fd593a83cc4c71556d3d86d835c51abd20a96`; **owner retains all product code**. This is independently preregistered replication of a narrow risk already documented in #662's `docs/HARDENING.md`, not a second fix implementation.
- Product/format/safety/conformance/frozen benchmarks/thresholds **unchanged**. No merge, version or release authority.
- Do not edit `docs/discovery/STATE.json`, owned by #574.
- Source code for range path: `src/cmpct/reader.py` on base HEAD, lines 346–370; source for native proof: `_fastscan_abi3.c`; source for independently created signed r24 archive: `tests/test_o215_fixed_chunk_admission.py` `_make_archive`.

## Question and disproof

Is the exact signed R24 S_CHUNKS logical-range result altered if a caller mutates the Reader's **exposed in-memory** reference list after the native prefix proof has been constructed? No signed archive bytes, physical blobs, payloads, path or read source descriptor change. Signed archive is *valid* and must pass preflight/read/verify before post-open mutation.

**Expected counterexample** (from independently executed pure-Python lower-rung model): 512 refs, three raw owners `A=b'A'`, `B=b'BB'`, `Z=b''`. Signed list `[B]+[A]*255+[Z]+[A]*255`; declared logical length exactly 512, initial native stride marks `(0,257)`. After native admission, swap only the two **in-memory** refs at indices 0 and 256. New reference list still has total 512 logical bytes, but its true prefix at 256 is 255, not cached 257. A fresh linear lookup at `read_range(257,1)` would return `b'A'` while stale fused marks predict `b'B'`.

Two distinct questions must remain separate: (a) whether **actual installed Reader** reproduces the model and returns a semantically wrong byte without rejecting the in-process mutation; (b) whether hostile signed malformed *on-disk* data is accepted, **not tested and not claimed here**. The public mutable Python object surface has no documented immutable-index contract; causal proof is bounded to caller mutation.

## Cheapest decisive test

Build the genuine CPython 3.11 ABI3 wheel and install noneditable in a fresh Ubuntu process. Before mutation validate source/extension identity, signed archive physical SHA, strong `verify()` and exact bytes. Confirm the native scan returned the expected prefix tuple. Capture source archive SHA both before/after mutation. Use fresh *independent byte concatenation* (not `CMPCT.read_range`) as reference and force a second, nonindexed strict `read_range` control on the same mutated descriptor shape (without changing the original source archive) to isolate the hint. Record actual mutated range byte/exceptions, marked/linear values, and source identities in durable JSON.

**Kill condition:** If installed Reader doesn't return the model's wrong-byte result, record `MODEL_NOT_TRANSFERRED` and preserve evidence; do NOT change the descriptor/model until it passes. If all authenticated archive bytes, initial strong verification or exact native helper identity cannot be established, classify **INFRA/EVIDENCE FAIL**, not positive/negative product evidence. A native extension that never executes is not a decisive test. This study's SCIENCE workflow must succeed on valid evidence even when the hypothesis is false; failed audit/integrity contract is a workflow failure.

## Alternatives and exported costs

Possible future repairs belong to the owner: freeze/copy descriptor list (memory/copying overhead), reader-private authenticated structural snapshot, epoch-aware immutable descriptor, or fail-closed mutation detection (per-read O(N) can erase the Q64 gains). Prefer a bounded immutable snapshot proof to a second full per-query scan; release judgment requires CPU/wall/RSS/bytes/resource-limit and adversarial parity. Do not claim a repair or promotion from this falsifier alone.

## Evidence and decision boundary

This is a **lower-rung installed product-correctness experiment** not a throughput comparison, cross-platform claim, complete extractor/recovery or release benchmark. Do not conflate an intentionally modified Python object with corrupted signed archive data. Record exact source SHA, CI run and artifact identities, any failures, and next cheapest owner-safe corrective fork. A negative result is valuable and must not be retested with different fixture until a distinct mechanism warrants it.
