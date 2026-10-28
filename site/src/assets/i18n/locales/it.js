/* CMPCT curated Italian adaptation pack — Surface 0.29.i.
   Footnote: every physical line in PHRASE_VALUES corresponds to the same-index canonical English phrase.
   The pack is model-curated and source-controlled; it is not runtime machine translation and is not
   labeled human-reviewed. */
import { phraseBlock } from "../locale-pack.js";
export const PHRASE_VALUES = phraseBlock(`
Vai al contenuto
Home di CMPCT
Navigazione principale
Lingua
Prestazioni
Motore
Prove
Laboratorio
Vista agente
SPAZIO LOGICO
RADICI FISICHE
FRONTIERA DELLE PRESTAZIONI · DAI BENCHMARK VERSIONATI
UN MODO MIGLIORE DI IMPACCHETTARE I FILE.
I formati di archivio hanno fatto pace con i compromessi.
CMPCT no.
Un progetto di archiviazione lossless progettato per far avanzare insieme byte memorizzati, accesso selettivo, identità esatta, integrità e recupero — e rifiutare release che arretrano la frontiera verificata.
Guarda i numeri
Crea un .cmpct
Mostrami dove perde ↓
Progetto
Ripetizioni
Runner
Ambiente registrato
Superficie
Formato canonico
Build
RISULTATO CHIAVE DEL TEST APPAIATO ATTUALE
TEMPO REALE DI CREAZIONE
ZIP / DEFLATE
7Z / LZMA2
ZSTD-19 SOLIDO
confronto strutturale appaiato
Caricamento delle ultime evidenze di benchmark versionate…
Caricamento dell’ultima frontiera di benchmark versionata…
Ricevuta delle evidenze ↓
byte memorizzati appaiati
risultato circoscritto dello scheduler
SENZA PERDITA
ACCESSO SELETTIVO
INTEGRITÀ
RECUPERO
DEDUPLICAZIONE
DECODIFICA LIMITATA
Priorità di progettazione CMPCT
LEGGE DI RELEASE / 01
Scopri con coraggio. Promuovi senza regressioni.
La ricerca può mostrare un compromesso. Una release non può nasconderlo. Regressione deterministica della dimensione dell’archivio:
0 byte consentiti
Regressione di velocità confermata fuori dal margine di rumore dello stesso runner:
release bloccata
GATE DELLE PRESTAZIONI
01 / L’ARENA
Non è un rapporto di compressione.
È una posizione prestazionale.
L’arena strutturale pone una domanda precisa: quanti byte ha memorizzato ogni strumento per lo stesso albero ostile? Le differenze nelle semantiche di accesso, recupero e durabilità restano esplicite invece di essere spacciate per parità.
BYTE MEMORIZZATI · MENO È MEGLIO
input logico
concorrente
Confronto delle dimensioni degli archivi
Leggilo correttamente:
una sconfitta in dimensione grezza contro un compressore solido può coesistere con semantiche migliori di accesso selettivo e recupero. Il sito conserva entrambi i fatti.
FRONTIERA PER CATEGORIA · ZSTD-19 SOLIDO
Gli archivi indipendenti dei workload sull’albero esatto conservano la propria provenienza invece di prendere in prestito il risultato dell’intera suite.
Caricamento delle evidenze per categoria su alberi esatti…
PANNELLO RED TEAM
LE SCONFITTE RESTANO VISIBILI
La credibilità di un benchmark nasce dai fallimenti conservati, non da una dashboard perfettamente verde.
Caricamento delle qualificazioni del benchmark…
RICEVUTA DELLE EVIDENZE
LIBRO APERTO
Ogni titolo conserva il proprio albero, record, ambito e livello di autorità. Più bella diventa un’affermazione, più facile deve essere ispezionarne la fonte.
Formato
Albero
File
Record
Contratto
Dati grezzi del sito ↗
JSON agente ↗
Orientamento LLM ↗
Storico benchmark ↗
02 / PERCHÉ PUÒ VINCERE
L’archivio viene compilato come un
grafo dell’informazione.
CMPCT cerca relazioni esatte tra gli oggetti richiesti, sceglie radici fisiche e registra percorsi di ricostruzione deterministici, mantenendo espliciti i costi di località, integrità e recupero.
Grafo concettuale dell’informazione
ALBERO LOGICO
byte richiesti
FLUSSI ESATTI
struttura condivisa
IDENTITÀ
oggetti deduplicati
RADICI LIMITATE
decodifica selettiva
INDICE + PROVA
integrità / recupero
Identità esatta
Contenuti identici possono convergere su un’unica radice fisica autenticata senza collassare percorsi logici indipendenti.
Archiviazione consapevole delle relazioni
Gli oggetti richiesti possono riutilizzare strutture compresse esatte invece di pagare spazio duplicato solo perché i nomi dei file differiscono.
Accesso selettivo
Leggi l’oggetto richiesto invece di rendere una gigantesca decompressione dell’intero archivio l’unica strada verso byte utili.
Contesto limitato
Il contesto tra file viene valutato e vincolato, così un guadagno di dimensione non può creare silenziosamente lavoro di lettura illimitato.
Integrità
Indici e dati fisici includono controlli espliciti; il successo non è definito come «il decompressore non si è lamentato».
Recupero fisico
Metadati autenticati ridondanti esistono come vero percorso del lettore, non come promessa di disaster recovery scritta in prosa.
03 / CANONICO VS FRONTIERA
Un progetto.
Due livelli di autorità.
La frontiera di ricerca può essere aggressiva. Il reader/writer canonico è il contratto di interoperabilità. Un bel sito non permette mai a una rappresentazione di ricerca di prendere in prestito autorità canonica.
IN PRODUZIONE / CANONICO
contratto reader / writer
FRONTIERA DI RICERCA
candidato benchmark
EVIDENZE PUBBLICHE
APERTE
le affermazioni derivano da record versionati
04 / PARITÀ DI ESECUZIONE CANONICA CON ZIP
CMPCT in produzione contro ZIP.
Dimensione, creazione, estrazione.
Parità operativa del reader/writer canonico ai confini della libreria e dei nuovi processi CLI. Rimane intenzionalmente separata dalla frontiera di ricerca dello storage.
Record versionato
Corpus
Dimensione archivio
Creazione in libreria
Estrazione in libreria
Creazione CLI
Estrazione CLI
05 / LABORATORIO NEL BROWSER
Smetti di leggere.
Creane uno.
Il writer portatile gira su questo dispositivo. I file non vengono caricati. Emette un sottoinsieme canonico conservativo e si disabilita invece di indovinare dopo una revisione del formato.
Verifica della compatibilità canonica…
Il writer si blocca in base alla revisione del formato del repository.
CREA
Writer CMPCT portatile
LOCALE
Trascina qui i file o sceglili
Trascina file o una cartella
Crea un archivio byte-esatto senza caricare dati.
Scegli file
Scegli cartella
Nessun file selezionato.
Crea .cmpct
La modalità portatile conserva file regolari, indicizzazione dei percorsi, deduplicazione per contenuto esatto, SHA-256/CRC32 e storage RAW/Deflate. La semantica completa del filesystem resta territorio della CLI.
ISPEZIONA
Lente dell’header
NESSUN UPLOAD
Leggi soltanto l’header fisso di un archivio CMPCT locale. La validazione strutturale completa resta al reader canonico e al core nativo.
Scegli un file .cmpct
Magic
Campo versione
Indice primario
Intervallo dati
06 / TRAIETTORIA DELLE RELEASE
Le release del core devono
guadagnarsi il numero.
Le release numeriche avanzano quando CMPCT stesso migliora materialmente. Le revisioni della superficie possono diventare radicalmente più belle senza fingere che il motore di archiviazione sia cambiato.
07 / PASSAGGIO ALL’INGEGNERIA
Bello fuori.
Ispezionabile fino in fondo.
La stessa superficie che rende CMPCT leggibile a una persona espone agli agenti stato leggibile dalla macchina ed evidenze ingegneristiche durevoli.
orientamento del progetto leggibile dalla macchina
evidenze pubbliche e stato delle release
ordine di lettura degli agenti e confine di autorità
Repository
Repository ↗
formato, benchmark, implementazione
Le prestazioni non sono uno screenshot. Sono un contratto di release.
Formato ↗
Benchmark ↗
Pre-1.0 · proposta di licenza non ancora adottata · le evidenze di benchmark versionate restano qualificate dall’ambiente e dalle semantiche registrate.
CMPNX11 è solo ricerca e non è leggibile dal reader canonico r24.
Il guadagno portatile di dimensione rispetto a v0.28 è piccolo (48,601 B / 0.035333%) e concentrato in 2 workload su 15; 13 workload ricadono intenzionalmente e in modo esatto sul comportamento precedente.
Prima della correzione dello scheduling, il portafoglio portatile accettato del tentativo 5 usava 2.175x il tempo di creazione di v0.28; qualsiasi affermazione sulla velocità dello scheduler vale soltanto per l’aggregato ostile fisso misurato.
Nell’aggregato strutturale ostile appaiato, il tentativo #5 è più piccolo di 7z/LZMA2 ma resta 82,112 B più grande di tar/Zstd-19 solido e 85,125 B più grande di ZPAQ m5.
I concorrenti con archivi solidi hanno semantiche diverse per lettura selettiva e recupero; queste righe confrontano byte memorizzati, non parità di funzionalità.
CMPCT conserva link, sparse file, uid-gid e xattrs nell’archivio; questa baseline ZIP Python dereferenzia i symlink e non conserva la semantica più ricca del filesystem.
frontiera di ricerca v0.29 accettata; r24 canonico invariato
un albero deterministico ostile alla somiglianza con 724 file; dimensioni degli archivi dell’intero albero nella stessa esecuzione; le differenze semantiche con gli archivi solidi restano esplicite
benchmark appaiato versionato
frontiera di ricerca
frontiera di ricerca CMPCT
candidato benchmark di ricerca
Nessun benchmark versionato è disponibile per la frontiera di ricerca.
Record:
commit:
file minuscoli
sorgenti
media
binari
deduplicazione e link
sparse
annidati
combinato
repository di sviluppo
spazio di lavoro office
libreria multimediale
analytics e database
log e telemetria
backup incrementali
incomprimibile e simile a cifrato
molti file minuscoli
artefatti ML
grande binario misto
versioni traslate
falsi vicini
cambio continuo dei confini
famiglia Deflate
incomprimibile
`);
export const MESSAGES = Object.freeze({
  files: "{n} file", file: "{n} file", logical: "{bytes} logici", logicalInputFiles: "{bytes} di input logico · {n} file",
  smallerThan: "{pct} più piccolo di {name}", largerThan: "{pct} più grande di {name}", sameStored: "stessi byte memorizzati di {name}", versus: "vs {name}",
  cmpctSmaller: "CMPCT più piccolo · byte memorizzati appaiati", cmpctLarger: "CMPCT più grande · byte memorizzati appaiati", sameBytes: "stessi byte memorizzati", unavailableMatched: "byte memorizzati appaiati non disponibili",
  currentFrontier: "frontiera di ricerca CMPCT attuale", categoryScore: "{wins}/{total} più piccoli · {losses} più grandi", noCategory: "evidenze per categoria non disponibili", noFreshCategory: "Per questa frontiera non sono disponibili evidenze recenti per categoria su alberi esatti.",
  comparisonUnavailable: "confronto non disponibile", noQualification: "Nessuna qualificazione di benchmark è registrata per questa frontiera pubblica.",
  heroIf: "Se {name} memorizza 100 MB in questo test appaiato, CMPCT richiede circa {value} MB.", heroNeeds: "CMPCT richiede attualmente circa {value} MB per ogni 100 MB memorizzati da {name} in questo test appaiato.",
  seriousBaseline: "Baseline seria di dimensione: {relation}.", scopedScheduler: "Risultato circoscritto dello scheduler: {pct}% di wall time in meno nel suo gate fisso.", canonicalRemains: "Il formato canonico resta r{revision}.",
  frontierQualification: "{frontier} · {files} file sull’albero strutturale appaiato.{serious}{speed} Il formato canonico resta r{revision}.", fixedSchedulerGate: "gate ostile fisso dello scheduler · non è un’affermazione globale di velocità", winsAgainst: "{wins}/{total} vittorie vs {name}",
  noCommittedParity: "Nessun record di parità versionato", repetitionsMedian: "mediana di {n}×", semanticQualification: "Qualificazione semantica:", interpretation: "Interpretazione:", currentProjectRelease: "Release attuale del progetto", versionedMilestone: "Traguardo versionato",
  writerVerified: "Writer portatile verificato per il formato canonico r{revision}.", regularSubset: "Solo sottoinsieme di file regolari; la semantica completa del filesystem resta territorio della CLI.", writerPaused: "Writer del browser sospeso dopo la revisione formato {revision}.", writerRefuses: "Questo build è verificato per r{supported}; si rifiuta di indovinare una grammatica più nuova.",
  readyLocally: "Pronto in locale", cliOverLimit: "Usa la CLI: oltre il limite del browser", input: "Input", archive: "Archivio", delta: "Delta", smaller: "{bytes} più piccolo", overhead: "{bytes} di overhead", buildingLocally: "Creazione locale…", builtOnDevice: "Archivio creato su questo dispositivo.",
  logicalFilesUnique: "{logical} file logici → {unique} blob unici · {deflate} Deflate / {raw} RAW.", saveCmpct: "Salva .cmpct", couldNotBuild: "Impossibile creare l’archivio.", fixedMagicError: "La firma magic fissa non sembra CMPCT.", inspection: "Ispezione", benchmarkUnavailable: "Dati benchmark non disponibili: {error}", canonicalDataMissing: "I dati canonici del sito non sono stati caricati."
});
