<div align="center">
  <a href="https://fcmo-ai.github.io/.CMPCT/?lang=de"><img src="../../.github/assets/repository-hero.svg" width="100%" alt="CMPCT — Archivformate haben sich mit Kompromissen abgefunden. CMPCT nicht."></a>

  **Ein universelles verlustfreies Archiv-/Containerprojekt, das gespeicherte Bytes, selektiven Zugriff, Integrität, Wiederherstellung und Portabilität gemeinsam voranbringen soll.**

  **[Website](https://fcmo-ai.github.io/.CMPCT/?lang=de)** · **[Browser-Labor](https://fcmo-ai.github.io/.CMPCT/?lang=de#lab)** · **[Benchmarks](../BENCHMARKS.md)** · **[Format](../FORMAT.md)** · **[Roadmap](../ROADMAP.md)** · **[Agenten-Einstieg](../CURRENT_STATE.md)**

  <sub>Core v0.29.0 · kanonisches Format r24 · Oberfläche 0.29.k · pre-1.0</sub>
</div>

> **Kuratierte Übersetzung.** Dies ist eine versionierte semantische Adaption des menschenorientierten README. Das englische [`README.md`](../../README.md) bleibt die kanonische Autorität. Zahlen, Pfade, Formatnamen und Evidenzgrenzen werden bewusst beibehalten. Diese Fassung wird nicht als von einem zweisprachigen Menschen geprüft bezeichnet, solange diese Prüfung nicht tatsächlich stattgefunden hat.

---

> **Leistung ist der Release-Vertrag.** Forschung darf einen unangenehmen Zielkonflikt entdecken. Ein promotetes Release darf ihn nicht verstecken: deterministische Archivgrößen-Regression hat **0-Byte-Toleranz**, eine bestätigte Geschwindigkeitsregression außerhalb der dokumentierten Rauschgrenze desselben Runners blockiert die Promotion, und verlierende Workloads bleiben öffentliche Evidenz.

## Warum CMPCT existiert

| | CMPCT will dies verbessern |
|---|---|
| **Gespeicherte Bytes** | Exakte Identität, inhaltsbewusste Repräsentationen und begrenzte Wiederverwendung von Beziehungen statt jede Datei als unabhängigen Bytestrom zu behandeln. |
| **Selektiver Zugriff** | Das angeforderte Objekt oder den Bereich lesen, ohne das ganze Archiv zwingend zu dekomprimieren. |
| **Integrität + Wiederherstellung** | Prüfungen, redundante Metadaten und Salvage-Pfade als ausführbares Leser-Verhalten statt als Disaster-Recovery-Prosa. |
| **Dateisystemtreue** | Links, Sparse-Dateien, Metadaten und Update-Semantik eines modernen General-Purpose-Containers bewahren. |
| **Interoperabilität** | Kanonischen Reader/Writer-Vertrag, ZIP-Export, Native-Core-Arbeit und Portabilitäts-Gates klar von experimenteller Grammatik trennen. |
| **Evidenzqualität** | Öffentliche Aussagen aus eingecheckten reproduzierbaren Datensätzen ableiten, Niederlagen behalten und Benchmark-Theater ablehnen. |

CMPCT ist nicht „Zstd mit einer neuen Endung“ und gibt sich nicht mit einem Sieg auf einem handverlesenen Ordner zufrieden. Ziel ist ein stärkeres Standardarchiv bei **Größe, Geschwindigkeit, Random Access, Treue, Integrität, Wiederherstellung, Updates und moderner Storage-Semantik**, ohne Kosten still an eine andere Stelle zu verschieben.

## Neueste verifizierte Front

**Projekt v0.29.0 — Mosaic / Residual Program Packing** bringt die verifizierte Forschungs-Engine voran, während das ausgelieferte kanonische Format bei **Revision 24** bleibt.

| v0.29 Forschungs-Evidenz | Ergebnis |
|---|---:|
| Portables geerbtes Frontier-Portfolio | **137,501,815 B** |
| Direkte v0.28-Basis | 137,550,416 B |
| Exakte Ersparnis | **48,601 B (0.035333%)** |
| Portable Workloads | **15** |
| Verbessert / regressiert | **2 / 0** |
| Exakte v0.28-Fallbacks | **13 / 15** |
| Feindliche Mechanismus-Suites | **4.407362% kleiner**, 9 verbessert / 0 regressiert über 18 Workloads |
| Fester feindlicher Scheduler | **182.454 s → 97.944 s Median (-46.318%)**, ausgewähltes Archiv byte-identisch |

Auf dem deterministischen, ähnlichkeitfeindlichen Aggregat mit 724 Dateien / 93,526,384 Bytes speichert der akzeptierte Versuch #5 **47,147,764 B**. Auf demselben Baum: ZPAQ Methode 5 47,062,639 B, solides tar+Zstd-19 47,065,652 B, 7z/LZMA2 47,430,343 B, Borg 76,461,311 B und ZIP/Deflate-9 76,690,799 B.

Diese Zeilen sind **gematchte Vergleiche gespeicherter Bytes, keine Behauptungen semantischer Parität**. Solid-Archive, Backup-Repositories und CMPCT haben unterschiedliche Trade-offs bei selektivem Lesen, Updates, Integrität und Wiederherstellung. Der dauerhafte Release-Datensatz ist [`docs/releases/v0.29.0.md`](../releases/v0.29.0.md); maschinenlesbare Evidenz liegt unter [`benchmarks/history/`](../../benchmarks/history/).

### Ausgeliefert vs Front

| Autorität | Aktueller Stand | Bedeutung |
|---|---|---|
| **Kanonischer Reader/Writer** | **Format r24** | Was `python -m cmpct create` schreibt und kanonische Reader verstehen müssen. |
| **Forschungsfront** | **CMPNX11 / v0.29.0** | Experimentelle Mosaic + Residual Program Packing Engine; keine kanonische r24-Syntax. |
| **Öffentliche Oberfläche** | **0.29.k** | Nur Repo-/Site-/Docs-Präsentation; ändert keine Archivsemantik und verbraucht keine Core-Version. |
| **Lizenz** | **Apache-2.0 vorgeschlagen** | Nur Vorschlag; noch keine finale öffentliche Lizenzgewährung. |

## Was CMPCT heute kann

Der kanonische r24-Prototyp bietet unter anderem: content-addressed Deduplizierung; adaptives Zstandard/raw Storage; Zstd-Dictionaries und Micro-Solid-Packs; content-defined Chunking; schnelle Byte-Range-Reads und paralleles Chunk-Decoding; Hardlink/Symlink/Sparse-Erhalt; UID/GID/xattrs; verschachtelte ZIP/WHL-Virtualisierung; verlustfreie PCM-WAV-Transformation, wenn sie gewinnt; Raw-Deflate-Wiederverwendung für ZIP-Export; CRC32 + SHA-256; redundante Head/Tail-Indizes und selbstbeschreibende Blob-Records; transaktionales Append-Journal; ZIP-Export auf Abruf; optionale reproduzierbare Erstellung und deterministische parallele Kandidatenkodierung.

Die v0.29-Forschung untersucht zusätzlich begrenzte FastCDC-ähnliche Einheiten, Multi-Band-Similarity-Suche, gemessene Depth-1 COPY/LITERAL-Deltas, begrenzte Multi-Root-Mosaic-Platzierung, Residual Program Packing, exakten v0.28-Fallback wenn die neue Darstellung nicht gewinnt, Lokalitäts-/Ressourcenlimits, optionale exakte DEFLATE-Vorkompression über eine gepinnte memory-safe Bridge, Merkle-authentifizierte Records, authentifizierte Tail-Recovery, strikte Remote-Range-Quellen und byte-identisches paralleles Portfolio-Scheduling.

Diese Mechanismen bleiben vom kanonischen Reader getrennt, bis Format-Integration, Konformität, Hardening, native Parität, Wiederherstellung und Portabilität unabhängig bestanden sind.

Die wichtigste Regel lautet: **inhaltgetriebene Auswahl, kein endungsgetriebener Aberglaube**. Ist eine spezialisierte Darstellung für die realen Bytes größer oder langsamer, soll CMPCT sie nicht verwenden.

## Schnellstart

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

Kanonische CLI-Erstellung in einem frischen Prozess ist absichtlich seriell, außer `--workers N` wird angegeben. Das v0.28-Release-Gate zeigte, dass Thread-Pool-Start bei einem kleinen Medienbaum ~10 ms kosten konnte, während sich die Bibliotheksarbeit kaum änderte. Die in-process `Builder`-API behält deterministische parallele Erstellung standardmäßig bei, wo der Setup-Aufwand amortisiert werden kann.

Optionaler nativer Content-Defined-Chunker unter Linux:

```bash
cc -O3 -shared -fPIC native/cmpct_cdc.c -o src/cmpct/libcmpct_cdc.so
```

Der Reader hängt **nicht** davon ab. Er beschleunigt Boundary-Auswahl beim Erstellen; Chunk-Grenzen werden explizit auf Platte gespeichert.

## Die Leistungsposition

Numerische Core-Release-Kandidaten werden vor Promotion gegen ihre direkte Basis gemessen. Die Regel ist asymmetrisch, weil Größe und Zeit unterschiedliche Messphysik haben:

- **Archivgröße:** identischer Input + Encoder-Semantik dürfen nie größer werden; **0 Bytes** Toleranz;
- **Erstellen/Extrahieren:** Basis und Kandidat auf demselben Runner mit wiederholten Medianen; bestätigte Verlangsamung außerhalb der dokumentierten relativen+absoluten Rauschgrenze blockiert;
- **Benchmark-Evidenz:** jedes numerische Core-Release committet einen frischen öffentlichen Record;
- **Korpora:** verlierende/adversariale Workloads bleiben sichtbar.

Siehe [`docs/PERFORMANCE_RELEASE_GATE.md`](../PERFORMANCE_RELEASE_GATE.md) und [`docs/BREAKTHROUGH_REHABILITATION.md`](../BREAKTHROUGH_REHABILITATION.md).

## Lesereihenfolge für neue Agenten

1. `docs/AGI_ENGINEERING_STANDARD.md`; 2. `README.md`; 3. `AGENTS.md`; 4. `docs/CURRENT_STATE.md`; 5. neueste passende Notiz unter `docs/releases/`; 6. `docs/PERFORMANCE_RELEASE_GATE.md`; 7. `docs/BREAKTHROUGH_REHABILITATION.md`; 8. `docs/FORMAT.md`; 9. `docs/HISTORY.md`; 10. `docs/ENTROPYGRAPH.md`, `docs/ENTROPYGRAPH_II_CAMPAIGN.md`, `docs/MOSAIC_V029_CAMPAIGN.md`; 11. `docs/HARDENING.md`; 12. `docs/PORTABILITY.md`, `docs/NATIVE_CORE.md`; 13. `docs/RESEARCH_LOG.md`; 14. `docs/BENCHMARKS.md`, `benchmarks/history/`; 15. `docs/PUBLIC_SURFACE.md`; 16. `docs/ROADMAP.md`.

Ein neuer Agent soll weder private Chats noch private Korpora oder unrelated Projektkontext benötigen.

## Repository-Karte

`src/cmpct/` enthält die kanonische r24-Referenz; `src/cmpct/resemblance.py` wiederverwendbare Similarity/Delta-Primitiven; `experiments/entropygraph_v025.py`, `entropygraph_v028.py`, `entropygraph_v029_release.py` die Forschungslinie; `benchmarks/` deterministische Korpora/Gates mit dauerhaften Records in `benchmarks/history/`; `fuzz/` Parser-/Ressourcenangriffe; `tools/check_*` Performance-/Versions-/Evidenzverträge; `site/` Website und Browser Lab; `native/` Beschleuniger und Shared Core; `docs/` Verträge, Kampagnen, Historie und Roadmap; `tests/` Format-, Round-trip-, Similarity-, Strict-Locality- und Reproduzierbarkeitsregressionen.

## Website

Die Live-Site ist gebaut, um **zuerst Wirkung zu erzeugen, dann die Behauptung zu beweisen und erst danach Vertrauen zu verdienen**. Headline-Werte, Konkurrenzleiter, Workload-Matrix, Niederlagen und Core-Status stammen aus versionierter Benchmark-Historie, nicht aus handgepflegten Marketing-Prozenten. Sie trennt streng **Forschungsfront**, **kanonische Parität** und **Oberflächenrevision**. Visuell darf sie aggressiv sein; diese Grenzen verwischen oder einen Sieg erfinden darf sie nicht.

**Öffnen:** https://fcmo-ai.github.io/.CMPCT/?lang=de

## Versionsdisziplin

1. **Numerische Core-Version (`MAJOR.MINOR.PATCH`)** — nur für materiellen Produktgewinn; nach v0.27.1 bewegt normale Entwicklung `MAJOR.MINOR` und hält `PATCH=0` für Packaging-Kompatibilität.
2. **Oberflächenrevision (`MAJOR.MINOR.LETTER`)** — Site, Docs, Repo-Präsentation, Workflow-Ergonomie; aktuell **`0.29.k`**. Sie ändert nicht allein `pyproject.toml` und benötigt keinen synthetischen Benchmark.
3. **On-Disk-Revision** — nur wenn Reader neue Grammatik/Storage-Semantik benötigen. Kanonisch bleibt **r24**.

CI verwirft numerische Bumps ohne Engine-/Archivarbeit, verlangt Release- und Benchmark-Evidenz für numerische Releases, validiert die alphabetische Surface-Linie und hält dies vom Performance-Regression-Gate getrennt.

## Geschichte, Provenienz und öffentliche Oberfläche

CMPCT entstand aus Seekable-Zstd-, indexed-Zstd-, adaptive-framing- und ZIP-Familien-Experimenten und wurde zum nativen content-aware Format. Technische Geschichte bleibt erhalten; Identitäten privater Korpora, private Artefakte und unrelated Projektprovenienz gehören nicht in den öffentlichen Record. Öffentliche Benchmarks müssen unabhängig reproduzierbar sein oder bewusst öffentliche/synthetische Inputs verwenden; historische Daten sind **keine universelle Leistungsgarantie**.

CMPCT muss für sich allein stehen. Repo und Website dürfen keine unrelated internen Projekte, private Kundendaten, private Korpora, persönliche Daten, Chattranskripte, Credentials, private Artefaktnamen oder interne Links voraussetzen oder offenlegen. Siehe `docs/PUBLIC_SURFACE.md`.

## Kanonizität

Dieses Repository ersetzt chat-lokale CMPCT-Prototypen und Benchmark-Skripte. Formatänderungen, Benchmarks, Experimente, Site-Arbeit und Designentscheidungen landen hier, aber mit unterschiedlichen Markern: materieller Engine-/Archivfortschritt verdient eine numerische Version; Site/Docs/Präsentation nutzen `SURFACE_REVISION`; Forschung bleibt explizit experimentell bis zur Promotion. Experimenteller Code darf keine kanonische Formatunterstützung behaupten, bevor er in Referenz-Reader/Writer und Konformität integriert ist.

## Lizenz

Apache License 2.0 ist die **derzeit vorgeschlagene Lizenz**, noch nicht die endgültig angenommene. Der unveränderte Vorschlag liegt in `LICENSE-APACHE-2.0-PROPOSED.txt`, die Adoption-Checkliste in `LICENSING.md`. Bis dieser Prozess abgeschlossen ist, darf CMPCT nicht als endgültig unter Apache-2.0 veröffentlicht dargestellt werden.

Hinweis: Der Repository-Hero ist absichtlich evergreen und enthält weder Benchmark-Prozente noch Release-Nummern. Evidenztragende Werte bleiben Text aus dem aktuellen Release-Record; historische Release-Notes und Benchmark-Records werden nicht nachträglich umgeschrieben.
