<div align="center">
  <a href="https://fcmo-ai.github.io/.CMPCT/?lang=fi"><img src="../../.github/assets/repository-hero.svg" width="100%" alt="CMPCT — Arkistomuodot tekivät rauhan kompromissien kanssa. CMPCT ei."></a>

  **Yleiskäyttöinen häviötön arkisto-/konttiprojekti, joka kehittää tallennettuja tavuja, valikoivaa pääsyä, eheyttä, palautusta ja siirrettävyyttä yhdessä.**

  **[Sivusto](https://fcmo-ai.github.io/.CMPCT/?lang=fi)** · **[Selainlaboratorio](https://fcmo-ai.github.io/.CMPCT/?lang=fi#lab)** · **[Benchmarkit](../BENCHMARKS.md)** · **[Formaatti](../FORMAT.md)** · **[Roadmap](../ROADMAP.md)** · **[Agentin aloitus](../CURRENT_STATE.md)**

  <sub>core v0.29.0 · kanoninen formaatti r24 · pinta 0.29.k · pre-1.0</sub>
</div>

> **Kuratoitu käännös.** Tämä on ihmisille tarkoitetun README:n versionhallittu semanttinen sovitus. Englanninkielinen [`README.md`](../../README.md) pysyy kanonisena auktoriteettina. Numerot, polut, formaattinimet ja todisterajat säilytetään tarkoituksella. Tekstiä ei merkitä kaksikielisen ihmisen tarkistamaksi ennen kuin tarkistus todella tapahtuu.

---

> **Suorituskyky on julkaisusopimus.** Tutkimus saa löytää epämukavan kompromissin. Promotoitu julkaisu ei saa piilottaa sitä: deterministisen arkistokoon regression toleranssi on **0 tavua**, saman runnerin dokumentoidun kohinamarginaalin ylittävä vahvistettu hidastuminen estää promotionin, ja häviävät workloadit jäävät julkiseksi näytöksi.

## Miksi CMPCT on olemassa

| | CMPCT pyrkii parantamaan |
|---|---|
| **Tallennetut tavut** | Täsmällinen identiteetti, sisältötietoiset esitykset ja rajattu suhteiden uudelleenkäyttö sen sijaan, että jokainen tiedosto olisi irrallinen tavujono. |
| **Valikoiva pääsy** | Pyydetyn objektin tai alueen lukeminen ilman koko arkiston pakollista purkua. |
| **Eheys + palautus** | Tarkistukset, redundantti metadata ja salvage-polut todellisena reader-käyttäytymisenä, ei disaster-recovery-proosana. |
| **Tiedostojärjestelmäuskollisuus** | Linkit, sparse files, metadata ja moderni update-semantikka säilyvät. |
| **Yhteentoimivuus** | Kanoninen reader/writer-sopimus, ZIP-export, native core ja portability gates pidetään erillään kokeellisesta kieliopista. |
| **Näytön laatu** | Julkiset väitteet reproducerattavista versionhallituista recordeista, tappiot näkyvissä, ei benchmarkteatteria. |

CMPCT ei ole ”Zstd uudella tiedostopäätteellä” eikä yhden käsin valitun hakemiston voitto riitä. Tavoite on vahvempi oletusarkisto **koon, nopeuden, random accessin, uskollisuuden, eheyden, palautuksen, päivitysten ja modernin storage-semantikan** suhteen ilman piilotettuja kustannuksia muualla.

## Uusin varmennettu eturaja

**Project v0.29.0 — Mosaic / Residual Program Packing** vie varmennettua tutkimusmoottoria eteenpäin, kun toimitettava kanoninen formaatti pysyy **revision 24**:ssä.

| v0.29 tutkimusnäyttö | Tulos |
|---|---:|
| Portabeli peritty frontier-portfolio | **137,501,815 B** |
| Suora v0.28-base | 137,550,416 B |
| Täsmällinen säästö | **48,601 B (0.035333%)** |
| Portabelit workloadit | **15** |
| Parani / regressio | **2 / 0** |
| Täsmälliset v0.28-fallbackit | **13 / 15** |
| Hostile mechanism suites | **4.407362% pienempi**, 9 parani / 0 regressiota 18 workloadilla |
| Kiinteä hostile scheduler | **182.454 s → 97.944 s mediaani (-46.318%)**, valittu arkisto byte-identical |

Deterministisellä resemblance-hostile aggregaatilla, jossa on 724 tiedostoa / 93,526,384 tavua, hyväksytty yritys #5 tallentaa **47,147,764 B**. Samalla puulla: ZPAQ m5 47,062,639 B, solid tar+Zstd-19 47,065,652 B, 7z/LZMA2 47,430,343 B, Borg 76,461,311 B ja ZIP/Deflate-9 76,690,799 B.

Nämä ovat **paritettuja tallennettujen tavujen vertailuja, eivät semanttisen pariteetin väitteitä**. Solid-arkistoilla, backup-repositoryillä ja CMPCT:llä on eri trade-offit. Pysyvä record: [`docs/releases/v0.29.0.md`](../releases/v0.29.0.md); machine-readable evidence: [`benchmarks/history/`](../../benchmarks/history/).

### Toimitettu vs eturaja

| Auktoriteetti | Tila | Merkitys |
|---|---|---|
| **Kanoninen reader/writer** | **r24** | Mitä `python -m cmpct create` kirjoittaa ja mitä kanonisten readerien on ymmärrettävä. |
| **Tutkimuseturaja** | **CMPNX11 / v0.29.0** | Kokeellinen Mosaic + Residual Program Packing; ei r24-syntaksia. |
| **Julkinen pinta** | **0.29.k** | Repo/site/docs-esitys ilman arkistosemanttista auktoriteettia. |
| **Lisenssi** | **Apache-2.0 ehdotettu** | Ehdotus, ei lopullinen julkinen grant. |

## Mitä CMPCT osaa nyt

Kanoninen r24 sisältää content-addressed deduplicationin, adaptiivisen Zstandard/raw storagen, Zstd dictionaries ja micro-solid packs, content-defined chunkingin, nopeat byte-range readit ja parallel decoden, hardlink/symlink/sparse preservationin, UID/GID/xattrs, ZIP/WHL virtualizationin, lossless PCM-WAV:n kun se voittaa, raw Deflate reusen ZIP-exportiin, CRC32 + SHA-256:n, redundantit head/tail indexes, self-describing blob records, transaction append journalin, on-demand ZIP-exportin sekä valinnaisen reproducerattavan/deterministisesti rinnakkaisen creationin.

v0.29 tutkii lisäksi bounded FastCDC units, multi-band similarity search, depth-1 COPY/LITERAL deltas, multi-root Mosaic placement, Residual Program Packing, exact v0.28 fallback, locality/resource ceilings, exact DEFLATE pinned memory-safe bridgen kautta, Merkle-authenticated records, authenticated tail recovery, strict remote range sources ja byte-identical parallel scheduling.

Tutkimusmekanismit pysyvät kanonisen readerin ulkopuolella, kunnes format integration, conformance, hardening, native parity, recovery ja portability on läpäisty erikseen.

Sääntö: **sisältöohjattu valinta, ei tiedostopäätefolklore**.

## Pikakäynnistys

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

Fresh-process CLI on tarkoituksella sarjallinen ilman `--workers N`:ää. v0.28-gate näki ~10 ms thread-pool startupin pienellä media-puulla; in-process `Builder` pitää deterministisen rinnakkaisen creationin oletuksena.

Valinnainen native Linux-chunker:

```bash
cc -O3 -shared -fPIC native/cmpct_cdc.c -o src/cmpct/libcmpct_cdc.so
```

Reader **ei riipu** helperistä; chunk-rajat tallennetaan eksplisiittisesti levylle.

## Suorituskykyasema

- **koko:** identtinen input + encoder semantics ei saa tuottaa suurempaa arkistoa; **0 tavua** toleranssia;
- **create/extract:** base ja candidate samalla runnerilla, toistetut mediaanit; vahvistettu slowdown noise envelopen ulkopuolella estää release:n;
- **evidence:** jokainen numeerinen core release committaa uuden julkisen benchmark-recordin;
- **corpora:** häviävät/adversarial workloadit pysyvät näkyvissä.

Katso [`docs/PERFORMANCE_RELEASE_GATE.md`](../PERFORMANCE_RELEASE_GATE.md) ja [`docs/BREAKTHROUGH_REHABILITATION.md`](../BREAKTHROUGH_REHABILITATION.md).

## Uuden agentin lukujärjestys

`docs/AGI_ENGINEERING_STANDARD.md` → `README.md` → `AGENTS.md` → `docs/CURRENT_STATE.md` → uusin `docs/releases/` → `docs/PERFORMANCE_RELEASE_GATE.md` → `docs/BREAKTHROUGH_REHABILITATION.md` → `docs/FORMAT.md` → `docs/HISTORY.md` → EntropyGraph/Mosaic-dokumentit → `docs/HARDENING.md` → `docs/PORTABILITY.md` + `docs/NATIVE_CORE.md` → `docs/RESEARCH_LOG.md` → `docs/BENCHMARKS.md` + `benchmarks/history/` → `docs/PUBLIC_SURFACE.md` → `docs/ROADMAP.md`.

Uuden agentin ei pitäisi tarvita yksityisiä chatteja, corpora tai unrelated projektikontekstia.

## Repositorykartta

`src/cmpct/` = kanoninen r24-reference; `experiments/` = tutkimuslinja; `benchmarks/` = deterministiset corpora/gates + `benchmarks/history/`; `fuzz/` = parser/resource-hyökkäykset; `tools/check_*` = sopimustarkistukset; `site/` = site + Browser Lab; `native/` = kiihdyttimet/shared core; `docs/` = sopimukset/kampanjat/historia/roadmap; `tests/` = format, round-trip, similarity, locality ja reproducibility regressions.

## Sivusto

Sivusto on tehty **vaikuttamaan ensin, todistamaan väite toiseksi ja ansaitsemaan luottamus viimeiseksi**. Luvut, kilpailijat, workloadit, tappiot ja core-status tulevat versionhallituista benchmarkeista. **Tutkimuseturaja**, **kanoninen pariteetti** ja **surface revision** pidetään erillään. Visuaalinen aggressiivisuus on sallittu; keksityt voitot eivät.

**Avaa:** https://fcmo-ai.github.io/.CMPCT/?lang=fi

## Versiokuri

1. **Numeerinen core (`MAJOR.MINOR.PATCH`)** — vain materiaalisesta tuoteparannuksesta; v0.27.1 jälkeen normaali eteneminen siirtää `MAJOR.MINOR`, `PATCH=0` packaging compatibilityn vuoksi.
2. **Surface (`MAJOR.MINOR.LETTER`)** — site/docs/repo/workflow; nyt **`0.29.k`**.
3. **On-disk revision** — vain jos readerit tarvitsevat uuden kieliopin/semantiikan; kanoninen **r24**.

CI pitää akselit erillään ja torjuu ansaitsemattomat bumpit.

## Historia, provenienssi ja julkinen pinta

CMPCT kasvoi Seekable-Zstd-, indexed-Zstd-, adaptive-framing- ja ZIP-family-kokeista. Tekninen historia säilyy; yksityiset corpusidentiteetit, artefaktit ja unrelated provenance eivät. Julkisten benchmarkien on oltava reproducerattavia tai käytettävä tarkoituksella julkisia/synteettisiä inputteja; historialliset tulokset **eivät ole universaali suorituskykytakuu**.

CMPCT:n on seisottava omillaan. Repo/site ei saa vaatia tai paljastaa unrelated sisäisiä projekteja, yksityisiä asiakastietoja, corpora, henkilötietoja, chattranskripteja, credentialseja, private artifact names tai sisäisiä linkkejä. Katso `docs/PUBLIC_SURFACE.md`.

## Kanonisuus

Repository korvaa chat-local prototyypit ja benchmarkscriptit. Materiaalinen engine/archive-edistys ansaitsee numeerisen releasen; site/docs/presentation käyttää `SURFACE_REVISION`:ia; tutkimus pysyy eksplisiittisesti kokeellisena promotioniin asti. Kokeellinen koodi ei saa väittää kanonista tukea ennen reference reader/writer- ja conformance-integraatiota.

## Lisenssi

Apache License 2.0 on **nyt ehdotettu lisenssi**, ei vielä lopullisesti hyväksytty. Teksti: `LICENSE-APACHE-2.0-PROPOSED.txt`; adoption checklist: `LICENSING.md`. Ennen prosessin valmistumista CMPCT:tä ei saa esittää lopullisesti Apache-2.0:n alla julkaistuna.
