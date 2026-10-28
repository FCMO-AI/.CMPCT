/* CMPCT curated Finnish adaptation pack — Surface 0.29.i.
   Footnote: one physical phrase line maps to one canonical English source phrase. Model-curated,
   source-controlled, no runtime translator, and not claimed human-reviewed. */
import { phraseBlock } from "../locale-pack.js";
export const PHRASE_VALUES = phraseBlock(`
Siirry sisältöön
CMPCT-etusivu
Päänavigaatio
Kieli
Suorituskyky
Moottori
Todisteet
Laboratorio
Agenttinäkymä
LOOGINEN TILA
FYYSISET JUURET
SUORITUSKYVYN ETURAJA · SUORAAN VERSIONHALLITUISTA BENCHMARKEISTA
PAREMPI TAPA PAKATA TIEDOSTOT.
Arkistomuodot tekivät rauhan kompromissien kanssa.
CMPCT ei.
Häviötön arkistointiprojekti, joka on suunniteltu parantamaan yhtä aikaa tallennettuja tavuja, valikoivaa käyttöä, täsmällistä identiteettiä, eheyttä ja palautusta — ja hylkäämään julkaisut, jotka siirtävät varmennetun eturajan taaksepäin.
Katso luvut
Rakenna .cmpct
Näytä missä se häviää ↓
Projekti
Toistot
Runner
Tallennettu ympäristö
Pinta
Kanoninen muoto
Build
NYKYISEN PARITETUN TESTIN PÄÄTULOS
LUONNIN WALL TIME
ZIP / DEFLATE
7Z / LZMA2
SOLID ZSTD-19
paritettu rakenteellinen vertailu
Ladataan uusinta versionhallittua benchmark-näyttöä…
Ladataan uusinta versionhallittua benchmark-etulinjaa…
Näyttökuitti ↓
paritetut tallennetut tavut
rajattu scheduler-tulos
HÄVIÖTÖN
VALIKOIVA PÄÄSY
EHEYS
PALAUTUS
DEDUPLIKOINTI
RAJATTU DEKOODAUS
CMPCT:n suunnitteluperiaatteet
JULKAISULAKI / 01
Tutki rohkeasti. Julkaise ilman regressiota.
Tutkimus saa paljastaa kompromissin. Julkaisu ei saa piilottaa sitä. Deterministinen arkistokoon regressio:
0 tavua sallittu
Vahvistettu nopeusregressio saman runnerin kohinamarginaalin ulkopuolella:
julkaisu estetty
SUORITUSKYKYPORTTI
01 / AREENA
Ei pakkaussuhde.
Suorituskykyasema.
Rakenteellinen areena kysyy yhden rajatun kysymyksen: kuinka monta tavua kukin työkalu tallensi samasta vihamielisestä puusta? Käytön, palautuksen ja kestävyyden semanttiset erot merkitään näkyviin sen sijaan, että niitä esitettäisiin valheellisena pariteettina.
TALLENNETUT TAVUT · VÄHEMPI ON PAREMPI
looginen syöte
kilpailija
Arkistokoon vertailu
Lue tämä oikein:
raakakoon tappio solid-pakkaajalle voi esiintyä samanaikaisesti vahvemman valikoivan käytön ja palautuksen semantiikan kanssa. Sivusto säilyttää molemmat tosiasiat.
KATEGORIAETURAJA · SOLID ZSTD-19
Itsenäiset workload-arkistot täsmällisillä puilla säilyttävät oman alkuperänsä sen sijaan, että lainaisivat koko testisarjan tulosta.
Ladataan kategoriakohtaista näyttöä täsmällisistä puista…
RED TEAM -TAULU
TAPPIOT PYSYVÄT NÄKYVISSÄ
Benchmarkin uskottavuus syntyy säilytetyistä epäonnistumisista, ei täydellisen vihreästä dashboardista.
Ladataan benchmarkin rajauksia…
NÄYTTÖKUITTI
AVOIN KIRJA
Jokainen pääväite säilyttää puunsa, tietueensa, rajauksensa ja auktoriteettitasonsa. Mitä näyttävämpi väite on, sitä helpommin sen lähde pitää voida tarkistaa.
Muoto
Puu
Tiedostot
Tietue
Sopimus
Sivuston raakadata ↗
Agentti-JSON ↗
LLM-orientaatio ↗
Benchmark-historia ↗
02 / MIKSI SE VOI VOITTAA
Arkisto käännetään
informaatiograafiksi.
CMPCT etsii täsmällisiä suhteita vaadittujen objektien välillä, valitsee fyysiset juuret ja tallentaa deterministiset rekonstruktio-polut pitäen lokaliteetin, eheyden ja palautuksen kustannukset näkyvinä.
Käsitteellinen informaatiograafi
LOOGINEN PUU
vaaditut tavut
TÄSMÄLLISET VIRRAT
jaettu rakenne
IDENTITEETTI
deduplikoidut objektit
RAJATUT JUURET
valikoiva dekoodaus
INDEKSI + TODISTE
eheys / palautus
Täsmällinen identiteetti
Identtinen sisältö voi yhdistyä yhteen todennettuun fyysiseen juureen romahduttamatta riippumattomia loogisia polkuja.
Suhdetietoinen tallennus
Vaaditut objektit voivat käyttää uudelleen täsmällistä pakattua rakennetta sen sijaan, että tallennustilaa kulutetaan kahdesti vain eri tiedostonimien vuoksi.
Valikoiva pääsy
Lue pyydetty objekti sen sijaan, että ainoa tie hyödyllisiin tavuihin olisi koko arkiston valtava purkuoperaatio.
Rajattu konteksti
Tiedostojen välistä kontekstia kokeillaan ja rajataan, jotta kokovoitto ei voi hiljaa luoda rajatonta lukutyötä.
Eheys
Indekseissä ja fyysisessä datassa on eksplisiittiset tarkistukset; onnistuminen ei tarkoita vain sitä, ettei purkaja valittanut.
Fyysinen palautus
Redundantti todennettu metadata on olemassa todellisena lukijapolkuna, ei pelkkänä tekstissä luvattuna disaster recovery -ominaisuutena.
03 / KANONINEN VS ETURAJA
Yksi projekti.
Kaksi auktoriteettitasoa.
Tutkimuseturaja saa olla aggressiivinen. Kanoninen reader/writer on yhteentoimivuussopimus. Kaunis sivusto ei koskaan anna tutkimusrepresentaation lainata kanonista auktoriteettia.
TOIMITETTU / KANONINEN
reader / writer -sopimus
TUTKIMUSETURAJA
benchmark-ehdokas
JULKINEN NÄYTTÖ
AVOIN
väitteet johdetaan versionhallituista tietueista
04 / KANONINEN ZIP-SUORITUSPARITEETTI
Toimitettu CMPCT vs ZIP.
Koko, luonti, purku.
Kanonisen reader/writerin operatiivinen pariteetti kirjasto- ja uuden CLI-prosessin rajoilla. Se pidetään tarkoituksella erillään tallennuksen tutkimuseturajasta.
Versionhallittu tietue
Korpus
Arkiston koko
Kirjasto: luonti
Kirjasto: purku
CLI: luonti
CLI: purku
05 / SELAINLABORATORIO
Lopeta lukeminen.
Tee yksi.
Siirrettävä writer toimii tällä laitteella. Tiedostoja ei ladata palvelimelle. Se kirjoittaa konservatiivisen kanonisen osajoukon ja mieluummin kytkeytyy pois kuin arvaa formaattirevision jälkeen.
Tarkistetaan kanonista yhteensopivuutta…
Writer portittaa itsensä repositoryn formaattirevision mukaan.
LUO
Siirrettävä CMPCT-writer
PAIKALLINEN
Pudota tiedostot tähän tai valitse tiedostot
Pudota tiedostot tai kansio
Rakenna tavuntarkka arkisto ilman datan lähettämistä.
Valitse tiedostot
Valitse kansio
Ei valittuja tiedostoja.
Rakenna .cmpct
Siirrettävä tila säilyttää tavalliset tiedostot, polkuindeksoinnin, täsmällisen sisällön deduplikoinnin, SHA-256/CRC32:n ja RAW/Deflate-tallennuksen. Täysi tiedostojärjestelmäsemantiikka kuuluu edelleen CLI:lle.
TARKASTA
Header-linssi
EI LÄHETYSTÄ
Lue vain paikallisen CMPCT-arkiston kiinteä header. Täysi rakenteellinen validointi kuuluu kanoniselle readerille ja native corelle.
Valitse .cmpct-tiedosto
Magic
Versiokenttä
Ensisijainen indeksi
Data-alue
06 / JULKAISUPOLKU
Core-julkaisujen pitää
ansaita numeronsa.
Numeroidut julkaisut etenevät, kun CMPCT itse paranee olennaisesti. Pintarevisiot voivat näyttää radikaalisti paremmilta ilman että esitetään arkistomoottorin muuttuneen.
07 / ENGINEERING-LUOVUTUS
Kaunis ulkoa.
Tarkastettavissa pohjaan asti.
Sama pinta, joka tekee CMPCT:stä ihmiselle luettavan, näyttää agenteille koneellisesti luettavan tilan ja kestävän engineering-näytön.
koneellisesti luettava projektiorientaatio
julkinen näyttö ja julkaisutila
agentin lukujärjestys ja auktoriteettiraja
Repository
Repository ↗
muoto, benchmarkit, toteutus
Suorituskyky ei ole kuvakaappaus. Se on julkaisusopimus.
Muoto ↗
Benchmarkit ↗
Pre-1.0 · lisenssiehdotusta ei ole vielä hyväksytty · versionhallittu benchmark-näyttö pysyy tallennetun ympäristön ja semantiikan rajaamana.
CMPNX11 on vain tutkimuskäyttöön eikä kanoninen r24-reader osaa lukea sitä.
Siirrettävä kokovoitto v0.28:aan nähden on pieni (48,601 B / 0.035333%) ja keskittyy kahteen 15 workloadista; 13 workloadia palaa tarkoituksella täsmälleen aiempaan.
Ennen korjattua schedulingia hyväksytty yrityksen 5 siirrettävä portfolio käytti 2.175x v0.28:n luontiajan; jokainen schedulerin nopeusväite koskee vain mitattua kiinteää vihamielistä aggregaattia.
Paritetussa vihamielisessä rakenteellisessa aggregaatissa yritys #5 on pienempi kuin 7z/LZMA2 mutta edelleen 82,112 B suurempi kuin solid tar/Zstd-19 ja 85,125 B suurempi kuin ZPAQ m5.
Solid-arkistokilpailijoilla on erilainen valikoivan luvun/palautuksen semantiikka; nämä rivit vertaavat tallennettuja tavuja, eivät ominaisuuspariteettia.
CMPCT säilyttää links/sparse/uid-gid/xattrs-tiedot arkistossa; tämä Python ZIP -baseline dereferoi symlinkit eikä säilytä rikkaampaa tiedostojärjestelmäsemantiikkaa.
hyväksytty v0.29-tutkimuseturaja; kanoninen r24 ennallaan
yksi deterministinen, samankaltaisuudelle vihamielinen 724 tiedoston puu; koko puun arkistokoot samasta ajosta; semanttiset erot solid-arkistoihin pysyvät eksplisiittisinä
paritettu versionhallittu benchmark
tutkimuseturaja
CMPCT-tutkimuseturaja
tutkimusbenchmark-ehdokas
Tutkimuseturajalle ei ole saatavilla versionhallittua benchmarkia.
Tietue:
commit:
pienet tiedostot
lähdekoodi
media
binääri
deduplikointi ja linkit
sparse
sisäkkäinen
yhdistetty
kehittäjärepository
toimistotyötila
mediakirjasto
analytics ja tietokanta
lokit ja telemetria
inkrementaaliset varmuuskopiot
pakkaamaton ja salatun kaltainen
paljon pieniä tiedostoja
ML-artefaktit
suuri sekabinääri
siirretyt versiot
väärät naapurit
rajapinnan vaihtelu
Deflate-perhe
pakkaamaton
`);
export const MESSAGES = Object.freeze({
  files: "{n} tiedostoa", file: "{n} tiedosto", logical: "{bytes} loogista", logicalInputFiles: "{bytes} loogista syötettä · {n} tiedostoa",
  smallerThan: "{pct} pienempi kuin {name}", largerThan: "{pct} suurempi kuin {name}", sameStored: "sama määrä tallennettuja tavuja kuin {name}", versus: "vs {name}",
  cmpctSmaller: "CMPCT pienempi · paritetut tallennetut tavut", cmpctLarger: "CMPCT suurempi · paritetut tallennetut tavut", sameBytes: "samat tallennetut tavut", unavailableMatched: "paritettuja tallennettuja tavuja ei saatavilla",
  currentFrontier: "nykyinen CMPCT-tutkimuseturaja", categoryScore: "{wins}/{total} pienempi · {losses} suurempi", noCategory: "kategoriakohtaista näyttöä ei saatavilla", noFreshCategory: "Tälle eturajalle ei ole tuoretta kategoriakohtaista näyttöä täsmällisistä puista.",
  comparisonUnavailable: "vertailu ei saatavilla", noQualification: "Tälle julkiselle eturajalle ei ole kirjattu benchmark-rajausta.",
  heroIf: "Jos {name} tallentaa tässä paritetussa testissä 100 MB, CMPCT tarvitsee noin {value} MB.", heroNeeds: "CMPCT tarvitsee tällä hetkellä noin {value} MB jokaista {name}:n tässä paritetussa testissä tallentamaa 100 MB kohti.",
  seriousBaseline: "Vakavasti otettava kokobaseline: {relation}.", scopedScheduler: "Rajattu scheduler-tulos: {pct}% pienempi wall time sen kiinteässä gate-testissä.", canonicalRemains: "Kanoninen formaatti pysyy r{revision}:ssä.",
  frontierQualification: "{frontier} · {files} tiedostoa paritetussa rakenteellisessa puussa.{serious}{speed} Kanoninen formaatti pysyy r{revision}:ssä.", fixedSchedulerGate: "kiinteä vihamielinen scheduler-gate · ei globaali nopeusväite", winsAgainst: "{wins}/{total} voittoa vs {name}",
  noCommittedParity: "Ei versionhallittua pariteettitietuetta", repetitionsMedian: "{n}× mediaani", semanticQualification: "Semanttinen rajaus:", interpretation: "Tulkinta:", currentProjectRelease: "Projektin nykyinen julkaisu", versionedMilestone: "Versioitu virstanpylväs",
  writerVerified: "Siirrettävä writer varmennettu kanoniselle r{revision}-formaatille.", regularSubset: "Vain tavallisten tiedostojen osajoukko; täysi tiedostojärjestelmäsemantiikka kuuluu CLI:lle.", writerPaused: "Selain-writer pysäytetty formaattirevision {revision} jälkeen.", writerRefuses: "Tämä build on varmennettu r{supported}:lle; se kieltäytyy arvaamasta uudempaa kielioppia.",
  readyLocally: "Valmis paikallisesti", cliOverLimit: "Käytä CLI:tä: selainrajan yli", input: "Syöte", archive: "Arkisto", delta: "Ero", smaller: "{bytes} pienempi", overhead: "{bytes} ylimäärää", buildingLocally: "Rakennetaan paikallisesti…", builtOnDevice: "Arkisto rakennettu tällä laitteella.",
  logicalFilesUnique: "{logical} loogista tiedostoa → {unique} uniikkia blobia · {deflate} Deflate / {raw} RAW.", saveCmpct: "Tallenna .cmpct", couldNotBuild: "Arkistoa ei voitu rakentaa.", fixedMagicError: "Kiinteä magic-tunniste ei näytä CMPCT:ltä.", inspection: "Tarkastus", benchmarkUnavailable: "Benchmark-data ei saatavilla: {error}", canonicalDataMissing: "Kanonista sivustodataa ei ladattu."
});
