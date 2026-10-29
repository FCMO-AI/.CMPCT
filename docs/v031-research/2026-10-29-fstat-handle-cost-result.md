# J24I13 — installed Win32 fstat economics: micro headroom confirmed, direct substitution unsafe

Date: 2026-10-29 UTC. **Scientific result / draft**, not a change to CMPCT product, code, format or release.

## Immutable provenance and coordination

- Prospective prediction (before test or workflow): [commit `6b8018de89657b55a1a1619de86ab6d28c6b8a73`](https://github.com/FCMO-AI/.CMPCT/commit/6b8018de89657b55a1a1619de86ab6d28c6b8a73); [preregistration](2026-10-29-j24i13-win32-fstat-economics-prereg.md).
- Research instrument and hosted workflow HEAD: `83de3046de68bbe2e47f5dcc587be77a11422ff3`, [PR #733](https://github.com/FCMO-AI/.CMPCT/pull/733), stacked on exact [#730](https://github.com/FCMO-AI/.CMPCT/pull/730) HEAD `f190a566950970895cec54e215538691aa7595ca`.
- Existing **product mechanism owner**: [O47 PR #401](https://github.com/FCMO-AI/.CMPCT/pull/401); #730 only composes it into private compaction. This result is *not* an independent competing Builder patch.
- Exact installed Builder Git blob `b3c8cbfbefb9d47ffa849bd939257215ee4b0a09` and research instrument Git blob `a585b3b6291369df92300efc03660eb22168ca5f` were retained by CI. No product files differed from #730.
- [Original hosted installed court run #40825268492](https://github.com/FCMO-AI/.CMPCT/actions/runs/40825268492) completed with Ubuntu and Windows scientific jobs **SUCCESS**. Success means an honest experiment completed; it is NOT product acceptance.

## Primary question and direct measurements

Control A: for each source entry, `os.stat(path, follow_symlinks=False)` then normal `open/read`. Candidate B: normal `open`, then `os.fstat` on its existing read fd and `read`. These have identical bytes and physical `st_dev/st_ino/st_nlink/st_mode/st_size` on **stable regular files** but intentionally different behavior under source symlink substitution. Two deterministic families: 256 independent 64-byte files, and one real owner+hardlink+content-identical physically independent copy. Four full paired ABBA rounds plus A/A for each family/host; all 64 raw operation samples/host persisted. This is a **component micro A/B**, not an actual Builder A/B nor a launchable replacement.

| Host / family | A pooled median | B pooled median | B vs A | Paired ABBA B/A | Threshold |
|---|---:|---:|---:|---|---|
| Windows 2022 / 256 independent files | 22.17425 ms | 15.04280 ms | **−32.16%** | 0.68422, 0.68251, 0.68797, 0.62460 | 4/4 >=10% savings |
| Windows 2022 / three path topology | 0.25525 ms | 0.18340 ms | −28.15% | 0.71334, 0.71853, 0.72227, 0.87536 | 4/4 |
| Ubuntu 24.04 / 256 files | 3.91575 ms | 3.61947 ms | −7.57% | 0.74978, 0.82514, 0.90976, 0.88679 | 3/4 |
| Ubuntu 24.04 / three path topology | 0.0564405 ms | 0.052663 ms | −6.69% | 0.93472, 0.92872, 0.92662, 0.81247 | 1/4 |

This is **positive measurement of a cheaper reuse seam** on regular files, especially Win32, without generalizing the 32% component timing to the prior +23.10% complete Builder regression. The 256-file source reconstructed independently from deterministic generator gives exact corpus digest `29939f1e0923c926f528d389c7c22010cf99c95eb79818e6af35db6334f6a9d7` on both hosts; the three-name topology digest is `c79def44f118300a7dc4988fdeff365b4052ca65f0cab773221bab50c0135ce6`. Physical link counts are `[2,2,1]`; the equal-byte copy was never coalesced. Total read bytes 16,384 and 12,375 respectively, on every A and B.

Independent stdlib ZIP/receipt audit recalculated every ABBA, A/A, pooled median and source digest against original artifacts, without importing CMPCT; both matched. Raw immutable original evidence:
- Windows artifact `12876635484`, ZIP SHA-256 `edf45ba2b900f64d22473bdcaa9b1c6d850670625ecb6eb7b7aa8f62fa1f4a98`.
- Ubuntu artifact `12876446348`, ZIP SHA-256 `0d46e3e9ddbf448efa8d898bf45909383451189b9eb116770e6580a31a8985c0`.

The historical #730 Windows full Builder-cost witness also survives independent recalculation: 3/4 paired ABBA candidate/control ratios 1.24969, 1.20254, 1.23405, with a fourth distorted by a 161.714 ms baseline outlier (0.45698 ratio), pooled median 1.23098. That result is a motivation, **not** attributed to this new implementation.

## Strongest negative: same-handle metadata alone is not secure admission

Both installed hosts explicitly confirmed `MISMATCH_CONFIRMED`: an `os.stat(path,follow_symlinks=False)` identifies a source symlink, whereas plain `open(path)` followed by `os.fstat(fd)` reports the **target's regular-file type**. Replacing O47's nonfollowing `os.stat` with plain open+fstat creates an archive-source semantic/security weakness if the leaf changes after `DirEntry.stat`.

**Therefore `DIRECT_OPEN_FSTAT_PRODUCT_REPLACEMENT = REJECTED` despite the measured micro speedup.** No benchmark, correctness or security gate was weakened to obtain the attractive number. The scientific positive leaves an architecture option: perform genuinely nonfollowing *handle-bound* source admission and read from the same authorized file handle; proof is **not supplied** by this experiment. Windows-specific tests must include symlink/reparse point substitution and ancestor rebind, hardlink topology and distinct-copy negative, file read after inspection, source mutation/failure handling, long path/permissions, and the deferred ZIP/WHL and sparse paths of Builder.

Primary OS/API references for a future design, not implementation evidence:
- CPython Windows `DirEntry.stat` documents zero `st_dev/st_ino/st_nlink`: https://docs.python.org/3.11/library/os.html#os.DirEntry.stat
- Microsoft `CreateFileW` documents `FILE_FLAG_OPEN_REPARSE_POINT` retaining a handle to an existing symlink rather than following its target: https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-createfilew
- Microsoft `FILE_STANDARD_INFO` exposes `NumberOfLinks` from an existing file handle: https://learn.microsoft.com/en-us/windows/win32/api/winbase/ns-winbase-file_standard_info
- This final-component flag by itself does not establish an immutable ancestor directory namespace. It needs an explicit security design rather than inference.

## Counterfactual, costs and decision

A prospective minimal regular-file cost micro before implementing a second alternative would have exposed substantial reuse headroom, but the independently observed **symlink-follow semantic gap** disqualifies naive fstat replacement at the same time. A smarter experiment should deliberately pair a performance oracle with the strongest missing safety invariant from the outset; that was done here. No repeated evidence earns a new Discovery Engine policy or STATE update.

The actual decision is **`WIN32_DESCRIPTOR_REUSE_HEADROOM_CONFIRMED / PLAIN_FSTAT_ADMISSION_REJECTED`**. Hold #733 research-only; inform #401/#730 owners. Next *different* narrowly authorized question for a sole owner is: can a Win32 nonfollowing handle be acquired and validated against reparse/identity changes while reading the same bytes, at a complete Builder cost below O47, without changing source topology, format, stored bytes or security? If not, retain O47's correctness and pay its Windows cost. Do not treat that micro court as an excuse to delay the already confirmed #726 stage-name safety veto, #731 sparse memory debt, or original whole product promotion gates.

No merge/release. Published `main` remains v0.30.0, revision-24. **Exact-head general CI and release gate status must be read separately:** the hosted J24I13 court is the result for `83de3046`; any documentation-only subsequent HEAD is not automatically an installed court success.
