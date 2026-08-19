<div align="center">
  <a href="https://fcmo-ai.github.io/.CMPCT/?lang=tr"><img src="../../.github/assets/repository-hero.svg" width="100%" alt="CMPCT — Arşiv biçimleri tavizlerle barıştı. CMPCT barışmadı."></a>

  **Depolanan baytları, seçici erişimi, bütünlüğü, kurtarmayı ve taşınabilirliği birlikte ileri taşımak için tasarlanmış genel amaçlı kayıpsız arşiv/kapsayıcı projesi.**

  **[Site](https://fcmo-ai.github.io/.CMPCT/?lang=tr)** · **[Tarayıcı Laboratuvarı](https://fcmo-ai.github.io/.CMPCT/?lang=tr#lab)** · **[Benchmarklar](../BENCHMARKS.md)** · **[Biçim](../FORMAT.md)** · **[Yol Haritası](../ROADMAP.md)** · **[Ajan başlangıcı](../CURRENT_STATE.md)**

  <sub>core v0.29.0 · kanonik biçim r24 · yüzey 0.29.k · pre-1.0</sub>
</div>

> **Küratörlü çeviri.** Bu belge, insanlara yönelik README’nin sürümlenmiş anlamsal uyarlamasıdır. İngilizce [`README.md`](../../README.md) kanonik otorite olarak kalır. Sayılar, yollar, biçim adları ve kanıt sınırları bilinçli olarak korunur. Gerçek bir iki dilli insan incelemesi olmadan “insan tarafından incelendi” etiketi kullanılmaz.

---

> **Performans sürüm sözleşmesidir.** Araştırma rahatsız edici bir ödünleşimi ortaya çıkarabilir. Promosyon alan bir sürüm bunu gizleyemez: deterministik arşiv boyutu regresyonunda **0 bayt tolerans**, aynı runner’ın belgelenmiş gürültü aralığı dışındaki doğrulanmış yavaşlama promosyonu engeller ve kaybeden workloadlar kamusal kanıt olarak kalır.

## CMPCT neden var

| | CMPCT bunu iyileştirmeye çalışıyor |
|---|---|
| **Depolanan baytlar** | Her dosyayı bağımsız akış saymak yerine tam kimlik, içerik-duyarlı temsil ve sınırlı ilişki yeniden kullanımı. |
| **Seçici erişim** | Tüm arşivi zorunlu olarak açmadan istenen nesne veya aralığı okumak. |
| **Bütünlük + kurtarma** | Kontrolleri, yedek meta veriyi ve salvage yollarını disaster-recovery metni değil gerçek reader davranışı yapmak. |
| **Dosya sistemi sadakati** | Linkler, sparse files, metadata ve modern update semantiğini korumak. |
| **Birlikte çalışabilirlik** | Kanonik reader/writer sözleşmesini, ZIP exportu, native core ve portability gate’lerini deneysel gramerden ayırmak. |
| **Kanıt kalitesi** | Kamusal iddiaları yeniden üretilebilir sürümlenmiş kayıtlardan türetmek, kayıpları korumak, benchmark tiyatrosunu reddetmek. |

CMPCT “yeni uzantılı Zstd” değildir ve seçilmiş tek bir klasörde kazanmakla yetinmez. Hedef, **boyut, hız, random access, sadakat, bütünlük, kurtarma, güncelleme ve modern storage semantiği** açısından daha güçlü varsayılan arşivdir; maliyeti gizlice başka yere taşımak değil.

## Son doğrulanmış sınır

**Project v0.29.0 — Mosaic / Residual Program Packing** doğrulanmış araştırma motorunu ilerletirken dağıtılan kanonik biçim **revision 24** olarak kalır.

| v0.29 araştırma kanıtı | Sonuç |
|---|---:|
| Portable inherited-frontier portfolio | **137,501,815 B** |
| Doğrudan v0.28 base | 137,550,416 B |
| Tam tasarruf | **48,601 B (0.035333%)** |
| Portable workload | **15** |
| İyileşti / geriledi | **2 / 0** |
| Tam v0.28 fallback | **13 / 15** |
| Hostile mechanism suites | **4.407362% daha küçük**, 18 workload’da 9 iyileşme / 0 regresyon |
| Fixed hostile scheduler | **182.454 s → 97.944 s medyan (-46.318%)**, seçilen arşiv byte-identical |

724 dosya / 93,526,384 baytlık deterministik resemblance-hostile agregada kabul edilen #5 denemesi **47,147,764 B** depolar. Aynı ağaçta ZPAQ m5 47,062,639 B, solid tar+Zstd-19 47,065,652 B, 7z/LZMA2 47,430,343 B, Borg 76,461,311 B ve ZIP/Deflate-9 76,690,799 B depolar.

Bunlar **eşleştirilmiş depolanan bayt karşılaştırmalarıdır, semantik parite iddiası değildir**. Solid arşivler, backup repositoryleri ve CMPCT farklı trade-offlar sunar. Kalıcı kayıt: [`docs/releases/v0.29.0.md`](../releases/v0.29.0.md); machine-readable evidence: [`benchmarks/history/`](../../benchmarks/history/).

### Dağıtılan vs araştırma sınırı

| Otorite | Durum | Anlam |
|---|---|---|
| **Kanonik reader/writer** | **r24** | `python -m cmpct create` çıktısı ve kanonik readerların anlaması gereken sözleşme. |
| **Araştırma sınırı** | **CMPNX11 / v0.29.0** | Deneysel Mosaic + Residual Program Packing; r24 sözdizimi değil. |
| **Kamusal yüzey** | **0.29.k** | Repo/site/docs sunumu; arşiv semantiği üzerinde otoritesi yok. |
| **Lisans** | **Apache-2.0 önerildi** | Yalnızca öneri; final kamusal grant değil. |

## CMPCT bugün ne yapabiliyor

Kanonik r24 prototipi content-addressed deduplication, adaptif Zstandard/raw storage, Zstd dictionary ve micro-solid pack, content-defined chunking, hızlı byte-range reads ve parallel decode, hardlink/symlink/sparse preservation, UID/GID/xattrs, ZIP/WHL virtualization, kazandığında lossless PCM-WAV dönüşümü, ZIP exportu için raw Deflate reuse, CRC32 + SHA-256, redundant head/tail indexes, self-describing blob records, transaction append journal, on-demand ZIP exportu ve isteğe bağlı reproducible/deterministic parallel creation içerir.

v0.29 ayrıca bounded FastCDC units, multi-band similarity search, depth-1 COPY/LITERAL deltas, multi-root Mosaic placement, Residual Program Packing, exact v0.28 fallback, locality/resource ceilings, pinned memory-safe bridge ile exact DEFLATE, Merkle-authenticated records, authenticated tail recovery, strict remote range sources ve byte-identical parallel scheduling araştırır.

Bu mekanizmalar format integration, conformance, hardening, native parity, recovery ve portability koşullarını bağımsız geçene kadar kanonik reader dışında kalır.

Ana kural: **içeriğe göre seçim, uzantıya göre folklor değil**.

## Hızlı başlangıç

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

Fresh-process CLI `--workers N` verilmedikçe bilinçli olarak serialdır. v0.28 gate küçük media tree’de thread-pool startup maliyetini ~10 ms buldu; in-process `Builder` varsayılan olarak deterministik paralelliği korur.

Opsiyonel native Linux chunker:

```bash
cc -O3 -shared -fPIC native/cmpct_cdc.c -o src/cmpct/libcmpct_cdc.so
```

Reader bu helpera **bağımlı değildir**; chunk sınırları diskte açıkça kaydedilir.

## Performans konumu

- **boyut:** aynı input + encoder semantics daha büyük arşiv üretemez; tolerans **0 bayt**;
- **create/extract:** base ve candidate aynı runner’da, tekrarlı medyanlarla; doğrulanmış yavaşlama noise envelope dışındaysa release engellenir;
- **evidence:** her numerik core release yeni bir kamusal benchmark kaydı commit eder;
- **corpora:** kaybeden/adversarial workloadlar görünür kalır.

Bkz. [`docs/PERFORMANCE_RELEASE_GATE.md`](../PERFORMANCE_RELEASE_GATE.md) ve [`docs/BREAKTHROUGH_REHABILITATION.md`](../BREAKTHROUGH_REHABILITATION.md).

## Yeni ajan okuma sırası

`docs/AGI_ENGINEERING_STANDARD.md` → `README.md` → `AGENTS.md` → `docs/CURRENT_STATE.md` → en yeni `docs/releases/` → `docs/PERFORMANCE_RELEASE_GATE.md` → `docs/BREAKTHROUGH_REHABILITATION.md` → `docs/FORMAT.md` → `docs/HISTORY.md` → EntropyGraph/Mosaic docs → `docs/HARDENING.md` → `docs/PORTABILITY.md` + `docs/NATIVE_CORE.md` → `docs/RESEARCH_LOG.md` → `docs/BENCHMARKS.md` + `benchmarks/history/` → `docs/PUBLIC_SURFACE.md` → `docs/ROADMAP.md`.

Yeni ajan özel chat, özel corpora veya unrelated proje bağlamına ihtiyaç duymamalıdır.

## Repository haritası

`src/cmpct/` = kanonik r24 referansı; `experiments/` = araştırma hattı; `benchmarks/` = deterministik corpora/gates ve `benchmarks/history/`; `fuzz/` = parser/resource saldırıları; `tools/check_*` = sözleşme kontrolleri; `site/` = site + Browser Lab; `native/` = hızlandırıcılar/shared core; `docs/` = sözleşmeler/kampanyalar/tarih/roadmap; `tests/` = format, round-trip, similarity, locality ve reproducibility regressions.

## Site

Site **önce etki yaratmak, sonra iddiayı kanıtlamak, en son güven kazanmak** için tasarlanmıştır. Sayılar, rakipler, workloadlar, kayıplar ve core durumu sürümlenmiş benchmark tarihinden gelir. **Araştırma sınırı**, **kanonik parite** ve **surface revision** kesin biçimde ayrılır. Görsel olarak agresif olabilir; zafer uyduramaz.

**Aç:** https://fcmo-ai.github.io/.CMPCT/?lang=tr

## Sürüm disiplini

1. **Numerik core (`MAJOR.MINOR.PATCH`)** — yalnızca maddi ürün ilerlemesi için; v0.27.1’den sonra normal ilerleme `MAJOR.MINOR`, packaging compatibility için `PATCH=0`.
2. **Surface (`MAJOR.MINOR.LETTER`)** — site/docs/repo/workflow; şu an **`0.29.k`**.
3. **On-disk revision** — readerların yeni gramer/semantiğe ihtiyacı olduğunda; kanonik **r24**.

CI eksenleri ayrı tutar ve kanıtsız bump’ları reddeder.

## Tarih, provenance ve kamusal yüzey

CMPCT Seekable-Zstd, indexed-Zstd, adaptive-framing ve ZIP-family deneylerinden doğdu. Teknik tarih korunur; özel corpus kimlikleri, artefaktlar ve unrelated provenance korunmaz. Kamusal benchmarklar yeniden üretilebilir olmalı veya bilinçli olarak kamusal/sentetik input kullanmalıdır; tarihsel sonuçlar **evrensel performans garantisi değildir**.

CMPCT kendi başına ayakta durmalıdır. Repo/site unrelated iç projeleri, özel müşteri verisini, corpora’yı, kişisel bilgiyi, chat kayıtlarını, credentials’ı, özel artefakt adlarını veya iç linkleri gerektiremez/açığa çıkaramaz. Bkz. `docs/PUBLIC_SURFACE.md`.

## Kanoniklik

Repository chat-local prototiplerin ve benchmark scriptlerinin yerini alır. Maddi engine/archive ilerlemesi numerik release kazanır; site/docs/sunum `SURFACE_REVISION` kullanır; araştırma promotion’a kadar açıkça deneysel kalır. Deneysel kod reference reader/writer ve conformance entegrasyonu olmadan kanonik destek iddia edemez.

## Lisans

Apache License 2.0 **şu an önerilen lisanstır**, final kabul edilmiş lisans değildir. Metin: `LICENSE-APACHE-2.0-PROPOSED.txt`; adoption checklist: `LICENSING.md`. Süreç tamamlanana kadar CMPCT Apache-2.0 altında nihai olarak yayınlanmış gibi sunulmamalıdır.
