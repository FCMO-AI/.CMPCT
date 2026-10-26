# J24F03 result — RAW mmap hash/write time-of-check/time-of-use source mutation

Date: 2026-10-26
Classification: **NEGATIVE PRODUCT INTEGRITY SCIENCE, HOSTED AUTHENTIC READER, NO SHIPPING SOURCE CHANGE**
Decision: **VULNERABILITY_REPRODUCED on Ubuntu 24.04 + macOS 14 for independent RAW S_CHUNKS and RAW S_CDC wire archives.**

## Preregistered authority and provenance

- Canonical `FCMO-AI/.CMPCT`, released **v0.30.0**, format revision **24**. Original development `agent/v031-development@4545d7d5b2a0b712b4b00f5a9c291d4a3a9e169b`.
- **Unchanged installed Reader Git blob:** `e716233403dabd0966863c45635e18fa5ac6afb8`. Workflow checks the checkout blob and the Python instrument independently re-hashes the installed outside-checkout reader source.
- **Prospective preregistration:** commit `438a126690f35575eff9692d8f9066148fec168f`, before instrument implementation commit `5cce02c5d2ac0f3182f12e12716e013cb0f8701b`.
- **Result-bearing exact PR HEAD:** `f90a346291d72849edacf92ebb0dbd355a72e863`.
- **Hosted run:** [GitHub Actions 40378364221](https://github.com/FCMO-AI/.CMPCT/actions/runs/40378364221): **2/2 jobs SUCCESS**, source-exact installed Reader; **4/4 adversarial trials reproduced**.
- **Original structured receipt artifacts:** Linux `12677780175`, macOS `12677610208`. Logs contain exact original and foreign hashes, processes, device/inode source identity and platform-specific results.

## Direct observations

The instrument **handwrites** format-r24 header, complete authenticated MessagePack indexes, 3 distinct RAW physical records with CRC32+SHA-256, a duplicate tail index and real commit footer; package codec only supplies Zstd encoding for the index. It never invokes CMPCT Builder. Each variant is independently opened by the installed Reader. Baseline `CMPCT.read` and `CMPCT.verify()` return the expected content; baseline ordinary extraction is exact.

The two storage maps encode the same 6,915 logical bytes:
- `S_CHUNKS`: `raw-fixed.bin`, complete archive **7,567 B**.
- `S_CDC`: `raw-cdc.bin`, complete archive **7,587 B**.

The original logical SHA-256 is `9852bedfc0ee06a17cebec7df6ef1a29dac199e2af507c6cfbfa39a536a12142`.

At the genuine first `os.write` from `_extract_chunked_verified`, AFTER its `digest.update(b)`, the instrument synchronizes a **different operating-system process** which rewrites ONLY the underlying source archive's first physical RAW payload using `pwrite` and `fsync`. No output temp or destination pathname is modified by that actor. The verified source mmap view now exposes altered bytes before the original Reader writes those same bytes to its private stage. The unchanged Reader then returns normally and publishes the altered output.

| Hosted host | Logical representation | Reader result | Published length | Published SHA |
|---|---|---|---:|---|
| Ubuntu 24.04 | RAW S_CHUNKS | **SUCCESS with wrong bytes** | 6,915 | `0d6feb2ec150cb7bda5eb97873de73e16879e5a128ea4573632e9918444668a5` |
| Ubuntu 24.04 | RAW S_CDC | **SUCCESS with wrong bytes** | 6,915 | same foreign SHA |
| macOS 14 | RAW S_CHUNKS | **SUCCESS with wrong bytes** | 6,915 | same foreign SHA |
| macOS 14 | RAW S_CDC | **SUCCESS with wrong bytes** | 6,915 | same foreign SHA |

All four reported `reader_exception=null`, an independently observed foreign published SHA, source original vs mutated SHA **different**, and source file inode/device/size **unchanged**. Original unmutated ordinary extraction control remained exact for each case. Child PIDs were independent (Ubuntu UID 1001, macOS UID 501). The mutated first RAW chunk SHA was `27a4a1c1babb3f961ed42028b1d6668118c69508492e4eac51da8985eb5cb18f`, while the chunk previously included in the Reader's running digest had SHA `9ef9ecca12780dd4bfd3ba1ab661692c12e876f3baa9fc8155442aa5599ae006`.

**Crucial distinction from J24F02 PR #527:** J24F03's archive/source **is changed intentionally by an actor with archive write permission**. J24F02's source archive was preserved and its *stage pathname* was swapped after SHA. These are separate trust boundaries, and fixing one does not necessarily fix the other.

## Causal mechanism and limits

`raw_direct` skips per-blob copying/CRC while relying on stronger whole-file SHA. It streams borrowed mmap memoryviews and performs:

1. `digest.update(b)` on the mapped source bytes;
2. later `os.write(stage_fd, b)` on what can now be **different** mapped source bytes;
3. final `digest.digest() == authenticated_whole_file_SHA`.

The external source-file write changes step (2), not the already-completed digest state in step (1). The mechanism is **hash-to-write mutable-buffer custody**, rather than a cryptographic collision, parser bug, or change of output namespace entry.

The detached immutable snapshot micro-control confirms a bounded immutable `bytes` buffer does not retroactively mutate, but **is not a tested product repair**. A prospective repair should ensure the *same immutable chunk bytes* feed both running SHA and stage write, or enforce an explicit immutable source contract; it must preserve bounded RSS, corruption handling, stage-output atomicity and all ordinary Reader semantics. Holding the stage inode/name separately remains a distinct unsolved issue (#528).

## Strongest negative / scope

The attack deliberately requires an **additional actor with write permission to the archive source inode** while the Reader is extracting and a deterministic first-write rendezvous. It does **not** prove unauthenticated remote exploitation, a naturally likely race, a broken archive on an immutable filesystem, Windows/Android behavior, or full-tree publication safety. The source archive is physically modified and no longer meets its original strong CRC/SHA records after attack. Ordinary verified reads on immutable source remain valid. The instrument's bounded-copy control is detached, and no repair, throughput or RSS measurements were performed. A platform/environment where concurrent source writes are disallowed would not admit this adversary.

## Science / Discovery decision and counterfactual

Primary question: can physical bytes change between verification digest intake and committed stage write even if the Reader never substitutes the stage inode? **YES on both POSIX hosts and both RAW-map representations.** This narrows the integrity frontier into **two independent ownership gaps**: mutable source/hash-to-write (this PR) and mutable output-name/publish-after-SHA (#527).

Cheapest prospective discriminator in retrospect: micro `mmap.ACCESS_READ` read-after-external-`pwrite` with separate SHA+write; it demonstrates the coherence mechanism but cannot replace this actual Reader court. The current episode earned one source-lifetime-specific engineering lesson: strong full-file hash can only authenticate **the bytes actually sent to the target**, not earlier mutable views. No evidence-backed broad Discovery Engine policy amendment was earned. `docs/discovery/STATE.json` remains under separate owner PR #440; no shared changes.

## Promotion / next target

**Product change: 0. Format change: 0. Release credit: 0. Benchmark credit: 0.** Next owner should first implement/test bounded immutable-byte capture on RAW extraction while preserving stage SHA/CRC and failure behavior, then separately address J24F02 output-stage namespace substitution; test same two native-host hostile courts on the *integrated installed source*. The stronger contract would also address source mutation **during** a chunk copy by hashing and writing the captured bytes, with indexed full logical SHA as the final arbiter. Any new copy tax on RSS/CPU/I/O requires real measurement; do not claim a free fix.

Other source races—same-inode archive truncation SIGBUS #460 and Deflate stream export #286—remain separate; this result should be handed to their respective owners for shared source-custody lessons rather than duplicate implementations.
