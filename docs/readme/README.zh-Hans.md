<div align="center">
  <a href="https://fcmo-ai.github.io/.CMPCT/?lang=zh-Hans"><img src="../../.github/assets/repository-hero.svg" width="100%" alt="CMPCT — 传统归档格式选择了与妥协共处。CMPCT 没有。"></a>

  **一个通用无损归档/容器项目，目标是在存储字节、选择性访问、完整性、恢复能力与可移植性上同时前进。**

  **[网站](https://fcmo-ai.github.io/.CMPCT/?lang=zh-Hans)** · **[浏览器实验室](https://fcmo-ai.github.io/.CMPCT/?lang=zh-Hans#lab)** · **[基准测试](../BENCHMARKS.md)** · **[格式](../FORMAT.md)** · **[路线图](../ROADMAP.md)** · **[代理入口](../CURRENT_STATE.md)**

  <sub>core v0.29.0 · 规范格式 r24 · surface 0.29.k · pre-1.0</sub>
</div>

> **人工策划式翻译。** 这是面向人类的 README 的版本化语义适配。英文 [`README.md`](../../README.md) 仍是规范权威。数字、路径、格式名称与证据边界会刻意保持一致。在真正经过双语人工审阅之前，本译文不会标注为“人工审阅完成”。

---

> **性能就是发布契约。** 研究可以发现令人不舒服的权衡，但被提升为正式版本时不能把它藏起来：确定性的归档大小回归 **0 字节容忍**；在同一 Runner 上超出文档化噪声范围的已确认减速会阻止晋级；失败 workload 继续作为公开证据保留。

## 为什么需要 CMPCT

| | CMPCT 想改进什么 |
|---|---|
| **存储字节** | 使用精确同一性、内容感知表示与受限关系复用，而不是把每个文件都视为完全无关的字节流。 |
| **选择性访问** | 直接读取所需对象或范围，而不是强制解压整个归档。 |
| **完整性 + 恢复** | 把校验、冗余元数据和 salvage 路径做成 reader 的真实行为，而不是 disaster-recovery 宣传文字。 |
| **文件系统保真** | 保留链接、sparse files、元数据与现代 update semantics。 |
| **互操作性** | 把规范 reader/writer 契约、ZIP export、native core 与 portability gates 和实验 grammar 分开。 |
| **证据质量** | 公开 claim 来自可复现的 committed record；失败不删；拒绝 benchmark theater。 |

CMPCT 不是“换了扩展名的 Zstd”，也不满足于在一个手选目录上获胜。目标是一个在 **大小、速度、random access、保真度、完整性、恢复、更新与现代 storage semantics** 上整体更强的默认归档格式，而不是把代价悄悄转移到别处。

## 最新验证前沿

**Project v0.29.0 — Mosaic / Residual Program Packing** 推进了已经验证的研究引擎，而正式交付的规范格式仍为 **revision 24**。

| v0.29 研究证据 | 结果 |
|---|---:|
| Portable inherited-frontier portfolio | **137,501,815 B** |
| Direct v0.28 base | 137,550,416 B |
| 精确节省 | **48,601 B (0.035333%)** |
| Portable workloads | **15** |
| 改善 / 回归 | **2 / 0** |
| Exact v0.28 fallbacks | **13 / 15** |
| Hostile mechanism suites | **小 4.407362%**，18 个 workload 中 9 改善 / 0 回归 |
| Fixed hostile scheduler | **182.454 s → 97.944 s 中位数 (-46.318%)**，所选归档 byte-identical |

在确定性的 resemblance-hostile 聚合（724 个文件 / 93,526,384 字节）上，采用的第 #5 次尝试存储 **47,147,764 B**。同一测试树上：ZPAQ m5 47,062,639 B，solid tar+Zstd-19 47,065,652 B，7z/LZMA2 47,430,343 B，Borg 76,461,311 B，ZIP/Deflate-9 76,690,799 B。

这些是 **同条件存储字节比较，不是语义对等声明**。solid archive、backup repository 与 CMPCT 具有不同 trade-off。长期记录：[`docs/releases/v0.29.0.md`](../releases/v0.29.0.md)；machine-readable evidence：[`benchmarks/history/`](../../benchmarks/history/)。

### 正式交付 vs 研究前沿

| 权威 | 当前状态 | 含义 |
|---|---|---|
| **规范 reader/writer** | **r24** | `python -m cmpct create` 实际写出的内容，以及规范 reader 必须理解的契约。 |
| **研究前沿** | **CMPNX11 / v0.29.0** | 实验性的 Mosaic + Residual Program Packing；不是 r24 语法。 |
| **公开 surface** | **0.29.k** | 仅表示 repo/site/docs 的展示版本，不改变归档语义。 |
| **许可证** | **Apache-2.0 提案中** | 只是提案，不是最终公开授权。 |

## CMPCT 现在能做什么

规范 r24 原型包括 content-addressed deduplication、adaptive Zstandard/raw storage、Zstd dictionaries 和 micro-solid packs、content-defined chunking、快速 byte-range reads 与 parallel decode、hardlink/symlink/sparse preservation、UID/GID/xattrs、ZIP/WHL virtualization、在有效时使用 lossless PCM-WAV、用于 ZIP export 的 raw Deflate reuse、CRC32 + SHA-256、冗余 head/tail indexes、self-describing blob records、transaction append journal、on-demand ZIP export，以及可选的 reproducible/deterministic parallel creation。

v0.29 还研究 bounded FastCDC units、multi-band similarity search、depth-1 COPY/LITERAL deltas、multi-root Mosaic placement、Residual Program Packing、exact v0.28 fallback、locality/resource ceilings、通过 pinned memory-safe bridge 的 exact DEFLATE、Merkle-authenticated records、authenticated tail recovery、strict remote range sources 与 byte-identical parallel scheduling。

这些研究机制必须分别通过 format integration、conformance、hardening、native parity、recovery 和 portability，之后才可能进入规范 reader。

原则：**按内容选择，不按扩展名迷信。**

## 快速开始

```bash
python -m pip install -e .
python -m cmpct create ./folder archive.cmpct
python -m cmpct create ./folder reproducible.cmpct --reproducible
python -m cmpct create ./large-folder parallel.cmpct --workers 8
python -m cmpct info archive.cmpct
python -m cmpct list archive.cmpct
python -m cmpct verify archive.cmpct
python -m cmpct extract archive.cmpct ./restored
python -m cmpct range archive.cmpct path/to/huge.bin 1048576 4096 -o slice.bin
python -m cmpct export-zip archive.cmpct legacy.zip
```

fresh-process CLI 在没有 `--workers N` 时故意保持 serial。v0.28 gate 在一个小 media tree 上测得约 10 ms 的 thread-pool startup 成本；in-process `Builder` 默认保留 deterministic parallel creation。

可选 native Linux chunker：

```bash
cc -O3 -shared -fPIC native/cmpct_cdc.c -o src/cmpct/libcmpct_cdc.so
```

reader **不依赖**此 helper；chunk 边界会明确写入磁盘。

## 性能位置

- **大小：** 相同 input + encoder semantics 不能产生更大归档；容忍 **0 字节**。
- **create/extract：** base 与 candidate 在同一 runner 上用重复中位数测量；超出 noise envelope 的已确认 slowdown 阻止 release。
- **evidence：** 每个数字 core release 都提交新的公开 benchmark record。
- **corpora：** 失败/adversarial workload 保持公开。

参见 [`docs/PERFORMANCE_RELEASE_GATE.md`](../PERFORMANCE_RELEASE_GATE.md) 与 [`docs/BREAKTHROUGH_REHABILITATION.md`](../BREAKTHROUGH_REHABILITATION.md)。

## 新代理阅读顺序

`docs/AGI_ENGINEERING_STANDARD.md` → `README.md` → `AGENTS.md` → `docs/CURRENT_STATE.md` → 最新 `docs/releases/` → `docs/PERFORMANCE_RELEASE_GATE.md` → `docs/BREAKTHROUGH_REHABILITATION.md` → `docs/FORMAT.md` → `docs/HISTORY.md` → EntropyGraph/Mosaic 文档 → `docs/HARDENING.md` → `docs/PORTABILITY.md` + `docs/NATIVE_CORE.md` → `docs/RESEARCH_LOG.md` → `docs/BENCHMARKS.md` + `benchmarks/history/` → `docs/PUBLIC_SURFACE.md` → `docs/ROADMAP.md`。

新代理不应依赖 private chat、private corpora 或 unrelated project context。

## Repository 地图

`src/cmpct/` = 规范 r24 reference；`experiments/` = 研究谱系；`benchmarks/` = deterministic corpora/gates + `benchmarks/history/`；`fuzz/` = parser/resource 攻击；`tools/check_*` = 契约检查；`site/` = site + Browser Lab；`native/` = accelerators/shared core；`docs/` = contracts/campaigns/history/roadmap；`tests/` = format、round-trip、similarity、locality、reproducibility regressions。

## 网站

网站的设计顺序是 **先产生冲击，再证明 claim，最后赢得信任**。数字、竞争者、workload、失败和 core status 都来自 versioned benchmark history。**研究前沿**、**规范对等**、**surface revision** 必须严格分开。视觉上可以激进，但不能捏造胜利。

**打开：** https://fcmo-ai.github.io/.CMPCT/?lang=zh-Hans

## 版本纪律

1. **数字 core (`MAJOR.MINOR.PATCH`)** — 只奖励实质产品进步；v0.27.1 之后常规进展移动 `MAJOR.MINOR`，为 packaging compatibility 保持 `PATCH=0`。
2. **Surface (`MAJOR.MINOR.LETTER`)** — site/docs/repo/workflow；当前 **`0.29.k`**。
3. **On-disk revision** — 仅在 reader 需要新 grammar/semantics 时变化；规范仍为 **r24**。

CI 将三条轴分开，并拒绝没有证据的版本提升。

## 历史、来源与公开 surface

CMPCT 从 Seekable-Zstd、indexed-Zstd、adaptive-framing 与 ZIP-family 实验发展而来。技术历史保留，但 private corpus identities、private artifacts 与 unrelated provenance 不进入公开记录。公开 benchmark 必须可复现，或明确使用 public/synthetic input；历史结果 **不是普遍性能保证**。

CMPCT 必须能独立成立。repo/site 不得要求或暴露 unrelated internal project、private customer data、private corpora、personal information、chat transcripts、credentials、private artifact names 或 internal links。参见 `docs/PUBLIC_SURFACE.md`。

## 规范性

该 repository 取代 chat-local prototype 与 benchmark script。实质 engine/archive 进展获得数字 release；site/docs/presentation 使用 `SURFACE_REVISION`；研究在 promotion 前保持明确 experimental。实验代码在接入 reference reader/writer 与 conformance 前不能声称规范支持。

## 许可证

Apache License 2.0 是 **当前建议许可证**，尚未最终采用。文本：`LICENSE-APACHE-2.0-PROPOSED.txt`；adoption checklist：`LICENSING.md`。流程完成前，不得把 CMPCT 表述为已最终以 Apache-2.0 发布。
