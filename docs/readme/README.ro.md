<div align="center">
  <a href="https://fcmo-ai.github.io/.CMPCT/?lang=ro"><img src="../../.github/assets/repository-hero.svg" width="100%" alt="CMPCT — Formatele de arhivă au făcut pace cu compromisul. CMPCT nu."></a>

  **Un proiect general de arhivă/container fără pierderi, conceput să avanseze împreună octeții stocați, accesul selectiv, integritatea, recuperarea și portabilitatea.**

  **[Site](https://fcmo-ai.github.io/.CMPCT/?lang=ro)** · **[Browser Lab](https://fcmo-ai.github.io/.CMPCT/?lang=ro#lab)** · **[Benchmarkuri](../BENCHMARKS.md)** · **[Format](../FORMAT.md)** · **[Roadmap](../ROADMAP.md)** · **[Intrare agenți](../CURRENT_STATE.md)**

  <sub>core v0.29.0 · format canonic r24 · suprafață 0.29.k · pre-1.0</sub>
</div>

> **Traducere curatoriată.** Aceasta este o adaptare semantică versionată a README-ului pentru oameni. [`README.md`](../../README.md) în engleză rămâne autoritatea canonică. Numerele, căile, numele formatelor și limitele dovezilor sunt păstrate intenționat. Textul nu este etichetat drept revizuit de un om bilingv până când acea revizie chiar are loc.

---

> **Performanța este contractul versiunii.** Cercetarea poate găsi un compromis incomod. O versiune promovată nu îl poate ascunde: regresia deterministă a dimensiunii arhivei are **toleranță 0 octeți**, o încetinire confirmată în afara marjei documentate a aceluiași runner blochează promovarea, iar workloadurile pierzătoare rămân dovezi publice.

## De ce există CMPCT

| | CMPCT încearcă să îmbunătățească |
|---|---|
| **Octeți stocați** | Identitate exactă, reprezentări conștiente de conținut și reutilizare limitată a relațiilor în locul tratării fiecărui fișier ca flux izolat. |
| **Acces selectiv** | Citește obiectul sau intervalul cerut fără decompresia obligatorie a întregii arhive. |
| **Integritate + recuperare** | Verificări, metadate redundante și căi de salvare ca comportament real al readerului, nu proză de disaster recovery. |
| **Fidelitate filesystem** | Păstrează linkuri, sparse files, metadate și semantica de update a unui container modern. |
| **Interoperabilitate** | Separă contractul canonic reader/writer, exportul ZIP, native core și porțile de portabilitate de gramatica experimentală. |
| **Calitatea dovezilor** | Afirmații publice din înregistrări reproductibile versionate, pierderi păstrate și fără teatru de benchmark. |

CMPCT nu este „Zstd cu o extensie nouă” și nu se mulțumește să câștige pe un folder ales manual. Ținta este o arhivă implicită mai puternică la **dimensiune, viteză, random access, fidelitate, integritate, recuperare, actualizări și semantică modernă de storage**, fără a muta costul în tăcere în altă parte.

## Cea mai recentă frontieră verificată

**Project v0.29.0 — Mosaic / Residual Program Packing** avansează motorul de cercetare verificat, în timp ce formatul canonic livrat rămâne **revision 24**.

| Dovezi v0.29 | Rezultat |
|---|---:|
| Portofoliu portabil moștenit | **137,501,815 B** |
| Bază directă v0.28 | 137,550,416 B |
| Economie exactă | **48,601 B (0.035333%)** |
| Workloaduri portabile | **15** |
| Îmbunătățite / regresate | **2 / 0** |
| Fallbackuri exacte v0.28 | **13 / 15** |
| Hostile mechanism suites | **4.407362% mai mic**, 9 îmbunătățite / 0 regresate în 18 workloaduri |
| Scheduler ostil fix | **182.454 s → 97.944 s mediană (-46.318%)**, arhivă selectată byte-identical |

Pe agregatul determinist resemblance-hostile cu 724 fișiere / 93,526,384 octeți, tentativa acceptată #5 stochează **47,147,764 B**. Pe același arbore: ZPAQ m5 47,062,639 B, solid tar+Zstd-19 47,065,652 B, 7z/LZMA2 47,430,343 B, Borg 76,461,311 B, ZIP/Deflate-9 76,690,799 B.

Acestea sunt **comparații asociate de octeți stocați, nu afirmații de paritate semantică**. Solid archives, repository-urile de backup și CMPCT au trade-offuri diferite. Record durabil: [`docs/releases/v0.29.0.md`](../releases/v0.29.0.md); dovezi machine-readable: [`benchmarks/history/`](../../benchmarks/history/).

### Livrat vs frontieră

| Autoritate | Stare | Sens |
|---|---|---|
| **Reader/writer canonic** | **r24** | Ce scrie `python -m cmpct create` și ce trebuie să înțeleagă readerele canonice. |
| **Frontieră de cercetare** | **CMPNX11 / v0.29.0** | Mosaic + Residual Program Packing experimental; nu sintaxă r24. |
| **Suprafață publică** | **0.29.k** | Prezentare repo/site/docs, fără autoritate asupra semanticii arhivei. |
| **Licență** | **Apache-2.0 propusă** | Propunere, nu grant public final. |

## Ce poate face CMPCT azi

Prototipul canonic r24 include content-addressed deduplication, Zstandard/raw adaptiv, dicționare Zstd și micro-solid packs, content-defined chunking, byte-range reads rapide și parallel decode, hardlink/symlink/sparse preservation, UID/GID/xattrs, ZIP/WHL virtualization, PCM-WAV lossless când câștigă, raw Deflate reuse pentru ZIP, CRC32 + SHA-256, head/tail indexes redundante, self-describing blob records, append journal tranzacțional, export ZIP la cerere și creare reproductibilă/determinist paralelă opțională.

v0.29 cercetează și bounded FastCDC units, multi-band similarity search, depth-1 COPY/LITERAL deltas, multi-root Mosaic placement, Residual Program Packing, exact v0.28 fallback, locality/resource ceilings, exact DEFLATE prin pinned memory-safe bridge, Merkle-authenticated records, authenticated tail recovery, strict remote range sources și byte-identical parallel scheduling.

Mecanismele rămân în afara readerului canonic până trec independent format integration, conformance, hardening, native parity, recovery și portability.

Regula: **selecție ghidată de conținut, nu folclor ghidat de extensie**.

## Pornire rapidă

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

Fresh-process CLI este serial intenționat fără `--workers N`. Gate-ul v0.28 a găsit ~10 ms cost de startup al thread poolului pe un mic arbore media; API-ul in-process `Builder` păstrează implicit paralelismul determinist.

Chunker native Linux opțional:

```bash
cc -O3 -shared -fPIC native/cmpct_cdc.c -o src/cmpct/libcmpct_cdc.so
```

Readerul **nu depinde** de helper; limitele chunkurilor sunt înregistrate explicit pe disc.

## Poziția de performanță

- **dimensiune:** input identic + encoder semantics nu pot produce o arhivă mai mare; **0 octeți** toleranță;
- **create/extract:** base și candidate pe același runner cu mediane repetate; încetinirea confirmată dincolo de noise envelope blochează;
- **evidence:** fiecare core release numeric committează un record public nou;
- **corpora:** workloadurile pierzătoare/adversarial rămân vizibile.

Vezi [`docs/PERFORMANCE_RELEASE_GATE.md`](../PERFORMANCE_RELEASE_GATE.md) și [`docs/BREAKTHROUGH_REHABILITATION.md`](../BREAKTHROUGH_REHABILITATION.md).

## Ordinea de citire pentru un agent nou

`docs/AGI_ENGINEERING_STANDARD.md` → `README.md` → `AGENTS.md` → `docs/CURRENT_STATE.md` → cel mai nou `docs/releases/` → `docs/PERFORMANCE_RELEASE_GATE.md` → `docs/BREAKTHROUGH_REHABILITATION.md` → `docs/FORMAT.md` → `docs/HISTORY.md` → documentele EntropyGraph/Mosaic → `docs/HARDENING.md` → `docs/PORTABILITY.md` + `docs/NATIVE_CORE.md` → `docs/RESEARCH_LOG.md` → `docs/BENCHMARKS.md` + `benchmarks/history/` → `docs/PUBLIC_SURFACE.md` → `docs/ROADMAP.md`.

Un agent nou nu trebuie să depindă de chat privat, corpora private sau contextul altui proiect.

## Harta repository-ului

`src/cmpct/` = referința canonică r24; `experiments/` = linia de cercetare; `benchmarks/` = corpora/gates deterministe și `benchmarks/history/`; `fuzz/` = atacuri parser/resource; `tools/check_*` = verificări de contract; `site/` = site + Browser Lab; `native/` = acceleratoare/shared core; `docs/` = contracte/campanii/istoric/roadmap; `tests/` = regresii format, round-trip, similarity, locality și reproducibility.

## Site

Site-ul trebuie să **creeze impact întâi, să dovedească afirmația apoi și să câștige încredere la final**. Cifrele, competitorii, workloadurile, pierderile și starea core vin din istoricul benchmark versionat. Separă strict **frontiera de cercetare**, **paritatea canonică** și **surface revision**. Poate fi agresiv vizual; nu poate inventa victorii.

**Deschide:** https://fcmo-ai.github.io/.CMPCT/?lang=ro

## Disciplina versiunilor

1. **Core numeric (`MAJOR.MINOR.PATCH`)** — doar pentru progres material; după v0.27.1 progresul normal mută `MAJOR.MINOR`, cu `PATCH=0` pentru packaging compatibility.
2. **Surface (`MAJOR.MINOR.LETTER`)** — site/docs/repo/workflow; acum **`0.29.k`**.
3. **On-disk revision** — doar pentru gramatică/semantică nouă necesară readerelor; canonic **r24**.

CI ține axele separate și respinge bumpuri nejustificate.

## Istoric, proveniență și suprafață publică

CMPCT a crescut din experimente Seekable-Zstd, indexed-Zstd, adaptive-framing și ZIP-family. Istoria tehnică rămâne; identitățile corpora private, artefactele private și unrelated provenance nu. Benchmarkurile publice trebuie să fie reproductibile sau să folosească intrări deliberat publice/sintetice; rezultatele istorice **nu sunt o garanție universală**.

CMPCT trebuie să stea singur. Repo și site nu pot cere sau expune proiecte interne fără legătură, date private de client, corpora private, date personale, transcrieri de chat, credentials, nume private de artefact sau linkuri interne. Vezi `docs/PUBLIC_SURFACE.md`.

## Canonicitate

Repository-ul înlocuiește prototipurile și benchmarkurile chat-local. Progresul material engine/archive primește release numeric; site/docs/prezentare folosesc `SURFACE_REVISION`; cercetarea rămâne explicit experimentală până la promotion. Codul experimental nu poate pretinde suport canonic fără integrare în reference reader/writer și conformance.

## Licență

Apache License 2.0 este **licența propusă acum**, nu cea final adoptată. Text: `LICENSE-APACHE-2.0-PROPOSED.txt`; checklist: `LICENSING.md`. Până la finalizare, CMPCT nu trebuie prezentat ca lansat definitiv sub Apache-2.0.
