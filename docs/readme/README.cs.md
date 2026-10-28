<div align="center">
  <a href="https://fcmo-ai.github.io/.CMPCT/?lang=cs"><img src="../../.github/assets/repository-hero.svg" width="100%" alt="CMPCT — Archivní formáty se smířily s kompromisy. CMPCT ne."></a>

  **Univerzální bezztrátový archivní/kontejnerový projekt, který posouvá společně uložené bajty, selektivní přístup, integritu, obnovu a portabilitu.**

  **[Web](https://fcmo-ai.github.io/.CMPCT/?lang=cs)** · **[Browser Lab](https://fcmo-ai.github.io/.CMPCT/?lang=cs#lab)** · **[Benchmarky](../BENCHMARKS.md)** · **[Formát](../FORMAT.md)** · **[Roadmap](../ROADMAP.md)** · **[Vstup pro agenty](../CURRENT_STATE.md)**

  <sub>core v0.29.0 · kanonický formát r24 · povrch 0.29.k · pre-1.0</sub>
</div>

> **Kurátorovaný překlad.** Jde o verzovanou sémantickou adaptaci README určeného lidem. Anglický [`README.md`](../../README.md) zůstává kanonickou autoritou. Čísla, cesty, názvy formátů a hranice důkazů se zachovávají. Text není označen jako zkontrolovaný dvojjazyčným člověkem, dokud taková kontrola skutečně neproběhne.

---

> **Výkon je smlouva vydání.** Výzkum smí odhalit nepříjemný kompromis. Promované vydání ho nesmí skrývat: deterministická regrese velikosti archivu má **toleranci 0 bajtů**, potvrzené zpomalení mimo dokumentovanou šumovou obálku stejného runneru blokuje promotion a prohrávající workloady zůstávají veřejným důkazem.

## Proč CMPCT existuje

| | CMPCT chce zlepšit |
|---|---|
| **Uložené bajty** | Přesnou identitu, obsahově uvědomělé reprezentace a omezené znovupoužití vztahů místo zacházení s každým souborem jako s nezávislým proudem. |
| **Selektivní přístup** | Číst požadovaný objekt nebo rozsah bez povinné dekomprese celého archivu. |
| **Integrita + obnova** | Kontroly, redundantní metadata a salvage cesty jako skutečné chování readeru, ne disaster-recovery próza. |
| **Věrnost filesystemu** | Zachovat odkazy, sparse soubory, metadata a update sémantiku moderního kontejneru. |
| **Interoperabilita** | Oddělit kanonický reader/writer kontrakt, ZIP export, native core a portability gates od experimentální gramatiky. |
| **Kvalita důkazů** | Veřejná tvrzení odvozovat z reprodukovatelných verzovaných záznamů, zachovat prohry a odmítat benchmarkové divadlo. |

CMPCT není „Zstd s novou příponou“ a nestačí mu vítězství na ručně vybrané složce. Cílem je silnější výchozí archiv v **velikosti, rychlosti, random access, věrnosti, integritě, obnově, aktualizacích a moderní storage sémantice**, bez skrytého přesunu nákladů jinam.

## Nejnovější ověřená fronta

**Projekt v0.29.0 — Mosaic / Residual Program Packing** posouvá ověřený výzkumný engine, zatímco dodávaný kanonický formát zůstává **revision 24**.

| Výzkumné důkazy v0.29 | Výsledek |
|---|---:|
| Přenosný zděděný frontier portfolio | **137,501,815 B** |
| Přímá báze v0.28 | 137,550,416 B |
| Přesná úspora | **48,601 B (0.035333%)** |
| Přenosné workloady | **15** |
| Zlepšeno / regrese | **2 / 0** |
| Přesné v0.28 fallbacky | **13 / 15** |
| Hostile mechanism suites | **4.407362% menší**, 9 zlepšení / 0 regresí přes 18 workloadů |
| Pevný hostile scheduler | **182.454 s → 97.944 s medián (-46.318%)**, vybraný archiv byte-identical |

Na deterministickém resemblance-hostile agregátu 724 souborů / 93,526,384 bajtů ukládá přijatý pokus #5 **47,147,764 B**. Na stejném stromě: ZPAQ m5 47,062,639 B, solid tar+Zstd-19 47,065,652 B, 7z/LZMA2 47,430,343 B, Borg 76,461,311 B a ZIP/Deflate-9 76,690,799 B.

Jde o **párované porovnání uložených bajtů, ne tvrzení o sémantické paritě**. Solid archivy, backup repository a CMPCT mají jiné trade-offy. Trvalý record: [`docs/releases/v0.29.0.md`](../releases/v0.29.0.md); machine-readable evidence: [`benchmarks/history/`](../../benchmarks/history/).

### Dodávané vs fronta

| Autorita | Stav | Význam |
|---|---|---|
| **Kanonický reader/writer** | **r24** | To, co zapisuje `python -m cmpct create` a co musí kanonické readery chápat. |
| **Výzkumná fronta** | **CMPNX11 / v0.29.0** | Experimentální Mosaic + Residual Program Packing; není to r24 syntaxe. |
| **Veřejný povrch** | **0.29.k** | Repo/site/docs prezentace bez autority nad archivní sémantikou. |
| **Licence** | **Apache-2.0 navržena** | Pouze návrh, ne finální veřejné udělení. |

## Co CMPCT umí dnes

Kanonický r24 prototyp zahrnuje content-addressed deduplication, adaptivní Zstandard/raw storage, Zstd dictionaries a micro-solid packs, content-defined chunking, rychlé byte-range reads a parallel decode, hardlink/symlink/sparse preservation, UID/GID/xattrs, ZIP/WHL virtualization, lossless PCM-WAV když vyhrává, raw Deflate reuse pro ZIP export, CRC32 + SHA-256, redundantní head/tail indexes, self-describing blob records, transakční append journal, ZIP export on demand a volitelnou reprodukovatelnou/deterministicky paralelní tvorbu.

v0.29 navíc zkoumá bounded FastCDC units, multi-band similarity search, depth-1 COPY/LITERAL deltas, multi-root Mosaic placement, Residual Program Packing, exact v0.28 fallback, locality/resource ceilings, exact DEFLATE přes pinned memory-safe bridge, Merkle-authenticated records, authenticated tail recovery, strict remote range sources a byte-identical parallel scheduling.

Tyto mechanismy zůstávají mimo kanonický reader, dokud samostatně neprojdou format integration, conformance, hardening, native parity, recovery a portability.

Pravidlo: **výběr podle obsahu, ne folklór podle přípony**.

## Rychlý start

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

Fresh-process CLI je záměrně sériové bez `--workers N`. Gate v0.28 naměřil ~10 ms start thread poolu na malém media stromu; in-process `Builder` ponechává deterministickou paralelní tvorbu jako default.

Volitelný native Linux chunker:

```bash
cc -O3 -shared -fPIC native/cmpct_cdc.c -o src/cmpct/libcmpct_cdc.so
```

Reader na helperu **nezávisí**; hranice chunků jsou explicitně zapsané na disku.

## Výkonnostní pozice

- **velikost:** identický input + encoder semantics nesmí dát větší archiv; tolerance **0 bajtů**;
- **create/extract:** base a candidate na stejném runneru, opakované mediány; potvrzené zpomalení mimo noise envelope blokuje release;
- **evidence:** každá numerická core release commitne čerstvý veřejný benchmark record;
- **corpora:** prohrávající/adversarial workloady zůstávají viditelné.

Viz [`docs/PERFORMANCE_RELEASE_GATE.md`](../PERFORMANCE_RELEASE_GATE.md) a [`docs/BREAKTHROUGH_REHABILITATION.md`](../BREAKTHROUGH_REHABILITATION.md).

## Pořadí čtení pro nového agenta

`docs/AGI_ENGINEERING_STANDARD.md` → `README.md` → `AGENTS.md` → `docs/CURRENT_STATE.md` → nejnovější `docs/releases/` → `docs/PERFORMANCE_RELEASE_GATE.md` → `docs/BREAKTHROUGH_REHABILITATION.md` → `docs/FORMAT.md` → `docs/HISTORY.md` → EntropyGraph/Mosaic docs → `docs/HARDENING.md` → `docs/PORTABILITY.md` + `docs/NATIVE_CORE.md` → `docs/RESEARCH_LOG.md` → `docs/BENCHMARKS.md` + `benchmarks/history/` → `docs/PUBLIC_SURFACE.md` → `docs/ROADMAP.md`.

Nový agent nemá potřebovat soukromé chaty, corpora ani kontext jiného projektu.

## Mapa repository

`src/cmpct/` = kanonická r24 reference; `experiments/` = výzkumná linie; `benchmarks/` = deterministická corpora/gates s historií v `benchmarks/history/`; `fuzz/` = parser/resource útoky; `tools/check_*` = kontraktní kontroly; `site/` = web + Browser Lab; `native/` = akcelerátory/shared core; `docs/` = kontrakty/kampaně/historie/roadmap; `tests/` = format, round-trip, similarity, locality a reproducibility regressions.

## Web

Web má **nejdřív vytvořit dopad, potom dokázat tvrzení a až pak získat důvěru**. Čísla, konkurenti, workloady, prohry a stav core pocházejí z verzované benchmark historie. Striktně odděluje **výzkumnou frontu**, **kanonickou paritu** a **surface revision**. Vizuální agresivita je povolena; vymyšlená vítězství ne.

**Otevřít:** https://fcmo-ai.github.io/.CMPCT/?lang=cs

## Disciplína verzí

1. **Numerická core verze (`MAJOR.MINOR.PATCH`)** — jen za materiální produktový pokrok; po v0.27.1 běžný postup posouvá `MAJOR.MINOR`, `PATCH=0` kvůli packaging compatibility.
2. **Surface (`MAJOR.MINOR.LETTER`)** — site/docs/repo/workflow; aktuálně **`0.29.k`**.
3. **On-disk revision** — pouze když readery potřebují novou gramatiku/sémantiku; kanonicky **r24**.

CI drží osy odděleně a odmítá nepodložené bump-y.

## Historie, provenience a veřejný povrch

CMPCT vyrostl z experimentů Seekable-Zstd, indexed-Zstd, adaptive-framing a ZIP-family. Technická historie zůstává, soukromé corpora/artefakty/unrelated provenance ne. Veřejné benchmarky musí být reprodukovatelné nebo používat záměrně veřejné/syntetické vstupy; historické výsledky **nejsou univerzální garance výkonu**.

CMPCT musí stát samo. Repo a web nesmí vyžadovat ani zveřejnit unrelated interní projekty, soukromá klientská data, corpora, osobní informace, chaty, credentials, private artifact names nebo interní links. Viz `docs/PUBLIC_SURFACE.md`.

## Kanoničnost

Repository nahrazuje chat-local prototypy a benchmark skripty. Materiální engine/archive pokrok získá numerickou release; site/docs/prezentace používají `SURFACE_REVISION`; výzkum zůstává explicitně experimentální do promotion. Experimentální kód nesmí tvrdit kanonickou podporu před integrací do reference reader/writer a conformance.

## Licence

Apache License 2.0 je **aktuálně navržená licence**, ne finálně přijatá. Text je v `LICENSE-APACHE-2.0-PROPOSED.txt`, checklist v `LICENSING.md`. Do dokončení procesu se CMPCT nesmí prezentovat jako definitivně vydané pod Apache-2.0.
