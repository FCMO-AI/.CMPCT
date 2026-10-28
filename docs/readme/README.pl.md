<div align="center">
  <a href="https://fcmo-ai.github.io/.CMPCT/?lang=pl"><img src="../../.github/assets/repository-hero.svg" width="100%" alt="CMPCT — Formaty archiwów pogodziły się z kompromisem. CMPCT nie."></a>

  **Uniwersalny, bezstratny projekt archiwum/kontenera, który rozwija jednocześnie rozmiar, dostęp selektywny, integralność, odzyskiwanie i przenośność.**

  **[Strona](https://fcmo-ai.github.io/.CMPCT/?lang=pl)** · **[Laboratorium](https://fcmo-ai.github.io/.CMPCT/?lang=pl#lab)** · **[Benchmarki](../BENCHMARKS.md)** · **[Format](../FORMAT.md)** · **[Roadmap](../ROADMAP.md)** · **[Start dla agentów](../CURRENT_STATE.md)**

  <sub>core v0.29.0 · format kanoniczny r24 · powierzchnia 0.29.k · pre-1.0</sub>
</div>

> **Tłumaczenie kuratorskie.** To wersjonowana adaptacja semantyczna README przeznaczonego dla ludzi. Angielski [`README.md`](../../README.md) pozostaje źródłem kanonicznym. Liczby, ścieżki, nazwy formatów i granice dowodów są zachowane. Tekst nie jest oznaczony jako sprawdzony przez dwujęzycznego człowieka, dopóki taka weryfikacja faktycznie nie nastąpi.

---

> **Wydajność jest kontraktem wydania.** Badania mogą ujawnić niewygodny kompromis. Promowane wydanie nie może go ukrywać: deterministyczna regresja rozmiaru archiwum ma **tolerancję 0 bajtów**, potwierdzone spowolnienie poza udokumentowanym marginesem szumu tego samego runnera blokuje promocję, a przegrywające workloady pozostają publicznym dowodem.

## Po co istnieje CMPCT

| | Co CMPCT chce poprawić |
|---|---|
| **Zapisane bajty** | Dokładna tożsamość, reprezentacje świadome treści i ograniczone ponowne użycie relacji zamiast traktowania każdego pliku jak osobnego strumienia. |
| **Dostęp selektywny** | Odczyt żądanego obiektu lub zakresu bez obowiązkowej dekompresji całego archiwum. |
| **Integralność + odzyskiwanie** | Kontrole, redundantne metadane i ścieżki ratunkowe jako realne zachowanie czytnika, nie marketingowa proza. |
| **Wierność systemu plików** | Zachowanie linków, sparse files, metadanych i semantyki aktualizacji nowoczesnego kontenera. |
| **Interoperacyjność** | Wyraźne oddzielenie kanonicznego kontraktu reader/writer, eksportu ZIP, native core i gate’ów przenośności od gramatyki eksperymentalnej. |
| **Jakość dowodów** | Publiczne twierdzenia z reprodukowalnych zapisanych rekordów, zachowane porażki i brak teatru benchmarkowego. |

CMPCT nie jest „Zstd z nowym rozszerzeniem” i nie wystarcza mu zwycięstwo na ręcznie dobranym katalogu. Celem jest mocniejszy domyślny format w **rozmiarze, szybkości, random access, wierności, integralności, odzyskiwaniu, aktualizacjach i nowoczesnej semantyce storage**, bez ukrytego przenoszenia kosztu gdzie indziej.

## Najnowszy zweryfikowany front

**Projekt v0.29.0 — Mosaic / Residual Program Packing** rozwija zweryfikowany silnik badawczy, podczas gdy dostarczany format kanoniczny pozostaje w **rewizji 24**.

| Dowody v0.29 | Wynik |
|---|---:|
| Przenośny odziedziczony portfel frontu | **137,501,815 B** |
| Bezpośrednia baza v0.28 | 137,550,416 B |
| Dokładna oszczędność | **48,601 B (0.035333%)** |
| Workloady przenośne | **15** |
| Poprawione / regresje | **2 / 0** |
| Dokładne fallbacki v0.28 | **13 / 15** |
| Hostile mechanism suites | **4.407362% mniej**, 9 poprawionych / 0 regresji w 18 workloadach |
| Stały hostile scheduler | **182.454 s → 97.944 s mediana (-46.318%)**, wybrane archiwum byte-identical |

Na deterministycznym, resemblance-hostile agregacie 724 plików / 93,526,384 bajtów zaakceptowana próba #5 zapisuje **47,147,764 B**. Na tym samym drzewie: ZPAQ m5 47,062,639 B, solid tar+Zstd-19 47,065,652 B, 7z/LZMA2 47,430,343 B, Borg 76,461,311 B, ZIP/Deflate-9 76,690,799 B.

To **sparowane porównania zapisanych bajtów, nie twierdzenia o parytecie semantycznym**. Solid archives, repozytoria backupowe i CMPCT mają inne kompromisy. Trwały rekord: [`docs/releases/v0.29.0.md`](../releases/v0.29.0.md); dane maszynowe: [`benchmarks/history/`](../../benchmarks/history/).

### Dostarczane vs front

| Autorytet | Stan | Znaczenie |
|---|---|---|
| **Kanoniczny reader/writer** | **r24** | To, co zapisuje `python -m cmpct create` i co muszą rozumieć kanoniczne czytniki. |
| **Front badawczy** | **CMPNX11 / v0.29.0** | Mosaic + Residual Program Packing; nie kanoniczna składnia r24. |
| **Powierzchnia publiczna** | **0.29.k** | Prezentacja repo/site/docs, bez wpływu na semantykę archiwum. |
| **Licencja** | **Apache-2.0 proponowana** | Tylko propozycja, jeszcze nie ostateczne publiczne nadanie. |

## Co CMPCT potrafi dziś

Kanonical r24 obejmuje content-addressed deduplication, adaptacyjny Zstandard/raw, słowniki Zstd i micro-solid packs, content-defined chunking, szybkie byte-range reads i parallel decode, zachowanie hardlink/symlink/sparse, UID/GID/xattrs, ZIP/WHL virtualization, lossless PCM-WAV tam gdzie wygrywa, raw Deflate reuse do eksportu ZIP, CRC32 + SHA-256, redundantne head/tail indexes, self-describing blob records, transakcyjny append journal, eksport ZIP na żądanie oraz opcjonalną reprodukowalną i deterministycznie równoległą kreację.

v0.29 dodatkowo bada ograniczone jednostki FastCDC, multi-band similarity search, COPY/LITERAL depth-1 deltas, multi-root Mosaic placement, Residual Program Packing, dokładny fallback v0.28, limity locality/resource, opcjonalny exact DEFLATE przez pinned memory-safe bridge, Merkle-authenticated records, authenticated tail recovery, strict remote range sources i byte-identical parallel scheduling.

Mechanizmy badawcze pozostają poza kanonicznym readerem do czasu niezależnego przejścia integracji formatu, conformance, hardening, native parity, recovery i portability.

Zasada: **wybór według treści, nie folklor według rozszerzenia**.

## Szybki start

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

Fresh-process CLI jest celowo serial, chyba że podasz `--workers N`. Gate v0.28 pokazał ~10 ms kosztu startu thread pool na małym drzewie media; in-process `Builder` zachowuje domyślnie deterministyczną równoległość.

Opcjonalny native chunker Linux:

```bash
cc -O3 -shared -fPIC native/cmpct_cdc.c -o src/cmpct/libcmpct_cdc.so
```

Reader **nie zależy** od tego helpera; granice chunków są jawnie zapisane na dysku.

## Pozycja wydajnościowa

- **rozmiar:** identyczny input + encoder semantics nie mogą dać większego archiwum; **0 bajtów** tolerancji;
- **create/extract:** base i candidate na tym samym runnerze, powtarzane mediany; potwierdzone spowolnienie poza noise envelope blokuje release;
- **evidence:** każda numerowana wersja commit-uje świeży publiczny rekord;
- **corpora:** przegrywające/adversarial workloady pozostają widoczne.

Patrz [`docs/PERFORMANCE_RELEASE_GATE.md`](../PERFORMANCE_RELEASE_GATE.md) i [`docs/BREAKTHROUGH_REHABILITATION.md`](../BREAKTHROUGH_REHABILITATION.md).

## Kolejność czytania dla nowego agenta

`docs/AGI_ENGINEERING_STANDARD.md` → `README.md` → `AGENTS.md` → `docs/CURRENT_STATE.md` → najnowsze `docs/releases/` → `docs/PERFORMANCE_RELEASE_GATE.md` → `docs/BREAKTHROUGH_REHABILITATION.md` → `docs/FORMAT.md` → `docs/HISTORY.md` → dokumenty EntropyGraph/Mosaic → `docs/HARDENING.md` → `docs/PORTABILITY.md` + `docs/NATIVE_CORE.md` → `docs/RESEARCH_LOG.md` → `docs/BENCHMARKS.md` + `benchmarks/history/` → `docs/PUBLIC_SURFACE.md` → `docs/ROADMAP.md`.

Nowy agent nie powinien potrzebować prywatnych chatów, corpusów ani kontekstu innych projektów.

## Mapa repozytorium

`src/cmpct/` = kanoniczne r24; `experiments/` = linia badawcza; `benchmarks/` = deterministyczne corpora/gates i `benchmarks/history/`; `fuzz/` = ataki parser/resource; `tools/check_*` = kontrakty jakości; `site/` = strona + Browser Lab; `native/` = akceleratory/shared core; `docs/` = kontrakty, kampanie, historia, roadmap; `tests/` = regresje formatu, round-trip, similarity, locality, reproducibility.

## Strona

Strona ma **najpierw robić wrażenie, potem dowodzić twierdzenia, a dopiero potem zdobywać zaufanie**. Liczby, konkurenci, workloady, porażki i stan core pochodzą z versioned benchmark history. **Front badawczy**, **parytet kanoniczny** i **surface revision** są rozdzielone. Wizualna agresja jest dozwolona; wymyślanie zwycięstw nie.

**Otwórz:** https://fcmo-ai.github.io/.CMPCT/?lang=pl

## Dyscyplina wersji

1. **Core numeryczny (`MAJOR.MINOR.PATCH`)** — tylko za materialny postęp produktu; po v0.27.1 normalny ruch zwiększa `MAJOR.MINOR`, z `PATCH=0` dla packaging compatibility.
2. **Surface (`MAJOR.MINOR.LETTER`)** — site/docs/repo/workflow; teraz **`0.29.k`**.
3. **On-disk revision** — tylko gdy czytniki potrzebują nowej gramatyki/semantyki; kanoniczne **r24**.

CI utrzymuje osie oddzielnie i odrzuca nieuzasadnione bump-y.

## Historia, provenance i powierzchnia publiczna

CMPCT wyrósł z eksperymentów Seekable-Zstd, indexed-Zstd, adaptive-framing i ZIP-family. Historia techniczna pozostaje; prywatne corpora, artefakty i unrelated provenance nie. Publiczne benchmarki muszą być reprodukowalne lub używać jawnie publicznych/syntetycznych wejść; historyczne wyniki **nie są uniwersalną gwarancją**.

CMPCT musi stać samodzielnie. Repo i site nie mogą wymagać ani ujawniać unrelated projektów wewnętrznych, danych klientów, prywatnych corpusów, danych osobowych, transkrypcji chatów, credentials, prywatnych artefaktów ani linków wewnętrznych. Patrz `docs/PUBLIC_SURFACE.md`.

## Kanoniczność

Repozytorium zastępuje chat-local prototypy i benchmarki. Materialny postęp engine/archive dostaje wersję numeryczną; site/docs/prezentacja używają `SURFACE_REVISION`; badania pozostają jawnie eksperymentalne do promocji. Kod eksperymentalny nie może twierdzić, że obsługuje format kanoniczny bez integracji z reference reader/writer i conformance.

## Licencja

Apache License 2.0 jest **obecną propozycją licencji**, nie przyjętą licencją końcową. Tekst: `LICENSE-APACHE-2.0-PROPOSED.txt`; lista adopcji: `LICENSING.md`. Do zakończenia procesu nie wolno przedstawiać CMPCT jako ostatecznie wydanego pod Apache-2.0.
