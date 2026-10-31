# J24I74 — physical signed mixed-journal import-cone transfer, exact-source result

Date: 2026-10-31 UTC. **PASS FOR THE PRESPECIFIED THREE-HOST SCIENTIFIC QUESTION; PRODUCT/RELEASE CREDIT ZERO.** The released truth remains CMPCT v0.30.0, revision-24 on `main@80c358f8824ec1b20d349c92ed94c898090969b0`.

## Source and prospective custody

- Frozen original hypothesis preregistered at commit `42c396eafc26ab5cc6f59b195bf27213037f646b`, before test, CI, and physical results. It inherits #878 (`a6695ba86d6a5b20eaced4eb8b54768f00724c9b`) with **no alterations** to the five algorithm ASTs, Reader/Writer, official evaluator or format.
- Original scientific test HEAD `3983914edf0bf94a023d5f19157ec262f4e1d577`: [Actions #41166007245](https://github.com/FCMO-AI/.CMPCT/actions/runs/41166007245), **3/3 actual host jobs SUCCESS**, physical archive + raw measurements and original no-CMPCT referee **9/9 adversarial challenges per host**.
- Stronger referee code HEAD `e17807e30d4140f607292e9cd5c6566c66801485`: [Actions #41166227766](https://github.com/FCMO-AI/.CMPCT/actions/runs/41166227766), **3/3 actual host jobs SUCCESS**. It added independent decoding of every one of 118 final member bodies from signed CMA4 physical data on each host, checked SHA-256 and CRC32, verified all replayed names and rejected a fully self-consistent forged member SHA receipt. **10/10 adversarial challenges per host**, source HEAD explicit in every receipt.
- First-head Engineering Evidence failed because PR template headings were missing; a second PR-body validation failed for absent `disproof` and `quality-ratchet` markers. Both were corrected in PR text without modifying evaluator rules. On the stronger code SHA, Engineering Evidence, CI Topology, R36, Version Discipline and Darwin xattr controls are **SUCCESS**. The final General Tests status must be inspected independently; neither specialized PASS nor administrative workflow SUCCESS can waive a red.
- Nothing here merges, releases, changes the compression engine, changes format/ABI, relaxes benchmark gates, or claims general arbitrary-filesystem coverage.

## Observed genuine output and scope

Each actual runner used the original public Builder to create 128 files and the real public Writer APIs to generate **21 RENAME + 21 DELETE + 21 PUT** signed deltas, giving **118 final regular-file members** and 64 authenticated generations (root + 63 operations). Every host independently ran the released public Reader, original experimental Owned Reader and exact-function-AST minimal import-cone Owned Reader against the **same actual physical archive bytes on that host**. The three classes agreed on full MessagePack index bytes, 118 member content SHA-256s, complete verify, extraction, public preflight, metadata record count and two tail damage recoveries to depth 62; impossible short format was rejected.

| Actual host | Physical CMPCT bytes | Public Reader open median | Minimal Owned open median | Ratio public/minimal | Original Owned median | Writer total wall |
|---|---:|---:|---:|---:|---:|---:|
| Ubuntu 24.04 | 29,040 | 2.0015 ms | 0.5577 ms | **3.589x** | 0.5559 ms | 123.85 ms |
| macOS 15 | 29,212 | 2.7714 ms | 0.6558 ms | **4.226x** | 0.7111 ms | 238.90 ms |
| Windows 2022 | 28,080 | 3.1888 ms | 1.0196 ms | **3.128x** | 1.0033 ms | 998.52 ms |

These are **six in-process warmed constructor observations per class per host**, not cold-interpreter, independent-process, stable production latency or full CLI performance. With both research classes already imported, the minimal module does **not** show a reliable warmed advantage over the original (Ubuntu 0.5577 vs 0.5559ms; macOS 0.6558 vs 0.7111ms; Windows 1.0196 vs 1.0033ms). The import-cost savings were established separately by #878 and cannot be inferred from this mixed-file court. The extra physical bytes across hosts include filesystem metadata and xattr differences; these are not same-input compression comparisons.

**Sparse xattrs:** real set/read/restore/extract `require_xattrs=True` on Ubuntu and macOS passed, including expected three surviving tagged paths `f0064.dat`, `f0100.dat`, `r0000.dat`. Windows executed the same 63 mixed public Writer operations **without physical xattrs**. No claim of Windows physical-xattr support.

**Memory and CPU negatives:** Python-traced peak on Ubuntu is minimal 141,939 B, original 142,059 B, public 141,813 B. On macOS minimal 142,317 B, original 142,437 B, public 142,167 B; Windows minimal 143,710 B, original 143,830 B, public 142,990 B. The small candidate overhead vs public is **not a memory Pareto win**. Windows `process_time_ns` displayed zero for sub-ms observations, so CPU speedup on that host is **unmeasured**, not zero cost.

## Original provider artifact custody and independent replay

The actual original provider artifacts on the stronger code SHA are immutable and provider-SHA-pinned:

| Host | Original Actions artifact | Original ZIP SHA-256 |
|---|---|---|
| Ubuntu | [#13029183674](https://github.com/FCMO-AI/.CMPCT/actions/runs/41166227766/artifacts/13029183674) | `7d9c7db0437112d3e63aa7abf198c2bb80210aeffa8188177b382e3c803151ec` |
| macOS | [#13028438122](https://github.com/FCMO-AI/.CMPCT/actions/runs/41166227766/artifacts/13028438122) | `d7d465f806b36c5f8aad8ea59de9c575f2522d4fdd2279ebe0e089054d917a2b` |
| Windows | [#13028937778](https://github.com/FCMO-AI/.CMPCT/actions/runs/41166227766/artifacts/13028937778) | `c0c763c1f35e393af1621daa5f164bc5b6b5a0184e4ff2545e6fd78a7831aa77` |

A **separate offline Python+ctypes/libzstd+msgpack interpreter** was applied to the three downloaded original ZIPs, without importing CMPCT or relying on its measured Reader. It independently verified all **192 SHA-authenticated footer payloads**, decoded and checked SHA-256/CRC32 for **447/447 physical CMA4 blob records** (including superseded/deleted original objects), reconstituted all **354 final member body SHA-256s** and compared against the actual Reader receipts, plus all 189 operation entries. Three additional differently rooted hostile alterations of original source/receipt bytes were rejected. The detached audit reports exactly those physical structures; it does not prove broader formats or physical xattr restoration from a replay host.

## Decision, collisions, counterfactual and debt

**Decision:** the unchanged minimal import-cone Owned Reader *survives* its first real mixed signed-journal/xattr/recovery transfer court on actual Ubuntu, macOS and Windows, in contrast to the earlier exclusively DELETE-only cold-process evidence. This is a material **scientific transfer/generalization result**, not authorization to ship the research subclass.

**Strongest opposing explanation:** the test uses one deterministic interleaving (RENAME → DELETE → PUT repeated), 128 original regular files, no hardlinks, no sparse extents, no hostile pointer rewires, no multiwriter CAS, no unpredictable path collisions, and only warm opens. The research Owned helper mutates decoded objects under exclusive private ownership; outside that boundary it is unsafe for retained aliases. These tests cannot establish a production Reader lifetime/ownership contract. The detached original SHA of the entire ZIP and CMA4 SHA are evidence of physical identity, not authenticated signer trust beyond revision-24 semantics.

**Prior art / owner coordination:** #823 owns Owned Reader product integration and large-N proof, #795/#817 own signed-journal/hardlink correctness, #853 owns DELETE-only lower-cost control, #875/#878 own cold process/import ablation, #574 owns shared Discovery STATE. This work used an isolated new research workflow/source pair and did not overwrite a competing branch, change shared state or modify policy.

**Counterfactual:** a single real mixed/positive sparse-xattr Writer fixture would have efficiently falsified an over-generalized DELETE-only import-ablation claim before modifying production Reader. This is useful as a **local evidence rung**; one positive observation does not justify changing discovery policy.

**Highest-leverage next target:** under the existing #823/#795 owners, test an actual minimized production Reader module with a public alias/lifetime contract on hardlinks, xattr ordinals and arbitrary mixed-operation patterns, then hostile truncation/pointer ancestry, installed native interoperability, RSS and full-product parity. A green isolated research court cannot waive the inherited General Tests and ZIP gate.
