# J24G98–99: immutable physical archive ownership, original-provider O0 verdict

**2026-10-31 UTC · exact evidence at research branch PR #869, no product change.**
Published canonical main remains `80c358f8824ec1b20d349c92ed94c898090969b0` (CMPCT v0.30.0, on-disk r24); the *research* base and source footer grammar have not changed. Two independently preregistered questions:
- J24G98: [preregistration](2026-10-31-j24g98-immutable-segmented-archive-prereg.md), commit `fd4f59858e8af77f72f362ecdfee400f3a8750d9`, before experiment;
- J24G99: [preregistration](2026-10-31-j24g99-rolling-tailpack-prereg.md), commit `4e2c4fcebd2934cafa2972ba4e822303199960ac`, before implementation.

## Real evidence, with provenance boundaries

Original physical inputs: four provider SHA-256-verified ZIPs from genuine Reader/Writer research #856 (4 footer archives, 16/128 members) and #853 (64 footer archives, 4096/8192 members), each originally generated on Ubuntu or Windows. **Both new mechanism courts execute on Ubuntu only; a Windows-origin archive does not turn Ubuntu execution into a Windows-host validation.**

| Court | Exact HEAD CI result and ID | Research decision | Original hosted ZIP SHA-256 |
|---|---|---|---|
| J24G98 per-footer immutable files | [Actions #41154158860](https://github.com/FCMO-AI/.CMPCT/actions/runs/41154158860) **SUCCESS**, 8 cases, 6 deliberately forged receipts rejected by separate stdlib referee | `SEGMENT_PER_FOOTER_O1_ADMISSION_FAIL` | `d02f27b6f9dd4e99ec4f69d5d9dc65c593f4cd0c43016558a48c8c310e6e9794` |
| J24G99 immutable root + rolling tail | [Actions #41154158984](https://github.com/FCMO-AI/.CMPCT/actions/runs/41154158984) **SUCCESS**, 8 cases, 9 forged receipts rejected by separate stdlib referee | `O0_ROLLING_TAILPACK_LOCAL_SCREEN_PASS` | `10576343b9e9af9a92ded554a26b23d3614739be523f0abdc36e309d01866b17` |

Original hosted artifacts: [J24G98 #13024856010](https://github.com/FCMO-AI/.CMPCT/actions/runs/41154158860/artifacts/13024856010) and [J24G99 #13023976889](https://github.com/FCMO-AI/.CMPCT/actions/runs/41154158984/artifacts/13023976889). Both contain the four untouched original source ZIPs, all raw 15-round read samples, allocation receipts, source identities, detached referee output, and SHA256SUMS. CI PASS is a **scientific counterfactual decision**, not a secure-publication or Reader-v0.31 qualification.

## Decisive physical cases (same original bytes, same Linux filesystem class; different CI runner instances)

| Input provenance, 64 signed footers | J98 final allocated / contiguous | J98 warm 4KiB read / contiguous | J99 final allocated / contiguous | J99 warm 4KiB read / contiguous |
|---|---:|---:|---:|---:|
| Ubuntu 4096 | 1.543× | 3.557× | 1.0086× | 1.035× |
| Ubuntu 8192 | 1.274× | 2.643× | 1.0043× | 0.988× |
| Windows-origin 4096 | 1.593× | 2.861× | 1.0185× | 1.026× |
| Windows-origin 8192 | 1.294× | 2.789× | 1.0047× | 1.005× |

Both courts reconstruct the **byte-for-byte original complete archive and all authentic footer-ended prefixes**. They detect corruption after *re-verification* using raw SHA-256, not an untrusted self-authentication claim. Original metadata and checksums of unchanged r24 bytes are preserved. The independent original ZIP SHA and source HEAD checks establish common source identity, **not equivalent-host time comparison**: do not interpret the J98/J99 cross-run ratios as a paired speedup. A detached cross-court auditor was run locally against the two downloaded provider ZIPs, checked the same 8 raw archives, SHA hashes, footer positions, all raw sample medians and stored byte costs; both provider ZIP SHA-256 values matched GitHub's recorded digests. No new product code imported.

**J24G98 scientific negative:** a physically separate 97-byte journal append per generation costs one full physical filesystem allocation block per tiny segment, plus the final manifest; deep archives require up to 65 simultaneously open cached file descriptors. Even cached reads failed the preregistered <=2× latency screen on the hosted Ubuntu court. Four shallow original archives also lose heavily: final allocated ratio 2–5×. The unchanged direct Writer append remains a superior baseline for storage and update bytes.

**J24G99 scoped positive:** reuse one immutable original base, rebuild only an immutable cumulative *tail file* after each append, and publish one new manifest via atomic same-directory replacement with file/directory fsync. Root + currently selected tail allow <=1.05× active allocated bytes and <=2× cached warm-read median for all four deep cases. Creation of the current tail is still a separate write and full archive source trust is external. At 64 footers the 63 real 97-byte appended events lead to **32× repeated tail-copy bytes** relative to direct append, but only **0.0033–0.0071×** the bytes needed to re-copy full immutable archives after each generation. This is physical-organization *headroom*, not installed CMPCT Writer economics.

## Strongest negative / hidden export

For each 64-footer case, J24G99 accumulated **98.529× new filesystem-block allocation relative to the 6,111 direct append bytes**, plus **190 filesystem sync calls** (127 file fsyncs and 63 directory fsyncs) and 63 manifest replacements. This includes copy-on-write tail and manifest write amplification; final live allocation is low only after older tail files are garbage-collected. Original previous-tail snapshot correctness was checked while its inode existed; real **concurrent readers, epoch grace periods, mutable same-UID writers, crash durability, CAS between writers, manifest-origin authentication, native/OS portability and complete system peak RSS remain UNPROVEN**. Small 4-footer inputs cost 1.5–3.0× allocated bytes and therefore need a generic size/rate admission and safe direct-append fallback. A mode-0444 tail is **not** immutable against an actor owning its path; the research tests explicitly do not assert hostile-source immutability.

An analytically visible earlier discriminator: 97-byte independently allocated immutable events cannot avoid rounding to the host filesystem's allocation unit (4,096B in these tests). The scientific decision would have been predicted by counting blocks and FD fanout *before* implementing a richer virtual Reader. This already follows the existing Discovery Engine exported-cost BONK filter, so **no new policy edit is earned**.

## Scope, concurrency, CI and disposition

This work modifies only two preregistrations, two source-exact detached mechanisms, two independent binary/receipt referees, and two specialised workflows on the existing **draft PR #869**, not `main`, any installed source, `native/`, version, on-disk format, frozen release thresholds, or promotion corpus. #574 currently owns `docs/discovery/STATE.json`, #871 owns the physical Reader A/B/C comparison, and #290/#836 own multiwriter exclusion; no collision with their mutation surfaces was encountered.

**Decision:** retire per-footer physical fragmentation at the bounded O0 screen, preserve rolling immutable tail as a non-shipping research seed with explicit 32×/98.5×/190-sync exported update debt. Do not promote. Cheapest high-value next proof is an *actual source-pinned Reader / writer-commit / concurrent-held-reader court* that prices FS-specific inode/CoW alternatives and proves CAS + crash/GC recovery without weakening #857/#860/#861/O23 or existing release barriers. Until then prefer stronger already-owned product work such as #823/#871 for reader reconstruction and #749 for verified publication custody. Do not start another nearby threshold variant.
