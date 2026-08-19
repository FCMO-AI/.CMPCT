<div align="center">
  <a href="https://fcmo-ai.github.io/.CMPCT/?lang=ja"><img src="../../.github/assets/repository-hero.svg" width="100%" alt="CMPCT — 従来のアーカイブ形式は妥協と折り合いをつけた。CMPCT は違う。"></a>

  **保存バイト数、選択アクセス、整合性、復旧性、可搬性を同時に前進させるための汎用ロスレス・アーカイブ／コンテナプロジェクト。**

  **[Web サイト](https://fcmo-ai.github.io/.CMPCT/?lang=ja)** · **[ブラウザラボ](https://fcmo-ai.github.io/.CMPCT/?lang=ja#lab)** · **[ベンチマーク](../BENCHMARKS.md)** · **[フォーマット](../FORMAT.md)** · **[ロードマップ](../ROADMAP.md)** · **[エージェント入口](../CURRENT_STATE.md)**

  <sub>core v0.29.0 · 正規フォーマット r24 · surface 0.29.k · pre-1.0</sub>
</div>

> **編集済み翻訳。** これは人向け README の意味を保った、バージョン管理された日本語版です。英語の [`README.md`](../../README.md) が引き続き正規の権威です。数値、パス、フォーマット名、証拠の範囲は意図的に維持しています。実際のバイリンガル人間レビューが行われるまでは「人間レビュー済み」とは表示しません。

---

> **性能はリリース契約そのもの。** 研究では不都合なトレードオフが見つかってよい。昇格するリリースがそれを隠すことは許されない。決定論的なアーカイブサイズ回帰は **0 バイト許容**、同一 Runner の文書化されたノイズ範囲を超える確認済み速度低下は昇格を止め、負けた workload も公開証拠として残る。

## CMPCT が存在する理由

| | CMPCT が改善しようとしていること |
|---|---|
| **保存バイト** | 各ファイルを無関係なバイト列として扱わず、完全一致の同一性、内容認識表現、制限された関係再利用を使う。 |
| **選択アクセス** | アーカイブ全体を必ず展開せず、要求されたオブジェクトや範囲だけを読む。 |
| **整合性 + 復旧** | 検査、冗長メタデータ、salvage 経路を disaster-recovery の説明文ではなく実際の reader 動作にする。 |
| **ファイルシステム忠実性** | リンク、sparse files、メタデータ、現代的な update semantics を保持する。 |
| **相互運用性** | 正規 reader/writer 契約、ZIP export、native core、portability gate を実験的 grammar から分離する。 |
| **証拠の質** | 公開 claim は reproducible な committed record から導出し、敗北を消さず、benchmark theater を拒む。 |

CMPCT は「新しい拡張子を付けた Zstd」ではない。手選びした一つのディレクトリで勝つだけでも足りない。目標は **サイズ、速度、random access、忠実性、整合性、復旧、更新、現代的 storage semantics** をまとめて強くし、コストを別の場所へ密かに押し付けないデフォルト・アーカイブだ。

## 最新の検証済みフロンティア

**Project v0.29.0 — Mosaic / Residual Program Packing** は検証済み研究エンジンを前進させる。一方、出荷される正規フォーマットは **revision 24** のまま。

| v0.29 研究証拠 | 結果 |
|---|---:|
| Portable inherited-frontier portfolio | **137,501,815 B** |
| Direct v0.28 base | 137,550,416 B |
| 正確な削減 | **48,601 B (0.035333%)** |
| Portable workloads | **15** |
| 改善 / 回帰 | **2 / 0** |
| Exact v0.28 fallbacks | **13 / 15** |
| Hostile mechanism suites | **4.407362% 小さい**、18 workload 中 9 改善 / 0 回帰 |
| Fixed hostile scheduler | **182.454 s → 97.944 s median (-46.318%)**、選択アーカイブは byte-identical |

決定論的な resemblance-hostile 集約（724 ファイル / 93,526,384 バイト）では、採用された試行 #5 が **47,147,764 B** を保存する。同じツリーで ZPAQ m5 は 47,062,639 B、solid tar+Zstd-19 は 47,065,652 B、7z/LZMA2 は 47,430,343 B、Borg は 76,461,311 B、ZIP/Deflate-9 は 76,690,799 B。

これは **同一条件の保存バイト比較であり、意味論的パリティの主張ではない**。solid archive、backup repository、CMPCT は異なる trade-off を持つ。永続 record: [`docs/releases/v0.29.0.md`](../releases/v0.29.0.md)。machine-readable evidence: [`benchmarks/history/`](../../benchmarks/history/)。

### 出荷版 vs 研究フロンティア

| 権威 | 現在 | 意味 |
|---|---|---|
| **正規 reader/writer** | **r24** | `python -m cmpct create` が書き、正規 reader が理解すべきもの。 |
| **研究フロンティア** | **CMPNX11 / v0.29.0** | 実験的 Mosaic + Residual Program Packing。r24 構文ではない。 |
| **公開 surface** | **0.29.k** | repo/site/docs の表示層。アーカイブ意味論の権威は持たない。 |
| **ライセンス** | **Apache-2.0 提案中** | 提案のみ。最終的な公開 grant ではない。 |

## CMPCT が現在できること

正規 r24 には content-addressed deduplication、adaptive Zstandard/raw storage、Zstd dictionaries と micro-solid packs、content-defined chunking、高速 byte-range reads と parallel decode、hardlink/symlink/sparse preservation、UID/GID/xattrs、ZIP/WHL virtualization、勝てる場合の lossless PCM-WAV、ZIP export 用 raw Deflate reuse、CRC32 + SHA-256、冗長 head/tail indexes、self-describing blob records、transaction append journal、on-demand ZIP export、任意の reproducible/deterministic parallel creation が含まれる。

v0.29 では bounded FastCDC units、multi-band similarity search、depth-1 COPY/LITERAL deltas、multi-root Mosaic placement、Residual Program Packing、exact v0.28 fallback、locality/resource ceilings、pinned memory-safe bridge 経由の exact DEFLATE、Merkle-authenticated records、authenticated tail recovery、strict remote range sources、byte-identical parallel scheduling も研究する。

これらは format integration、conformance、hardening、native parity、recovery、portability を独立に通過するまで正規 reader には入らない。

原則は **内容で選ぶ。拡張子の俗説で選ばない。**

## クイックスタート

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

fresh-process CLI は `--workers N` がない限り意図的に serial。v0.28 gate では小さな media tree で thread-pool startup が約 10 ms のコストになった。in-process `Builder` は deterministic parallel creation を既定で維持する。

任意の native Linux chunker:

```bash
cc -O3 -shared -fPIC native/cmpct_cdc.c -o src/cmpct/libcmpct_cdc.so
```

reader はこの helper に **依存しない**。chunk 境界は明示的に disk に記録される。

## 性能ポジション

- **サイズ:** 同一 input + encoder semantics で大きくなることは許さない。許容 **0 バイト**。
- **create/extract:** base と candidate を同じ runner で繰り返し中央値測定。noise envelope 外の確認済み slowdown は release を止める。
- **evidence:** 数値 core release ごとに新しい公開 benchmark record を commit。
- **corpora:** 敗北/adversarial workload も残す。

[`docs/PERFORMANCE_RELEASE_GATE.md`](../PERFORMANCE_RELEASE_GATE.md) と [`docs/BREAKTHROUGH_REHABILITATION.md`](../BREAKTHROUGH_REHABILITATION.md) を参照。

## 新しいエージェントの読み順

`docs/AGI_ENGINEERING_STANDARD.md` → `README.md` → `AGENTS.md` → `docs/CURRENT_STATE.md` → 最新の `docs/releases/` → `docs/PERFORMANCE_RELEASE_GATE.md` → `docs/BREAKTHROUGH_REHABILITATION.md` → `docs/FORMAT.md` → `docs/HISTORY.md` → EntropyGraph/Mosaic docs → `docs/HARDENING.md` → `docs/PORTABILITY.md` + `docs/NATIVE_CORE.md` → `docs/RESEARCH_LOG.md` → `docs/BENCHMARKS.md` + `benchmarks/history/` → `docs/PUBLIC_SURFACE.md` → `docs/ROADMAP.md`。

新しいエージェントが private chat、private corpora、無関係な project context を必要としないことが目標。

## Repository マップ

`src/cmpct/` = 正規 r24 reference、`experiments/` = 研究系列、`benchmarks/` = determinisitic corpora/gates + `benchmarks/history/`、`fuzz/` = parser/resource attacks、`tools/check_*` = contract checks、`site/` = site + Browser Lab、`native/` = accelerators/shared core、`docs/` = contracts/campaigns/history/roadmap、`tests/` = format/round-trip/similarity/locality/reproducibility regressions。

## Web サイト

サイトは **まず印象を作り、次に claim を証明し、最後に信頼を獲得する** よう設計されている。数値、競合、workload、敗北、core status は versioned benchmark history から生成。**研究フロンティア**、**正規パリティ**、**surface revision** を厳格に分離する。視覚的には攻めてよいが、勝利を捏造してはいけない。

**開く:** https://fcmo-ai.github.io/.CMPCT/?lang=ja

## バージョン規律

1. **数値 core (`MAJOR.MINOR.PATCH`)** — 実質的な製品改善だけ。v0.27.1 以降、通常の進行は `MAJOR.MINOR`、packaging compatibility のため `PATCH=0`。
2. **Surface (`MAJOR.MINOR.LETTER`)** — site/docs/repo/workflow。現在 **`0.29.k`**。
3. **On-disk revision** — reader に新しい grammar/semantics が必要なときだけ。正規は **r24**。

CI は軸を分離し、根拠のない bump を拒否する。

## 歴史、provenance、公開 surface

CMPCT は Seekable-Zstd、indexed-Zstd、adaptive-framing、ZIP-family の実験から成長した。技術史は残すが、private corpus identities、private artifacts、unrelated provenance は公開記録に入れない。公開 benchmark は再現可能、または意図的に公開/合成 input を使う必要がある。過去の結果は **普遍的な性能保証ではない**。

CMPCT は単独で成立しなければならない。repo/site は unrelated internal project、private customer data、private corpora、personal information、chat transcripts、credentials、private artifact names、internal links を要求・公開してはならない。`docs/PUBLIC_SURFACE.md` 参照。

## 正規性

この repository は chat-local prototype と benchmark script を置き換える。実質的な engine/archive 進歩は数値 release、site/docs/presentation は `SURFACE_REVISION`、研究は promotion まで明示的 experimental。実験コードは reference reader/writer と conformance に統合されるまで正規サポートを主張できない。

## ライセンス

Apache License 2.0 は **現在の提案ライセンス** であり、最終採用済みではない。本文: `LICENSE-APACHE-2.0-PROPOSED.txt`。採用 checklist: `LICENSING.md`。完了まで CMPCT を Apache-2.0 で正式リリース済みと表現してはいけない。
