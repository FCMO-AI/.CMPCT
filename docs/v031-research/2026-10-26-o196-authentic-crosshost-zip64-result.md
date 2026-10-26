# O196 — Authentic Linux-built 4 GiB sparse r24 → ZIP64 on three hosts

Date: 2026-10-26 UTC. Status: **SCIENTIFIC POSITIVE, PRODUCT PROMOTION NOT EARNED**.
Owner: PR #526; O193 ZIP64 product owner: PR #521. Frozen preregistration before test: `526e756e0d23e2076fb778cf4bf06cec7e76776a`.
No released CMPCT code, on-disk format, inherited test, benchmark or release rule was changed.

## Original scientific question and sources

Parent O195 #524 demonstrated authentic 4 GiB S_SPARSE → ZIP64 on Ubuntu only. O193 #521's 3-host scientific CI exercised streaming in a small-member branch, not genuine 4 GiB. O196 asks if **one Linux-built true 4 GiB archive** can be transported byte-identically to installed O193 Readers on Linux/macOS/Windows and exported into interoperable ZIP64, with full decode/hash/CRC correctness and bounded per-request reads.

Scientific original exact-head candidate `ed1d233b65502c3c7615d7118ad7ceee6f78e4c6` was successfully tested at [run 40362046472](https://github.com/FCMO-AI/.CMPCT/actions/runs/40362046472). Source-identical script with stronger independently parsed ZIP64 physical local header and repaired Win64 RSS measurement: `90e7346296f8c54fc6f07ce46a60f43d04b4c482`, [run 40362795475](https://github.com/FCMO-AI/.CMPCT/actions/runs/40362795475). Both runs yielded **4/4 jobs SUCCESS** (one producer and three consumers). All result claims below refer to the latter stronger source HEAD; do not transfer outcomes across commits by implication.

## Independent downloaded artifact audit — source bound

Three separate original result JSON artifacts and producer receipt were downloaded and compared with a separately authored Python auditor, not just the GitHub green job labels.

| Datum | Observed |
| --- | --- |
| Logical source input | 4,294,967,296 bytes (exact 4 GiB) |
| Linux physical allocation | 16,777,216 bytes |
| Host physical and r24 index extents | 4,096 each |
| Source representation | genuine `S_SPARSE`, Builder-generated |
| CMPCT stored archive | 533,466 bytes |
| Original archive SHA-256 | `6c2777f4b4489af547da1df8f2fb474a56ae9c1d41fb76664ebe3b5d54196867` |
| Full logical source SHA-256 | `aa8eab1213de329104d81b6ea925c8455e55ccdd47b0457fa6abe9c1f65cf1c3` |
| Original archive transfer | SHA-identical on all three hosts |
| Reader identity | same installed-source normalized SHA on all hosts |
| Real ZIP size | 4,415,465 bytes on all hosts |
| Real ZIP SHA-256 | `7ce189d00534541413941d7cebf0fec9899a71c5e70839aac4b90da9656abbd9` on all hosts |
| ZIP member full decoded SHA | exactly source logical SHA, all hosts |
| ZIP member CRC32 | identical, independently checked by stdlib reader on EOF |
| ZIP64 local header independently parsed | all hosts: ZIP v4.5, 32-bit length sentinels, 64-bit logical size 4,294,967,296 and compressed 4,415,307 |
| Bounded reader requests | exactly 4,096 × 1,048,576 bytes on every host |
| Format/release modification | NONE |

### Platform results (one noisy observational repetition; not a fair between-host benchmark)

| Host | ZIP export wall | Export CPU | Full independent ZIP readback wall | Observed process peak RSS |
| --- | ---: | ---: | ---: | ---: |
| Ubuntu 24.04 | 39.371 s | 39.365 s | 12.740 s | 69,566,464 B |
| macOS 14 | 26.228 s | 25.766 s | 4.633 s | 131,579,904 B |
| Windows 2022 | 24.305 s | 24.297 s | 15.361 s | 67,293,184 B |

The original run independently reached full ZIP/SHA PASS with Ubuntu 10.437 s, macOS 26.147 s and Windows 33.565 s. **The large variation across machines/runs disallows a clean performance comparison, improvement claim or extrapolated bound.** Windows original RSS was unavailable because the ctypes call used the incorrect Win64 API signature; corrected exact-head RSS now has a native PeakWorkingSetSize receipt. Some readers may internally decode larger physical frames even when `read_range` requests are <=1 MiB, so these figures do not establish a universal memory ceiling.

## Scientific decision / falsification

**Scoped positive:** the same physical archived CMPCT bytes were consumed by 3 independently installed O193 Readers and exported into identical ZIP64 bytes; full authentic 4 GiB payload SHA and CRC were verified in each receiver; an independent `struct` parser checked the ZIP64 physical local header rather than trusting the writer's own ZIP index parser. No product implementation or portability contract was altered.

**Still unproven:** external 7-Zip/Info-ZIP interoperability (Python writer/reader share code); malicious index handling; giant unsplittable compressed decode units; concurrent source/output change, transaction/crash durability; broad real-world sparse distributions; full resource bounds; cross-OS timing competitiveness; and release conformance/fingerprint-bound benchmarks. One synthetic sparse source must not be generalized to arbitrary data. Same logical input but source mtime changes between independent producer runs may change archive/ZIP SHA without a product regression.

**Counterfactual:** O193's small synthetic branch court and O195's one-host 4GiB court could not certify this cross-host statement, so transporting a single authentic >4GiB archive was necessary decision-changing evidence. One host-specific failure would have falsified the scoped claim without allowing a smaller workload or relaxed checksum. A compact independent ZIP64 local-header parser was an affordable additional falsifier. No discovery-policy change earned.

**Coordination:** existing O193 remains sole product owner; O195 indexing stays unpromoted after its <5% end-to-end gain. The next highest-value action is an external ZIP consumer (7-Zip/Info-ZIP) on the already created ZIP64 bytes, followed by actual host-specific adversarial/resilience gates; no third Reader implementation or new version from this investigation.

## Provenance

Run 1: [40362046472](https://github.com/FCMO-AI/.CMPCT/actions/runs/40362046472) original source `ed1d233...` (4/4 SUCCESS).

Run 2: [40362795475](https://github.com/FCMO-AI/.CMPCT/actions/runs/40362795475), stronger source `90e7346296f8c54fc6f07ce46a60f43d04b4c482` (4/4 SUCCESS). Raw result ZIP artifacts: producer `12669700755`, Ubuntu `12669451401`, macOS `12669725946`, Windows `12668428842`. Independently audited result JSON SHA-256: `ad316251e8a069b11206c014d6c49f148da5558ec48cf628b4e36be6b07dcc88` (local audit package, not a replacement for GitHub originals).

## Product/release verdict

Research evidence: **PASS**. Product semantic claim: **only the tested sparse 4GiB profile**. Compression/competitor win: **NOT CLAIMED** (physical sparse topology semantics differ from ZIP). Generic CI/release: separate gates. No canonical merge, no numeric release.
