/* CMPCT curated Polish adaptation pack — Surface 0.29.i.
   Footnote: one physical phrase line maps to one canonical English source phrase. Model-curated,
   source-controlled, no runtime translator, and not mislabeled as human-reviewed. */
import { phraseBlock } from "../locale-pack.js";
export const PHRASE_VALUES = phraseBlock(`
Przejdź do treści
Strona główna CMPCT
Nawigacja główna
Język
Wydajność
Silnik
Dowody
Laboratorium
Widok agenta
PRZESTRZEŃ LOGICZNA
KORZENIE FIZYCZNE
FRONT WYDAJNOŚCI · WPROST Z ZAPISANYCH BENCHMARKÓW
LEPSZY SPOSÓB PAKOWANIA PLIKÓW.
Formaty archiwów pogodziły się z kompromisem.
CMPCT nie.
Bezstratny projekt archiwizacyjny zaprojektowany tak, by jednocześnie poprawiać liczbę zapisanych bajtów, dostęp selektywny, dokładną tożsamość, integralność i odzyskiwanie — oraz odrzucać wydania cofające zweryfikowaną granicę.
Zobacz liczby
Zbuduj .cmpct
Pokaż, gdzie przegrywa ↓
Projekt
Powtórzenia
Runner
Zapisane środowisko
Warstwa wizualna
Format kanoniczny
Build
GŁÓWNY WYNIK OBECNEGO TESTU PAROWANEGO
CZAS RZECZYWISTY TWORZENIA
ZIP / DEFLATE
7Z / LZMA2
SOLIDNY ZSTD-19
sparowane porównanie strukturalne
Ładowanie najnowszych zapisanych dowodów benchmarkowych…
Ładowanie najnowszego zapisanego frontu benchmarkowego…
Pokwitowanie dowodów ↓
sparowane zapisane bajty
wynik ograniczonego planisty
BEZSTRATNE
DOSTĘP SELEKTYWNY
INTEGRALNOŚĆ
ODZYSKIWANIE
DEDUPLIKACJA
OGRANICZONE DEKODOWANIE
Priorytety projektowe CMPCT
PRAWO WYDANIA / 01
Odkrywaj odważnie. Wydawaj bez regresji.
Badania mogą ujawnić kompromis. Wydanie nie może go ukryć. Deterministyczna regresja rozmiaru archiwum:
0 bajtów dozwolone
Potwierdzona regresja szybkości poza marginesem szumu tego samego runnera:
wydanie zablokowane
BRAMKA WYDAJNOŚCI
01 / ARENA
To nie współczynnik kompresji.
To pozycja wydajnościowa.
Arena strukturalna zadaje jedno wąskie pytanie: ile bajtów zapisało każde narzędzie dla tego samego wrogiego drzewa? Różnice w semantyce dostępu, odzyskiwania i trwałości pozostają jawne zamiast być przedstawiane jako parytet.
ZAPISANE BAJTY · MNIEJ ZNACZY LEPIEJ
wejście logiczne
konkurent
Porównanie rozmiarów archiwów
Czytaj to poprawnie:
przegrana w surowym rozmiarze z kompresorem solidnym może współistnieć z mocniejszą semantyką dostępu selektywnego i odzyskiwania. Strona zachowuje oba fakty.
FRONT KATEGORII · SOLIDNY ZSTD-19
Niezależne archiwa workloadów na dokładnych drzewach zachowują własne pochodzenie zamiast pożyczać wynik całego zestawu.
Ładowanie dowodów kategorii na dokładnych drzewach…
TABLICA RED TEAM
PORAŻKI POZOSTAJĄ WIDOCZNE
Wiarygodność benchmarku bierze się z zachowanych porażek, nie z idealnie zielonego panelu.
Ładowanie zastrzeżeń benchmarku…
POKWITOWANIE DOWODÓW
OTWARTA KSIĘGA
Każdy nagłówek zachowuje przypisane drzewo, rekord, zakres i poziom autorytetu. Im atrakcyjniejsza staje się teza, tym łatwiej powinno być sprawdzić jej źródło.
Format
Drzewo
Pliki
Rekord
Kontrakt
Surowe dane strony ↗
JSON agenta ↗
Orientacja LLM ↗
Historia benchmarków ↗
02 / DLACZEGO MOŻE WYGRAĆ
Archiwum jest kompilowane jako
graf informacji.
CMPCT wyszukuje dokładne relacje między wymaganymi obiektami, wybiera korzenie fizyczne i zapisuje deterministyczne ścieżki rekonstrukcji, jawnie uwzględniając koszty lokalności, integralności i odzyskiwania.
Koncepcyjny graf informacji
DRZEWO LOGICZNE
wymagane bajty
DOKŁADNE STRUMIENIE
współdzielona struktura
TOŻSAMOŚĆ
zdeduplikowane obiekty
OGRANICZONE KORZENIE
dekodowanie selektywne
INDEKS + DOWÓD
integralność / odzyskiwanie
Dokładna tożsamość
Identyczna zawartość może zbiegać się do jednego uwierzytelnionego korzenia fizycznego bez zlewania niezależnych ścieżek logicznych.
Przechowywanie świadome relacji
Wymagane obiekty mogą ponownie używać dokładnej skompresowanej struktury zamiast płacić za duplikację tylko dlatego, że różnią się nazwy plików.
Dostęp selektywny
Czytaj żądany obiekt zamiast robić z jednej ogromnej dekompresji całego archiwum jedyną drogę do użytecznych bajtów.
Ograniczony kontekst
Kontekst między plikami jest testowany i ograniczany, aby zysk rozmiaru nie powodował po cichu nieograniczonej pracy odczytu.
Integralność
Indeksy i dane fizyczne mają jawne kontrole; sukces nie oznacza po prostu „dekompresor nie zgłosił błędu”.
Odzyskiwanie fizyczne
Nadmiarowe uwierzytelnione metadane istnieją jako rzeczywista ścieżka czytnika, a nie obietnica disaster recovery zapisana w prozie.
03 / KANONICZNE VS FRONT
Jeden projekt.
Dwa poziomy autorytetu.
Front badawczy może być agresywny. Kanoniczny reader/writer jest kontraktem interoperacyjności. Ładna strona nigdy nie pozwala reprezentacji badawczej pożyczać autorytetu kanonicznego.
WYSYŁANE / KANONICZNE
kontrakt reader / writer
FRONT BADAWCZY
kandydat benchmarkowy
DOWODY PUBLICZNE
OTWARTE
tezy wynikają z zapisanych rekordów
04 / KANONICZNY PARYTET WYKONANIA Z ZIP
Wysyłany CMPCT kontra ZIP.
Rozmiar, tworzenie, rozpakowanie.
Parytet operacyjny kanonicznego readera/writera na granicy biblioteki i świeżych procesów CLI. Celowo pozostaje oddzielony od badawczego frontu przechowywania.
Zapisany rekord
Korpus
Rozmiar archiwum
Tworzenie w bibliotece
Rozpakowanie w bibliotece
Tworzenie CLI
Rozpakowanie CLI
05 / LABORATORIUM W PRZEGLĄDARCE
Dość czytania.
Zbuduj jedno.
Przenośny writer działa na tym urządzeniu. Pliki nie są wysyłane. Emituje konserwatywny podzbiór kanoniczny i wyłącza się zamiast zgadywać po zmianie rewizji formatu.
Sprawdzanie zgodności kanonicznej…
Writer blokuje się zgodnie z rewizją formatu repozytorium.
UTWÓRZ
Przenośny writer CMPCT
LOKALNIE
Upuść pliki tutaj albo je wybierz
Upuść pliki lub folder
Zbuduj archiwum dokładne bajt w bajt bez wysyłania danych.
Wybierz pliki
Wybierz folder
Nie wybrano plików.
Zbuduj .cmpct
Tryb przenośny zachowuje zwykłe pliki, indeksowanie ścieżek, deduplikację po dokładnej treści, SHA-256/CRC32 i zapis RAW/Deflate. Pełna semantyka systemu plików pozostaje domeną CLI.
SPRAWDŹ
Lupa nagłówka
BEZ WYSYŁANIA
Czytaj tylko stały nagłówek lokalnego archiwum CMPCT. Pełna walidacja strukturalna pozostaje przy czytniku kanonicznym i natywnym rdzeniu.
Wybierz plik .cmpct
Magic
Pole wersji
Indeks główny
Zakres danych
06 / TRAJEKTORIA WYDAŃ
Wydania rdzenia muszą
zasłużyć na numer.
Wydania numeryczne rosną, gdy sam CMPCT materialnie się poprawia. Rewizje warstwy wizualnej mogą wyglądać radykalnie lepiej bez udawania, że zmienił się silnik archiwum.
07 / PRZEKAZANIE INŻYNIERSKIE
Ładne z zewnątrz.
Sprawdzalne aż do samego dna.
Ta sama warstwa, która czyni CMPCT czytelnym dla człowieka, udostępnia agentom stan czytelny maszynowo i trwałe dowody inżynieryjne.
maszynowo czytelna orientacja projektu
publiczne dowody i stan wydań
kolejność czytania agenta i granica autorytetu
Repozytorium
Repozytorium ↗
format, benchmarki, implementacja
Wydajność to nie zrzut ekranu. To kontrakt wydania.
Format ↗
Benchmarki ↗
Pre-1.0 · propozycja licencji nie została jeszcze przyjęta · zapisane dowody benchmarkowe pozostają kwalifikowane przez zarejestrowane środowisko i semantykę.
CMPNX11 jest wyłącznie badawczy i nie jest czytelny przez kanoniczny reader r24.
Przenośny zysk rozmiaru względem v0.28 jest mały (48,601 B / 0.035333%) i skupiony w 2 z 15 workloadów; 13 workloadów celowo wraca dokładnie do poprzedniego zachowania.
Przed poprawką schedulingu zaakceptowany przenośny portfel z próby 5 zużywał 2.175x czasu tworzenia v0.28; każde twierdzenie o szybkości schedulera dotyczy tylko zmierzonego stałego wrogiego agregatu.
Na sparowanym wrogim agregacie strukturalnym próba #5 jest mniejsza od 7z/LZMA2, ale nadal o 82,112 B większa od solidnego tar/Zstd-19 i o 85,125 B większa od ZPAQ m5.
Konkurenci z archiwami solidnymi mają inną semantykę odczytu selektywnego i odzyskiwania; te wiersze porównują zapisane bajty, nie parytet funkcji.
CMPCT zachowuje linki/sparse/uid-gid/xattrs w archiwum; ten punkt odniesienia ZIP w Pythonie dereferencjonuje symlinki i nie zachowuje bogatszej semantyki systemu plików.
zaakceptowany front badawczy v0.29; kanoniczne r24 bez zmian
jedno deterministyczne drzewo 724 plików wrogie podobieństwu; rozmiary archiwów całego drzewa z tego samego przebiegu; różnice semantyczne względem archiwów solidnych pozostają jawne
sparowany zapisany benchmark
front badawczy
front badawczy CMPCT
kandydat benchmarku badawczego
Brak zapisanego benchmarku dla frontu badawczego.
Rekord:
commit:
małe pliki
kod źródłowy
media
binarne
deduplikacja i linki
sparse
zagnieżdżone
połączone
repozytorium deweloperskie
środowisko biurowe
biblioteka mediów
analityka i baza danych
logi i telemetria
kopie przyrostowe
niekompresowalne i podobne do zaszyfrowanych
wiele małych plików
artefakty ML
duże mieszane dane binarne
przesunięte wersje
fałszywi sąsiedzi
niestabilność granic
rodzina Deflate
niekompresowalne
`);
export const MESSAGES = Object.freeze({
  files: "{n} plików", file: "{n} plik", logical: "{bytes} logicznych", logicalInputFiles: "{bytes} wejścia logicznego · {n} plików",
  smallerThan: "{pct} mniej niż {name}", largerThan: "{pct} więcej niż {name}", sameStored: "tyle samo zapisanych bajtów co {name}", versus: "vs {name}",
  cmpctSmaller: "CMPCT mniejszy · sparowane zapisane bajty", cmpctLarger: "CMPCT większy · sparowane zapisane bajty", sameBytes: "te same zapisane bajty", unavailableMatched: "sparowane zapisane bajty niedostępne",
  currentFrontier: "obecny front badawczy CMPCT", categoryScore: "{wins}/{total} mniejszych · {losses} większych", noCategory: "dowody kategorii niedostępne", noFreshCategory: "Brak świeżych dowodów kategorii na dokładnych drzewach dla tego frontu.",
  comparisonUnavailable: "porównanie niedostępne", noQualification: "Dla tego publicznego frontu nie zapisano kwalifikacji benchmarku.",
  heroIf: "Jeśli {name} zapisuje 100 MB w tym teście parowanym, CMPCT potrzebuje około {value} MB.", heroNeeds: "CMPCT potrzebuje obecnie około {value} MB na każde 100 MB zapisywane przez {name} w tym teście parowanym.",
  seriousBaseline: "Poważny punkt odniesienia rozmiaru: {relation}.", scopedScheduler: "Ograniczony wynik schedulera: {pct}% mniej wall time w jego stałej bramce.", canonicalRemains: "Format kanoniczny pozostaje r{revision}.",
  frontierQualification: "{frontier} · {files} plików na sparowanym drzewie strukturalnym.{serious}{speed} Format kanoniczny pozostaje r{revision}.", fixedSchedulerGate: "stała wroga bramka schedulera · nie globalne twierdzenie o szybkości", winsAgainst: "{wins}/{total} wygranych vs {name}",
  noCommittedParity: "Brak zapisanego rekordu parytetu", repetitionsMedian: "mediana z {n}×", semanticQualification: "Zastrzeżenie semantyczne:", interpretation: "Interpretacja:", currentProjectRelease: "Bieżące wydanie projektu", versionedMilestone: "Wersjonowany kamień milowy",
  writerVerified: "Przenośny writer zweryfikowany dla kanonicznego formatu r{revision}.", regularSubset: "Tylko podzbiór zwykłych plików; pełna semantyka systemu plików pozostaje domeną CLI.", writerPaused: "Writer przeglądarki wstrzymany po rewizji formatu {revision}.", writerRefuses: "Ten build jest zweryfikowany dla r{supported}; odmawia zgadywania nowszej gramatyki.",
  readyLocally: "Gotowe lokalnie", cliOverLimit: "Użyj CLI: ponad limit przeglądarki", input: "Wejście", archive: "Archiwum", delta: "Różnica", smaller: "{bytes} mniej", overhead: "{bytes} narzutu", buildingLocally: "Budowanie lokalnie…", builtOnDevice: "Archiwum zbudowane na tym urządzeniu.",
  logicalFilesUnique: "{logical} plików logicznych → {unique} unikalnych blobów · {deflate} Deflate / {raw} RAW.", saveCmpct: "Zapisz .cmpct", couldNotBuild: "Nie udało się zbudować archiwum.", fixedMagicError: "Stała sygnatura magic nie wygląda jak CMPCT.", inspection: "Inspekcja", benchmarkUnavailable: "Dane benchmarku niedostępne: {error}", canonicalDataMissing: "Nie załadowano kanonicznych danych strony."
});
