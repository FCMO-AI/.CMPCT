/* CMPCT curated Traditional Chinese adaptation pack — Surface 0.29.i.
   Footnote: one physical phrase line maps to one canonical English source phrase. Model-curated,
   source-controlled, no runtime translator, and not claimed human-reviewed. */
import { phraseBlock } from "../locale-pack.js";
export const PHRASE_VALUES = phraseBlock(`
跳到正文
CMPCT 首頁
主導覽
語言
效能
引擎
證據
實驗室
代理檢視
邏輯空間
物理根
效能前沿 · 直接來自已提交的基準測試
一種更好的檔案封裝方式。
傳統封存格式選擇了與妥協共處。
CMPCT 沒有。
一個無損封存專案，旨在同時推進儲存位元組、選擇性存取、精確同一性、完整性與復原能力，並拒絕任何讓已驗證前沿倒退的發布。
查看數據
建立 .cmpct
看看它在哪裡輸 ↓
專案
重複次數
Runner
記錄環境
介面層
規範格式
Build
目前同條件測試的核心結果
建立實際耗時
ZIP / DEFLATE
7Z / LZMA2
SOLID ZSTD-19
同條件結構比較
正在載入最新已提交的基準證據…
正在載入最新已提交的基準前沿…
證據回執 ↓
同條件儲存位元組
限定範圍的排程器結果
無損
選擇性存取
完整性
復原
去重
受限解碼
CMPCT 設計優先級
發布法則 / 01
大膽探索。無回歸再晉級。
研究可以暴露權衡，發布不能掩蓋它。確定性的封存大小回歸：
允許 0 位元組
超出同一 Runner 雜訊範圍的已確認速度回歸：
發布阻止
效能門檻
01 / 競技場
這不是壓縮率。
這是效能位置。
結構競技場只問一個明確問題：對於同一棵敵對測試樹，每種工具實際儲存了多少位元組？存取、復原和耐久性語義的差異必須保持標註，而不能被包裝成虛假的功能對等。
儲存位元組 · 越少越好
邏輯輸入
競爭者
封存大小比較
請正確理解：
在原始大小上輸給 solid 壓縮器，並不妨礙 CMPCT 同時擁有更強的選擇性存取與復原語義。本站保留這兩個事實。
分類前沿 · SOLID ZSTD-19
每個 workload 在其精確測試樹上獨立產生的封存保留自身來源，不借用整套測試的總結果。
正在載入精確測試樹的分類證據…
RED TEAM 看板
失敗必須保持可見
基準測試的可信度來自被保留的失敗，而不是一塊全綠的儀表板。
正在載入基準限定條件…
證據回執
公開帳本
每個標題都攜帶對應的測試樹、記錄、範圍與權威級別。主張越漂亮，來源就越應該容易核查。
格式
測試樹
檔案
記錄
契約
網站原始資料 ↗
代理 JSON ↗
LLM 導覽 ↗
基準歷史 ↗
02 / 為什麼它能贏
封存被編譯成一個
資訊圖。
CMPCT 搜尋所需物件之間的精確關係，選擇物理根，並記錄確定性的重建路徑，同時明確保留局部性、完整性與復原成本。
概念資訊圖
邏輯樹
所需位元組
精確資料流
共享結構
同一性
已去重物件
受限根
選擇性解碼
索引 + 證明
完整性 / 復原
精確同一性
相同內容可以匯聚到一個經過認證的物理根，而不會合併彼此獨立的邏輯路徑。
關係感知儲存
所需物件可以重用精確的壓縮結構，而不必僅因檔名不同就支付重複儲存成本。
選擇性存取
直接讀取所要求的物件，而不是把一次巨大的全封存解壓變成取得有效位元組的唯一途徑。
受限上下文
跨檔案上下文會被試驗並受到約束，從而避免一次大小收益悄悄製造無限的讀取工作。
完整性
索引與物理資料都帶有明確校驗；成功不等於「解壓器沒有報錯」。
物理復原
冗餘且已認證的中繼資料以真實讀取路徑存在，而不是只寫在文件裡的 disaster recovery 承諾。
03 / 規範版 VS 前沿
一個專案。
兩個權威級別。
研究前沿可以激進。規範 reader/writer 才是互通契約。再漂亮的網站，也不能讓研究表示借用規範版本的權威。
已交付 / 規範
reader / writer 契約
研究前沿
基準候選
公開證據
開放
所有主張來自已提交記錄
04 / 規範 ZIP 執行對等測試
已交付 CMPCT vs ZIP。
大小、建立、解包。
在函式庫呼叫和全新 CLI 行程邊界上衡量規範 reader/writer 的運行對等性，並刻意與研究儲存前沿分開。
已提交記錄
語料集
封存大小
函式庫內建立
函式庫內解包
CLI 建立
CLI 解包
05 / 瀏覽器實驗室
別再只看了。
自己做一個。
可攜 writer 在本裝置執行。檔案不會上傳。它只輸出保守的規範子集；格式修訂後寧可停用，也不會猜測新語法。
正在檢查規範相容性…
writer 會根據 repository 的格式修訂自動設定門檻。
建立
可攜 CMPCT writer
本機
將檔案拖到這裡或選擇檔案
拖入檔案或資料夾
無需上傳資料即可建立位元組完全一致的封存。
選擇檔案
選擇資料夾
尚未選擇檔案。
建立 .cmpct
可攜模式保留一般檔案、路徑索引、精確內容去重、SHA-256/CRC32 與 RAW/Deflate 儲存。完整檔案系統語義仍屬於 CLI。
檢查
標頭透鏡
不上傳
只讀取本機 CMPCT 封存的固定標頭。完整結構驗證仍由規範 reader 與 native core 負責。
選擇 .cmpct 檔案
Magic
版本欄位
主索引
資料範圍
06 / 發布軌跡
核心版本必須
配得上這個版本號。
只有 CMPCT 本身獲得實質改進，數字版本才前進。介面修訂可以變得截然更漂亮，但不能假裝封存引擎發生了變化。
07 / 工程交接
外表漂亮。
底層也能查到底。
同一個讓人類易於理解 CMPCT 的介面，也向代理揭露機器可讀狀態與持久工程證據。
機器可讀的專案導覽
公開證據與發布狀態
代理閱讀順序與權威邊界
Repository
Repository ↗
格式、基準、實作
效能不是截圖，而是發布契約。
格式 ↗
基準 ↗
Pre-1.0 · 授權方案尚未正式採用 · 已提交的基準證據仍受其記錄環境與語義條件限制。
CMPNX11 僅用於研究，規範 r24 reader 無法讀取。
相較 v0.28，可攜大小收益很小（48,601 B / 0.035333%），並集中在 15 個 workload 中的 2 個；其餘 13 個 workload 有意進行完全一致的回退。
在修正 scheduling 之前，已接受的第 5 次可攜組合使用了 v0.28 建立時間的 2.175x；任何 scheduler 速度主張都僅限於已測量的固定敵對聚合。
在同條件敵對結構聚合上，第 #5 次嘗試小於 7z/LZMA2，但仍比 solid tar/Zstd-19 大 82,112 B，比 ZPAQ m5 大 85,125 B。
solid 封存競爭者具有不同的選擇讀取/復原語義；這些列比較的是儲存位元組，不是功能對等。
CMPCT 在封存中保留 links/sparse/uid-gid/xattrs；該 Python ZIP baseline 會解參照 symlink，無法保留更豐富的檔案系統語義。
已接受的 v0.29 研究前沿；規範 r24 不變
一棵確定性的 724 檔案相似性敵對測試樹；同一 run 的整樹封存大小；與 solid 封存的語義差異保持明確
同條件已提交基準
研究前沿
CMPCT 研究前沿
研究基準候選
沒有可用於研究前沿的已提交基準。
記錄：
commit：
微小檔案
原始碼
媒體
二進位
去重與連結
稀疏檔案
巢狀
組合
開發 repository
辦公工作區
媒體庫
分析與資料庫
日誌與遙測
增量備份
不可壓縮與類似加密
大量小檔案
ML 產物
大型混合二進位
位移版本
偽鄰居
邊界擾動
Deflate 系列
不可壓縮
`);
export const MESSAGES = Object.freeze({
  files: "{n} 個檔案", file: "{n} 個檔案", logical: "邏輯 {bytes}", logicalInputFiles: "邏輯輸入 {bytes} · {n} 個檔案",
  smallerThan: "比 {name} 小 {pct}", largerThan: "比 {name} 大 {pct}", sameStored: "與 {name} 的儲存位元組相同", versus: "對比 {name}",
  cmpctSmaller: "CMPCT 較小 · 同條件儲存位元組", cmpctLarger: "CMPCT 較大 · 同條件儲存位元組", sameBytes: "儲存位元組相同", unavailableMatched: "無同條件儲存位元組",
  currentFrontier: "目前 CMPCT 研究前沿", categoryScore: "{wins}/{total} 較小 · {losses} 較大", noCategory: "無分類證據", noFreshCategory: "該前沿沒有精確測試樹上的最新分類證據。",
  comparisonUnavailable: "無法比較", noQualification: "該公開前沿沒有記錄任何基準限定條件。",
  heroIf: "如果 {name} 在這項同條件測試中儲存 100 MB，CMPCT 約需 {value} MB。", heroNeeds: "在這項同條件測試中，{name} 每儲存 100 MB，CMPCT 目前約需 {value} MB。",
  seriousBaseline: "嚴肅的大小基準：{relation}。", scopedScheduler: "限定範圍的 scheduler 結果：在固定門檻測試中 wall time 降低 {pct}%。", canonicalRemains: "規範格式仍為 r{revision}。",
  frontierQualification: "{frontier} · 同條件結構樹含 {files} 個檔案。{serious}{speed} 規範格式仍為 r{revision}。", fixedSchedulerGate: "固定敵對 scheduler 門檻 · 不是全域速度主張", winsAgainst: "對 {name} 為 {wins}/{total} 勝",
  noCommittedParity: "無已提交對等記錄", repetitionsMedian: "{n}× 中位數", semanticQualification: "語義限定：", interpretation: "解讀：", currentProjectRelease: "目前專案版本", versionedMilestone: "版本化里程碑",
  writerVerified: "可攜 writer 已針對規範 r{revision} 驗證。", regularSubset: "僅支援一般檔案子集；完整檔案系統語義仍屬於 CLI。", writerPaused: "格式修訂 {revision} 後瀏覽器 writer 已暫停。", writerRefuses: "該 build 已針對 r{supported} 驗證；不會猜測更新語法。",
  readyLocally: "本機就緒", cliOverLimit: "請使用 CLI：超出瀏覽器限制", input: "輸入", archive: "封存", delta: "差值", smaller: "小 {bytes}", overhead: "{bytes} 額外開銷", buildingLocally: "正在本機建立…", builtOnDevice: "已在本裝置建立封存。",
  logicalFilesUnique: "{logical} 個邏輯檔案 → {unique} 個唯一 blob · {deflate} Deflate / {raw} RAW。", saveCmpct: "儲存 .cmpct", couldNotBuild: "無法建立封存。", fixedMagicError: "固定 Magic 看起來不是 CMPCT。", inspection: "檢查", benchmarkUnavailable: "基準資料不可用：{error}", canonicalDataMissing: "未載入規範網站資料。"
});
