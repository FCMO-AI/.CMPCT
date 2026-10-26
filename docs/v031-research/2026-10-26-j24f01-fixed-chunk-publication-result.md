# J24F01 — frozen revision-24 S_CHUNKS/S_CDC publication: hosted result

**Status:** DECISION COMPLETE for this *bounded POSIX, fixed-byte, installed Reader* question. Product unchanged; no format/release/promotion credit.
**Preregistration:** [J24F01](2026-10-26-j24f01-fixed-chunk-publication-prereg.md), committed at `ad8b84e8659778e20d500f91b5b825e7e4db051a` before implementation/evidence.
**Base:** canonical v0.31 branch HEAD `4545d7d5b2a0b712b4b00f5a9c291d4a3a9e169b`.
**Measured candidate:** `6448af5dba1c7619500cb0b4e52b4b99442518a9`, Reader blob `e716233403dabd0966863c45635e18fa5ac6afb8`, original independent golden vector blob `91141405bb10b2e1226b0652e3aa0a13ba41846c`.
**PR:** https://github.com/FCMO-AI/.CMPCT/pull/486

## Primary question / scientific decision

The true installed revision-24 Reader **did** stage and then replace destination directory entries without blocking on pre-existing FIFO/symlink-to-FIFO leaves for both frozen `S_CHUNKS` (kind 1) and `S_CDC` (kind 5), on Ubuntu 24.04 and macOS 14. Both reconstructed the exact logical SHA from independently hand-built archives and preserved original archives and external aliased targets. Mutating the *last* RAW physical chunk after two earlier chunks caused a codec/integrity failure, preserved the original destination regular file **and inode**, and removed the temporary staging file. This is a positive result for these two storage descriptions, not a global Reader-extraction safety claim.

The deliberately harsh alternative — direct write to final existing FIFO — has documented negative evidence in O108/O121 (#463/#471) for `S_BLOB`, `S_SPARSE`, `S_PACK`, `S_VZIP`. J24F01 does not change or waive those defects. It completes the independent r24 frozen **chunked** publication comparison instead of duplicating the Builder-produced O108 S_CDC observations.

## Exact hosted evidence

Original complete source-bound run `40259605676`: https://github.com/FCMO-AI/.CMPCT/actions/runs/40259605676

Companion pull-request-triggered run `40259609077`: https://github.com/FCMO-AI/.CMPCT/actions/runs/40259609077

| Host | Tests | Ordinary successful replacement | Damaged-last-chunk refusal | Timeout | Skips / failures |
| --- | ---: | ---: | ---: | ---: | ---: |
| Ubuntu 24.04 | 14 | 12 | 2 | 0 | 0 |
| macOS 14 | 14 | 12 | 2 | 0 | 0 |
| **Total** | **28 PASS** | **24** | **4** | **0** | **0** |

Each host covered exactly seven destination arrangements for each of two storage kinds: fresh, regular, FIFO without reader, symlink→FIFO, symlink→external regular, hardlink to external regular, and corrupted physical *last* chunk with pre-existing regular leaf. All 28 subprocesses returned within the strict 7-second deadline.

The Linux 14 subprocess durations were 0.066730–0.075856 s (median across mixed cases 0.069052 s); macOS 0.061831–0.098533 s (median 0.074757 s). These are observational availability witnesses only — process startup is included, sample is tiny; **no create/extract performance credit**.

Independent fixed-vector fingerprints:
- `fixed.bin`: archive SHA-256 `cff02f4546171358fdf2498370bab0da014e25c23efae6fdf947c9b6307816e9`, logical SHA-256 `c2798f6e3c1590b2e87627cfc3652dddee29b1c4329e13dcdf0109c580be248a` (998 logical B, r24 kind 1).
- `cdc.bin`: archive SHA-256 `f862799c28f79d92123ee6311b4e0f726f6a50530d7caedfaca5b310179c47c7`, logical SHA-256 `e12c5f35853b8f6aa6caf7946e0525861f3ab0f8e0d4822879f0a1b735eb5f56` (1104 logical B, r24 kind 5).

Raw CI ZIPs, including full JUnit, installed import locations, source/blob SHAs, row-level observations and independent 14-case audits:
- Ubuntu artifact `12624570676`: https://github.com/FCMO-AI/.CMPCT/actions/runs/40259605676/artifacts/12624570676
- macOS artifact `12624361415`: https://github.com/FCMO-AI/.CMPCT/actions/runs/40259605676/artifacts/12624361415

The prospective checks established that both the Reader source and golden vector were the original Git blobs; CMPCT imported from independently installed `site-packages` rather than from the checkout. Python code paths and all test/evaluation expectations were preserved after preregistration. One evidence-strengthening revision removed a vacuous always-true file assertion; another required the corruption error to be a real codec/integrity refusal; a final revision moved corruption from the first chunk to the last, to exercise **partial** staging cleanup without changing the prerecorded kill condition.

## Architecture and inherited controls

The result makes a representation-dependent physical-ownership distinction explicit. For `S_CHUNKS`/`S_CDC`, successful extraction replaces an existing output leaf's directory entry. When that leaf was a hardlink, the outside existing inode retained its old contents and identity while the new output inode became independent; symlink external targets were likewise untouched. This is **not** preservation of the destination inode or original hardlink relationship. Direct-write storage descriptions have different semantics and can block on FIFO. A future unified Reader output policy must choose and prove the desired inode/alias contract deliberately, not treat all representations as equivalent.

The known neighboring Reader security owners remain #269, #472, #479; their branches were not modified and no simultaneous implementation claim was taken. J24F01 changes only its own new test, workflow and research records. No `src/`, native, format, release locks, tests from other PRs or frozen benchmarks are changed.

## Strongest negative / adversarial review

The original fixed archives contain only three small chunks each and the corrupt last-chunk test is a single-bit payload mutation, not a comprehensive malformed-r24 proof. Success cannot prove concurrent directory replacement safety, failure durability across sudden power loss, mmap SIGBUS resistance after external truncation, recoverability of all partial writes, physical reservation correctness on Windows, broad resource bounds, or runtime performance. Actual installed library Reader, not native C ABI, is measured.

Also, the staged strategy intentionally **breaks existing destination inode/hardlink relationships** on success; other paths may preserve them, so the codebase does not yet expose one universal output-identity contract. Do not count a positive staged-mode result as repair of confirmed direct-write FIFO issues. A corrupt-tail error on these fixtures proves no publication and clean temp removal, not transaction atomicity on an arbitrary filesystem.

## Discovery / counterfactual / transition

**Primary hypothesis:** staged S_CHUNKS shares S_CDC's POSIX FIFO nonblocking and external-leaf custody, using genuine independently-authored r24 archives — supported on two hosted POSIX systems. **Decision change:** the previously unmeasured fixed-chunk branch now has exact fixed-vector publication evidence, and the safe/unsafe Reader implementation boundary is better resolved. **Collision:** no same-question PR identified; neighboring Reader owners remain separate. **Counterfactual:** inspection of the common `_extract_chunked_verified` path was a cheap causal prediction, but did not prove installed fixed-archive behavior or partial-staging cleanup. **Discovery policy lesson:** none earned; `docs/discovery/STATE.json` deliberately unchanged.

**Next highest-leverage unclaimed product action:** the Reader owners should converge a single explicit output publication/admission contract across all representations and separately verify direct-write FIFO and TOCTOU repairs without destroying intended inode/hardlink semantics. Independently, gate material promotion on full exact-source CI and substantive official parity; no release requested by this evidence-only PR.
