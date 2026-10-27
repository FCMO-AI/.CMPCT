# J24B05 — Signed hardlink alias-size guard: exact-hosted result

**Decision (2026-10-27 UTC):** **ACCEPT scoped candidate** for strict authenticated preflight: three hosted OS suites passed on product-code HEAD `f5b341cce87f9bc703a61c80428d8f855bd65f62`. **NO MERGE / NO RELEASE**. This result note is a subsequent **documentation-only** commit: rerun exact-head gates before claiming final-doc-HEAD green; do not attribute results of a later changed source to the earlier run.

## Lineage and immutable evidence

- Released floor: `main@80c358f8824ec1b20d349c92ed94c898090969b0`, CMPCT 0.30.0 / revision 24.
- Research defect: J24B04 [#610](https://github.com/FCMO-AI/.CMPCT/pull/610), authentic reauthenticated alias sizes 136/120/0 against 128-byte terminal owner accepted by published preflight/read/verify across three hosts.
- Strict memoized graph parent: [#342](https://github.com/FCMO-AI/.CMPCT/pull/342) `a480d7ae2f1480f15e73eda2b04e48b1a75e66b1`, parser blob `6c629ab504504a50fbbf8d1ae9e4cf0b31757a05`; its prior hosted chain/star ABBA showed **41.63×** 4096-chain speedup but ~6–7% star slowdown vs its own earlier predecessor.
- Preregistered question [J24B05](2026-10-27-j24b05-hardlink-alias-size-prereg.md) commit `68ce39203f28e55cd93c7b2b4dd483219c3f49a8` *before* validation source edits, real test, workflow and ABBA code.
- Product candidate: `src/cmpct/validation.py` blob `7261c7ec824259436dd90930722782bc04615281`, no Reader/Builder/native/format/codec/benchmark mutation.

## Source-identical hosted verdict

[Actions #40567116245](https://github.com/FCMO-AI/.CMPCT/actions/runs/40567116245) **SUCCESS, 3/3 hosts**, exact commit `f5b341cce87f9bc703a61c80428d8f855bd65f62`. Installed CMPCT via `pip install -e \".[test]\"` and pinned `git rev-parse HEAD`, validator blob. Each host ran unchanged inherited #342 source tests together with newly-authored Builder-independent signed-r24 mismatch controls:

| Host | Targeted pytest verdict | Genuine source identity |
| --- | --- | --- |
| Windows Server 2022 | **40 passed / 0 failed** (0.52 s) | pinned to HEAD |
| macOS 14 | **40 passed / 0 failed** (0.33 s) | pinned to HEAD |
| Ubuntu 24.04 | **40 passed / 0 failed** (0.35 s) | pinned to HEAD |

Total **120 targeted passes**; not full suite. Source logs/artifacts:

- Windows artifact [#12763512228](https://github.com/FCMO-AI/.CMPCT/actions/runs/40567116245/artifacts/12763512228), ZIP SHA-256 `ff6e873bc48da15167977d5965de0eabc284da34b78a83d3b286cb17ad70e827`.
- macOS artifact [#12762948318](https://github.com/FCMO-AI/.CMPCT/actions/runs/40567116245/artifacts/12762948318), ZIP SHA-256 `c04ef60e73c828d37a20c3f6389e7330000ab2183b06de66fea9cb8de86f651d`.
- Ubuntu artifact [#12762579564](https://github.com/FCMO-AI/.CMPCT/actions/runs/40567116245/artifacts/12762579564), ZIP SHA-256 `956a0be2032761baa0542576d6ea9526462180fe89fffa5cdb3b9733a5cd2c11`, includes raw ABBA JSON and process-independent Python allocation probe.

The artifact digests are as returned by GitHub's artifact API, not an independently downloaded ZIP rehash. The signed-wire test itself verifies primary and tail index commitments plus physical-byte identity, but the new suite is not a separately written full wire decoder; J24B04 supplies distinct original scientific evidence.

## Exact-parent same-archive ABBA (Ubuntu 24.04)

Historical exact `#342` parser is loaded from its committed Git blob. One identical physical authenticated r24 archive per shape is passed to both source versions; construction, fresh-process startup, materialization are **excluded**. Four A-B-B-A blocks = **8 raw measured invocations per source/shape**, raw nanoseconds in the Ubuntu JSON artifact.

| Aliases / shape | Parent median (ms) | Guard median (ms) | Guard / parent |
| --- | ---: | ---: | ---: |
| 512 chain | 2.418 | 2.451 | 1.013× |
| 512 star | 2.421 | 2.435 | 1.006× |
| 2048 chain | 9.092 | 9.199 | 1.012× |
| 2048 star | 8.933 | 9.138 | 1.023× |
| 4096 chain | 18.434 | 18.591 | 1.009× |
| 4096 star | 18.243 | 18.619 | 1.021× |

**Negative preserved:** the guard adds about **0.6–2.3%** measured preflight latency on these small/mid synthetic cases compared with the exact #342 memoized parent. The earlier star slowdown in #342 itself remains; neither is hidden. Raw observations and environmental identity remain attached. This is not a full cold Reader open / 4M-object / production CPU benchmark.

Separate `tracemalloc` 4096-chain probe: parent **3,049,986 B** peak, candidate **3,049,826 B** peak, residual 11,408 / 11,248 B respectively. **These are Python traced allocations, not RSS**; no claim of full process memory improvement.

## Causal scope and limitations

A hardlink alias's authenticated declared size must equal its ultimate **regular-file** owner size. The new guard evaluates that equality for each alias **during the existing memoized graph walk** using original index row objects; no extra walk and no new physical decode. Valid chain/star and reversed index permutations, size 128 control, hostile 136/120/0 and mismatched middle/outer alias, missing/indirect owners, cycles, symlink/directory terminals and inherited signed-tree constraints passed in the hosted targeted court.

**Important remaining defect:** this patch enforces strict **`preflight_archive` admission only**. Ordinary `CMPCT.read/read_range/verify` still delegate to target when called without structural preflight. It does not compose #609 direct S_BLOB guard, protect against #528 post-SHA inode substitution, solve #569 cold-open debt, or make a release. A coherent single authenticated Reader admission boundary is the ownership direction, not a second per-read traversal.

## Concurrency / promotion / policy

Child draft [#615](https://github.com/FCMO-AI/.CMPCT/pull/615) depends on memoized graph owner #342 (itself stacked on #339), and must not merge ahead of its parent. #610 remains research-only. #609 owns direct file/symlink guard; #569 owns Reader composition. No cross-owner file was changed. `docs/discovery/STATE.json` and discovery doctrine remain unchanged (stale cache; state reconciliation owned by #574). No process-policy lesson earned merely by one positive court.

Next decision: inspect new exact-head CI after this report commit; compare full/held-out Reader-open CPU/wall/RSS, source-identical star/chain at scale, and integrate this one invariant at the composed Reader's **same authenticated index admission** without repeating the traversal or weakening exact release and format gates.
