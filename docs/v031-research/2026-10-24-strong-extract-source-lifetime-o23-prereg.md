# O23 preregistration — same-handle source mutation after strong verify

Date: 2026-10-24 UTC
Status: PREDICTION FROZEN BEFORE TEST IMPLEMENTATION.
Parent: PR #258 exact HEAD `2cf7c3915cd618b9a72a5dc26bdd15a25cb75230` (revision 24, v0.30.0 released unchanged). Independent adjacent lanes: O20 PR #370 demonstrates a static CRC-repaired SHA-stale archive can pass ordinary extraction; O21 PR #373 measures same-Reader `verify(); extractall()` only on immutable sources. O19 PR #367 attacks temporary destination inodes, not the source-lifetime assumption here.

## Primary question

Does successful `CMPCT.verify()` bind subsequent `extractall()` on the **same open Reader instance** to exactly the bytes it verified, if another writer updates the **same source inode** in between while keeping CRC32 correct and the index/physical SHA256 commitments unchanged?

## Mechanism and prospective predictions

The Python Reader memory-maps its source. `verify()` reads a blob and checks its physical SHA, but `_blob()` caches only decoded objects <=2 MiB. Therefore a later extract may consume a newly changed direct RAW blob larger than 2 MiB after the earlier successful strong verify. A small S_PACK should still be served from the previously verified immutable decoded bytes. The noncached RAW result is a **source-identity contract gap**, not an algorithmic SHA collision.

1. In both immutable controls, fresh installed Reader `verify(); extractall()` publishes exact original contents and matches independently computed SHA256.
2. For a 4 MiB direct RAW, mutate exactly its physical CRC32 field and payload on the same inode **after successful verify and before extractall**; leave physical SHA256 and authenticated index/footer unchanged. After mutation, ordinary `extractall()` on the same Reader is predicted to publish the modified bytes, despite the previous successful verify. Fresh Reader `verify()` must reject with explicit SHA256 identity failure; normal CRC32 must accept the repaired bytes. No claimed external signature.
3. For a 128-byte S_PACK, use the same protocol. The preverified same Reader is predicted to publish original cached content (cache is a protective but representation-dependent accident), while a fresh Reader `verify()` rejects CRC-repaired SHA-inconsistent physical PACK bytes. This PACK arm is a discriminating control, not a promise that caching will remain an API contract.
4. Size, `st_dev`, and `st_ino` must be unchanged across mutation; original/mutant archive images must share identical index, on-disk physical hash and file size. Mutation is deliberately applied **after** verification with no concurrent read while writing; this removes scheduling flakiness while exercising the lifetime boundary.
5. An already-mutated archive must fail explicit `verify()` through the correct physical SHA cause, not a parser, CRC, I/O or format error. This confirms the mutation is genuinely invisible to the cheaper CRC path, not to the stronger hash.

## Strong simpler control

The simple O21 policy (`verify(); extractall()` with a single open Reader) is the baseline. No new extractor, lock, source snapshot or cryptographic signature will be implemented until the possibility and shape of the actual defect are established. Reading the source through an isolated immutable copy would be a stronger policy but exports complete archive I/O/storage costs. A changed pathname by atomic rename is an inferior falsifier: an open fd correctly stays on the old inode; this court explicitly changes the same inode.

## Falsification and boundaries

The core proposed unsafe-publication claim is falsified if direct RAW extraction fails closed or publishes the original verified bytes, provided the same-inode CRC-repaired mutation genuinely occurred and post-mutation ordinary fresh `read()` returns mutant bytes. If fresh Reader cannot open/read the changed source under ordinary CRC semantics, the fixture is invalid, not a successful security result. If the PACK arm does not preserve cached original bytes, report that contradiction rather than tuning the test.

Only one immutable source and two exact synthetic structures; no proof of exploitability under permission separation, concurrent publication safety, network sources, portability, complete tree semantics, performance or release. The internal SHA256 commitment is not externally authenticated provenance. Any demonstrated gap narrows the O21 policy trust model; it does not automatically require default extraction to change.

## Custody, evidence and action

Pin the unchanged source file SHA for `src/cmpct/reader.py` to PR #258; reuse the immutable independent r24 physical fixture in `benchmarks/v031_pack_physical_sha_court.py` (Git blob `2383bf9a8f7ce8a9a01028ccf1072169897df3f1`). New script and GitHub Actions workflow must be added only after this preregistration commit. Verify via installed package on an Ubuntu runner with actual controlled same-inode mutation; retain raw JSON, SHA, source SHA, pre/post file stat and all negative controls even on an adverse result. No parser/Writer/Builder/format/release change or product credit. If valid, hand off the result to O21/O20 owners, and compare isolation/snapshot options only after a prospective whole-system cost model.

One decision is sufficient: **`verify(); extractall()` is/is not an authenticated snapshot under this source mutation model**. Do not repeat mechanism variants after a decisive result.
