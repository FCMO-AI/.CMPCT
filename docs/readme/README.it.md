<div align="center">
  <a href="https://fcmo-ai.github.io/.CMPCT/?lang=it"><img src="../../.github/assets/repository-hero.svg" width="100%" alt="CMPCT — I formati di archivio hanno fatto pace con i compromessi. CMPCT no."></a>

  **Un progetto di archivio/contenitore lossless general-purpose, progettato per far avanzare insieme byte memorizzati, accesso selettivo, integrità, recupero e portabilità.**

  **[Sito](https://fcmo-ai.github.io/.CMPCT/?lang=it)** · **[Browser Lab](https://fcmo-ai.github.io/.CMPCT/?lang=it#lab)** · **[Benchmark](../BENCHMARKS.md)** · **[Formato](../FORMAT.md)** · **[Roadmap](../ROADMAP.md)** · **[Ingresso agenti](../CURRENT_STATE.md)**

  <sub>core v0.29.0 · formato canonico r24 · superficie 0.29.k · pre-1.0</sub>
</div>

> **Traduzione curata.** Questa è un’adattamento semantico versionato del README rivolto alle persone. Il [`README.md`](../../README.md) inglese resta l’autorità canonica. Numeri, percorsi, nomi dei formati e limiti delle prove vengono preservati intenzionalmente. Non viene dichiarata revisione umana bilingue finché non avviene davvero.

---

> **Le prestazioni sono il contratto di release.** La ricerca può scoprire un compromesso scomodo. Una release promossa non può nasconderlo: regressione deterministica della dimensione dell’archivio con **tolleranza 0 byte**, regressione di velocità confermata oltre il rumore documentato dello stesso runner blocca la promozione, e i workload perdenti restano prove pubbliche.

## Perché esiste CMPCT

| | CMPCT vuole migliorare |
|---|---|
| **Byte memorizzati** | Identità esatta, rappresentazioni consapevoli del contenuto e riuso limitato delle relazioni invece di trattare ogni file come flusso indipendente. |
| **Accesso selettivo** | Leggere l’oggetto o intervallo richiesto senza decomprimere obbligatoriamente l’intero archivio. |
| **Integrità + recupero** | Controlli, metadati ridondanti e percorsi di salvataggio come comportamento reale del reader, non prosa di disaster recovery. |
| **Fedeltà filesystem** | Preservare link, sparse file, metadati e semantica di aggiornamento attesi da un contenitore moderno. |
| **Interoperabilità** | Separare contratto canonico reader/writer, export ZIP, native core e gate di portabilità dalla grammatica sperimentale. |
| **Qualità delle prove** | Derivare le affermazioni pubbliche da record riproducibili versionati, conservare le sconfitte e rifiutare il teatro dei benchmark. |

CMPCT non è «Zstd con una nuova estensione» e non si accontenta di vincere su una cartella scelta a mano. L’obiettivo è un archivio predefinito più forte su **dimensione, velocità, accesso casuale, fedeltà, integrità, recupero, aggiornamenti e semantica moderna dello storage**, senza spostare silenziosamente il costo altrove.

## Ultima frontiera verificata

**Progetto v0.29.0 — Mosaic / Residual Program Packing** fa avanzare il motore di ricerca verificato mentre il formato canonico distribuito resta alla **revisione 24**.

| Prove di ricerca v0.29 | Risultato |
|---|---:|
| Portfolio portatile ereditato | **137,501,815 B** |
| Base diretta v0.28 | 137,550,416 B |
| Risparmio esatto | **48,601 B (0.035333%)** |
| Workload portatili | **15** |
| Migliorati / regressi | **2 / 0** |
| Fallback esatti v0.28 | **13 / 15** |
| Suite meccanismi ostili | **4.407362% più piccolo**, 9 migliorati / 0 regressi su 18 workload |
| Scheduler ostile fisso | **182.454 s → 97.944 s mediana (-46.318%)**, archivio selezionato byte-identico |

Sull’aggregato deterministico ostile alla somiglianza di 724 file / 93,526,384 byte, il tentativo accettato #5 memorizza **47,147,764 B**. Sullo stesso albero: ZPAQ metodo 5 47,062,639 B, tar+Zstd-19 solid 47,065,652 B, 7z/LZMA2 47,430,343 B, Borg 76,461,311 B e ZIP/Deflate-9 76,690,799 B.

Queste sono **comparazioni appaiate di byte memorizzati, non affermazioni di parità semantica**. Archivi solid, repository di backup e CMPCT hanno trade-off diversi. Record durevole: [`docs/releases/v0.29.0.md`](../releases/v0.29.0.md); prove machine-readable: [`benchmarks/history/`](../../benchmarks/history/).

### Produzione vs frontiera

| Autorità | Stato | Significato |
|---|---|---|
| **Reader/writer canonico** | **r24** | Ciò che `python -m cmpct create` scrive e i reader canonici devono capire. |
| **Frontiera di ricerca** | **CMPNX11 / v0.29.0** | Mosaic + Residual Program Packing sperimentale; non sintassi r24. |
| **Superficie pubblica** | **0.29.k** | Presentazione repo/sito/docs, senza autorità sulla semantica. |
| **Licenza** | **Apache-2.0 proposta** | Solo proposta, non ancora concessione finale. |

## Cosa sa fare oggi

Il prototipo canonico r24 include deduplicazione content-addressed, Zstandard/raw adattivo, dizionari Zstd e micro-solid pack, content-defined chunking, range read e decode parallelo, hardlink/symlink/sparse, UID/GID/xattrs, virtualizzazione ZIP/WHL, trasformazione PCM-WAV lossless quando conviene, riuso raw Deflate per ZIP, CRC32 + SHA-256, indici head/tail ridondanti e blob auto-descrittivi, journal append transazionale, export ZIP, creazione riproducibile opzionale e codifica parallela deterministica.

La ricerca v0.29 aggiunge unità di somiglianza FastCDC limitate, ricerca multi-band, delta COPY/LITERAL depth-1, Mosaic multi-root, Residual Program Packing, fallback esatto v0.28, limiti di località/risorse, DEFLATE esatto opzionale tramite bridge memory-safe fissato, record Merkle autenticati, tail recovery autenticata, remote range source stretti e scheduling parallelo byte-identico.

Questi meccanismi restano fuori dal reader canonico finché non superano integrazione formato, conformità, hardening, parità nativa, recupero e portabilità.

Regola centrale: **selezione guidata dal contenuto, non folklore guidato dall’estensione**.

## Avvio rapido

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

La creazione CLI canonica in un processo nuovo è seriale salvo `--workers N`. Il gate v0.28 ha mostrato che avviare il thread pool può costare ~10 ms su un piccolo albero media; l’API `Builder` in-process mantiene invece il parallelismo deterministico di default.

Chunker nativo Linux opzionale:

```bash
cc -O3 -shared -fPIC native/cmpct_cdc.c -o src/cmpct/libcmpct_cdc.so
```

Il reader **non dipende** da questo helper; i confini dei chunk restano registrati su disco.

## Posizione prestazionale

- **dimensione:** stessi input + semantica encoder non possono produrre più byte; tolleranza **0 byte**;
- **creazione/estrazione:** base e candidato sullo stesso runner, mediane ripetute; slowdown confermato oltre la soglia blocca la release;
- **prove:** ogni release numerica committa un record benchmark pubblico nuovo;
- **corpora:** workload perdenti/adversariali restano visibili.

Vedi [`docs/PERFORMANCE_RELEASE_GATE.md`](../PERFORMANCE_RELEASE_GATE.md) e [`docs/BREAKTHROUGH_REHABILITATION.md`](../BREAKTHROUGH_REHABILITATION.md).

## Ordine di lettura per un nuovo agente

`docs/AGI_ENGINEERING_STANDARD.md` → `README.md` → `AGENTS.md` → `docs/CURRENT_STATE.md` → ultima nota in `docs/releases/` → `docs/PERFORMANCE_RELEASE_GATE.md` → `docs/BREAKTHROUGH_REHABILITATION.md` → `docs/FORMAT.md` → `docs/HISTORY.md` → documenti EntropyGraph/Mosaic → `docs/HARDENING.md` → `docs/PORTABILITY.md` + `docs/NATIVE_CORE.md` → `docs/RESEARCH_LOG.md` → `docs/BENCHMARKS.md` + `benchmarks/history/` → `docs/PUBLIC_SURFACE.md` → `docs/ROADMAP.md`.

Un agente nuovo non deve richiedere chat private, corpora privati o contesto di progetti non correlati.

## Mappa del repository

`src/cmpct/` è l’implementazione canonica r24; `experiments/` contiene la linea di ricerca; `benchmarks/` corpora e gate deterministici con storia durable in `benchmarks/history/`; `fuzz/` attacca parser/risorse; `tools/check_*` impone i contratti; `site/` contiene sito e Browser Lab; `native/` acceleratori e core condiviso; `docs/` contratti/campagne/storia/roadmap; `tests/` regressioni formato, round-trip, somiglianza, località e riproducibilità.

## Sito web

Il sito è progettato per **creare impatto prima, provare l’affermazione poi, guadagnare fiducia alla fine**. Numeri, concorrenti, workload, sconfitte e stato del core provengono dai benchmark versionati. Separa rigorosamente **frontiera di ricerca**, **parità canonica** e **revisione di superficie**. Può essere aggressivo visivamente; non può inventare vittorie.

**Apri:** https://fcmo-ai.github.io/.CMPCT/?lang=it

## Disciplina delle versioni

1. **Core numerico (`MAJOR.MINOR.PATCH`)** — solo per miglioramenti materiali; dopo v0.27.1 il progresso normale muove `MAJOR.MINOR`, `PATCH=0` per compatibilità packaging.
2. **Superficie (`MAJOR.MINOR.LETTER`)** — sito/docs/presentazione/workflow; attuale **`0.29.k`**.
3. **Revisione on-disk** — cambia solo con nuova grammatica/semantica; canonico **r24**.

CI mantiene questi assi separati e rifiuta bump numerici non supportati da lavoro del motore, note ed evidenze.

## Storia, provenienza e superficie pubblica

CMPCT nasce da esperimenti Seekable-Zstd, indexed-Zstd, adaptive-framing e famiglia ZIP. La storia tecnica resta, identità di corpora privati e artefatti privati no. I benchmark pubblici devono essere riproducibili o usare input deliberatamente pubblici/sintetici; dati storici **non sono garanzia universale**.

CMPCT deve stare in piedi da solo: repository e sito non devono esporre progetti interni non correlati, dati clienti, corpora privati, informazioni personali, chat, credenziali, artefatti privati o link interni. Vedi `docs/PUBLIC_SURFACE.md`.

## Canonicità

Questo repository sostituisce prototipi e benchmark locali alle chat. Progresso materiale del motore guadagna una release numerica; sito/docs/presentazione usano `SURFACE_REVISION`; ricerca resta esplicitamente sperimentale finché non viene promossa. Codice sperimentale non può dichiarare supporto canonico senza integrazione nel reader/writer di riferimento e nei test di conformità.

## Licenza

Apache License 2.0 è la **licenza proposta**, non ancora quella adottata. Testo proposto: `LICENSE-APACHE-2.0-PROPOSED.txt`; checklist: `LICENSING.md`. Fino al completamento, CMPCT non va presentato come definitivamente rilasciato sotto Apache-2.0.
