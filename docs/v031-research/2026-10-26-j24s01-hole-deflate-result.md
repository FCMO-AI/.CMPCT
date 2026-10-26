# J24S01 — Exact-source charged sparse-hole DEFLATE fragment oracle result

**Date:** 2026-10-26 UTC. **Status:** `RESEARCH_ONLY_POSITIVE` on bounded explicit-hole inputs; **NO CMPCT PRODUCT CREDIT**. Preregistration is immutable at `b27903007189840b2114ab3ad65fc6d05837307f` and preceded implementation `76f69dec14f150891f17f08f258eb06ba05d597c`.

## Source/hosted evidence

Repo: `FCMO-AI/.CMPCT`; research PR #525; exact host-executed HEAD `5da494d4a851ed6eb339b23b17377dafeb52cdf6`; J24S01 workflow [40360901489](https://github.com/FCMO-AI/.CMPCT/actions/runs/40360901489), scientific job `121705722864`: **SUCCESS**, terminal `J24S01_ORACLE_VERIFIED`. Original raw observation artifact [12667769877](https://github.com/FCMO-AI/.CMPCT/actions/runs/40360901489/artifacts/12667769877), artifact digest `sha256:f889fe801e393af4d11dc7406dde13387c28b515dceb9ac5d8af4928ba6d6aaa`. Source code `research/j24s01_sparse_hole_deflate_oracle.py`. Full JSON repeated measurements, compression calls, original logical CRC32/SHA256 and raw DEFLATE hashes live in hosted artifact, not this summary.

**Scope:** offline raw RFC1951 DEFLATE compression + complete incremental SHA256 and CRC32 over all logical bytes, followed by independent bounded raw-deflate decode to exact EOF/length/hash/CRC. Not a CMPCT archive, not a ZIP64 container, not an installed Reader benchmark. Proven on Ubuntu Python3.12 with system zlib; no cross-platform or data-safety promotion.

## Observed measurements: medians of 3 interleaved runs

| Logical construction | zlib level | Ordinary median wall | Reused zero-fragment median wall | Speedup (charged hashes) | Ordinary DEFLATE bytes | Template DEFLATE bytes | Byte change |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 256 MiB explicit zero holes | 1 | 0.585551 s | 0.275223 s | **2.128x** | 1,171,371 | 1,176,066 | **+0.401%** |
| 256 MiB explicit zero holes | 6 | 1.111979 s | 0.275310 s | **4.039x** | 260,916 | 265,474 | **+1.747%** |
| 256 MiB mixed, 4KiB nonzero per 16MiB | 1 | 0.588088 s | 0.278163 s | **2.114x** | 1,245,721 | 1,241,474 | **−0.341%** |
| 256 MiB mixed, 4KiB nonzero per 16MiB | 6 | 1.115755 s | 0.281770 s | **3.960x** | 335,531 | 331,106 | **−1.319%** |
| 64 MiB no-hole data | 1 | 1.892936 s | 1.896051 s | **0.998x** | 67,129,269 | 67,129,269 | 0 B |
| 64 MiB no-hole data | 6 | 2.082106 s | 2.085504 s | **0.998x** | 67,129,339 | 67,129,339 | 0 B |

The no-hole `template` arm selects the **same continuous ordinary encoder**, from the absence of hole descriptors, not from workload name. It is byte-identical to the ordinary control. No speedup claimed on data without structurally admitted holes.

## Scientific decision and strongest simpler control

Original prospective `>1.5x fully charged wall` and `<=5% byte overhead` conditions passed on two levels for zero holes. Mixed-case `<=10% overhead` passed (in fact a smaller stream here), and no-hole exact fallback passed. All independent inflate/EOF/full SHA/CRC checks succeeded. The experiment demonstrates that sparse-hole knowledge can eliminate redundant *compression* of semantically known zeros without deleting the semantic SHA/CRC work. This is an execution/representation oracle, **not** a demonstration of end-to-end `export_zip()` speed, resident memory, source-mutation safety or release readiness.

The stronger framing control `framed` also compresses independently flushed blocks but recomputes zero fragments. Raw per-arm results remain in the artifact. The key causal distinction is admission of already known hole content, not merely framed Deflate boundaries; however, reusing fragments may degrade longer cross-block dictionary compression on less sparse content, making prospective full-byte admission essential.

## Negative/counterfactual and generality limits

1. Zero-hole template increases raw DEFLATE bytes by 0.401% (level1) and 1.747% (level6). The candidate is **not Pareto-dominant on size alone**; admission must preserve incumbent when byte overhead is undesirable, particularly under zero-byte release-parity law. This explicit regression debt cannot be waived with total wall savings.
2. The very high fraction of known holes is an unusually favorable information-structure predicate. Random content without holes sees exactly zero compressor benefit and ordinary fallback.
3. The current script materializes a standalone complete **compressed** DEFLATE stream in a BytesIO and constructs 1MiB zero slices for hashing; it does *not* validate bounded temporary I/O, ZIP64 headers/metadata, physical filesystem sparseness or O193 Reader's authentic sparse extent parser. It does not prove peak RSS.
4. In an actual 4GiB file, source `read_range`, index traversals, SHA/CRC, compression, ZIP writing and staging compete for wall; the expensive subsystem might move. O195's 4.225% extent-index advantage shows that local micro optimizations cannot claim a product effect absent full export.
5. Real byte-identity and compression ratios change with arbitrary data context, nonzero span sizes, sync overhead and levels; no content/fixture identity may enter the admission predicate.

**Cheapest counterfactual:** the byte-aligned RFC1951/Z_SYNC_FLUSH composition plus a fully SHA/CRC charged 256MiB offline A/B was enough to decide whether a new compression-work frame deserved product testing; a 4GiB installed build or another metadata index optimization was not necessary to discover this opportunity. This is one episode, **not** evidence for a Discovery Engine policy rewrite.

## Next executable target

A distinct owner-coordinated *installed real-r24* experiment should take the authentic O193 4GiB sparse Builder/Reader source and implement a bounded, **content/structure-driven** DEFLATE fragment adapter in a separate branch or invoke an owner-reviewed streaming hook, while preserving O193 full member SHA, ZIP CRC, identity, DOS timestamp, POSIX metadata and O179/O181 publication obligations. On one runner compare true whole `export_zip` wall+CPU+peak RSS+temporary I/O+ZIP bytes against unchanged O193, verify exact decoded 4GiB independently and include wrong-order extents, nonzero-byte changes and nonhole controls. Use the current incumbent if the candidate exports size/regression debt; do not weaken frozen parity gates.

**Decision:** `ADVANCE_TO_AUTHENTIC_PRODUCT_FALSIFIER`; source/format/version unchanged; no merge/release credit; no concurrency collision encountered (O193/O195 owners respected); Discovery policy and `STATE.json` unchanged.
