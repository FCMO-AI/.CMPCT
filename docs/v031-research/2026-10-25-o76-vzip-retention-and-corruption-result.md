# O76 / O76b — exact-source VZIP range-retention economics and integrity mismatch

**UTC date:** 2026-10-25. **Status:** scientific result only; **NO PRODUCT PROMOTION / NO MERGE / NO RELEASE**.

## Provenance, preregistrations, and non-overlap

Canonical development parent `agent/v031-development@4545d7d5b2a0b712b4b00f5a9c291d4a3a9e169b`. Actual Builder Git blob `663ef0922992b1fbb8f19e6eea88d55c10a56044`, Reader `e716233403dabd0966863c45635e18fa5ac6afb8`, Codec `29526db4203723d83523fc95d074c346b63d7587`; physical archive format revision 24. O76 was preregistered in `13f5dd076033d2d8a593ec376d1e3cf86ece866b` before the source-exact instrument. O76b (a **new question after seeing O76**, without changing O76 criteria) was preregistered at `cf8e5202eb48005b8f18681236e1dcc32c4ef74b` before the hostile instrument.

O76 intact-source result: [source-bound CI #40186308430](https://github.com/FCMO-AI/.CMPCT/actions/runs/40186308430), original result HEAD `632ec5b81260602b774fcf62a382443ba28a8764`, [artifact #12595289599](https://github.com/FCMO-AI/.CMPCT/actions/runs/40186308430/artifacts/12595289599), ZIP SHA-256 `187e8dc6b21455c92c141ffc51922b6203b8a222358fc7937ff73f48746658cc`. Independent ZIP/JSON reading confirmed 4 cases, 48 authentic Reader range observations, 8 complete builds, complete archive sizes and source/result identities. All inputs round-tripped through installed CMPCT read, verify and extraction. O76b hosted [exact-source CI #40186653376](https://github.com/FCMO-AI/.CMPCT/actions/runs/40186653376), source HEAD `5490712c514b287b3c00e91f54de5ebdc394a09a`, [artifact #12596143902](https://github.com/FCMO-AI/.CMPCT/actions/runs/40186653376/artifacts/12596143902), ZIP SHA-256 `024142da5943cedc976ac4e589cb60da802774d44229af7985fc7e5ea242c98e`, original hostile JSON SHA-256 `a3053fcbb6eb0b7c57e0900a0caea6c7ca54edd62bbcfde631ecf733b38a2bcf`. The unchanged exact source was wheel-installed outside the checkout on Ubuntu 24.04 CPython 3.11.

## Original O76 intact-archive observation

The only encoder difference is the existing `Builder(deflate_reuse_min)` policy: 65536 generates mode-2 Deflate from expanded content; 0 retains original exact Deflate as mode 0. Both Reader, ZIP source and physical r24 decoder are identical. A 64-byte physical ZIP range was selected from *inside the first compressed member*. Each case had six fresh-Reader samples per arm (ABBA order over three cycles), with measured process CPU, wall, materialized bytes, complete archive bytes/SHA and original/extracted SHA.

| ZIP source / arm | Mode | Complete CMPCT bytes: regenerate / retained | Median selected 64B wall: regenerate / retained | Ratio |
|---|---|---:|---:|---:|
| 2 MiB repeated payload | 2 / 0 | 1,276 / 3,277 (+2,001 B) | 10.256 ms / 0.0386 ms | 265.78× |
| 8 MiB periodic payload | 2 / 0 | 2,240 / 34,095 (+31,855 B) | 40.392 ms / 0.0380 ms | 1063.89× |
| 2 MiB mixed entropy | 2 / 0 | 34,422 / 39,139 (+4,717 B) | 11.064 ms / 0.0288 ms | 384.10× |
| 2 MiB independent random negative | 0 / 0 | 2,099,027 / 2,099,027 | 0.127 ms / 0.150 ms | 0.85× (noise/control) |

For eligible inputs, logical materialization through `_blob` was 2,097,272 / 8,388,728 bytes in the regenerated arm versus 120 bytes in the retained arm. **This is decoded/materialized logical work, not measured physical disk I/O.** The prospective intact-archive >=8×/<=64 KiB test was satisfied on three structurally different input families. Creation wall in the same hosted run was also lower for retained on these three cases; all original raw samples remain available. This is *not* full release performance or proof of improved worst-case integrity.

## O76b adversarial disproof of equal integrity tier

A prior unmeasured semantic difference matters: mode 2 accesses raw content through `_blob`, validating a physical blob's CRC; mode 0 `_stream` returns the encoded Deflate payload directly from `mmap` for a range request without verifying that physical payload. O76b independently copied authentic CMPCT files then flipped exactly one compressed-data byte in the selected physical range of mode 0 (outside index/footer), while mutating the mode-2 blob in its own copy. Two original source ZIP families were used: repeated 2 MiB and periodic 8 MiB. Original unmutated archives verified and returned exact ranges first.

**Observed on both families:**
- **Mode 0 retained**: `read_range` **returned silently altered 64-byte data** (selected-range SHA differed from the authentic source); a separate fresh `CMPCT.verify()` **rejected** the same corrupted archive.
- **Mode 2 regenerated**: fresh `read_range` **rejected** the corrupted physical blob, and fresh `CMPCT.verify()` also **rejected**.
- No Reader, evaluator, data, release threshold or archive format modification was used to manufacture this outcome. Raw hostile mutation offsets, before/after bytes, SHA and exception types are preserved in original artifact JSON.

**Decision change:** O76's 265–1064× intact-input speed advantage is **not equal corruption-detection semantics** under these controlled physical mutations. In particular, it **cannot** be promoted as an equivalent authenticated selective-range improvement. The original prospective intact-input microeconomic result remains valid and is not retrospectively falsified: it answered a narrower, clean-input question. The hostile result constrains promotion and identifies an explicit proof/performance frontier. Normal range behavior elsewhere in CMPCT may also have tiered integrity and the format documentation explicitly distinguishes normal CRC from full strong `verify`; this experiment does *not* claim a novel universal security vulnerability.

## Counterfactual / alternative designs

The cheapest earlier discriminator would have been a one-byte physical corruption test **before** investing in a full retained-stream product policy. Static code inspection already indicated the integrity-tier difference, so a short hostile control could have warned that speed on intact archives was insufficient for authenticated-range credit. A credible candidate must preserve a clear API guarantee: (1) explicitly weak/unchecked selected-byte range API and honest labeling; (2) an authenticated per-blob/stream range receipt or cached prior strong proof tied to an immutable owned source; or (3) a differently owned representation that preserves both fast selected access and integrity. A simple one-time verify without source immutability is insufficient under concurrent mutation. Choosing a mode0 stream on all input files would also export complete stored bytes, so generic admission and whole-system economics remain material.

## Negative / residual debt and handoff

Source exactness and installed-product tests are green for **this scoped research**, but its 64-byte warm filesystem-cache timings omit cold disk I/O, OS-level page-fault accounting, cumulative process start, platform transfers, native RSS, streaming extraction, concurrency, source mutability, and final-format official parity. Original O76 `verify_wall_ns` was measured *after a prior full read* in the same Reader and is **warm-cache**, not independent cold verify. Do not use it as a strong verification-throughput claim. The random negative is not a win. No product file, frozen official benchmark, release law or Discovery Engine policy was changed.

**Next safest discriminator:** re-run a byte-identical retained-vs-regenerated comparison under the same *explicit* authenticated selective-range contract (proof binding and full CPU/RSS/bytes accounting). If per-range authentication consumes the speed headroom, retire retention as a performance-only direction; otherwise consider a bounded admission policy once real complete-archive economics and exact-head release gates are obtained. Coordinate with O63 #418, O68 #424, O70 #426 and O73 #429 rather than starting duplicate physical ownership implementations. No canonical merge or v0.31 release authority is asserted.
