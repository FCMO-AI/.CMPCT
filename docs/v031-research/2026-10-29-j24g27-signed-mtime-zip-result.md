# J24G27 result — published r24 Reader rejects valid pre-1970 ZIP export on Windows

**Date: 2026-10-29 UTC.** **Decision: H1 PASS; H2 CONFIRMED on Windows; H3 PASS on successful ZIP outputs.** Scientific/correctness evidence, not a product fix or release milestone.

## Source, preregistration and exact hosted execution

- Published unchanged CMPCT `main@80c358f8824ec1b20d349c92ed94c898090969b0`, v0.30.0/r24. Reader Git blob `e716233403dabd0966863c45635e18fa5ac6afb8`, Builder blob `663ef0922992b1fbb8f19e6eea88d55c10a56044`.
- Preregistered in commit `84cd8c77870e47eb9f3d570368d7677fb4196990` **before** implementing or executing the research workflow.
- Result-bearing [Actions #40796399439](https://github.com/FCMO-AI/.CMPCT/actions/runs/40796399439): research source at `101355b27275fd301fa98ef5b0c48502ed0fc19c`; first-party generator and all three fixed-wire host jobs SUCCESS. Successful *court* means a result was classified correctly, **not** that Windows ZIP export succeeded.
- Earlier run [#40795883634](https://github.com/FCMO-AI/.CMPCT/actions/runs/40795883634) failed Windows pre-test *source-identity setup*, because Git-for-Windows converted LF to CRLF during checkout/install. The instrument was corrected to accept only this reversible, proven newline transform; any other changed source bytes are rejected. Keep this infrastructure failure as evidence, not a product negative.

## Fixed authentic revision-24 physical inputs

Identical first-party Builder-created physical archives from one Linux generation were downloaded to every host. No host regenerated the data.

| Entry mtime_ns | Archive SHA-256 | Bytes | Logical content SHA-256 |
|---|---|---:|---|
| -1000000000 (1969-12-31 23:59:59 UTC) | `09a6566a6cf54a2876a2b42205722b6887092b6c472707ece8f7f4aad173c0bd` | 966 | `00d85eb9b08a9445667353a18dccbeda7554e05a3e3f42df238edeaf6978d2b5` |
| 1577880000000000000 (2020-01-01 12:00 UTC) | `9a3db9b49f2079252b07e891b3946f6d8cbf40d0c1104a607dc95d7add88c730` | 978 | `00d85eb9b08a9445667353a18dccbeda7554e05a3e3f42df238edeaf6978d2b5` |

An independent auditor (no CMPCT source imports) used system libzstd, MessagePack, physical little-endian parsing, CRC32, primary/tail SHA256 and payload SHA256: **81 checks PASS, 8/8 mutated physical files rejected**. Both archives share an identical physical compressed blob record; the signed timestamp differs in their authenticated indexes. This is a bounded physical format audit, not an independent complete Reader.

## Direct results on the identical physical inputs (two fresh processes per host)

| Source-exact published Reader | Ubuntu 24.04 | macOS 14 | Windows 2022 |
|---|---|---|---|
| Negative mtime index preserved | PASS ×2 | PASS ×2 | PASS ×2 |
| Negative mtime `read()` / `verify()` | PASS ×2 | PASS ×2 | PASS ×2 |
| Negative mtime `export_zip()` | **SUCCESS ×2** | **SUCCESS ×2** | **OSError [Errno 22] ×2** |
| Ordinary 2020 mtime `read()` / `verify()` / `export_zip()` | PASS ×2 | PASS ×2 | PASS ×2 |
| `time.localtime(-1)` platform control | 1969 returned | 1969 returned | **OSError [Errno 22]** |

Both Windows traceback receipts identify `_zip_dos_time` → `time.localtime` as the failure site. Successful ZIP outputs were individually decoded via Python stdlib `zipfile`, member bytes verified, and DOS year checked. On the pinned UTC POSIX runners the pre-1970 output has ZIP DOS date 1980-12-31 23:59:58: released code clamps **year only**, retaining the old month/day. This is not an assertion of cross-timezone ZIP bit identity.

Original [Actions #40796399439](https://github.com/FCMO-AI/.CMPCT/actions/runs/40796399439) artifact IDs: source physical inputs `12863089140`; Ubuntu `12863848133`; macOS `12863972635`; Windows `12864047507`. Independently recomputed receipt classification, fixed-source identity, all manifest SHA256s, cross-run decisions and successful ZIP digests: **206 checks PASS and 5/5 falsified receipt copies rejected**. Filesystem and Windows runtime behavior itself was observed by the hosted execution, not independently re-executed by the receipt auditor.

## Causal mechanism, strongest limitations, owner and next action

The exact released Reader calls `time.localtime(mtime_ns/1_000_000_000 if mtime_ns else 315532800)` **before** attempting to clamp the year to the ZIP DOS date interval. [Microsoft documents that Windows `localtime` refuses pre-1970](https://learn.microsoft.com/en-us/cpp/c-runtime-library/reference/localtime-localtime32-localtime64?view=msvc-170); [Python documents platform C-runtime time boundaries](https://docs.python.org/3.11/library/time.html). A valid physical signed negative-mtime r24 archive thus passes ordinary content reconstruction and strong verification but fails this legacy ZIP endpoint on Windows.

The same `_zip_dos_time` source is inherited by existing atomic-ZIP owner [PR #492](https://github.com/FCMO-AI/.CMPCT/pull/492) (Reader blob `496e70bdc06ddc17aa90e4fc0e9f10a6bc5c5332`). Reconcile with that existing owner rather than opening a duplicate ZIP writer fix. A future candidate must choose explicit DOS-clamp compatibility, preserve inherited Deflate/CRC/ZIP64/source/destination/atomic-publication semantics, and prove cross-host exact-content acceptance and same-input performance parity.

No product implementation, source/format change, compression win, create/extract throughput, RSS or release credit. Only this signed-time cross-host failure and ordinary control are proven; general timestamp domain/other ZIP readers are not fully explored. `docs/discovery/STATE.json` and its owner #574, release locks, benchmark comparators, policy and historical receipts remain unchanged.

**Counterfactual lesson:** a platform C-runtime lower-bound check of the existing `localtime` call could prospectively predict the failure family before a costly full experiment. The authentic physical same-input court provides product truth, while a lone platform-time microprobe could not. One episode does not earn a discovery-policy modification.
