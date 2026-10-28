<div align="center">
  <a href="https://fcmo-ai.github.io/.CMPCT/?lang=sv"><img src="../../.github/assets/repository-hero.svg" width="100%" alt="CMPCT — Arkivformat har accepterat kompromisser. CMPCT har inte det."></a>

  **Ett generellt förlustfritt arkiv-/containerprojekt byggt för att flytta lagrade byte, selektiv åtkomst, integritet, återställning och portabilitet framåt tillsammans.**

  **[Webbplats](https://fcmo-ai.github.io/.CMPCT/?lang=sv)** · **[Webblabb](https://fcmo-ai.github.io/.CMPCT/?lang=sv#lab)** · **[Benchmarks](../BENCHMARKS.md)** · **[Format](../FORMAT.md)** · **[Roadmap](../ROADMAP.md)** · **[Agentstart](../CURRENT_STATE.md)**

  <sub>core v0.29.0 · kanoniskt format r24 · yta 0.29.k · pre-1.0</sub>
</div>

> **Kurerad översättning.** Detta är en versionsstyrd semantisk anpassning av den människoorienterade README:n. Engelska [`README.md`](../../README.md) är fortsatt kanonisk auktoritet. Siffror, sökvägar, formatnamn och bevisgränser bevaras avsiktligt. Texten märks inte som mänskligt tvåspråkigt granskad innan sådan granskning faktiskt har skett.

---

> **Prestanda är releasekontraktet.** Forskning får hitta en obekväm avvägning. En promotad release får inte dölja den: deterministisk regression i arkivstorlek har **0 byte tolerans**, bekräftad inbromsning utanför dokumenterad brusmarginal på samma runner blockerar promotion, och förlorande workloads förblir offentliga bevis.

## Varför CMPCT finns

| | CMPCT vill förbättra |
|---|---|
| **Lagrade byte** | Exakt identitet, innehållsmedvetna representationer och begränsat relationsåterbruk i stället för att behandla varje fil som en fristående ström. |
| **Selektiv åtkomst** | Läs objektet eller intervallet som efterfrågas utan att obligatoriskt dekomprimera hela arkivet. |
| **Integritet + återställning** | Checks, redundant metadata och salvage-vägar som verkligt readerbeteende, inte disaster-recovery-prosa. |
| **Filsystemtrohet** | Bevara länkar, sparse files, metadata och modern update-semantik. |
| **Interoperabilitet** | Separera kanoniskt reader/writer-kontrakt, ZIP-export, native core och portability gates från experimentell grammatik. |
| **Beviskvalitet** | Offentliga claims från reproducerbara versionsstyrda records, bevarade förluster och inget benchmarkteater. |

CMPCT är inte ”Zstd med en ny filändelse” och nöjer sig inte med att vinna på en handplockad katalog. Målet är ett starkare standardarkiv för **storlek, hastighet, random access, trohet, integritet, återställning, uppdateringar och modern lagringssemantik** utan att smyga kostnaden någon annanstans.

## Senaste verifierade front

**Projekt v0.29.0 — Mosaic / Residual Program Packing** flyttar den verifierade forskningsmotorn framåt medan levererat kanoniskt format förblir **revision 24**.

| v0.29 forskningsbevis | Resultat |
|---|---:|
| Portabelt ärvt frontier-portfolio | **137,501,815 B** |
| Direkt v0.28-bas | 137,550,416 B |
| Exakt besparing | **48,601 B (0.035333%)** |
| Portabla workloads | **15** |
| Förbättrade / regressionsfall | **2 / 0** |
| Exakta v0.28-fallbacks | **13 / 15** |
| Hostile mechanism suites | **4.407362% mindre**, 9 förbättrade / 0 regressionsfall över 18 workloads |
| Fast hostile scheduler | **182.454 s → 97.944 s median (-46.318%)**, valt arkiv byte-identiskt |

På den deterministiska resemblance-hostile aggregationen med 724 filer / 93,526,384 byte lagrar accepterat försök #5 **47,147,764 B**. På samma träd: ZPAQ m5 47,062,639 B, solid tar+Zstd-19 47,065,652 B, 7z/LZMA2 47,430,343 B, Borg 76,461,311 B och ZIP/Deflate-9 76,690,799 B.

Detta är **matchade jämförelser av lagrade byte, inte semantiska paritetsclaims**. Solid-arkiv, backuprepositories och CMPCT har olika trade-offs. Beständig record: [`docs/releases/v0.29.0.md`](../releases/v0.29.0.md); machine-readable evidence: [`benchmarks/history/`](../../benchmarks/history/).

### Levererat vs front

| Auktoritet | Status | Betydelse |
|---|---|---|
| **Kanonisk reader/writer** | **r24** | Vad `python -m cmpct create` skriver och kanoniska readers måste förstå. |
| **Forskningsfront** | **CMPNX11 / v0.29.0** | Experimentell Mosaic + Residual Program Packing; inte r24-syntax. |
| **Offentlig yta** | **0.29.k** | Repo/site/docs-presentation utan semantisk auktoritet. |
| **Licens** | **Apache-2.0 föreslagen** | Förslag, inte slutlig offentlig grant. |

## Vad CMPCT kan idag

Kanonisk r24 innehåller content-addressed deduplication, adaptiv Zstandard/raw storage, Zstd dictionaries och micro-solid packs, content-defined chunking, snabba byte-range reads och parallel decode, hardlink/symlink/sparse preservation, UID/GID/xattrs, ZIP/WHL virtualization, lossless PCM-WAV när det vinner, raw Deflate reuse för ZIP-export, CRC32 + SHA-256, redundanta head/tail indexes, self-describing blob records, transaction append journal, on-demand ZIP-export och valfri reproducerbar/deterministiskt parallell creation.

v0.29 utforskar dessutom bounded FastCDC units, multi-band similarity search, depth-1 COPY/LITERAL deltas, multi-root Mosaic placement, Residual Program Packing, exact v0.28 fallback, locality/resource ceilings, exact DEFLATE via pinned memory-safe bridge, Merkle-authenticated records, authenticated tail recovery, strict remote range sources och byte-identical parallel scheduling.

Forskningsmekanismerna hålls utanför den kanoniska readern tills format integration, conformance, hardening, native parity, recovery och portability klaras separat.

Regel: **innehållsstyrt val, inte filändelsefolklore**.

## Snabbstart

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

Fresh-process CLI är avsiktligt seriell utan `--workers N`. v0.28-gaten såg ~10 ms thread-pool startup på ett litet mediaträd; in-process `Builder` behåller deterministisk parallell creation som standard.

Valfri native Linux-chunker:

```bash
cc -O3 -shared -fPIC native/cmpct_cdc.c -o src/cmpct/libcmpct_cdc.so
```

Readern **beror inte** på hjälparen; chunkgränser lagras explicit på disk.

## Prestandaposition

- **storlek:** identisk input + encoder semantics får aldrig skapa större arkiv; **0 byte** tolerans;
- **create/extract:** base och candidate på samma runner med upprepade medianer; bekräftad inbromsning utanför noise envelope blockerar;
- **evidence:** varje numerisk core release committar en färsk offentlig benchmarkrecord;
- **corpora:** förlorande/adversarial workloads förblir synliga.

Se [`docs/PERFORMANCE_RELEASE_GATE.md`](../PERFORMANCE_RELEASE_GATE.md) och [`docs/BREAKTHROUGH_REHABILITATION.md`](../BREAKTHROUGH_REHABILITATION.md).

## Läsordning för ny agent

`docs/AGI_ENGINEERING_STANDARD.md` → `README.md` → `AGENTS.md` → `docs/CURRENT_STATE.md` → senaste `docs/releases/` → `docs/PERFORMANCE_RELEASE_GATE.md` → `docs/BREAKTHROUGH_REHABILITATION.md` → `docs/FORMAT.md` → `docs/HISTORY.md` → EntropyGraph/Mosaic-dokument → `docs/HARDENING.md` → `docs/PORTABILITY.md` + `docs/NATIVE_CORE.md` → `docs/RESEARCH_LOG.md` → `docs/BENCHMARKS.md` + `benchmarks/history/` → `docs/PUBLIC_SURFACE.md` → `docs/ROADMAP.md`.

En ny agent ska inte behöva privata chattar, privata corpora eller unrelated projektkontext.

## Repositorykarta

`src/cmpct/` = kanonisk r24-reference; `experiments/` = forskningslinje; `benchmarks/` = deterministiska corpora/gates och `benchmarks/history/`; `fuzz/` = parser/resource-attacker; `tools/check_*` = kontraktskontroller; `site/` = site + Browser Lab; `native/` = acceleratorer/shared core; `docs/` = kontrakt/kampanjer/historik/roadmap; `tests/` = format, round-trip, similarity, locality och reproducibility regressions.

## Webbplats

Sajten är byggd för att **skapa effekt först, bevisa claimen sedan och förtjäna förtroende sist**. Siffror, konkurrenter, workloads, förluster och core-status kommer från versionsstyrd benchmarkhistorik. Den skiljer strikt mellan **forskningsfront**, **kanonisk paritet** och **surface revision**. Visuellt aggressiv är tillåtet; påhittade vinster är det inte.

**Öppna:** https://fcmo-ai.github.io/.CMPCT/?lang=sv

## Versionsdisciplin

1. **Numerisk core (`MAJOR.MINOR.PATCH`)** — bara för materiell produktförbättring; efter v0.27.1 flyttar normal progression `MAJOR.MINOR`, `PATCH=0` för packaging compatibility.
2. **Surface (`MAJOR.MINOR.LETTER`)** — site/docs/repo/workflow; nu **`0.29.k`**.
3. **On-disk revision** — bara när readers behöver ny grammatik/semantik; kanoniskt **r24**.

CI håller axlarna separata och vägrar oförtjänta bumps.

## Historik, proveniens och offentlig yta

CMPCT växte ur Seekable-Zstd, indexed-Zstd, adaptive-framing och ZIP-family experiment. Teknisk historik bevaras; privata corpusidentiteter, artefakter och unrelated provenance gör det inte. Offentliga benchmarks måste vara reproducerbara eller använda avsiktligt offentliga/syntetiska inputs; historiska resultat är **ingen universell prestandagaranti**.

CMPCT ska stå på egna ben. Repo/site får inte kräva eller exponera unrelated interna projekt, privat kunddata, corpora, personuppgifter, chattranskript, credentials, privata artefaktnamn eller interna länkar. Se `docs/PUBLIC_SURFACE.md`.

## Kanonicitet

Repositoryt ersätter chat-local prototyper och benchmarkscript. Materiell engine/archive-progress får numerisk release; site/docs/presentation använder `SURFACE_REVISION`; forskning förblir uttryckligen experimentell fram till promotion. Experimentell kod får inte påstå kanoniskt stöd utan integration i reference reader/writer och conformance.

## Licens

Apache License 2.0 är den **nu föreslagna licensen**, inte den slutligt antagna. Text: `LICENSE-APACHE-2.0-PROPOSED.txt`; adoption checklist: `LICENSING.md`. Fram till slutförandet får CMPCT inte beskrivas som slutligen publicerat under Apache-2.0.
