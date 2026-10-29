# J24I37 — Preregistered native direct-compressed complete-verification work court

**Scientific scope:** no Builder/Reader/native product edit, no format or release edit, no benchmark threshold change. Parent is the existing native CRC owner #765 at exactly `9ef1644d8c6129de4d7d8008bfdadad5fffcbe06`, itself stacked on #759. Published `main` remains v0.30.0 / r24. This record is intentionally committed before implementing the court or observing any hosted result.

## Question and baseline

Does the existing `Archive::verify_complete` repeatedly allocate/decode/hash the entire directly compressed physical member for each fixed 8-MiB logical verification slice, and is its resulting exported work large enough to prioritize a bounded single-pass verification architecture over sub-2% header-read micro-optimizations?

**Observed source facts at parent:** `native/cmpct-core/src/vzip_dispatch.rs` invokes `read_range` in an 8-MiB loop. For `Storage::Direct`, `lib.rs::read_blob_range` invokes `decode_zstd_blob` / `decode_deflate_blob`; each decodes and hashes the *entire* member before returning a slice. For a legal size `N` with `M=ceil(N / 8 MiB)`, the apparent decoded-work bound is `M × N`, not `N`. The physical compressed record is also reread M times. This is source-level derivation, **not** yet measured end-to-end overhead.

**Product applicability limit:** normal large generic files use CDC/fixed chunks; do not equate an artificially large direct-Zstd specimen with common Builder policy. WAV/FLAC direct storage is an independently relevant exception; only a separate WAV/FLAC held-out court can establish product prevalence.

## Competing actions and BONK

1. **Surgical one-header reuse** (#765 J24I36d): measured -1.21% / -0.75% relative to the CRC-bearing candidate on small direct members, signal close to A/A drift; keep as candidate, not a broad performance solution.
2. **Decoded-buffer memoization:** eliminates repeat decode but can require the whole member (up to 256 MiB) resident, exporting RSS and lifetime/cache identity risks.
3. **Decoder-state streaming through complete verification:** potentially single-pass for direct Zstd/Deflate, bounded output, but must retain independent SHA, physical CRC, length/trailing-frame admission, dictionary/WAV details, and current path/descriptor ownership.
4. **Cheap falsifier first (chosen):** before changing the verified code, measure actual source-exact decoded-work and I/O amplification of the existing verifier against an explicitly *non-equivalent-RSS*, optimistic one-shot strong-check control on the very same r24 archive. Kill a complicated product rewrite if the gain is not material.

## Prospective experiment

Create **independently framed** r24 archives (not Builder policy claims), each with one valid direct Zstd member of 8, 32, and 64 MiB logical size. Generate immutable deterministic content from a fixed seeded repeated binary tile; sign both physical CMA4 SHA/CRC and both compressed indexes + footer. Audit physical headers, index hashes, tail, decoded content, CRC, and the member identity using a **detached parser without importing CMPCT**. Independently verify genuine files with installed Python CMPCT and compiled Rust.

On Ubuntu native Rust, time (inside the executable after archive open) two distinct operations on the *same input*: A = actual `Archive::verify_complete()`, B = one `read_range(0,0,full_size)` followed by independent SHA-256+CRC32 over its returned buffer. B preserves payload/checksum semantics but **not** the 8-MiB RSS boundary; it is an optimistic micro-oracle only. Alternate ABBA/BAAB runs, exclude warmup, retain raw per-run samples, and record Linux `/proc/self/io` read-character deltas and `/proc/self/status` VmHWM (RSS evidence must be labeled separately from clean-process peak). Avoid process-start attribution to the library timer.

## Prospective prediction / decisive discriminator

For 8 MiB, actual verification and B should be broadly near one full direct decode (aside from additional SHA/CRC); for 32 and 64 MiB, actual verification should reread/redecode the complete direct compressed blob 4 and 8 times respectively. If actual read-character ratio over B **fails to scale materially** (e.g., <=1.5x at 64 MiB), the source-level mechanism is incomplete/overstated: retire the architecture priority and investigate the observed path. If ratio and time rise with M, preserve the measured scaling as a *research bottleneck*, then test a bounded streaming decoder with correct tail admission and all codecs before any product promotion.

No error in an independent parser may be counted as a product failure. No A/B result earns release or production credit. Existing general CI, #765 source-head pins, inherited performance regressions, and security debts remain unchanged.

## Alternate explanations / hostile checks

Large repeated content may favor decompressor caching, page cache, branch predictor, or CPU cache; preserve separate rchar and wall, avoid claims about physical disk I/O from page cache. The single full read might be artificially fast because of higher RSS, or slow due to allocation. An 8 MiB control and two larger sizes distinguish fixed overhead from N² scaling. A direct 64 MiB research archive is format-conformant but not evidence that current Builder normally emits it. Assert exact hashes and original content to prevent comparison of different data; don't tune sizes after seeing results.

## Decision / handoff

One primary science question; owner #765 is not rewritten. If decisive, append result with commit SHA, GitHub Actions ID, raw receipts, strongest negative, and whether the broader/native product lane is justified. Any subsequent product change must be separately preregistered and measure RSS, CPU/wall, full physical reads, corruption/trailing streams, recovery/portability, and inherited controls.
