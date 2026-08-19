<div align="center">
  <a href="https://fcmo-ai.github.io/.CMPCT/?lang=nl"><img src="../../.github/assets/repository-hero.svg" width="100%" alt="CMPCT — Archiefformaten hebben vrede gesloten met compromissen. CMPCT niet."></a>

  **Een algemeen lossless archief-/containerproject dat opgeslagen bytes, selectieve toegang, integriteit, herstel en portabiliteit samen vooruit wil brengen.**

  **[Website](https://fcmo-ai.github.io/.CMPCT/?lang=nl)** · **[Browserlab](https://fcmo-ai.github.io/.CMPCT/?lang=nl#lab)** · **[Benchmarks](../BENCHMARKS.md)** · **[Formaat](../FORMAT.md)** · **[Roadmap](../ROADMAP.md)** · **[Agent-startpunt](../CURRENT_STATE.md)**

  <sub>core v0.29.0 · canoniek formaat r24 · surface 0.29.k · pre-1.0</sub>
</div>

> **Gecureerde vertaling.** Dit is een versiebeheerbare semantische bewerking van de mensgerichte README. De Engelse [`README.md`](../../README.md) blijft canoniek. Getallen, paden, formaatnamen en grenzen van bewijs blijven bewust ongewijzigd. Deze tekst wordt niet als door een tweetalige mens beoordeeld aangeduid zolang dat niet werkelijk is gebeurd.

---

> **Prestaties zijn het releasecontract.** Onderzoek mag een ongemakkelijke afruil vinden. Een gepromote release mag die niet verbergen: deterministische regressie in archiefgrootte heeft **0-byte tolerantie**, bevestigde vertraging buiten de gedocumenteerde ruisgrens van dezelfde runner blokkeert promotie, en verliezende workloads blijven openbaar bewijs.

## Waarom CMPCT bestaat

| | CMPCT wil dit beter maken |
|---|---|
| **Opgeslagen bytes** | Exacte identiteit, inhoudsbewuste representaties en begrensd hergebruik van relaties in plaats van elk bestand als losstaande bytestroom te behandelen. |
| **Selectieve toegang** | Het gevraagde object of bereik lezen zonder het hele archief verplicht te decomprimeren. |
| **Integriteit + herstel** | Checks, redundante metadata en salvage-paden als echt readergedrag, niet als disaster-recovery-proza. |
| **Bestandssysteemtrouw** | Links, sparse bestanden, metadata en updatesemantiek van een moderne container behouden. |
| **Interoperabiliteit** | Canoniek reader/writer-contract, ZIP-export, native core en portability gates scheiden van experimentele grammatica. |
| **Bewijskwaliteit** | Publieke claims afleiden uit reproduceerbare vastgelegde records, verliezen bewaren en benchmarktheater weigeren. |

CMPCT is niet “Zstd met een nieuwe extensie” en is niet tevreden met één handgekozen map. Het doel is een sterker standaardarchief op **grootte, snelheid, random access, trouw, integriteit, herstel, updates en moderne opslagsemantiek**, zonder kosten stil elders neer te leggen.

## Nieuwste geverifieerde front

**Project v0.29.0 — Mosaic / Residual Program Packing** brengt de geverifieerde onderzoeksengine vooruit terwijl het verzonden canonieke formaat **revision 24** blijft.

| v0.29 onderzoek | Resultaat |
|---|---:|
| Portable geërfd frontier-portfolio | **137,501,815 B** |
| Directe v0.28-basis | 137,550,416 B |
| Exacte besparing | **48,601 B (0.035333%)** |
| Portable workloads | **15** |
| Verbeterd / regressie | **2 / 0** |
| Exacte v0.28-fallbacks | **13 / 15** |
| Hostile mechanism suites | **4.407362% kleiner**, 9 verbeterd / 0 regressie over 18 workloads |
| Vaste hostile scheduler | **182.454 s → 97.944 s mediaan (-46.318%)**, geselecteerd archief byte-identiek |

Op de deterministische similarity-hostile boom van 724 bestanden / 93,526,384 bytes slaat poging #5 **47,147,764 B** op. Op dezelfde boom: ZPAQ m5 47,062,639 B, solid tar+Zstd-19 47,065,652 B, 7z/LZMA2 47,430,343 B, Borg 76,461,311 B en ZIP/Deflate-9 76,690,799 B.

Dit zijn **gematchte vergelijkingen van opgeslagen bytes, geen semantische-pariteitsclaims**. Solid archieven, backuprepositories en CMPCT hebben andere afruilen. Release-record: [`docs/releases/v0.29.0.md`](../releases/v0.29.0.md); machineleesbaar bewijs: [`benchmarks/history/`](../../benchmarks/history/).

### Verzonden vs frontier

| Autoriteit | Huidige staat | Betekenis |
|---|---|---|
| **Canonieke reader/writer** | **r24** | Wat `python -m cmpct create` schrijft en canonieke readers moeten begrijpen. |
| **Onderzoeksfront** | **CMPNX11 / v0.29.0** | Experimentele Mosaic + Residual Program Packing; geen canonieke r24-syntax. |
| **Publieke surface** | **0.29.k** | Alleen repo/site/docs-presentatie. |
| **Licentie** | **Apache-2.0 voorgesteld** | Voorstel, nog geen definitieve publieke grant. |

## Wat CMPCT vandaag kan

De canonieke r24-prototype ondersteunt content-addressed deduplicatie, adaptieve Zstandard/raw-opslag, Zstd-dictionaries en micro-solid packs, content-defined chunking, snelle byte-range reads en parallel decode, hardlink/symlink/sparse-behoud, UID/GID/xattrs, ZIP/WHL-virtualisatie, lossless PCM-WAV waar winstgevend, raw Deflate-hergebruik voor ZIP-export, CRC32 + SHA-256, redundante head/tail-indexen, zelfbeschrijvende blobrecords, transactioneel append-journal, ZIP-export op aanvraag en optionele reproduceerbare/deterministisch parallelle creatie.

v0.29 onderzoekt daarnaast begrensde FastCDC-units, multi-band similarity search, gemeten depth-1 COPY/LITERAL-delta’s, begrensde multi-root Mosaic-placement, Residual Program Packing, exacte v0.28-fallbacks, locality/resource ceilings, exacte optionele DEFLATE-precompressie via een gepinde memory-safe bridge, Merkle-authenticated records, authenticated tail recovery, strikte remote range sources en byte-identieke parallelle scheduling.

Deze mechanismen blijven buiten de canonieke reader totdat format integration, conformance, hardening, native parity, recovery en portability onafhankelijk slagen.

Hoofdregel: **inhoudsgestuurde selectie, geen extensie-folklore**.

## Snel starten

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

Fresh-process CLI-creatie is bewust serieel tenzij `--workers N` is opgegeven. Het v0.28-gate vond ~10 ms thread-pool startup op een kleine mediaboom; de in-process `Builder` API houdt deterministische parallelle creatie standaard aan.

Optionele native Linux-chunker:

```bash
cc -O3 -shared -fPIC native/cmpct_cdc.c -o src/cmpct/libcmpct_cdc.so
```

De reader is **niet afhankelijk** van deze helper; chunkgrenzen worden expliciet op disk vastgelegd.

## Prestatiepositie

- **archiefgrootte:** identieke input + encodersemantiek mag nooit groter worden; **0 bytes** tolerantie;
- **create/extract:** base en candidate op dezelfde runner met herhaalde medianen; bevestigde vertraging buiten de ruisgrens blokkeert;
- **bewijs:** elke numerieke core-release commit een nieuw openbaar benchmarkrecord;
- **corpora:** verliezende/adversarial workloads blijven zichtbaar.

Zie [`docs/PERFORMANCE_RELEASE_GATE.md`](../PERFORMANCE_RELEASE_GATE.md) en [`docs/BREAKTHROUGH_REHABILITATION.md`](../BREAKTHROUGH_REHABILITATION.md).

## Leesvolgorde nieuwe agent

`docs/AGI_ENGINEERING_STANDARD.md` → `README.md` → `AGENTS.md` → `docs/CURRENT_STATE.md` → nieuwste `docs/releases/` → `docs/PERFORMANCE_RELEASE_GATE.md` → `docs/BREAKTHROUGH_REHABILITATION.md` → `docs/FORMAT.md` → `docs/HISTORY.md` → EntropyGraph/Mosaic-docs → `docs/HARDENING.md` → `docs/PORTABILITY.md` + `docs/NATIVE_CORE.md` → `docs/RESEARCH_LOG.md` → `docs/BENCHMARKS.md` + `benchmarks/history/` → `docs/PUBLIC_SURFACE.md` → `docs/ROADMAP.md`.

Een nieuwe agent hoort geen private chats, private corpora of unrelated projectcontext nodig te hebben.

## Repositorykaart

`src/cmpct/` = canonieke r24-referentie; `experiments/` = onderzoekslijn; `benchmarks/` = deterministische corpora/gates, met duurzame records in `benchmarks/history/`; `fuzz/` = parser/resource-aanvallen; `tools/check_*` = contractchecks; `site/` = site + Browser Lab; `native/` = accelerators/shared core; `docs/` = contracten/campagnes/historie/roadmap; `tests/` = format-, round-trip-, similarity-, locality- en reproducibility-regressies.

## Website

De live site is ontworpen om **eerst impact te maken, daarna de claim te bewijzen en vervolgens vertrouwen te verdienen**. Prestatiecijfers, competitor ladder, workloadmatrix, verliezen en core-status komen uit vastgelegde benchmarkhistorie. De site scheidt **onderzoeksfront**, **canonieke pariteit** en **surface revision** strikt. Visueel mag hij agressief zijn; grenzen vervagen of een overwinning verzinnen mag niet.

**Open:** https://fcmo-ai.github.io/.CMPCT/?lang=nl

## Versiediscipline

1. **Numerieke core-versie (`MAJOR.MINOR.PATCH`)** — alleen voor materiële productverbetering; na v0.27.1 beweegt normale vooruitgang `MAJOR.MINOR`, met `PATCH=0` voor packaging compatibility.
2. **Surface revision (`MAJOR.MINOR.LETTER`)** — site/docs/repo-presentatie/workflow; huidig **`0.29.k`**.
3. **On-disk revision** — alleen bij nieuwe readergrammatica/storage-semantiek; canoniek **r24**.

CI houdt deze assen gescheiden en weigert ongefundeerde numerieke bumps.

## Geschiedenis, provenance en publieke surface

CMPCT groeide uit Seekable-Zstd, indexed-Zstd, adaptive-framing en ZIP-familie-experimenten. Technische geschiedenis blijft; private corpusidentiteiten, private artifacts en unrelated provenance niet. Publieke benchmarks moeten reproduceerbaar zijn of bewust publieke/synthetische input gebruiken; historische resultaten zijn **geen universele prestatiegarantie**.

CMPCT moet op zichzelf staan. Repo en site mogen geen unrelated interne projecten, private klantdata, private corpora, persoonsgegevens, chatlogs, credentials, private artifactnamen of interne links vereisen of blootstellen. Zie `docs/PUBLIC_SURFACE.md`.

## Canonicaliteit

Dit repository vervangt chatlokale CMPCT-prototypes en benchmarkscripts. Materiële engine/archive-vooruitgang verdient een numerieke release; site/docs/presentatie gebruiken `SURFACE_REVISION`; onderzoek blijft expliciet experimenteel tot promotie. Experimentele code mag geen canonieke ondersteuning claimen vóór integratie in reference reader/writer en conformance.

## Licentie

Apache License 2.0 is de **huidige voorgestelde licentie**, nog niet definitief aangenomen. De ongewijzigde voorgestelde tekst staat in `LICENSE-APACHE-2.0-PROPOSED.txt`, de adoption-checklist in `LICENSING.md`. Tot afronding mag CMPCT niet als definitief onder Apache-2.0 uitgebracht worden voorgesteld.
