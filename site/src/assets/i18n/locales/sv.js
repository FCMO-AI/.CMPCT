/* CMPCT curated Swedish adaptation pack — Surface 0.29.i.
   Footnote: one physical phrase line maps to one canonical English source phrase. Model-curated,
   source-controlled, no runtime translator, and not claimed human-reviewed. */
import { phraseBlock } from "../locale-pack.js";
export const PHRASE_VALUES = phraseBlock(`
Hoppa till innehållet
CMPCT-startsida
Huvudnavigering
Språk
Prestanda
Motor
Bevis
Labb
Agentvy
LOGISKT UTRYMME
FYSISKA RÖTTER
PRESTANDAFRONT · DIREKT FRÅN INCHECKADE BENCHMARKS
ETT BÄTTRE SÄTT ATT PACKA FILER.
Arkivformat har accepterat kompromisser.
CMPCT har inte det.
Ett förlustfritt arkivprojekt byggt för att flytta lagrade byte, selektiv åtkomst, exakt identitet, integritet och återställning framåt samtidigt — och avvisa releaser som flyttar den verifierade fronten bakåt.
Se siffrorna
Bygg en .cmpct
Visa var den förlorar ↓
Projekt
Upprepningar
Runner
Registrerad miljö
Yta
Kanoniskt format
Build
HUVUDRESULTAT I DET AKTUELLA MATCHADE TESTET
WALL-TIME FÖR SKAPANDE
ZIP / DEFLATE
7Z / LZMA2
SOLID ZSTD-19
matchad strukturell jämförelse
Läser in senaste incheckade benchmarkbevis…
Läser in senaste incheckade benchmarkfront…
Beviskvitto ↓
matchade lagrade byte
avgränsat schedulerresultat
FÖRLUSTFRITT
SELEKTIV ÅTKOMST
INTEGRITET
ÅTERSTÄLLNING
DEDUPLIKERING
BEGRÄNSAD AVKODNING
CMPCT:s designprioriteringar
RELEASELAG / 01
Upptäck djärvt. Promota utan regression.
Forskning får avslöja en avvägning. En release får inte dölja den. Deterministisk regression i arkivstorlek:
0 byte tillåtna
Bekräftad hastighetsregression utanför brusmarginalen för samma runner:
release blockerad
PRESTANDAGATE
01 / ARENAN
Inte ett kompressionsförhållande.
En prestandaposition.
Den strukturella arenan ställer en smal fråga: hur många byte lagrade varje verktyg för samma fientliga träd? Skillnader i åtkomst-, återställnings- och hållbarhetssemantik förblir märkta i stället för att tvättas till påstådd paritet.
LAGRADE BYTE · LÄGRE ÄR BÄTTRE
logisk indata
konkurrent
Jämförelse av arkivstorlek
Läs detta rätt:
en förlust i rå storlek mot en solid kompressor kan samexistera med starkare semantik för selektiv åtkomst och återställning. Sajten bevarar båda fakta.
KATEGORIFRONT · SOLID ZSTD-19
Oberoende workload-arkiv på exakta träd behåller sin egen proveniens i stället för att låna resultatet för hela sviten.
Läser in kategoribevis på exakta träd…
RED TEAM-TAVLA
FÖRLUSTER FÖRBLIR SYNLIGA
Benchmarktrovärdighet kommer från bevarade misslyckanden, inte en perfekt grön dashboard.
Läser in benchmarkkvalificeringar…
BEVISKVITTO
ÖPPEN BOK
Varje rubrik behåller sitt träd, sin post, sitt omfång och sin auktoritetsnivå. Ju snyggare ett påstående blir, desto enklare ska källan vara att granska.
Format
Träd
Filer
Post
Kontrakt
Rå webbdata ↗
Agent-JSON ↗
LLM-orientering ↗
Benchmarkhistorik ↗
02 / VARFÖR DEN KAN VINNA
Arkivet kompileras som en
informationsgraf.
CMPCT söker exakta relationer mellan nödvändiga objekt, väljer fysiska rötter och registrerar deterministiska rekonstruktionsvägar medan kostnader för lokalitet, integritet och återställning hålls explicita.
Konceptuell informationsgraf
LOGISKT TRÄD
nödvändiga byte
EXAKTA STRÖMMAR
delad struktur
IDENTITET
deduplicerade objekt
BEGRÄNSADE RÖTTER
selektiv avkodning
INDEX + BEVIS
integritet / återställning
Exakt identitet
Identiskt innehåll kan konvergera till en autentiserad fysisk rot utan att slå ihop oberoende logiska vägar.
Relationsmedveten lagring
Nödvändiga objekt kan återanvända exakt komprimerad struktur i stället för att betala dubbel lagring bara för att filnamnen skiljer sig.
Selektiv åtkomst
Läs objektet som efterfrågas i stället för att göra en gigantisk dekomprimering av hela arkivet till den enda vägen till användbara byte.
Begränsad kontext
Kontext över filer provas och begränsas så att en storleksvinst inte tyst skapar obegränsat läsarbete.
Integritet
Index och fysisk data bär explicita kontroller; framgång betyder inte bara ”dekomprimeraren klagade inte”.
Fysisk återställning
Redundant autentiserad metadata finns som en verklig läsarväg, inte som ett disaster-recovery-löfte i prosa.
03 / KANONISKT VS FRONT
Ett projekt.
Två auktoritetsnivåer.
Forskningsfronten får vara aggressiv. Den kanoniska reader/writer:n är interoperabilitetskontraktet. En snygg sajt låter aldrig en forskningsrepresentation låna kanonisk auktoritet.
LEVERERAT / KANONISKT
reader / writer-kontrakt
FORSKNINGSFRONT
benchmarkkandidat
OFFENTLIGA BEVIS
ÖPPNA
påståenden härleds från incheckade poster
04 / KANONISK ZIP-EXEKVERINGSPARITET
Levererad CMPCT vs ZIP.
Storlek, skapa, extrahera.
Operativ paritet för den kanoniska reader/writer:n vid biblioteks- och färska CLI-processgränser. Den hålls avsiktligt separat från lagringens forskningsfront.
Incheckad post
Korpus
Arkivstorlek
Bibliotek: skapa
Bibliotek: extrahera
CLI: skapa
CLI: extrahera
05 / WEBBLABBET
Sluta läsa.
Gör en.
Den portabla writer:n kör på den här enheten. Filer laddas inte upp. Den skriver en konservativ kanonisk delmängd och stänger hellre av sig än gissar efter en formatrevision.
Kontrollerar kanonisk kompatibilitet…
Writer:n gate:ar sig mot repositoryts formatrevision.
SKAPA
Portabel CMPCT-writer
LOKALT
Släpp filer här eller välj filer
Släpp filer eller en mapp
Bygg ett byte-exakt arkiv utan att ladda upp data.
Välj filer
Välj mapp
Inga filer valda.
Bygg .cmpct
Portabelt läge bevarar vanliga filer, sökvägsindexering, deduplicering av exakt innehåll, SHA-256/CRC32 och RAW/Deflate-lagring. Full filsystemsemantik är fortsatt CLI-territorium.
INSPEKTERA
Headerlins
INGEN UPPLADDNING
Läs endast den fasta headern i ett lokalt CMPCT-arkiv. Full strukturell validering stannar hos den kanoniska reader:n och native core.
Välj en .cmpct-fil
Magic
Versionsfält
Primärt index
Dataspann
06 / RELEASEBANA
Core-releaser måste
förtjäna numret.
Numeriska releaser går framåt när CMPCT självt förbättras materiellt. Ytrevisioner kan bli radikalt snyggare utan att låtsas att arkivmotorn ändrades.
07 / ENGINEERING-ÖVERLÄMNING
Snyggt utanpå.
Granskningsbart hela vägen ner.
Samma yta som gör CMPCT läsbart för en människa visar maskinläsbart tillstånd och varaktiga engineeringbevis för agenter.
maskinläsbar projektorientering
offentliga bevis och releasestatus
agenters läsordning och auktoritetsgräns
Repository
Repository ↗
format, benchmarks, implementation
Prestanda är inte en skärmdump. Det är ett releasekontrakt.
Format ↗
Benchmarks ↗
Pre-1.0 · licensförslaget är ännu inte antaget · incheckade benchmarkbevis förblir kvalificerade av registrerad miljö och semantik.
CMPNX11 är endast för forskning och kan inte läsas av den kanoniska r24-reader:n.
Den portabla storleksvinsten över v0.28 är liten (48,601 B / 0.035333%) och koncentrerad till 2 av 15 workloads; 13 workloads faller avsiktligt tillbaka exakt.
Före korrigerad scheduling använde det accepterade portabla portföljen i försök 5 2.175x skapandetiden för v0.28; varje scheduler-hastighetspåstående gäller bara det uppmätta fasta fientliga aggregatet.
På det matchade fientliga strukturella aggregatet är försök #5 mindre än 7z/LZMA2 men fortfarande 82,112 B större än solid tar/Zstd-19 och 85,125 B större än ZPAQ m5.
Konkurrenter med solid-arkiv har annan semantik för selektiv läsning/återställning; dessa rader jämför lagrade byte, inte funktionsparitet.
CMPCT bevarar links/sparse/uid-gid/xattrs i arkivet; denna Python ZIP-baseline derefererar symlänkar och bevarar inte den rikare filsystemsemantiken.
accepterad v0.29-forskningsfront; kanonisk r24 oförändrad
ett deterministiskt likhetsfientligt träd med 724 filer; arkivstorlekar för hela trädet i samma körning; semantiska skillnader mot solid-arkiv förblir explicita
matchad incheckad benchmark
forskningsfront
CMPCT-forskningsfront
forskningsbenchmarkkandidat
Ingen incheckad benchmark är tillgänglig för forskningsfronten.
Post:
commit:
små filer
källkod
media
binärt
deduplicering och länkar
sparse
nästlat
kombinerat
utvecklarrepository
kontorsarbetsyta
mediebibliotek
analytics och databas
loggar och telemetri
inkrementella säkerhetskopior
inkomprimerbart och krypteringslikt
många små filer
ML-artefakter
stor blandad binärdata
förskjutna versioner
falska grannar
gränsförskjutning
Deflate-familj
inkomprimerbart
`);
export const MESSAGES = Object.freeze({
  files: "{n} filer", file: "{n} fil", logical: "{bytes} logiska", logicalInputFiles: "{bytes} logisk indata · {n} filer",
  smallerThan: "{pct} mindre än {name}", largerThan: "{pct} större än {name}", sameStored: "samma lagrade byte som {name}", versus: "vs {name}",
  cmpctSmaller: "CMPCT mindre · matchade lagrade byte", cmpctLarger: "CMPCT större · matchade lagrade byte", sameBytes: "samma lagrade byte", unavailableMatched: "matchade lagrade byte saknas",
  currentFrontier: "aktuell CMPCT-forskningsfront", categoryScore: "{wins}/{total} mindre · {losses} större", noCategory: "kategoribevis saknas", noFreshCategory: "Färska kategoribevis på exakta träd saknas för denna front.",
  comparisonUnavailable: "jämförelse saknas", noQualification: "Ingen benchmarkkvalificering är registrerad för denna offentliga front.",
  heroIf: "Om {name} lagrar 100 MB i detta matchade test behöver CMPCT ungefär {value} MB.", heroNeeds: "CMPCT behöver nu ungefär {value} MB för varje 100 MB som {name} lagrar i detta matchade test.",
  seriousBaseline: "Seriös storleksbaseline: {relation}.", scopedScheduler: "Avgränsat schedulerresultat: {pct}% lägre wall time på dess fasta gate.", canonicalRemains: "Det kanoniska formatet förblir r{revision}.",
  frontierQualification: "{frontier} · {files} filer på det matchade strukturella trädet.{serious}{speed} Det kanoniska formatet förblir r{revision}.", fixedSchedulerGate: "fast fientlig schedulergate · inte ett globalt hastighetspåstående", winsAgainst: "{wins}/{total} vinster vs {name}",
  noCommittedParity: "Ingen incheckad paritetspost", repetitionsMedian: "median av {n}×", semanticQualification: "Semantisk kvalificering:", interpretation: "Tolkning:", currentProjectRelease: "Aktuell projektrelease", versionedMilestone: "Versionerad milstolpe",
  writerVerified: "Portabel writer verifierad för kanoniskt format r{revision}.", regularSubset: "Endast delmängd vanliga filer; full filsystemsemantik är fortsatt CLI-territorium.", writerPaused: "Browser-writer pausad efter formatrevision {revision}.", writerRefuses: "Denna build är verifierad för r{supported}; den vägrar gissa en nyare grammatik.",
  readyLocally: "Klar lokalt", cliOverLimit: "Använd CLI: över browsergränsen", input: "Indata", archive: "Arkiv", delta: "Skillnad", smaller: "{bytes} mindre", overhead: "{bytes} overhead", buildingLocally: "Bygger lokalt…", builtOnDevice: "Arkiv byggt på denna enhet.",
  logicalFilesUnique: "{logical} logiska filer → {unique} unika blobs · {deflate} Deflate / {raw} RAW.", saveCmpct: "Spara .cmpct", couldNotBuild: "Kunde inte bygga arkivet.", fixedMagicError: "Den fasta magic-signaturen ser inte ut som CMPCT.", inspection: "Inspektion", benchmarkUnavailable: "Benchmarkdata saknas: {error}", canonicalDataMissing: "Kanonisk webbdata kunde inte laddas."
});
