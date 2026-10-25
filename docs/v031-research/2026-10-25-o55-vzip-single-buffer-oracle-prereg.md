# O55 — Single captured-byte VZIP source-coherence and byte-parity oracle (preregistered)

Date: 2026-10-25 UTC
Status: PROSPECTIVE, RESEARCH-ONLY / NOT PRODUCT SOURCE
Parent discovery: O54 source-exact run 40163268238, commit 377fe5887d30b53b636491f918fdca918d702743.
Owner boundary: product Builder issue #408 / PR #405. DO NOT edit owner source.

## Decisive previous observation
O54's true installed original O50 Builder on Ubuntu/macOS/Windows **emits an unverifiable r24 S_VZIP** under a deterministic same-inode, equal-length in-place ZIP_A->ZIP_B mutation after `make_vzip_recipe`'s first `ap.read_bytes()` and before its independent `ZipFile(ap)` open. All 3 hosts: stable A/B controls PASS, mutation count exactly 1, same physical inode and length, Builder returns, `read` and `verify` reject virtual ZIP reconstruction. This is the previously observed starting evidence, not an O55 prediction.

## O55 distinct mechanism question
Can the existing one full `original` bytes buffer already acquired by the codec be made the sole truth for *all* virtual-ZIP parsing and physical stream extraction, so a captured ZIP_A yields a coherent archive even when its source path changes afterward, while producing byte-for-byte identical complete CMPCT archives on immutable input?

The lower-rung **reference/oracle** is an independent research function reproducing `make_vzip_recipe`'s algorithm from a bytes argument. It runs ZipFile over `io.BytesIO(original)` and extracts compressed stream slices directly from the same `original` buffer, with the same add_content callbacks. It is injected in a test through the Builder's existing `make_vzip_recipe` function seam, never committed to `src/`. The Builder's later separate `rawsha=p.read_bytes()` is an outstanding source-lifetime policy defect; for S_VZIP that row hash is currently dropped in favor of the recipe's original digest, and O55 makes no assertion about other storage types.

## Prospectively observable acceptance
1. Independent stable ZIP A and B: actual original v0.31 O50 and oracle Builder produce *identical complete r24 bytes* and Reader verifies/extracts original bytes; both exercise actual S_VZIP.
2. Mutate the same regular source inode and preserve length **after the oracle's captured A bytes** but before parsing them. Oracle Builder must emit an authentic r24 archive that Reader verifies/reads exactly A, instead of O54's unverifiable mixed-generation artifact.
3. Prototype's reference recipe and candidate/physical bytes must preserve *all* SHA/CRC, logical filesystem semantics, compression choices and stored length on these examples.
4. Repeat with multiple entry ZIP_STORED and ZIP_DEFLATED entries; if the original codec rejects a particular ZIP through `deflate_level_for`, do not award parity or product credit on that example.
5. Directly record input/snapshot/archive SHA, identity witness, source captures and full-archive byte equality. Do not claim filesystem I/O/CPU/RSS savings without measuring them on full real product. The main bounded cost is retaining the already-acquired ZIP byte buffer plus any new in-memory stream views/copies.

## Stronger controls and rejection
No instrument may modify Reader, frozen comparators, validator, source under immutable controls, or canonical sample ZIP structure to secure parity. A valid oracle archive produced after source mutation is not a full atomic filesystem snapshot: neither other files nor in-place malicious mutation during the *initial* captured-byte read are covered. Any changed stable complete archive bytes, failed verify/read, source-fingerprint mismatch, missing VZIP admission, or leaked external read is a disproof/INCONCLUSIVE appropriately, not a successful fix.

## BONK economics
Alternatives considered: (a) open the path independently again and compare path metadata (retains ABA and repeat I/O), (b) pinned root+source descriptors (helps ancestry/identity but mutable file contents can still change), (c) fully materialized private file snapshot (extra bytes/temp I/O). This reference reuses the *already-required* full raw ZIP buffer and avoids extra file reopen semantics for VZIP only. Test carrying-cost and product byte parity first, without implementing a full fd-rooted Builder source manager. No product promotion is authorized by this oracle; route eventual implementation and full release gates to the #405 owner.

## Source and timing law
O54 preregistration/source are immutable historical predecessors. O55's predictions are recorded here **before** coding the detached reference tests. Exact HEAD/host CI artifacts will remain distinguishable from earlier O54. No version bump, core format change, merge, or release.
