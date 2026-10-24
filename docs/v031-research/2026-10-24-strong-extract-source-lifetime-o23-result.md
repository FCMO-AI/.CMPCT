# O23/O23b — strong-extraction source lifetime and cache boundary

Date: 2026-10-24 UTC
Status: **HOSTED SCIENTIFIC FALSIFIER POSITIVE — PRODUCT SOURCE UNCHANGED — NO RELEASE CREDIT**

## Frozen question and exact source

Question: does calling `verify(); extractall()` sequentially on one open CMPCT Reader establish that every published byte matches the archive's **previously verified** physical SHA commitment when a permitted writer modifies the archive inode between the calls?

Released product floor v0.30.0 / revision 24; research owner #258 exact parent `2cf7c3915cd618b9a72a5dc26bdd15a25cb75230`. Reader source Git blob `60f52328467ca509bb410abe6a34810c50917cb5`; independently constructed revision-24 physical-record fixture generator blob `2383bf9a8f7ce8a9a01028ccf1072169897df3f1`.

Original O23 preregistration `58cc0bbbcdac901998bb08c6f1a2855b8bca40ac` preceded code implementation `6f712e2efa4e446ca867e7a734943f1b5631ce7c`. Follow-up O23b preregistration `14de362dfd8e2577240836825f265a88693ff2ac` preceded cross-factor test implementation `54e778f44b2950f334324f06d44a9a32b20a8bb4`.

## Independently hosted evidence

**Original O23:** [Actions run 40125737167](https://github.com/FCMO-AI/.CMPCT/actions/runs/40125737167), job `120966621877`, source `962a86ef938745f4a4da6e42b96319d101f138e8`, artifact `12572856738`; workflow **SUCCESS**. Runtime output:
- 4 MiB direct RAW, cached owner indices `[]`: subsequent **same-Reader extraction published MUTATED_UNVERIFIED** physical bytes.
- 128 B micro-PACK, cached owner indices `[0]`: subsequent **same-Reader extraction published ORIGINAL_VERIFIED** physical bytes.

**Crossed O23b:** [Actions run 40126057416](https://github.com/FCMO-AI/.CMPCT/actions/runs/40126057416), job `120967596123`, source `7090a3fd33b008b440bc4ac4388010d8c48dce08`, artifact `12573491481`; workflow **SUCCESS**. Registered result `CACHE_SIZE_CROSSED_CAUSAL_PREDICTION_CONFIRMED`:

| Exact independently constructed r24 owner | 128 B (decoded owner in Reader cache) | 4 MiB (decoded owner not cached) |
|---|---|---|
| Direct RAW | **ORIGINAL_VERIFIED**, cache `[0]` | **MUTATED_UNVERIFIED**, cache `[]` |
| Shared S_PACK | **ORIGINAL_VERIFIED**, cache `[0]` | **MUTATED_UNVERIFIED**, cache `[]` |

**Decision:** the **decoded-owner cache size** is the stronger causal discriminator than storage kind for these four exact fixtures. The active Reader's `_blob()` caches decoded objects only when <=2 MiB, and after a verified source inode is rewritten, larger objects are decoded again from the modified memory mapping. Caching is contingent implementation behavior, **not a security or transaction guarantee**. The generated 4-MiB S_PACK is a valid independent revision-24 Reader fixture; no claim is made that canonical Builder would admit a pack of that size.

## Independent gates applied in each cell

- Fresh source and mutated archive were separately checked by whole-image SHA; physical record bytes change, archive total byte length and unchanged authenticated index/physical SHA do not.
- A successful `verify()` precedes the source mutation in the very same Reader instance.
- Controlled `pwrite()` changes the same file inode while retaining `st_dev`, `st_ino` and file size. CRC32 is repaired, physical SHA256 remains its original committed value; the change is within the physical record.
- Independent fresh Reader ordinary CRC-tier `read()` returns exactly the mutated logical bytes, proving the cheaper reader path accepts the altered payload.
- Independent fresh Reader `verify()` rejects with the **specific** physical-SHA failure, not generic I/O, format or CRC failure.
- Immutable-source controls successfully `verify(); extractall()` and reconstruct the original bytes exactly.
- Published filesystem bytes are independently compared to original and one-byte-mutated logical SHA256. An unexpected result cannot be silently classified as success.
- Both runs preserve source SHAs, JSON observations, runtime logs, source lineages and artifacts under the exact GitHub run identities above.

## Strongest negative / scope of claim

The **simple O21 same-handle policy is not an authenticated source snapshot under a permitted in-place source-inode modification**. O21's measured immutable-source runtime ratios remain valid within its original contract; they do **not** establish lifetime integrity in mutable-source scenarios. Ordinary `extractall()` deliberately offers a cheaper CRC tier than `verify()`, as O20 showed. This finding does not prove a concurrency exploit under privilege separation, system-level integrity forgery, arbitrary archive handling, Windows/macOS behavior, or multi-entry atomic publication. Internal SHA commitments are not signatures of an external publisher. No complete strong extractor was built; source isolation, recomputation and publication costs remain unmeasured.

## Counterfactual, next frontier and integration ownership

The earlier observable most valuable for the original O23 study was the `_blob()` 2 MiB cache condition. The first PACK-vs-RAW contrast was causally confounded with owner size; crossed O23b exposed that ambiguity prospectively, predicted both omitted cells, then confirmed it without changing thresholds. A source-immutable contract or an actual source snapshot is a **different guarantee** from a one-time `verify()` call. Any proposed remedy must name its physical byte ownership/protection boundary from verification to publication, test adversarial same-inode writes and destination mutation, and fully charge snapshot I/O, CPU, RSS, storage, read amplification and recovery versus O21.

The immediate economical choice is to **document/enforce trusted immutable-source preconditions** for the simple `verify(); extractall()` policy or design one bounded, source-owning, verify-to-publish operation if the product explicitly requires mutation resistance. Do not claim that caching, an `O_TMPFILE` name policy, a postwrite SHA read-back, or merely retaining the same Reader object closes this gap.

No product changes, no benchmark changes, no format/release changes, no policy self-modification. Repository shared `docs/discovery/STATE.json` is being reconciled by PR #240; do not duplicate ownership.
