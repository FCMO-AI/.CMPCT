<div align="center">
  <a href="https://fcmo-ai.github.io/.CMPCT/?lang=hu"><img src="../../.github/assets/repository-hero.svg" width="100%" alt="CMPCT — Az archívumformátumok kiegyeztek a kompromisszummal. A CMPCT nem."></a>

  **Általános célú, veszteségmentes archívum/konténer projekt, amely a tárolt bájtokat, a szelektív hozzáférést, az integritást, a helyreállítást és a hordozhatóságot együtt fejleszti.**

  **[Webhely](https://fcmo-ai.github.io/.CMPCT/?lang=hu)** · **[Böngészőlabor](https://fcmo-ai.github.io/.CMPCT/?lang=hu#lab)** · **[Benchmarkok](../BENCHMARKS.md)** · **[Formátum](../FORMAT.md)** · **[Roadmap](../ROADMAP.md)** · **[Ügynök-belépő](../CURRENT_STATE.md)**

  <sub>core v0.29.0 · kanonikus formátum r24 · felület 0.29.k · pre-1.0</sub>
</div>

> **Kurált fordítás.** Ez az embereknek szóló README verziózott, szemantikai adaptációja. Az angol [`README.md`](../../README.md) marad a kanonikus autoritás. A számokat, útvonalakat, formátumneveket és bizonyítéki korlátokat tudatosan megőrizzük. A szöveget nem jelöljük kétnyelvű ember által ellenőrzöttnek, amíg ilyen ellenőrzés ténylegesen nem történt.

---

> **A teljesítmény a kiadási szerződés.** A kutatás találhat kellemetlen kompromisszumot. Egy promótált kiadás ezt nem rejtheti el: a determinisztikus archívumméret-regresszió **0 bájt toleranciájú**, az azonos runner dokumentált zajsávján kívüli igazolt lassulás blokkolja a promóciót, a vesztes workloadok pedig nyilvános bizonyítékként megmaradnak.

## Miért létezik a CMPCT

| | Ezt akarja jobbá tenni |
|---|---|
| **Tárolt bájtok** | Pontos azonosságot, tartalomtudatos reprezentációkat és korlátozott kapcsolati újrahasznosítást használni ahelyett, hogy minden fájlt független bájtfolyamként kezelnénk. |
| **Szelektív hozzáférés** | A kért objektum vagy tartomány olvasása az egész archívum kötelező kibontása nélkül. |
| **Integritás + helyreállítás** | Ellenőrzések, redundáns metaadatok és salvage utak valódi olvasói viselkedésként, nem disaster-recovery prózaként. |
| **Fájlrendszer-hűség** | Linkek, sparse fájlok, metaadatok és modern update-szemantika megőrzése. |
| **Interoperabilitás** | A kanonikus reader/writer szerződés, ZIP export, native core és portability gate-ek elválasztása a kísérleti nyelvtantól. |
| **Bizonyítékminőség** | Nyilvános állítások reprodukálható, verziózott rekordokból; veszteségek megőrzése; benchmark-színház elutasítása. |

A CMPCT nem „Zstd új kiterjesztéssel”, és nem elég neki egy kézzel kiválasztott könyvtár megnyerése. A cél erősebb alapértelmezett archívum **méretben, sebességben, random accessben, hűségben, integritásban, helyreállításban, frissítésekben és modern tárolási szemantikában**, rejtett költségáthelyezés nélkül.

## Legfrissebb igazolt front

**Projekt v0.29.0 — Mosaic / Residual Program Packing** előrébb viszi az igazolt kutatási motort, miközben a szállított kanonikus formátum **24-es revízió** marad.

| v0.29 kutatási bizonyíték | Eredmény |
|---|---:|
| Hordozható örökölt frontier portfolio | **137,501,815 B** |
| Közvetlen v0.28 bázis | 137,550,416 B |
| Pontos megtakarítás | **48,601 B (0.035333%)** |
| Hordozható workloadok | **15** |
| Javult / regresszió | **2 / 0** |
| Pontos v0.28 fallback | **13 / 15** |
| Hostile mechanism suite-ok | **4.407362% kisebb**, 9 javult / 0 regresszió 18 workloadon |
| Fix hostile scheduler | **182.454 s → 97.944 s medián (-46.318%)**, kiválasztott archívum bájtazonos |

A determinisztikus, hasonlóság-ellenes 724 fájlos / 93,526,384 bájtos aggregátumon az elfogadott #5 próbálkozás **47,147,764 B**-ot tárol. Ugyanezen a fán: ZPAQ m5 47,062,639 B, solid tar+Zstd-19 47,065,652 B, 7z/LZMA2 47,430,343 B, Borg 76,461,311 B, ZIP/Deflate-9 76,690,799 B.

Ezek **párosított tároltbájt-összehasonlítások, nem szemantikai paritásállítások**. A solid archívumok, backup repositoryk és CMPCT eltérő trade-offokat adnak. Tartós record: [`docs/releases/v0.29.0.md`](../releases/v0.29.0.md); gépi bizonyíték: [`benchmarks/history/`](../../benchmarks/history/).

### Szállított vs front

| Autoritás | Állapot | Jelentés |
|---|---|---|
| **Kanonikus reader/writer** | **r24** | Amit a `python -m cmpct create` ír, és amit a kanonikus readereknek érteniük kell. |
| **Kutatási front** | **CMPNX11 / v0.29.0** | Kísérleti Mosaic + Residual Program Packing; nem r24 szintaxis. |
| **Nyilvános felület** | **0.29.k** | Repo/site/docs prezentáció, archívumszemantikai autoritás nélkül. |
| **Licenc** | **Apache-2.0 javasolt** | Csak javaslat, még nem végleges nyilvános engedély. |

## Mit tud ma a CMPCT

A kanonikus r24 prototípus tartalmaz content-addressed deduplikációt, adaptív Zstandard/raw tárolást, Zstd dictionaryket és micro-solid packeket, content-defined chunkingot, gyors byte-range readet és parallel decode-ot, hardlink/symlink/sparse megőrzést, UID/GID/xattrst, ZIP/WHL virtualizációt, lossless PCM-WAV transzformot ahol nyer, raw Deflate újrahasznosítást ZIP exporthoz, CRC32 + SHA-256 ellenőrzést, redundáns head/tail indexeket, self-describing blob recordokat, tranzakciós append journalt, on-demand ZIP exportot és opcionális reprodukálható/determinisztikusan párhuzamos létrehozást.

A v0.29 ezen felül bounded FastCDC egységeket, multi-band similarity searchöt, depth-1 COPY/LITERAL deltákat, multi-root Mosaic placementet, Residual Program Packinget, exact v0.28 fallbackot, locality/resource plafonokat, pinned memory-safe bridge-en át exact DEFLATE-et, Merkle-authenticated recordokat, authenticated tail recoveryt, strict remote range source-okat és byte-identical parallel schedulingot vizsgál.

A kutatási mechanizmusok csak akkor kerülhetnek a kanonikus readerbe, ha külön teljesítik a format integration, conformance, hardening, native parity, recovery és portability követelményeket.

Alapszabály: **tartalomvezérelt kiválasztás, nem kiterjesztésvezérelt folklór**.

## Gyors kezdés

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

A fresh-process CLI létrehozás szándékosan soros `--workers N` nélkül. A v0.28 gate kis media fán ~10 ms thread-pool startup költséget talált; az in-process `Builder` alapból determinisztikus párhuzamos létrehozást tart.

Opcionális native Linux chunker:

```bash
cc -O3 -shared -fPIC native/cmpct_cdc.c -o src/cmpct/libcmpct_cdc.so
```

A reader **nem függ** tőle; a chunk-határok explicit módon lemezre kerülnek.

## Teljesítménypozíció

- **méret:** azonos input + encoder semantics soha nem adhat nagyobb archívumot; **0 bájt** tolerancia;
- **create/extract:** base és candidate ugyanazon a runneren, ismételt mediánokkal; igazolt lassulás a zajsávon túl blokkol;
- **bizonyíték:** minden numerikus core release friss nyilvános benchmark recordot commitol;
- **corpora:** vesztes/adversarial workloadok láthatók maradnak.

Lásd [`docs/PERFORMANCE_RELEASE_GATE.md`](../PERFORMANCE_RELEASE_GATE.md) és [`docs/BREAKTHROUGH_REHABILITATION.md`](../BREAKTHROUGH_REHABILITATION.md).

## Új ügynök olvasási sorrendje

`docs/AGI_ENGINEERING_STANDARD.md` → `README.md` → `AGENTS.md` → `docs/CURRENT_STATE.md` → legújabb `docs/releases/` → `docs/PERFORMANCE_RELEASE_GATE.md` → `docs/BREAKTHROUGH_REHABILITATION.md` → `docs/FORMAT.md` → `docs/HISTORY.md` → EntropyGraph/Mosaic docs → `docs/HARDENING.md` → `docs/PORTABILITY.md` + `docs/NATIVE_CORE.md` → `docs/RESEARCH_LOG.md` → `docs/BENCHMARKS.md` + `benchmarks/history/` → `docs/PUBLIC_SURFACE.md` → `docs/ROADMAP.md`.

Egy új ügynöknek nem szabad privát chatre, privát corpusra vagy más projekt kontextusára szorulnia.

## Repository térkép

`src/cmpct/` = kanonikus r24 referencia; `experiments/` = kutatási vonal; `benchmarks/` = determinisztikus corpora/gate-ek és `benchmarks/history/`; `fuzz/` = parser/resource támadások; `tools/check_*` = szerződésellenőrzések; `site/` = web + Browser Lab; `native/` = gyorsítók/shared core; `docs/` = szerződések/kampányok/történet/roadmap; `tests/` = format, round-trip, similarity, locality és reproducibility regressziók.

## Webhely

A webhely célja: **először hatást kelteni, aztán bizonyítani, végül bizalmat szerezni**. A számok, versenytársak, workloadok, veszteségek és core-állapot verziózott benchmark történelemből jön. Szétválasztja a **kutatási frontot**, **kanonikus paritást** és **surface revisiont**. Vizuálisan lehet agresszív; győzelmet nem találhat ki.

**Megnyitás:** https://fcmo-ai.github.io/.CMPCT/?lang=hu

## Verziófegyelem

1. **Numerikus core (`MAJOR.MINOR.PATCH`)** — csak anyagi termékjavulásért; v0.27.1 után normál előrelépés `MAJOR.MINOR`, `PATCH=0` packaging compatibility miatt.
2. **Surface (`MAJOR.MINOR.LETTER`)** — site/docs/repo/workflow; jelenleg **`0.29.k`**.
3. **On-disk revision** — csak új reader grammatika/szemantika esetén; kanonikus **r24**.

CI külön tartja ezeket és elutasítja az alátámasztatlan bumpokat.

## Történet, proveniencia és nyilvános felület

A CMPCT Seekable-Zstd, indexed-Zstd, adaptive-framing és ZIP-family kísérletekből nőtt ki. A technikai történet megmarad; privát corpusidentitások, artefaktumok és unrelated provenance nem. A nyilvános benchmarknak reprodukálhatónak vagy szándékosan nyilvános/szintetikus inputon alapulónak kell lennie; a történeti eredmény **nem univerzális garancia**.

A CMPCT-nek önmagában kell megállnia. Repo és site nem igényelhet vagy tehet közzé unrelated belső projekteket, privát ügyféladatot, corpust, személyes adatot, chat transcriptet, credentialt, privát artefaktumnevet vagy belső linket. Lásd `docs/PUBLIC_SURFACE.md`.

## Kanonikusság

Ez a repository felváltja a chat-local prototípusokat és benchmark scripteket. Anyagi engine/archive fejlődés numerikus release-t kap; site/docs/prezentáció `SURFACE_REVISION`-t használ; kutatás explicit kísérleti marad promotionig. Kísérleti kód reference reader/writer és conformance integráció nélkül nem állíthat kanonikus támogatást.

## Licenc

Az Apache License 2.0 a **jelenleg javasolt licenc**, nem a végleg elfogadott. A javasolt szöveg: `LICENSE-APACHE-2.0-PROPOSED.txt`; adoption checklist: `LICENSING.md`. A folyamat lezárásáig a CMPCT nem mutatható be végleg Apache-2.0 alatt kiadottként.
