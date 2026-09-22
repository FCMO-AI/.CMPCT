# T01 native / ZIP exact-head receipt — 2026-09-04

Status: **accepted exact-candidate mechanism / portability evidence; T01 remains open pending hosted Android on this fingerprint, required physical ARM64, and the remaining release-lock obligations.**

This receipt is coordination/evidence state only. It does not change the release fingerprint, archive grammar, product selector, benchmark corpus, threshold, locality ceiling, recovery semantics, integrity law, or platform requirement.

## Candidate identity

- exact source SHA: `52ebabc63c7ea74a1665a5720359977e552ad5c2`
- release fingerprint independently emitted by native authority and ZIP portability: `67c5f6009d3fa34c56c6d1706597060f56196eca4019a64f97ca5735021a68fa`
- portable Cargo lock SHA-256: `3a4babc7a43ef0aadca37ac0a49695b185419dd8aa2cbebcb5653202ed6a71a2`
- native-core Cargo lock SHA-256: `007f963ed4e135c6dcacb09cd353064ddda87453af481990ca17f7a221402cc1`

The two release-fingerprint-emitting lanes checked out the exact source above from clean worktrees before tool mutation. Both recomputed the strict release fingerprint after their substantive matrices and proved it unchanged. Native-core independently checked out the same exact source and proved its committed dependency lock remained byte-identical through its full matrix.

## Native authority — accepted

- workflow: `v030-native-authority.yml`
- run: `33906151331`
- result-bearing job: `101131475053` (`native-authority`) — **success**
- artifact: `9949599042`, `cmpct-v030-native-authority-52ebabc63c7ea74a1665a5720359977e552ad5c2`
- artifact ZIP digest: `sha256:c8dc54739d332512ebb081d060f3c706826b85163919d0d0270b495814621414`
- evidence schema: `cmpct-v030-native-authority-evidence-v2`

Result-bearing facts proved by the job include G04 native parity, PrefixGraph native parity, Logs inverse native parity/recovery/filesystem semantics, builder-independent goldens, native recovery, implicit-v4 native parity/recovery, r24 fallback strong verification, and shared-core use. The selected Python custody/profile suite reported `42 passed`; the portable Rust unit suite reported `22 passed`; compact-control preparity reported `3 passed`; ZIP-factor preparity reported `2 passed`. The job also proved `native-r24-strong-verify=PASS` and truthful absence of unsupported r24 locality authority.

## ZIP portability — accepted

- workflow: `v030-zip-portability.yml`
- run: `33906151346`
- result-bearing job: `101131485307` (`zip-portability`) — **success**
- artifact: `9949577880`, `cmpct-v030-zip-portability-52ebabc63c7ea74a1665a5720359977e552ad5c2`
- artifact ZIP digest: `sha256:6f6af4b6d10b67490a2c33c924ddec85933c17766518edd09e5b8749a1d61833`
- evidence schema: `cmpct-v030-zip-portability-evidence-v2`

The exact-candidate lane built the shared portable CLI with `cargo build --release --locked`, proved the portable lock did not mutate, and emitted the same release fingerprint as native authority. Stock ZIP round-trip/export passed for r24 fallback, G04 and PrefixGraph (`314` bytes in the fixed portability vector for each), and transactional failure remained atomic. The evidence facts `stock_zip_extract_tree_equal`, `r24_fallback_export`, `g04_export`, `prefixgraph_export`, and `atomic_publication` are all true.

## Native core — accepted for this source / lock

- workflow: `native-core.yml`
- run: `33906151295`
- result-bearing job: `101131444236` (`native-core`) — **success**

This job checked out the same exact source SHA, required the committed native-core lock, recorded lock SHA-256 `007f963ed4e135c6dcacb09cd353064ddda87453af481990ca17f7a221402cc1`, ran lint/tests/release build with `--locked`, and proved the lock remained byte-identical. Its full native matrix passed, including Python-oracle cross-check, non-Rust C ABI use, list/range CLI, ZIP semantic-parity smoke, direct-codec/chunk-map/sparse/micro-pack/Zstd-dictionary/WAV-FLAC/virtual-ZIP ABI gates, and hostile/range behavior. The Rust test groups shown in the result-bearing log included 1 core unit test, 4 physical Deflate mode-0 tests, 1 retained-Deflate golden, 4 virtual-ZIP dispatch tests, and 3 virtual-ZIP golden tests, all green.

Native-core does not itself mint the release-fingerprint JSON artifact. Therefore this receipt does **not** pretend it independently emitted `67c5...`; its binding is the exact source SHA plus the independently recorded native-core lock identity. The clean deterministic release fingerprint for that source is independently reproduced by the native-authority and ZIP-portability lanes above.

## Decision

The frozen-dependency T01 native/ZIP revalidation requested at source `52ebabc...` has succeeded. The earlier ambient-Cargo-resolution D0 custody defect is retired for these three exact-source lanes: both committed Rust dependency graphs are now explicit, locked, and mutation-checked during their release-facing builds.

This is a D5/Custody advance, not a compression or runtime breakthrough. No benchmark byte or runtime delta is promoted by this receipt.

T01 is **not DONE**. Exact-fingerprint hosted Android v2 evidence must still match this candidate fingerprint before physical ARM64 can carry release credit, and the real physical ARM64 receipt remains mandatory. Any later release-critical fingerprint change makes this receipt historical mechanism evidence rather than final release authority.

Release remains **LOCKED**.