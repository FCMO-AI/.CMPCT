# O18 — Bounded public-C staged CDC publication: exact-head hosted result

**Date:** 2026-10-24 UTC. **Outcome:** `CDC_STAGED_LOGICAL_SHA_BARRIER_PASS` for the specified Linux/private-flat-directory research court. **NOT merged, shipped or release-approved.** CMPCT released v0.30.0/r24 and unmerged v0.31 are unchanged.

## Authority, frozen prediction and source identity
- Source parent: PR [#359](https://github.com/FCMO-AI/.CMPCT/pull/359) at `c2b61c5290382c3df5eb92c6381b83b1ba0e02d0`; inherited Rust and C header Git blobs `ce12c76d9f4901af1e2b95d5d88883ffb2a72d2e` and `dc6b689febd383618abe31d4d2ea3ccda7fb1d3b` were checked in hosted CI. Their code was **not modified**.
- Preregistered research-only question at `b9432a938450fd00fcabfd804067de894a29af9c` **before** code, tests and workflow; see `NATIVE_SIGNED_INDEX_STAGE_O18_PREREG.md`.
- Actual measured source HEAD: `8afe7952c18d76ba86578c5bd5999a49f77cdbc1`.
- [Hosted O18 run 40106987456](https://github.com/FCMO-AI/.CMPCT/actions/runs/40106987456) **SUCCESS**; result-bearing artifact [12565825020](https://github.com/FCMO-AI/.CMPCT/actions/runs/40106987456/artifacts/12565825020), ZIP SHA-256 `1c60db3013098bc8d9ff72e837fb54c11bae1979d2c3cf3883fcf2214cfd1d17`. ZIP/JSON manifest independently inspected and the JSON digest matched `4b31af58e6a7ff185435b6b4438d20cde36284cbd0d1e785a5ec550bd5afdb45`.
- Hosted source Git checkout, original native source blobs, cargo fmt/test/build, strict C/OpenSSL compile and independent Python oracle were **PASS**.

## What was materially established
The research-only C client uses the existing public Reader ABI to enumerate exactly one selected regular entry, read its existing signed-index logical SHA, reconstruct in 64-KiB ranges to an `openat(O_EXCL|O_NOFOLLOW)` private-stage inode, compute SHA-256 over the bytes submitted for writing, `fsync` the stage file, and only then expose the final leaf by `linkat` without overwrite if the digest matches. It removes its stage name on return. The C consumer does not parse the on-disk index, cannot invent missing hashes, and has no archive-sized content buffer.

Two genuine independent Builder-produced revision-24 CDC corpora (different seeds/bytes) were tested:

| Corpus CDC logical bytes | Complete CMPCT stored bytes | Real source SHA-256 | C positive / final leaf | Signed-index contradiction | Direct RAW no row SHA | Existing destination symlink |
| ---: | ---: | --- | --- | --- | --- | --- |
| 1,500,000 | 1,587,526 | `d3dd342e01cc2779f21419b8fa82306e5195da747b9978c28cfa7b18e711c28b` | exit **0**, exact | exit **5**, no final/stage | exit **4**, no files | exit **6**, canary exact |
| 2,100,000 | 2,187,758 | `10fa80e43af99d6a291b1774f0d760723b653d2893ebb04b37210d247599218a` | exit **0**, exact | exit **5**, no final/stage | exit **4**, no files | exit **6**, canary exact |

**2/2 positives and 6/6 preregistered negative observations passed.** Both original source SHA-256 values equal both the reported C streamed SHA and independent SHA-256 of the final output. Exactly one leaf remains after each positive; no stage file remains. Both Builder outputs were proven genuinely `S_CDC` with the correct stored logical SHA; direct RAW controls were genuinely `S_BLOB` / `CODEC_RAW` and had no logical row SHA.

## Independent contradictory control
The Python instrument took the genuine source archive, replaced only the CDC logical row SHA with an intentionally false 32-byte digest, then independently rebuilt **both** compressed r24 indexes, their commitments and footer. The physical record region was **byte-for-byte unchanged**. The normal Python Reader independently refused full CDC reconstruction as an integrity failure. The native C 64-KiB partial-range consumer reached the **digest mismatch barrier** and refused to publish its final leaf; its error explicitly was `O18_REJECT status=5 native_rc=0` on both corpus sizes. This distinguishes whole-logical-file verification by the consumer from a native range-read error or malformed index rejection. The re-sealed index is self-committed but not externally authenticated.

Source/physical-record identities from the two cases:
- 1.5 MB: original CMPCT SHA `6272c0e6740eeae9c9b44e081b75acc02d4a37171383710936b61f7dc953475d`; contradictory archive `eec768e4bbba7e844ce436254937e7b92c1b84f3588e147984ff93730a0cfae8` (1,587,456 B vs original 1,587,526 B, physical records unchanged).
- 2.1 MB: original CMPCT SHA `61b62b3b4c127012d77fc74c738cb487a3c6938e39fe9ece38c875dffb85f9c6`; contradictory archive `140cd883d4c4a3b64a91e4bf8df3b3631dd12792dc5ac222caeb5430ef90f8d4` (2,187,690 B vs original 2,187,758 B, physical records unchanged).

## Whole-system accounting and strongest criticism
Research only: C scratch allocation **64 KiB** plus constant OpenSSL SHA state and per-operation buffers. The Rust Reader has its own memory allocations and the instrument **did not measure whole-process RSS**. Host Python subprocess wall time was reported in the raw JSON (single observations, **not** a benchmark):
- CDC 1.5 MB: positive **6.4053 ms**, deliberate SHA mismatch **5.4528 ms**, RAW rejection **1.4427 ms**, hostile-root rejection **1.4253 ms**.
- CDC 2.1 MB: positive **6.0902 ms**, deliberate SHA mismatch **6.6918 ms**, RAW rejection **1.4415 ms**, hostile-root rejection **1.2806 ms**.
These are two isolated observations, cannot support speedup/regression claims. Stored archive bytes are real Builder output sizes, not savings against a historical codec.

**Critical limitations:** stage SHA is computed over the bytes *provided to* `write_all`, not re-read from disk after fsync; without a concurrent mutation adversary this verifies the intended serialized output, not durable bit-level post-write media integrity. The stage has a predictable private basename; preflight is vulnerable to concurrent destination changes or root rebinding. No directory fsync, transactional tree rollback, crash recovery, source fd identity freeze, fully signed trust anchor, RAW or full generic filesystem, portable OS package, inode-topology composition, xattrs/ACL/uid/gid, Rust RSS ceiling or official release ABBA. A malicious party able to reseal both index copies could choose a different commitment, so *index authentication here is internal integrity, not authenticity of an external signer*. These limitations are **not** waived.

## Decision, counterfactual, continuity
**Scoped hypothesis supported:** an existing CDC logical row SHA suffices for an operation-scoped staged-before-final-name barrier in this private Linux C consumer; a contradictory self-resealed r24 index becomes a no-publication negative even though bounded partial-range calls do not individually require the full row hash. **RAW remains explicitly unsupported** where a logical row SHA does not exist. No representation, release, policy or product convergence credit. No benchmark gate adjusted.

The cheapest prospective discriminator was to inspect the Builder's stored row SHA and native range semantics, which O12 already established and O18 confirmed. No general discovery-policy lesson earns amendment on one court. `docs/discovery/STATE.json` untouched because other work owns it. Follow-up: build a separate integrated full-tree court using PR #351's inode semantics and PR #359's SHA metadata under safe descriptor-root publication, authenticate complete logical output (including signed source lifetime), and separately test mutation between validation and commit. Require an externally anchored trust model if authenticity, rather than self-contained corruption detection, is promised.

**Exact-head status:** O18 specialized court SUCCESS on `8afe795...`. The commit adding this results document is **documentation-only** relative to that measurement; do not transfer other CI/checks until its own head is evaluated. Release version v0.30.0/r24 unchanged, merge NO, release credit 0.

## Evidence-gate operational correction (not scientific credit)
The first PR engineering-evidence run `40106987357` rejected the PR metadata because the evidence heading was spelled `Prospective evidence` rather than the exact required `Evidence`. Changing the PR description followed by a rerun of the same attempt did **not** help: GitHub reran with the original pull-request event snapshot. New source HEAD `14873f032394449f84bf7a56e1ad7817df2419b5` triggered fresh evidence runs `40107391982` and `40107423702`; these correctly identified a second metadata omission: the literal `quality-ratchet` falsifiability marker was absent despite a `Quality ratchet` section. The PR description was updated to state the marker explicitly. This is **metadata correction, not experimental result or evaluator relaxation**. Only a new actual CI event with the corrected PR body can earn evidence-gate success. Historical reds remain recorded.

