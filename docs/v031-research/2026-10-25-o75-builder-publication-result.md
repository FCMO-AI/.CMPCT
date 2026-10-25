# O75 — Builder output publication: authenticated three-host result

2026-10-25 UTC. Research/product-correctness candidate only. **No release or merge credit.**

## Frozen question and exact source custody

- Original hypothesis/preregistration **before implementation**: `0e2713874c15c455d30c31c3a6f64a2856360bce`, `docs/v031-research/2026-10-25-o75-builder-publication-prereg.md`. This file is unchanged.
- Canonical base: `agent/v031-development@4545d7d5b2a0b712b4b00f5a9c291d4a3a9e169b`; original Builder Git blob `663ef0922992b1fbb8f19e6eea88d55c10a56044`.
- Modified Builder blob: `d92c78119e9613b2c3ae1886a8fba841dc313fca`.
- **Actual result-bearing installed-product HEAD:** `3e75c2de6a3414cc1ad19cc739d52ce379ec47d5`. Original [hosted GitHub Actions run 40185137862](https://github.com/FCMO-AI/.CMPCT/actions/runs/40185137862): **3/3 success**, Ubuntu 24.04 job `121144225242`, macOS 14 job `121144225423`, Windows 2025 job `121144225376`. The workflow verifies the exact PR HEAD, immutable base Builder blob, preregistration ancestry and installation from the real package, not source-tree import.
- Raw durable original artifacts: Ubuntu `12596111222` SHA-256 `ff4aa1ee81ab34ca319911067ff7987201e87beddf37d11d638a7072b8b1a85a`; macOS `12596026297` SHA-256 `89daf0d2fb7e61bc6de560a2ed309f41c3d44668d3b90bd79abe919eba3f237b`; Windows `12595791876` SHA-256 `8b7558ab4e62749a0e3a102d6a17b1dae87e36df7c3310992b51bf5319e70ccf`.

## Original-source negative and candidate controls

A successful authentic old Builder created and the real Reader strongly verified archive **A**, before the test modified the physical input to **B**.

| Observation | Ubuntu 24.04 | macOS 14 | Windows 2025 |
| --- | ---: | ---: | ---: |
| Healthy archive A before injected old final-write I/O failure | 1,059 B | 1,059 B | 1,057 B |
| Archive remaining after historical torn write | **41 B** | **41 B** | **41 B** |
| Previously verified A still usable after original error? | **NO** | **NO** | **NO** |
| Candidate failure after deliberate partial staged `os.write` | Old A preserved | Old A preserved | Old A preserved |
| Candidate failure at deliberate `os.replace` | Old A preserved | Old A preserved | Old A preserved |
| Orphan temporary files after both candidate failures | 0 | 0 | 0 |
| Full candidate B CMPCT archive length | 1,065 B | 1,065 B | 1,065 B |
| Candidate B complete bytes vs authentic historical Builder on *same host* | **IDENTICAL** | **IDENTICAL** | **IDENTICAL** |
| Actual installed Reader `verify()` and member reads | PASS | PASS | PASS |
| Fresh output mode matches historical | 0644 | 0644 | 0666 |

The historical negative is *not* merely source inspection: the instrument executes the **actual original Builder Git blob** as a separate Python module and patches only its final write with a controlled torn 41-byte write plus `OSError`. For candidate, patching the real OS write produces one short write and one injected error; the real candidate stages through the temp path and preserves A. A second candidate control injects `OSError` in `os.replace`. Both failures leave original exact archive SHA unchanged and no staging leftovers. Normal candidate B was compared as a **complete artifact**, not merely decompressed member hashes, and verified with real Reader.

Ubuntu/macOS candidate B archive SHA-256: `ae831575d8359c0cbd08534472d9f9c0dc2c1cdeb814b5fe5aa024fe6aec99b8`. Windows on its own same-host control: `8907f5bd27fbd8de936b383ac538fb0e266585c53677bc650b9d43e43f3bcc2f`. **No cross-host reproducible archive identity claim.** The preceding canonical cross-host reproducibility investigations remain independent.

## Price: raw same-process/cached-wall A/B (research only)

Both implementations were built five times each on the same local synthetic tree, no process startup, warm cache and sequential paired order. Raw ns follow; medians are descriptive and **not** a statistical release/ABBA performance judgment:

| Host | Historical five wall times (ns) | Staged five wall times (ns) | Historical median | Staged median | Delta |
| --- | --- | --- | ---: | ---: | ---: |
| Ubuntu | 380688, 361247, 378268, 379192, 345750 | 410062, 370541, 376589, 387424, 392742 | 0.378268 ms | 0.387424 ms | **+0.009156 ms / +2.42%** |
| macOS | 431792, 426375, 499584, 341583, 443583 | 2335417, 477583, 535584, 548500, 405000 | 0.431792 ms | 0.535584 ms | **+0.103792 ms / +24.04%** |
| Windows | 1283100, 1266400, 1256300, 1299800, 1481500 | 1729000, 1750700, 1753500, 1792700, 1812400 | 1.283100 ms | 1.753500 ms | **+0.470400 ms / +36.66%** |

These sub-millisecond absolute costs are large *relative* to the toy baseline, especially on Windows. The macOS staged run has a 2.335417 ms outlier. **This is measurable overhead, not a free improvement.** No create CPU, RSS, cold whole-system benchmark, temporary write syscall tracing, I/O bandwidth, official same-runner direct-base ABBA or multi-size gate was completed here. **Do not claim performance pass** even when the unrelated administrative r24/ZIP workflow has a green label.

Staging temporarily materializes **one complete additional archive**: on this example 1,065 B of candidate data before publish while A still occupies 1,059/1,057 B. It also pays temporary O_EXCL open, close, potential fchmod and replacement. Extra Python payload copy is not required beyond the existing full archive `payload`.

## Strongest adverse semantic caveats

- **Process-level I/O exception atomicity only.** `os.replace` does not guarantee persistence after sudden power loss. No `fsync(temp)` or `fsync(parent-directory)` guarantees were added.
- A previous output inode is *replaced*, rather than written in place. **Hardlinks to the destination will continue referring to the former archive**; legacy direct overwrite changed all aliases. Open file descriptors refer to the old inode. This is a behavioral contract decision, not a free win.
- An existing destination symlink leaf will be replaced rather than followed; that is safer against accidental following, but different compatibility semantics. Any dangerous symlink-parent or concurrent namespace swap requires separately owned path-safety work.
- On Windows, replacing a target that is currently open may fail under share modes where a direct write could proceed.
- No concurrent output-writer serialization, race-safe source snapshot, ACL preservation, network filesystem rename guarantee or disk-full/power-loss simulation has been established.
- These limitations and significant tiny-file performance debt prevent automatic promotion.

## CI/routing negatives and follow-up

The initial exact-head fast topology gate **failed** because this new automatic fast-workflow had `cancel-in-progress: false`. Hosted source-specific gate itself passed; engineering evidence, native core, fuzzing, version discipline and R36 were green. CI topology's legitimate policy requires fast jobs to use `cancel-in-progress: true` unless covered by the narrow deep/release receipt exception. A later isolated workflow-only commit `d8d1ea1de95a7d9f296e8a1fc40d7a79c5eab208` corrected the classifier source without modifying the product, test, historical source or raw original scientific measurements. **New final-head CI must be checked independently**; old red must remain visible.

The administrative r24/ZIP workflow was green on result-bearing HEAD but its **substantive performance job was SKIPPED** under the known latest-commit classifier. The generic test suite was still running at the previous observation; never mark it green before seeing its final state.

## Scientific decision / counterfactual

**Confirmed:** the original final `write_bytes` output path can corrupt a previously valid archive under an injected late I/O error; a same-parent staged publication prevents that specific destruction with identical valid output bytes in all three hosted environments. A complete self-contained archive and recovery are valuable only if previous valid results survive failed creation.

**Narrowed:** result is scoped to process-level errors, same-host file semantics, and bounded source fixtures. It says nothing positive about true power-failure durability, output inode alias compatibility or whole-product performance.

**Cheapest discriminating observation:** the original implementation's destructive open mode together with an authentic partial-write injection, not a new encoder/codec or larger frozen benchmark. The source-faithful A/B isolated publishing as the causal owner.

**Next actionable promotion fork:** first review intended semantics for destination inode aliases, symlink leaves and permissions; then run frozen direct-base whole-product timing/CPU/RSS/temp-I/O across representative small/large cases on exact code, keeping all release comparators unchanged. Only if that economic and correctness burden is acceptable should the legitimate integration owner consider merging a staged publishing contract. Alternatively keep direct Builder semantics and require caller-owned staging explicitly. No Discovery Engine policy, shared state, format or release status change justified by this single new result.
