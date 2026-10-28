<div align="center">
  <a href="https://fcmo-ai.github.io/.CMPCT/?lang=zh-Hant"><img src="../../.github/assets/repository-hero.svg" width="100%" alt="CMPCT — 傳統封存格式選擇了與妥協共處。CMPCT 沒有。"></a>

  **一個通用無損封存/容器專案，目標是在儲存位元組、選擇性存取、完整性、復原能力與可攜性上同時前進。**

  **[網站](https://fcmo-ai.github.io/.CMPCT/?lang=zh-Hant)** · **[瀏覽器實驗室](https://fcmo-ai.github.io/.CMPCT/?lang=zh-Hant#lab)** · **[基準測試](../BENCHMARKS.md)** · **[格式](../FORMAT.md)** · **[路線圖](../ROADMAP.md)** · **[代理入口](../CURRENT_STATE.md)**

  <sub>core v0.29.0 · 規範格式 r24 · surface 0.29.k · pre-1.0</sub>
</div>

> **策劃式翻譯。** 這是面向人類的 README 的版本化語義調整。英文 [`README.md`](../../README.md) 仍是規範權威。數字、路徑、格式名稱與證據邊界會刻意保持一致。在真正經過雙語人工審閱之前，本譯文不會標示為「人工審閱完成」。

---

> **效能就是發布契約。** 研究可以發現令人不舒服的權衡，但被提升為正式版本時不能把它藏起來：確定性的封存大小回歸 **0 位元組容忍**；在同一 Runner 上超出文件化雜訊範圍的已確認減速會阻止晉級；失敗 workload 會繼續作為公開證據保留。

## 為什麼需要 CMPCT

| | CMPCT 想改進什麼 |
|---|---|
| **儲存位元組** | 使用精確同一性、內容感知表示與受限關係重用，而不是把每個檔案都視為完全無關的位元組流。 |
| **選擇性存取** | 直接讀取所需物件或範圍，而不是強制解壓整個封存。 |
| **完整性 + 復原** | 把校驗、冗餘中繼資料和 salvage 路徑做成 reader 的真實行為，而不是 disaster-recovery 宣傳文字。 |
| **檔案系統保真** | 保留連結、sparse files、中繼資料與現代 update semantics。 |
| **互通性** | 把規範 reader/writer 契約、ZIP export、native core 與 portability gates 和實驗 grammar 分開。 |
| **證據品質** | 公開 claim 來自可重現的 committed record；失敗不刪；拒絕 benchmark theater。 |

CMPCT 不是「換了副檔名的 Zstd」，也不滿足於在一個手選目錄上獲勝。目標是一個在 **大小、速度、random access、保真度、完整性、復原、更新與現代 storage semantics** 上整體更強的預設封存格式，而不是把代價悄悄轉移到別處。

## 最新驗證前沿

**Project v0.29.0 — Mosaic / Residual Program Packing** 推進了已驗證的研究引擎，而正式交付的規範格式仍為 **revision 24**。

| v0.29 研究證據 | 結果 |
|---|---:|
| Portable inherited-frontier portfolio | **137,501,815 B** |
| Direct v0.28 base | 137,550,416 B |
| 精確節省 | **48,601 B (0.035333%)** |
| Portable workloads | **15** |
| 改善 / 回歸 | **2 / 0** |
| Exact v0.28 fallbacks | **13 / 15** |
| Hostile mechanism suites | **小 4.407362%**，18 個 workload 中 9 改善 / 0 回歸 |
| Fixed hostile scheduler | **182.454 s → 97.944 s 中位數 (-46.318%)**，所選封存 byte-identical |

在確定性的 resemblance-hostile 聚合（724 個檔案 / 93,526,384 位元組）上，採用的第 #5 次嘗試儲存 **47,147,764 B**。同一測試樹上：ZPAQ m5 47,062,639 B，solid tar+Zstd-19 47,065,652 B，7z/LZMA2 47,430,343 B，Borg 76,461,311 B，ZIP/Deflate-9 76,690,799 B。

這些是 **同條件儲存位元組比較，不是語義對等聲明**。solid archive、backup repository 與 CMPCT 具有不同 trade-off。長期記錄：[`docs/releases/v0.29.0.md`](../releases/v0.29.0.md)；machine-readable evidence：[`benchmarks/history/`](../../benchmarks/history/)。

### 正式交付 vs 研究前沿

| 權威 | 目前狀態 | 含義 |
|---|---|---|
| **規範 reader/writer** | **r24** | `python -m cmpct create` 實際寫出的內容，以及規範 reader 必須理解的契約。 |
| **研究前沿** | **CMPNX11 / v0.29.0** | 實驗性的 Mosaic + Residual Program Packing；不是 r24 語法。 |
| **公開 surface** | **0.29.k** | 僅表示 repo/site/docs 的展示版本，不改變封存語義。 |
| **授權** | **Apache-2.0 提案中** | 只是提案，不是最終公開授權。 |

## CMPCT 現在能做什麼

規範 r24 原型包括 content-addressed deduplication、adaptive Zstandard/raw storage、Zstd dictionaries 和 micro-solid packs、content-defined chunking、快速 byte-range reads 與 parallel decode、hardlink/symlink/sparse preservation、UID/GID/xattrs、ZIP/WHL virtualization、在有效時使用 lossless PCM-WAV、用於 ZIP export 的 raw Deflate reuse、CRC32 + SHA-256、冗餘 head/tail indexes、self-describing blob records、transaction append journal、on-demand ZIP export，以及可選的 reproducible/deterministic parallel creation。

v0.29 還研究 bounded FastCDC units、multi-band similarity search、depth-1 COPY/LITERAL deltas、multi-root Mosaic placement、Residual Program Packing、exact v0.28 fallback、locality/resource ceilings、透過 pinned memory-safe bridge 的 exact DEFLATE、Merkle-authenticated records、authenticated tail recovery、strict remote range sources 與 byte-identical parallel scheduling。

這些研究機制必須分別通過 format integration、conformance、hardening、native parity、recovery 和 portability，之後才可能進入規範 reader。

原則：**按內容選擇，不按副檔名迷信。**

## 快速開始

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

fresh-process CLI 在沒有 `--workers N` 時刻意保持 serial。v0.28 gate 在一個小 media tree 上量到約 10 ms 的 thread-pool startup 成本；in-process `Builder` 預設保留 deterministic parallel creation。

可選 native Linux chunker：

```bash
cc -O3 -shared -fPIC native/cmpct_cdc.c -o src/cmpct/libcmpct_cdc.so
```

reader **不依賴**此 helper；chunk 邊界會明確寫入磁碟。

## 效能位置

- **大小：** 相同 input + encoder semantics 不能產生更大封存；容忍 **0 位元組**。
- **create/extract：** base 與 candidate 在同一 runner 上用重複中位數測量；超出 noise envelope 的已確認 slowdown 阻止 release。
- **evidence：** 每個數字 core release 都提交新的公開 benchmark record。
- **corpora：** 失敗/adversarial workload 保持公開。

參見 [`docs/PERFORMANCE_RELEASE_GATE.md`](../PERFORMANCE_RELEASE_GATE.md) 與 [`docs/BREAKTHROUGH_REHABILITATION.md`](../BREAKTHROUGH_REHABILITATION.md)。

## 新代理閱讀順序

`docs/AGI_ENGINEERING_STANDARD.md` → `README.md` → `AGENTS.md` → `docs/CURRENT_STATE.md` → 最新 `docs/releases/` → `docs/PERFORMANCE_RELEASE_GATE.md` → `docs/BREAKTHROUGH_REHABILITATION.md` → `docs/FORMAT.md` → `docs/HISTORY.md` → EntropyGraph/Mosaic 文件 → `docs/HARDENING.md` → `docs/PORTABILITY.md` + `docs/NATIVE_CORE.md` → `docs/RESEARCH_LOG.md` → `docs/BENCHMARKS.md` + `benchmarks/history/` → `docs/PUBLIC_SURFACE.md` → `docs/ROADMAP.md`。

新代理不應依賴 private chat、private corpora 或 unrelated project context。

## Repository 地圖

`src/cmpct/` = 規範 r24 reference；`experiments/` = 研究譜系；`benchmarks/` = deterministic corpora/gates + `benchmarks/history/`；`fuzz/` = parser/resource 攻擊；`tools/check_*` = 契約檢查；`site/` = site + Browser Lab；`native/` = accelerators/shared core；`docs/` = contracts/campaigns/history/roadmap；`tests/` = format、round-trip、similarity、locality、reproducibility regressions。

## 網站

網站的設計順序是 **先產生衝擊，再證明 claim，最後贏得信任**。數字、競爭者、workload、失敗和 core status 都來自 versioned benchmark history。**研究前沿**、**規範對等**、**surface revision** 必須嚴格分開。視覺上可以激進，但不能捏造勝利。

**開啟：** https://fcmo-ai.github.io/.CMPCT/?lang=zh-Hant

## 版本紀律

1. **數字 core (`MAJOR.MINOR.PATCH`)** — 只獎勵實質產品進步；v0.27.1 之後常規進展移動 `MAJOR.MINOR`，為 packaging compatibility 保持 `PATCH=0`。
2. **Surface (`MAJOR.MINOR.LETTER`)** — site/docs/repo/workflow；目前 **`0.29.k`**。
3. **On-disk revision** — 僅在 reader 需要新 grammar/semantics 時變化；規範仍為 **r24**。

CI 將三條軸分開，並拒絕沒有證據的版本提升。

## 歷史、來源與公開 surface

CMPCT 從 Seekable-Zstd、indexed-Zstd、adaptive-framing 與 ZIP-family 實驗發展而來。技術歷史保留，但 private corpus identities、private artifacts 與 unrelated provenance 不進入公開記錄。公開 benchmark 必須可重現，或明確使用 public/synthetic input；歷史結果 **不是普遍效能保證**。

CMPCT 必須能獨立成立。repo/site 不得要求或暴露 unrelated internal project、private customer data、private corpora、personal information、chat transcripts、credentials、private artifact names 或 internal links。參見 `docs/PUBLIC_SURFACE.md`。

## 規範性

該 repository 取代 chat-local prototype 與 benchmark script。實質 engine/archive 進展獲得數字 release；site/docs/presentation 使用 `SURFACE_REVISION`；研究在 promotion 前保持明確 experimental。實驗程式碼在接入 reference reader/writer 與 conformance 前不能聲稱規範支援。

## 授權

Apache License 2.0 是 **目前建議授權**，尚未最終採用。文字：`LICENSE-APACHE-2.0-PROPOSED.txt`；adoption checklist：`LICENSING.md`。流程完成前，不得把 CMPCT 表述為已最終以 Apache-2.0 發布。
