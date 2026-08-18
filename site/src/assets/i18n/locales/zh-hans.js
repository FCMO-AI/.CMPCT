/* CMPCT curated Simplified Chinese adaptation pack — Surface 0.29.i.
   Footnote: one physical phrase line maps to one canonical English source phrase. Model-curated,
   source-controlled, no runtime translator, and not claimed human-reviewed. */
import { phraseBlock } from "../locale-pack.js";
export const PHRASE_VALUES = phraseBlock(`
跳到正文
CMPCT 首页
主导航
语言
性能
引擎
证据
实验室
代理视图
逻辑空间
物理根
性能前沿 · 直接来自已提交的基准测试
一种更好的文件打包方式。
传统归档格式选择了与妥协共处。
CMPCT 没有。
一个无损归档项目，旨在同时推进存储字节、选择性访问、精确同一性、完整性与恢复能力，并拒绝任何让已验证前沿倒退的发布。
查看数据
创建 .cmpct
看看它在哪里输 ↓
项目
重复次数
Runner
记录环境
界面层
规范格式
Build
当前同条件测试的核心结果
创建实际耗时
ZIP / DEFLATE
7Z / LZMA2
SOLID ZSTD-19
同条件结构比较
正在加载最新已提交的基准证据…
正在加载最新已提交的基准前沿…
证据回执 ↓
同条件存储字节
限定范围的调度器结果
无损
选择性访问
完整性
恢复
去重
受限解码
CMPCT 设计优先级
发布法则 / 01
大胆探索。无回归再晋级。
研究可以暴露权衡，发布不能掩盖它。确定性的归档大小回归：
允许 0 字节
超出同一 Runner 噪声范围的已确认速度回归：
发布阻止
性能门槛
01 / 竞技场
这不是压缩率。
这是性能位置。
结构竞技场只问一个明确的问题：对于同一棵敌对测试树，每种工具实际存了多少字节？访问、恢复和耐久性语义的差异必须保持标注，而不能被包装成虚假的功能对等。
存储字节 · 越少越好
逻辑输入
竞争者
归档大小比较
请正确理解：
在原始大小上输给 solid 压缩器，并不妨碍 CMPCT 同时拥有更强的选择性访问与恢复语义。本站保留这两个事实。
分类前沿 · SOLID ZSTD-19
每个 workload 在其精确测试树上独立生成的归档保留自身来源，不借用整套测试的总结果。
正在加载精确测试树的分类证据…
RED TEAM 看板
失败必须保持可见
基准测试的可信度来自被保留的失败，而不是一块全绿的仪表盘。
正在加载基准限定条件…
证据回执
公开账本
每个标题都携带对应的测试树、记录、范围与权威级别。主张越漂亮，来源就越应该容易核查。
格式
测试树
文件
记录
契约
网站原始数据 ↗
代理 JSON ↗
LLM 导览 ↗
基准历史 ↗
02 / 为什么它能赢
归档被编译成一个
信息图。
CMPCT 搜索所需对象之间的精确关系，选择物理根，并记录确定性的重建路径，同时明确保留局部性、完整性与恢复成本。
概念信息图
逻辑树
所需字节
精确数据流
共享结构
同一性
已去重对象
受限根
选择性解码
索引 + 证明
精确同一性
相同内容可以汇聚到一个经过认证的物理根，而不会合并彼此独立的逻辑路径。
关系感知存储
所需对象可以复用精确的压缩结构，而不必仅因文件名不同就支付重复存储成本。
选择性访问
直接读取所请求的对象，而不是把一次巨大的全归档解压变成获取有效字节的唯一途径。
受限上下文
跨文件上下文会被试验并受到约束，从而避免一次大小收益悄悄制造无限的读取工作。
完整性
索引与物理数据都带有明确校验；成功不等于“解压器没有报错”。
物理恢复
冗余且已认证的元数据以真实读取路径存在，而不是只写在文档里的 disaster recovery 承诺。
03 / 规范版 VS 前沿
一个项目。
两个权威级别。
研究前沿可以激进。规范 reader/writer 才是互操作契约。再漂亮的网站，也不能让研究表示借用规范版本的权威。
已交付 / 规范
reader / writer 契约
研究前沿
基准候选
公开证据
开放
所有主张来自已提交记录
04 / 规范 ZIP 执行对等测试
已交付 CMPCT vs ZIP。
大小、创建、解包。
在库调用和全新 CLI 进程边界上衡量规范 reader/writer 的运行对等性，并刻意与研究存储前沿分开。
已提交记录
语料集
归档大小
库内创建
库内解包
CLI 创建
CLI 解包
05 / 浏览器实验室
别再只看了。
自己做一个。
便携 writer 在本设备运行。文件不会上传。它只输出保守的规范子集；格式修订后宁可禁用，也不会猜测新语法。
正在检查规范兼容性…
writer 会根据 repository 的格式修订自动设置门槛。
创建
便携 CMPCT writer
本地
将文件拖到这里或选择文件
拖入文件或文件夹
无需上传数据即可创建字节完全一致的归档。
选择文件
选择文件夹
尚未选择文件。
创建 .cmpct
便携模式保留常规文件、路径索引、精确内容去重、SHA-256/CRC32 与 RAW/Deflate 存储。完整文件系统语义仍属于 CLI。
检查
头部透镜
不上传
只读取本地 CMPCT 归档的固定头部。完整结构验证仍由规范 reader 和 native core 负责。
选择 .cmpct 文件
Magic
版本字段
主索引
数据范围
06 / 发布轨迹
核心版本必须
配得上这个版本号。
只有 CMPCT 本身获得实质改进，数字版本才前进。界面修订可以变得截然更漂亮，但不能假装归档引擎发生了变化。
07 / 工程交接
外表漂亮。
底层也能查到底。
同一个让人类易于理解 CMPCT 的界面，也向代理暴露机器可读状态与持久工程证据。
机器可读的项目导览
公开证据与发布状态
代理阅读顺序与权威边界
Repository
Repository ↗
格式、基准、实现
性能不是截图，而是发布契约。
格式 ↗
基准 ↗
Pre-1.0 · 许可方案尚未正式采用 · 已提交的基准证据仍受其记录环境与语义条件限制。
CMPNX11 仅用于研究，规范 r24 reader 无法读取。
相较 v0.28，便携大小收益很小（48,601 B / 0.035333%），并集中在 15 个 workload 中的 2 个；其余 13 个 workload 有意进行完全一致的回退。
在修正 scheduling 之前，已接受的第 5 次便携组合使用了 v0.28 创建时间的 2.175x；任何 scheduler 速度主张都仅限于已测量的固定敌对聚合。
在同条件敌对结构聚合上，第 #5 次尝试小于 7z/LZMA2，但仍比 solid tar/Zstd-19 大 82,112 B，比 ZPAQ m5 大 85,125 B。
solid 归档竞争者具有不同的选择读取/恢复语义；这些行比较的是存储字节，不是功能对等。
CMPCT 在归档中保留 links/sparse/uid-gid/xattrs；该 Python ZIP baseline 会解引用 symlink，无法保留更丰富的文件系统语义。
已接受的 v0.29 研究前沿；规范 r24 不变
一棵确定性的 724 文件相似性敌对测试树；同一 run 的整树归档大小；与 solid 归档的语义差异保持明确
同条件已提交基准
研究前沿
CMPCT 研究前沿
研究基准候选
没有可用于研究前沿的已提交基准。
记录：
commit：
微小文件
源码
媒体
二进制
去重与链接
稀疏文件
嵌套
组合
开发 repository
办公工作区
媒体库
分析与数据库
日志与遥测
增量备份
不可压缩与类似加密
大量小文件
ML 制品
大型混合二进制
偏移版本
伪邻居
边界扰动
Deflate 系列
不可压缩
`);
export const MESSAGES = Object.freeze({
  files: "{n} 个文件", file: "{n} 个文件", logical: "逻辑 {bytes}", logicalInputFiles: "逻辑输入 {bytes} · {n} 个文件",
  smallerThan: "比 {name} 小 {pct}", largerThan: "比 {name} 大 {pct}", sameStored: "与 {name} 的存储字节相同", versus: "对比 {name}",
  cmpctSmaller: "CMPCT 更小 · 同条件存储字节", cmpctLarger: "CMPCT 更大 · 同条件存储字节", sameBytes: "存储字节相同", unavailableMatched: "无同条件存储字节",
  currentFrontier: "当前 CMPCT 研究前沿", categoryScore: "{wins}/{total} 更小 · {losses} 更大", noCategory: "无分类证据", noFreshCategory: "该前沿没有精确测试树上的最新分类证据。",
  comparisonUnavailable: "无法比较", noQualification: "该公开前沿没有记录任何基准限定条件。",
  heroIf: "如果 {name} 在这项同条件测试中存储 100 MB，CMPCT 约需 {value} MB。", heroNeeds: "在这项同条件测试中，{name} 每存储 100 MB，CMPCT 当前约需 {value} MB。",
  seriousBaseline: "严肃的大小基线：{relation}。", scopedScheduler: "限定范围的 scheduler 结果：在固定门槛测试中 wall time 降低 {pct}%。", canonicalRemains: "规范格式仍为 r{revision}。",
  frontierQualification: "{frontier} · 同条件结构树含 {files} 个文件。{serious}{speed} 规范格式仍为 r{revision}。", fixedSchedulerGate: "固定敌对 scheduler 门槛 · 不是全局速度主张", winsAgainst: "对 {name} 为 {wins}/{total} 胜",
  noCommittedParity: "无已提交对等记录", repetitionsMedian: "{n}× 中位数", semanticQualification: "语义限定：", interpretation: "解读：", currentProjectRelease: "当前项目版本", versionedMilestone: "版本化里程碑",
  writerVerified: "便携 writer 已针对规范 r{revision} 验证。", regularSubset: "仅支持常规文件子集；完整文件系统语义仍属于 CLI。", writerPaused: "格式修订 {revision} 后浏览器 writer 已暂停。", writerRefuses: "该 build 已针对 r{supported} 验证；不会猜测更新语法。",
  readyLocally: "本地就绪", cliOverLimit: "请使用 CLI：超出浏览器限制", input: "输入", archive: "归档", delta: "差值", smaller: "小 {bytes}", overhead: "{bytes} 额外开销", buildingLocally: "正在本地创建…", builtOnDevice: "已在本设备创建归档。",
  logicalFilesUnique: "{logical} 个逻辑文件 → {unique} 个唯一 blob · {deflate} Deflate / {raw} RAW。", saveCmpct: "保存 .cmpct", couldNotBuild: "无法创建归档。", fixedMagicError: "固定 Magic 看起来不是 CMPCT。", inspection: "检查", benchmarkUnavailable: "基准数据不可用：{error}", canonicalDataMissing: "未加载规范站点数据。"
});
