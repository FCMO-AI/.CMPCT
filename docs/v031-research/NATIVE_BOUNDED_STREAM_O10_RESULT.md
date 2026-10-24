# O10 / O10b — Native C bounded streaming versus eager output retention

Date: 2026-10-24  
Status: **SCOPED POSITIVE — HOSTED EVIDENCE CLIENT, NOT A RELEASED PRODUCT**  
Parent/source: PR #327 `030bd50aff682592f67eba1dc5376b83bfe83fae`, with **zero product-code changes** (confirmed GitHub compare). Public v0.30.0 and r24 remain unchanged.  
Frozen hypothesis: `NATIVE_BOUNDED_STREAM_O10_PREREG.md`, commit `f1264f7545955755514c57ec9f6c9755b7c6ec1d`, preceding implementation.  
Original O10 full client/test commit `87f43842672e8750b1a0bf591e60274c5d050019`; corrected O10b executable-source and workflow commit **`4bc0f7b48fda08ab418c85198b684c65d6bbd52f`**.

## Verification provenance
- Initial [O10 run 40074088123](https://github.com/FCMO-AI/.CMPCT/actions/runs/40074088123): SUCCESS, artifact ID `12552009170`, ZIP SHA-256 `7ba7cae67b737229b8baca69b9f7bded1929b9f9ec30cefb8743cdac32e189df`. All 48 outputs exact and symlink canary PASS. **Original peak RSS INVALID** due to fork/exec-inherited parent high-water mark.
- Corrected [O10b run 40074631510](https://github.com/FCMO-AI/.CMPCT/actions/runs/40074631510): **SUCCESS** exact head `4bc0f7b48fda08ab418c85198b684c65d6bbd52f`, artifact ID `12553070222`, ZIP digest `sha256:ba52dd39b27c496e016641a1ec6d05e61bc7145d9106457f81c9f1298318b4c1`. Includes original source SHA comparisons every reconstruction; 4 cohorts × 12 full independent C subprocesses = **48/48 byte-exact output trees**; symlink external canary PASS. Six alternating observations per mode/cohort, no discarded trials.
- O10b **measurement-only** `tests/native_pack_process_rss_o10.h` forced equally into baseline and candidate C clients, obtains Linux process-local `/proc/self/status:VmHWM` after first confirming `getrusage(RUSAGE_SELF).ru_maxrss` can inherit Python benchmark parent memory across fork+exec. Initial falsified result retained in `NATIVE_BOUNDED_STREAM_O10_RSS_FALSE_BASELINE.md`.

## Direct same-runner O10b measurements

Medians with process startup, ABI opening, extraction and output file writes included, **unchanged O7 serial** versus a **new test-only 64KiB-streaming POSIX C consumer**:

| Cohort | Files / logical bytes | Eager RSS KiB | Stream RSS KiB | Eager wall ms | Stream wall ms | Eager CPU ms | Stream CPU ms |
|---|---:|---:|---:|---:|---:|---:|---:|
| Independent RAW 16 | 16 / 4,194,304 | 6,734 | **2,560** | 3.1605 | **1.8347** | 3.0880 | **1.7530** |
| Independent RAW 64 | 64 / 16,777,216 | 19,280 | **2,674** | 12.2406 | **5.9331** | 12.1025 | **5.7985** |
| Independent RAW 128 | 128 / 33,554,432 | 36,020 | **2,754** | 23.7446 | **11.4145** | 23.6280 | **11.3060** |
| Structured PACK 512 | 512 / 393,216 | 3,560 | 3,540 | 131.4895 | 117.0544 | 131.3710 | 116.9155 |

For 32MiB output, Linux process-local peak RSS decreases **33,266 KiB (~92.4%)**, about **13.1×** lower. Complete C test-client wall decreases ~**2.08×**. For the 512 shared Zstd-PACK corpus, RSS is effectively tied; this result does **not** supersede the stronger grouped batch O7 performance control (~9.5× on its favorable corpus), because both O10 alternatives use independent serial reads and repeat compressed PACK decoding.

Observed O10b RSS sample ranges (eager / stream in KiB): raw16 6,712–6,832 / 2,544–2,648; raw64 19,256–19,376 / 2,620–2,728; raw128 35,992–36,108 / 2,712–2,808; structured512 3,504–3,568 / 3,500–3,628. No overlap for RAW; considerable overlap for shared Zstd corpus. Raw per-trial medians, wall, CPU, RSS and SHA are retained in the GitHub artifact.

## Decision, falsifiability, strongest negative
**Question:** Does an independent public-native ABI test client with one fixed range buffer avoid the all-members heap amplification of the inherited O7 evidence client, without changing archive bytes or publishing incorrect source data?

**Disposition:** **SCIENTIFIC POSITIVE ON RAW OUTPUT MEMORY, PRODUCT UNPROVEN.** Cheap control confirmed a real *test-consumer* memory owner. Does not prove a shipping memory-safe extractor. Both candidates use precisely the same Reader and source archive. A faster streaming client on RAW does not imply the Reader's ABI suddenly authenticates every logical file: its RAW selective range implementation only checks physical framing and returns requested bytes without complete on-call SHA-256; the harness's independent original-file SHA verifier supplies the separate output equality court. Cross-call mutation or atomicity is unproven.

Adversarial symlink control: preexisting destination leaf symlink causes nonzero exit, target canary unchanged. However this does not prove symlink-safe arbitrary nested extraction, existing destination race defense, whole-tree atomic publication, hardlinks/xattrs/ACL/sparse semantics, crash consistency, Windows/SMB, or a global native library memory budget. The stream client leaves earlier files published if a later one fails; it is **not** a substitute for a secure product extractor.

**Bounded implementation note:** The new source checks a 512MiB aggregate output limit and 128MiB per entry, and uses a 64KiB range buffer. These are test policy caps, not CMPCT format limits or a shipping guarantee.

## Counterfactual lesson and future target
Test the RSS accounting source **before** investing in a full benchmark. Two unrelated C clients reporting identical RSS after heavy Python parent allocation should trigger a cheap fork+exec highwater control; process-local `VmHWM` distinguishes actual children. The strongest next engineering route is an authenticated, failure-atomic, globally budgeted, descriptor-confined native extraction engine preserving specialized Zstd owner batching and efficient RAW range access; instrument filesystem semantic completeness, per-file SHA, global RSS, I/O, cold startup, portable behavior and recovery. Unmodified O7 remains only an eager serial strong comparator, not a shipping extractor.

No benchmark threshold, frozen experiment, Discovery Engine policy, product source, released archive bytes, format or release advancement was changed. The full release parity gate's aggregate SUCCESS on this research PR had its **substantive performance job SKIPPED**; it is no release-performance approval. CI status must be reported against its exact source head; this newly committed result document is a documentation-only descendant and must not inherit old exact-head workflow success claims.
