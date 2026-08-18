/* CMPCT curated Japanese adaptation pack — Surface 0.29.i.
   Footnote: one physical phrase line maps to one canonical English source phrase. Model-curated,
   source-controlled, no runtime translator, and not claimed human-reviewed. */
import { phraseBlock } from "../locale-pack.js";
export const PHRASE_VALUES = phraseBlock(`
本文へ移動
CMPCT ホーム
メインナビゲーション
言語
性能
エンジン
証拠
ラボ
エージェント表示
論理空間
物理ルート
性能フロンティア · コミット済みベンチマークから直接表示
ファイルを、もっと賢く詰める。
従来のアーカイブ形式は妥協と折り合いをつけた。
CMPCT は違う。
保存バイト数、選択アクセス、完全一致の同一性、整合性、復旧性を同時に前進させ、検証済みフロンティアを後退させるリリースを拒むよう設計されたロスレスアーカイブプロジェクト。
数値を見る
.cmpct を作る
負けている場所を見る ↓
プロジェクト
反復回数
Runner
記録済み環境
サーフェス
正規フォーマット
Build
現在の同一条件テストの主要結果
作成ウォールタイム
ZIP / DEFLATE
7Z / LZMA2
SOLID ZSTD-19
同一条件の構造比較
最新のコミット済みベンチマーク証拠を読み込み中…
最新のコミット済みベンチマークフロンティアを読み込み中…
証拠レシート ↓
同一条件の保存バイト数
範囲限定スケジューラ結果
ロスレス
選択アクセス
整合性
復旧
重複排除
制限付きデコード
CMPCT の設計優先事項
リリース規律 / 01
大胆に発見する。回帰なしで昇格する。
研究ではトレードオフが見つかってよい。リリースがそれを隠すことは許されない。決定論的なアーカイブサイズ回帰:
許容 0 バイト
同一 runner のノイズ範囲外で確認された速度回帰:
リリース停止
性能ゲート
01 / アリーナ
圧縮率の話ではない。
性能上の位置だ。
構造アリーナが問うのは一つだけ。同じ敵対的ツリーを各ツールが何バイトで保存したか。アクセス、復旧、耐久性の意味論の違いは、偽の同等性に洗い替えず明示する。
保存バイト · 少ないほど良い
論理入力
競合
アーカイブサイズ比較
正しく読む:
solid 圧縮に生サイズで負けても、選択アクセスや復旧の意味論が強いことは両立する。このサイトは両方の事実を残す。
カテゴリ別フロンティア · SOLID ZSTD-19
各 workload の正確なツリーで独立作成したアーカイブは、全体スイートの結果を借りず、それぞれの来歴を保持する。
正確なツリーのカテゴリ証拠を読み込み中…
RED TEAM ボード
敗北は隠さない
ベンチマークの信頼性は、完璧に緑のダッシュボードではなく、失敗を残すことから生まれる。
ベンチマーク条件を読み込み中…
証拠レシート
オープンブック
すべての見出しに、ツリー、記録、範囲、権威レベルを結び付ける。主張が魅力的になるほど、出典は簡単に検査できなければならない。
フォーマット
ツリー
ファイル
記録
契約
サイト生データ ↗
エージェント JSON ↗
LLM ガイド ↗
ベンチマーク履歴 ↗
02 / なぜ勝てるのか
アーカイブは
情報グラフとしてコンパイルされる。
CMPCT は必要なオブジェクト間の正確な関係を探し、物理ルートを選び、決定論的な再構築経路を記録する。同時に局所性、整合性、復旧コストを明示する。
概念的な情報グラフ
論理ツリー
必要バイト
完全一致ストリーム
共有構造
同一性
重複排除済みオブジェクト
制限付きルート
選択デコード
インデックス + 証明
整合性 / 復旧
完全一致の同一性
同一内容は、独立した論理パスを潰さず、一つの認証済み物理ルートへ収束できる。
関係を理解する保存
必要なオブジェクトは、ファイル名が違うだけで重複保存するのではなく、正確な圧縮構造を再利用できる。
選択アクセス
有用なバイトを得る唯一の方法を巨大な全体展開にせず、要求されたオブジェクトだけを読む。
制限付きコンテキスト
ファイル横断コンテキストを試験し制限することで、サイズ改善が無制限の読み取り作業を密かに生まないようにする。
整合性
インデックスと物理データには明示的な検査がある。「デコンプレッサが文句を言わなかった」だけを成功とはしない。
物理復旧
冗長な認証済みメタデータは、文章上の disaster recovery の約束ではなく、実際のリーダー経路として存在する。
03 / 正規版 VS フロンティア
一つのプロジェクト。
二つの権威レベル。
研究フロンティアは攻めてよい。正規 reader/writer は相互運用契約だ。美しいサイトでも、研究表現に正規版の権威を借用させない。
出荷版 / 正規
reader / writer 契約
研究フロンティア
ベンチマーク候補
公開証拠
公開
主張はコミット済み記録から導出
04 / 正規 ZIP 実行パリティ
出荷版 CMPCT vs ZIP。
サイズ、作成、展開。
正規 reader/writer のライブラリ境界と新規 CLI プロセス境界での運用パリティ。研究ストレージフロンティアとは意図的に分離する。
コミット済み記録
コーパス
アーカイブサイズ
ライブラリ作成
ライブラリ展開
CLI 作成
CLI 展開
05 / ブラウザラボ
読むのはここまで。
実際に作る。
ポータブル writer はこの端末で動作する。ファイルはアップロードしない。保守的な正規サブセットだけを出力し、フォーマット改訂後に推測するくらいなら停止する。
正規互換性を確認中…
writer は repository のフォーマット改訂に対して自動的にゲートする。
作成
ポータブル CMPCT writer
ローカル
ここにファイルをドロップ、または選択
ファイルまたはフォルダをドロップ
データを送信せず、バイト単位で正確なアーカイブを作成。
ファイルを選択
フォルダを選択
ファイル未選択。
.cmpct を作成
ポータブルモードは通常ファイル、パス索引、完全一致内容の重複排除、SHA-256/CRC32、RAW/Deflate 保存を維持する。完全なファイルシステム意味論は CLI の領域。
検査
ヘッダーレンズ
アップロードなし
ローカル CMPCT アーカイブの固定ヘッダーだけを読む。完全な構造検証は正規 reader と native core が担当する。
.cmpct ファイルを選択
Magic
バージョンフィールド
プライマリインデックス
データ範囲
06 / リリース軌道
コアリリースは
番号を勝ち取る必要がある。
数値リリースは CMPCT 自体が実質的に改善したときだけ進む。サーフェス改訂は、アーカイブエンジンが変わったふりをせず劇的に美しくできる。
07 / エンジニアリング引き渡し
外側は美しく。
最深部まで検査可能。
人間に CMPCT を読みやすくする同じサーフェスが、エージェントには機械可読な状態と永続的なエンジニアリング証拠を提示する。
機械可読なプロジェクトガイド
公開証拠とリリース状態
エージェントの読み順と権威境界
Repository
Repository ↗
フォーマット、ベンチマーク、実装
性能はスクリーンショットではない。リリース契約だ。
フォーマット ↗
ベンチマーク ↗
Pre-1.0 · ライセンス案は未採用 · コミット済みベンチマーク証拠には記録済み環境と意味論の条件が引き続き付く。
CMPNX11 は研究専用で、正規 r24 reader では読めない。
v0.28 に対するポータブルサイズ改善は小さく (48,601 B / 0.035333%)、15 workload 中 2 つに集中する。13 workload は意図的に完全フォールバックする。
修正済み scheduling 以前、採用された試行 5 のポータブルポートフォリオは v0.28 の 2.175x の作成時間を使用した。scheduler の速度主張は測定した固定敵対的集約にのみ適用される。
同一条件の敵対的構造集約では、試行 #5 は 7z/LZMA2 より小さいが、solid tar/Zstd-19 より 82,112 B、ZPAQ m5 より 85,125 B 大きい。
solid アーカイブ競合は選択読み取り/復旧の意味論が異なる。ここで比較するのは保存バイトであり、機能パリティではない。
CMPCT は links/sparse/uid-gid/xattrs をアーカイブに保持する。この Python ZIP baseline は symlink を実体参照し、より豊かなファイルシステム意味論を保持しない。
採用済み v0.29 研究フロンティア; 正規 r24 は変更なし
決定論的な 724 ファイルの類似性敵対ツリー一つ; 同一 run の全ツリーアーカイブサイズ; solid アーカイブとの意味論差は明示したまま
同一条件のコミット済みベンチマーク
研究フロンティア
CMPCT 研究フロンティア
研究ベンチマーク候補
研究フロンティアのコミット済みベンチマークはありません。
記録:
commit:
小ファイル
ソース
メディア
バイナリ
重複排除とリンク
sparse
ネスト
統合
開発 repository
オフィスワークスペース
メディアライブラリ
analytics とデータベース
ログとテレメトリ
増分バックアップ
非圧縮性・暗号化類似
大量の小ファイル
ML アーティファクト
大規模混在バイナリ
シフトしたバージョン
偽近傍
境界変動
Deflate 系
非圧縮性
`);
export const MESSAGES = Object.freeze({
  files: "{n} ファイル", file: "{n} ファイル", logical: "論理 {bytes}", logicalInputFiles: "論理入力 {bytes} · {n} ファイル",
  smallerThan: "{name} より {pct} 小さい", largerThan: "{name} より {pct} 大きい", sameStored: "{name} と同じ保存バイト", versus: "{name} 比",
  cmpctSmaller: "CMPCT が小さい · 同一条件の保存バイト", cmpctLarger: "CMPCT が大きい · 同一条件の保存バイト", sameBytes: "保存バイト同一", unavailableMatched: "同一条件の保存バイトは利用不可",
  currentFrontier: "現在の CMPCT 研究フロンティア", categoryScore: "{wins}/{total} 小さい · {losses} 大きい", noCategory: "カテゴリ証拠なし", noFreshCategory: "このフロンティアには正確なツリーの新しいカテゴリ証拠がありません。",
  comparisonUnavailable: "比較不可", noQualification: "この公開フロンティアには記録済みベンチマーク条件がありません。",
  heroIf: "この同一条件テストで {name} が 100 MB 保存する場合、CMPCT は約 {value} MB 必要です。", heroNeeds: "この同一条件テストでは、{name} が 100 MB 保存するごとに CMPCT は現在約 {value} MB 必要です。",
  seriousBaseline: "本格的なサイズ基準: {relation}。", scopedScheduler: "範囲限定 scheduler 結果: 固定ゲートで wall time が {pct}% 低下。", canonicalRemains: "正規フォーマットは r{revision} のままです。",
  frontierQualification: "{frontier} · 同一条件の構造ツリー {files} ファイル。{serious}{speed} 正規フォーマットは r{revision} のままです。", fixedSchedulerGate: "固定敵対的 scheduler ゲート · 全体的な速度主張ではない", winsAgainst: "{name} に {wins}/{total} 勝",
  noCommittedParity: "コミット済みパリティ記録なし", repetitionsMedian: "{n}× の中央値", semanticQualification: "意味論上の条件:", interpretation: "解釈:", currentProjectRelease: "現在のプロジェクトリリース", versionedMilestone: "バージョン化された節目",
  writerVerified: "ポータブル writer は正規 r{revision} で検証済み。", regularSubset: "通常ファイルのサブセットのみ。完全なファイルシステム意味論は CLI の領域。", writerPaused: "フォーマット改訂 {revision} 後、ブラウザ writer は停止中。", writerRefuses: "この build は r{supported} で検証済み。新しい文法を推測しません。",
  readyLocally: "ローカルで準備完了", cliOverLimit: "CLI を使用: ブラウザ上限超過", input: "入力", archive: "アーカイブ", delta: "差分", smaller: "{bytes} 小さい", overhead: "{bytes} オーバーヘッド", buildingLocally: "ローカルで作成中…", builtOnDevice: "この端末でアーカイブを作成しました。",
  logicalFilesUnique: "論理 {logical} ファイル → 一意 blob {unique} · {deflate} Deflate / {raw} RAW。", saveCmpct: ".cmpct を保存", couldNotBuild: "アーカイブを作成できませんでした。", fixedMagicError: "固定 Magic が CMPCT に見えません。", inspection: "検査", benchmarkUnavailable: "ベンチマークデータを利用できません: {error}", canonicalDataMissing: "正規サイトデータを読み込めませんでした。"
});
