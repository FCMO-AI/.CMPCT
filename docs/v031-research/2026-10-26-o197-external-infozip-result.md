# O197 — Mature external Info-ZIP validates authentic CMPCT 4 GiB ZIP64

Date: 2026-10-26 UTC. Status: **SCIENTIFIC POSITIVE FOR ONE GENUINE SPARSE 4 GiB PROFILE; NO PRODUCT PROMOTION**.
Parent O196 PR #526, head before O197 `38c73861917420184c00e99186d6c747b3a8258d`; product implementation inherited from O193 #521. Released CMPCT remains v0.30.0/on-disk r24.

## Prospective question, frozen prediction and selection

Preregistration was committed at `3f66850bf0d020f473655f5962249982670400f9` before O197 instrument/CI and before any O197 hosted observation. O196 proved cross-host CMPCT-to-ZIP64 4 GiB export and readback on Ubuntu/macOS/Windows, but the exporter and full reader were both CPython `zipfile`. O197 asked whether a **mature external consumer, Info-ZIP UnZip 6.00**, could parse and CRC-verify those authentic bytes, read all 4 GiB through bounded stdout and reproduce the original source SHA. Stronger alternative: writer+reader sharing Python library can conceal mutual format assumptions. Simpler alternatives (more CPython reads or a custom parser) offered less information. This is not a new encoding method, release or codec benchmark.

## Authentic scientific run and exact code identity

- Draft PR: [#529](https://github.com/FCMO-AI/.CMPCT/pull/529).
- Result-bearing scientific HEAD: `f39d84d4a4996a33fd56f332b2455b06ec6d7c2a`.
- GitHub Actions independent Info-ZIP [run 40372284581](https://github.com/FCMO-AI/.CMPCT/actions/runs/40372284581): 1/1 job **SUCCESS**.
- Original downloadable raw JSON [artifact 12672233735](https://github.com/FCMO-AI/.CMPCT/actions/runs/40372284581/artifacts/12672233735): producer, inherited O196 consumer, independent O197 receipts.
- Installed Reader normalized SHA-256 `c65c4a3d02e943479fee89efbb3b5808289c1cd5f821a30141549a50173ebcea`. All three receipts attest the exact `f39d84...` checkout. GitHub event merge SHA is distinct and not treated as installed source HEAD.
- External consumer version: `UnZip 6.00 of 20 April 2009, by Debian`, compiled with GCC 13.2.0 on Linux x86_64.
- Independent local post-download receipt cross-check: PASS; original JSON SHA-256 values (producer `c7b84480bc9c29c066ea53de85a1047f9ccbf945d348c2b816635a77d0ba17e4`, CMPCT consumer `9e55f7bac4fede22b2fbcb2d4828c6325c64259ed6d70d09a5b3da211f9947f5`, Info-ZIP `11fd5d7f6b6ea15b9e0d1e131c7784c3534fe20d9a2df52274063db808620f11`). Original ZIP/CMPCT binaries were **not** part of downloaded JSON evidence; their byte identity was measured within the hosted instrument and attested by receipts.

## Direct product-derived measured facts

| Property | Result |
| --- | --- |
| Builder-produced logical sparse source | 4,294,967,296 bytes = 4 GiB |
| Linux physical allocated source | 16,777,216 bytes |
| True source/index sparse extents | 4,096 / 4,096 |
| Authentic r24 CMPCT archive size | 533,466 bytes |
| Original archive SHA-256 | `743558c475a07641b76ac7b231547a6616e7a2bfecfbce0a1c3e9d5f17b894fa` |
| Exact source decoded SHA-256 | `aa8eab1213de329104d81b6ea925c8455e55ccdd47b0457fa6abe9c1f65cf1c3` |
| Complete CMPCT-generated ZIP64 output | 4,415,465 bytes |
| ZIP SHA-256 (O197 run; differs from independent O196 runs due input mtime) | `967649d8ebb221f5896309d0338427b168a87aa3b6eac09981183e27d7a3dcc6` |
| ZIP64 32-bit length sentinels | present |
| ZIP64 local true uncompressed size | 4,294,967,296 bytes |
| ZIP64 compressed member length | 4,415,307 bytes |
| ZIP required version | 4.5 |
| Inherited O196 complete Python `zipfile` SHA/CRC | PASS |

## Independently rooted Info-ZIP evidence

| Control | Result |
| --- | --- |
| Native tool binary version | PASS: Info-ZIP UnZip 6.00 |
| Small known-good ZIP readiness control | PASS, exit 0 |
| Original real CMPCT ZIP64 `unzip -tqq` native CRC/Deflate | **PASS**, exit 0, 19.342 s wall |
| Native `unzip -p <original.zip> sparse.bin` streaming output | **PASS**, exit 0 |
| Full external output bytes | **4,294,967,296** exactly |
| Full externally decoded SHA-256 | **equal to source SHA-256** |
| Stream wall time | **20.184 s** (single-run observation; not official performance) |
| Maximum bounded Python pipe read request | 4 MiB; largest returned chunk 65,536 bytes |
| Compromised compressed-data copy `unzip -tqq` | **REJECTED**, exit 2 |
| Negative independent error detail | `bad CRC 676b13ea (should be 84770cfb)` |
| Corruption offset | ZIP byte 1,084 (1,024 bytes into actual Deflate stream), byte 0→255 |
| Original CMPCT and ZIP hashes after both controls | UNCHANGED, witnessed within hosted instrument |

The negative control changed a **separate copy**, left the ZIP headers/central CRC unmodified, and yielded Info-ZIP's native CRC mismatch. This means the independent consumer is not being credited from a permissive success code alone: it detects physical compressed-content damage in the same full-size scenario.

## Strongest negative, portability, resource and scope

This is **one real Builder-selected S_SPARSE 4 GiB member** on Ubuntu 24.04 Info-ZIP 6.00, not proof that all ZIP64 layouts or malformed members are supported. O196 previously found the generated ZIP bytes byte-identical across three OSes for the *separate O196 run*; O197 did not transfer its new archive across hosts and must not claim a new cross-host external run. Source ZIP SHA can change across independent builders because source `mtime_ns` changes; the original source logical SHA remained identical. Info-ZIP cannot establish authenticated CMPCT archive structural safety, arbitrary selective-read efficiency, crash durability or large-frame RSS bounds. The external tool's resource usage was not separately measured; the 4 MiB limit applies to Python's stdout reading buffer, not all extraction memory.

No archive format, CMPCT Reader/Builder, original O196 court, frozen benchmark, performance comparator, Discovery policy, canonical branch, numeric version or release gate was modified.

## Decision / counterfactual / handoff

**Decision changed:** one genuine CMPCT ZIP64 >4 GiB member now has both CPython and an independent mature Info-ZIP full-member accept+CRC+SHA result, with a hostile corrupted-byte negative. It earns **scoped external interoperability evidence**, not a new production feature or release. No need to implement a third ZIP writer on this result.

The earliest prospective discriminator was precisely the independent mature consumer on the already-proven O196 archive. Merely parsing a ZIP64 local header or running Python-to-Python did not close that uncertainty. No repeated evidence suggests a Discovery Engine policy change.

**Next unclaimed frontier:** malformed ZIP64 member/layout handling and bounded resource/product resilience; or integration of this independent court into the O193 owner composition without duplicating implementation. A safety priority is issue #528's verified chunk-stage inode publication race, separately under J24F02 #527 ownership. Preserve same-input semantics and source SHA; do not reinterpret evidence as ZIP/Zstd size or speed domination.

**Product status:** scientific PASS; General CMPCT tests and release parity are separate obligations; no canonical merge, no release.
