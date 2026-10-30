# J24G67 result — one-time admitted sorted DELETE replay, physical Reader A/B

**2026-10-30 UTC. Decision: `SIMPLE_DELETE_BISECT_SURVIVES_RESEARCH_HURDLE` on 3/3 platforms. RESEARCH ONLY — no product source change, merge or release.** This is the prospective test in [J24G67 preregistration](2026-10-30-j24g67-delete-bisect-prereg.md), committed at `8b34b8a41cc890f0668fa944a245b80e6451dd3a` before the experiment, on inherited J24G63 [#805](https://github.com/FCMO-AI/.CMPCT/pull/805) source `7f509d244325d4b6ea6d0e752ea365f79c33a742`.

## Exact evidence and source custody

- Result-bearing experiment code HEAD: `f6068d405fefe0c6b457f9062d39578eb63e4847`, [Draft #811](https://github.com/FCMO-AI/.CMPCT/pull/811).
- Hosted original [Actions #41014070509](https://github.com/FCMO-AI/.CMPCT/actions/runs/41014070509): Ubuntu 24.04, macOS 14 and Windows 2022 **three jobs SUCCESS**. Source attestation requires exact Git blobs: replay `03743ca2a06c022c2ec64243a90fe373cf91e899`, Reader `29a8be64f3acfb027750351c6a567fd82cf7dc97`, Builder `a2160a2f6b1ca3ef8cd94897cb68bb2fcb74ebc2`, transactions `3eef7fdc3f6deca5ddd6d9edf1292c7e2c864f11`.
- Original artifact downloads and provider ZIP SHA-256: Ubuntu [#12959230175](https://github.com/FCMO-AI/.CMPCT/actions/runs/41014070509/artifacts/12959230175) `0868e729040c04d758edbb70a51420271c72d964bb275d68f95809a18ba40447`; macOS [#12959135410](https://github.com/FCMO-AI/.CMPCT/actions/runs/41014070509/artifacts/12959135410) `3ffedb97973ddeceb1c4e98daf992f3afacb0a9f14594d1c220adc29d7327479`; Windows [#12959305055](https://github.com/FCMO-AI/.CMPCT/actions/runs/41014070509/artifacts/12959305055) `f5e97b005d2866995d216861d20dd83f696040f0feac207614a4a15e5a592208`.
- The original three artifacts were **separately downloaded and re-examined after CI**, without CMPCT imports. Each ZIP SHA was checked against its GitHub-provided digest; raw sample SHA, source, branch/prereg identity, calculated medians and speedups, ABBA block structure, candidate eligibility counters, archive hash, stored bytes and semantic-index hash were reverified.
- A second independent physical archive inspector using only standard Python `struct/hashlib/msgpack` and the system `zstd` executable decoded each of 64 footer records, checked its SHA-256 digest, independently applied 63 genuine DEL operations, and reproduced the 2,048-row final MessagePack index SHA from the Reader receipt on each platform. It did **not** invoke CMPCT's Reader, footer scanner or journal replay. The checks were performed on the exact downloaded ZIP bytes, not regenerated fixture files.

## Prospective product-seam research result

One physical Builder + 63 public Writer `append_delete` operations, 2,111 initial files and 2,048 survivors. No extra checkpoint or rewritten physical archive. The prospective alternative preserves the existing sorted file rows, checks canonical sorted uniqueness once on first eligible delta, then applies each single DELETE using binary search and `list.pop`. It keeps **no retained name→row dictionary**. Non-single-DELETE, malformed, missing path, noncanonical rows or sparse per-file metadata disables the candidate and calls the unchanged original helper. The only change is a temporary research-process monkeypatch of the Reader's replay callback; **none of this is installed in the product**.

Eight alternating ABBA blocks on each host produced **32 uninstrumented Reader-open observations** per platform (16 control + 16 candidate). Python process startup/imports are outside these measurements; the operating system file cache is not necessarily cold.

| Host | Reference median Reader-open | Candidate median Reader-open | Saving | Same-host speedup | Frozen >=2x + >=3ms gate |
|---|---:|---:|---:|---:|---|
| Ubuntu | 58.904 ms | 3.823 ms | **55.082 ms** | **15.410x** | PASS |
| macOS | 47.536 ms | 2.929 ms | **44.608 ms** | **16.231x** | PASS |
| Windows | 65.216 ms | 4.411 ms | **60.805 ms** | **14.784x** | PASS |

The result exceeds the preregistered cross-host 2/3 hurdle on **3/3** systems, but **cannot** be translated into a 15x faster released Reader. This is a research-instrumented callback on an unmerged candidate path.

Every candidate replay recorded `optimized==63`, `fallback==0`, `admission_scans==1`. Every control/candidate opening returned the exact same per-host effective index MessagePack SHA, and the original Reader verified all 2,048 live members. The index and logical content were independently reconstructed from physical revision-24 footer bytes. Named adverse input tests: 12/12; deterministic sequences: 500; exact exception-class/message parity for malformed/future operations; no source argument mutation. On-host detached arithmetic and two receipt tamper tests also passed on 3/3 platforms.

Raw receipt JSON SHA-256 values: Ubuntu `9eeae4589c92809a0e44e76c05d1cbfb5d5597d1305fdba83b650d1603f85e1d`, macOS `84dee0dc0e5d5ccb60917a56623cc7d8cedfe6cde19d496f8d3a5f7ea577a08f`, Windows `3d345ba3278a93f3047f7ae3600adb3f927416f5cde7c2e2df255d050537e43b`.

## Independent contradictions and strongest self-critique

**Platform byte identities are not all identical.** Linux and macOS generated the same exact 300,548-byte CMPCT archive (SHA `a08faa4d6ea1d914f840e1e5335183e26c6eac3d14745ed5a1f3c57bf21a08ac`). Windows generated a different 300,548-byte archive (SHA `0e8cc78b46a937a0cddd46b6dd11007725542a4310d76a31323285e74d67aabe`). The independent decoded row comparison localized the divergence to platform mode: POSIX file mode **420 decimal = 0644** vs Windows **438 decimal = 0666**. The DEL operation path names and final live filename sets match. **Never claim a same-byte cross-host benchmark; each A/B is same-byte within its own host.**

The original artifact ZIPs had different provider hashes, as expected. macOS timing dispersion is larger than Linux/Windows, though every one of its eight alternating-block paired speedup ratios stayed >=13.49x. Windows CPU timing is coarse and the candidate median reported 0ms; therefore this is **not** proof of CPU-free replay. The decisive metric is wall time.

Only the **candidate** tracemalloc peak was recorded (1,349,046 B Ubuntu; 1,349,278 B macOS; 1,353,345 B Windows). No comparable baseline peak or platform RSS measurement exists. This is not a memory win. Admission for hardlink-inode/fsmeta metadata and mixed operations is intentionally refused, so broad cross-generation product generality is not established. The new `list.pop` still shifts trailing rows, so O(N) work remains; observed 15x does not mean constant-time operations. Model-sorted initial state is a strict precondition; malformed or unexpected transient state must fall back. The prior #808 mixed signed-fsmeta factoring work offers a broader alternative but is not a same-input/same-runner comparison with this outcome.

No direct measurement was made of cold-disk open, production Reader source after integration, release fingerprint, C/Rust ABI, peak RSS, creation/extraction CPU/wall, temporary I/O, selective read amplification, hardlink/xattr restoration, tail truncation or 64th-checkpoint recovery. No old/frozen benchmark or release threshold was changed.

## Decision and owner handoff

This simpler-control mechanism survives the **lower-rung research / Reader-monkeypatch** tribunal. Promote **only to an integration candidate, not to public product**. Reader owner [#795](https://github.com/FCMO-AI/.CMPCT/pull/795) must compare this with [#808](https://github.com/FCMO-AI/.CMPCT/pull/808)'s general mixed-operations factoring and [#810](https://github.com/FCMO-AI/.CMPCT/pull/810)'s physical signed-fsmeta court. It should keep a single shared authority for r24 replay and be allowed to choose the general mechanism if its broader applicability repays memory/complexity. This narrow path, if retained, must have explicit generic admission and zero change in file semantics or release gates.

The next cheapest decisive test is **same-source physical Reader A/B with both candidate paths** on the same 2,048-file DELETE archive plus a signed-xattr/hardlink mixed archive, with whole-system CPU/RSS and tail/64th checkpoint recovery. Either ordinary baseline may win; differences in produced archive bytes, file modes, owner metadata or Python runtime must be charged, never suppressed.

Discovery Engine: primary question changed from unexplained DELETE bottleneck to *simple eligible replay may remove most cost*. No claim collision: #808/#810 own mixed/xattr; this PR owns only the DELETE-only simple control. Counterfactual prospective discriminator: one-time sorted admission + binary-search/pop could have been attempted before a broad data structure rewrite, because #805/#809 already observed DELETE-only bottleneck; this is a local opportunity-cost lesson, not yet a justified global discovery-policy edit. `docs/discovery/STATE.json` remains untouched because #574 owns its stale global reconciliation. **Product/release credit 0.**
