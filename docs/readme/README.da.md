<div align="center">
  <a href="https://fcmo-ai.github.io/.CMPCT/?lang=da"><img src="../../.github/assets/repository-hero.svg" width="100%" alt="CMPCT — Arkivformater har sluttet fred med kompromiser. CMPCT har ikke."></a>

  **Et generelt tabsfrit arkiv-/containerprojekt, der flytter lagrede bytes, selektiv adgang, integritet, gendannelse og portabilitet fremad samlet.**

  **[Website](https://fcmo-ai.github.io/.CMPCT/?lang=da)** · **[Browserlab](https://fcmo-ai.github.io/.CMPCT/?lang=da#lab)** · **[Benchmarks](../BENCHMARKS.md)** · **[Format](../FORMAT.md)** · **[Roadmap](../ROADMAP.md)** · **[Agent-start](../CURRENT_STATE.md)**

  <sub>core v0.29.0 · kanonisk format r24 · overflade 0.29.k · pre-1.0</sub>
</div>

> **Kurateret oversættelse.** Dette er en versionsstyret semantisk tilpasning af den menneskevendte README. Den engelske [`README.md`](../../README.md) er fortsat kanonisk autoritet. Tal, stier, formatnavne og evidensgrænser bevares med vilje. Teksten mærkes ikke som menneskeligt tosproget gennemgået, før det faktisk er sket.

---

> **Ydelse er releasekontrakten.** Forskning må finde et ubehageligt trade-off. En promoveret release må ikke skjule det: deterministisk regression i arkivstørrelse har **0-byte tolerance**, bekræftet langsommelighed uden for samme runners dokumenterede støjmargen blokerer promotion, og tabende workloads forbliver offentlige beviser.

## Hvorfor CMPCT findes

| | CMPCT vil forbedre |
|---|---|
| **Lagrede bytes** | Præcis identitet, indholdsbevidste repræsentationer og begrænset genbrug af relationer i stedet for at behandle hver fil som en isoleret strøm. |
| **Selektiv adgang** | Læs det ønskede objekt eller interval uden obligatorisk dekompression af hele arkivet. |
| **Integritet + gendannelse** | Checks, redundant metadata og salvage-stier som reel readeradfærd, ikke disaster-recovery-prosa. |
| **Filsystemtrohed** | Bevar links, sparse files, metadata og moderne update-semantik. |
| **Interoperabilitet** | Hold kanonisk reader/writer-kontrakt, ZIP-export, native core og portability gates adskilt fra eksperimentel grammatik. |
| **Evidenskvalitet** | Offentlige claims fra reproducerbare versionerede records, synlige tab og ingen benchmarkteater. |

CMPCT er ikke “Zstd med en ny filendelse” og er ikke tilfreds med én håndplukket mappe. Målet er et stærkere standardarkiv for **størrelse, hastighed, random access, trohed, integritet, gendannelse, opdateringer og moderne storage-semantik**, uden skjulte omkostninger andetsteds.

## Seneste verificerede front

**Projekt v0.29.0 — Mosaic / Residual Program Packing** flytter den verificerede forskningsmotor fremad, mens det leverede kanoniske format forbliver **revision 24**.

| v0.29 forskning | Resultat |
|---|---:|
| Portabelt arvet frontier-portfolio | **137,501,815 B** |
| Direkte v0.28-base | 137,550,416 B |
| Præcis besparelse | **48,601 B (0.035333%)** |
| Portable workloads | **15** |
| Forbedret / regression | **2 / 0** |
| Præcise v0.28-fallbacks | **13 / 15** |
| Hostile mechanism suites | **4.407362% mindre**, 9 forbedret / 0 regression over 18 workloads |
| Fast hostile scheduler | **182.454 s → 97.944 s median (-46.318%)**, valgt arkiv byte-identisk |

På det deterministiske resemblance-hostile aggregat med 724 filer / 93,526,384 bytes lagrer accepteret forsøg #5 **47,147,764 B**. På samme træ: ZPAQ m5 47,062,639 B, solid tar+Zstd-19 47,065,652 B, 7z/LZMA2 47,430,343 B, Borg 76,461,311 B og ZIP/Deflate-9 76,690,799 B.

Det er **matchede sammenligninger af lagrede bytes, ikke semantiske paritetsclaims**. Solid-arkiver, backuprepositories og CMPCT har forskellige trade-offs. Permanent record: [`docs/releases/v0.29.0.md`](../releases/v0.29.0.md); maskinlæsbar evidens: [`benchmarks/history/`](../../benchmarks/history/).

### Leveret vs front

| Autoritet | Status | Betydning |
|---|---|---|
| **Kanonisk reader/writer** | **r24** | Hvad `python -m cmpct create` skriver, og kanoniske readers skal forstå. |
| **Forskningsfront** | **CMPNX11 / v0.29.0** | Eksperimentel Mosaic + Residual Program Packing; ikke r24-syntaks. |
| **Offentlig overflade** | **0.29.k** | Repo/site/docs-præsentation uden semantisk autoritet. |
| **Licens** | **Apache-2.0 foreslået** | Forslag, ikke endelig offentlig grant. |

## Hvad CMPCT kan i dag

Kanonisk r24 indeholder content-addressed deduplication, adaptiv Zstandard/raw storage, Zstd dictionaries og micro-solid packs, content-defined chunking, hurtige byte-range reads og parallel decode, hardlink/symlink/sparse preservation, UID/GID/xattrs, ZIP/WHL virtualization, lossless PCM-WAV når det vinder, raw Deflate reuse til ZIP-export, CRC32 + SHA-256, redundante head/tail indexes, self-describing blob records, transaction append journal, on-demand ZIP-export og valgfri reproducerbar/deterministisk parallel creation.

v0.29 undersøger også bounded FastCDC units, multi-band similarity search, depth-1 COPY/LITERAL deltas, multi-root Mosaic placement, Residual Program Packing, exact v0.28 fallback, locality/resource ceilings, exact DEFLATE via pinned memory-safe bridge, Merkle-authenticated records, authenticated tail recovery, strict remote range sources og byte-identical parallel scheduling.

Forskningsmekanismer forbliver uden for kanonisk reader, indtil format integration, conformance, hardening, native parity, recovery og portability er bestået separat.

Regel: **indholdsstyret valg, ikke filendelsesfolklore**.

## Hurtig start

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

Fresh-process CLI er med vilje serial uden `--workers N`. v0.28-gaten målte ~10 ms thread-pool startup på et lille medietræ; in-process `Builder` beholder deterministisk parallel creation som standard.

Valgfri native Linux-chunker:

```bash
cc -O3 -shared -fPIC native/cmpct_cdc.c -o src/cmpct/libcmpct_cdc.so
```

Readeren **afhænger ikke** af helperen; chunkgrænser lagres eksplicit på disk.

## Ydelsesposition

- **størrelse:** identisk input + encoder semantics må aldrig give større arkiv; **0 bytes** tolerance;
- **create/extract:** base og candidate på samme runner med gentagne medianer; bekræftet slowdown uden for noise envelope blokerer;
- **evidens:** hver numerisk core release committer en frisk offentlig benchmarkrecord;
- **corpora:** tabende/adversarial workloads forbliver synlige.

Se [`docs/PERFORMANCE_RELEASE_GATE.md`](../PERFORMANCE_RELEASE_GATE.md) og [`docs/BREAKTHROUGH_REHABILITATION.md`](../BREAKTHROUGH_REHABILITATION.md).

## Læserækkefølge for ny agent

`docs/AGI_ENGINEERING_STANDARD.md` → `README.md` → `AGENTS.md` → `docs/CURRENT_STATE.md` → nyeste `docs/releases/` → `docs/PERFORMANCE_RELEASE_GATE.md` → `docs/BREAKTHROUGH_REHABILITATION.md` → `docs/FORMAT.md` → `docs/HISTORY.md` → EntropyGraph/Mosaic-docs → `docs/HARDENING.md` → `docs/PORTABILITY.md` + `docs/NATIVE_CORE.md` → `docs/RESEARCH_LOG.md` → `docs/BENCHMARKS.md` + `benchmarks/history/` → `docs/PUBLIC_SURFACE.md` → `docs/ROADMAP.md`.

En ny agent bør ikke behøve private chats, private corpora eller unrelated projektkontekst.

## Repositorykort

`src/cmpct/` = kanonisk r24-reference; `experiments/` = forskningslinje; `benchmarks/` = deterministiske corpora/gates + `benchmarks/history/`; `fuzz/` = parser/resource-angreb; `tools/check_*` = kontraktchecks; `site/` = site + Browser Lab; `native/` = acceleratorer/shared core; `docs/` = kontrakter/kampagner/historik/roadmap; `tests/` = format, round-trip, similarity, locality og reproducibility regressions.

## Website

Sitet er bygget til at **skabe effekt først, bevise påstanden bagefter og fortjene tillid til sidst**. Tal, konkurrenter, workloads, tab og core-status kommer fra versioneret benchmarkhistorik. **Forskningsfront**, **kanonisk paritet** og **surface revision** holdes strengt adskilt. Visuel aggression er tilladt; opdigtede sejre er ikke.

**Åbn:** https://fcmo-ai.github.io/.CMPCT/?lang=da

## Versionsdisciplin

1. **Numerisk core (`MAJOR.MINOR.PATCH`)** — kun for materiel produktfremgang; efter v0.27.1 flytter normal progression `MAJOR.MINOR`, `PATCH=0` for packaging compatibility.
2. **Surface (`MAJOR.MINOR.LETTER`)** — site/docs/repo/workflow; nu **`0.29.k`**.
3. **On-disk revision** — kun når readers behøver ny grammatik/semantik; kanonisk **r24**.

CI holder akserne separate og afviser ufortjente bumps.

## Historik, provenance og offentlig overflade

CMPCT voksede ud af Seekable-Zstd, indexed-Zstd, adaptive-framing og ZIP-family eksperimenter. Teknisk historik bevares; private corpusidentiteter, artifacts og unrelated provenance gør ikke. Offentlige benchmarks skal være reproducerbare eller bruge bevidst offentlige/syntetiske input; historiske resultater er **ikke en universel ydelsesgaranti**.

CMPCT skal stå alene. Repo/site må ikke kræve eller eksponere unrelated interne projekter, private kundedata, corpora, persondata, chattranskripter, credentials, private artifactnavne eller interne links. Se `docs/PUBLIC_SURFACE.md`.

## Kanonicitet

Repositoryet erstatter chat-local prototyper og benchmarkscripts. Materiel engine/archive-fremgang får numerisk release; site/docs/præsentation bruger `SURFACE_REVISION`; forskning forbliver eksplicit eksperimentel indtil promotion. Eksperimentel kode må ikke hævde kanonisk støtte uden integration i reference reader/writer og conformance.

## Licens

Apache License 2.0 er den **aktuelt foreslåede licens**, ikke den endeligt vedtagne. Tekst: `LICENSE-APACHE-2.0-PROPOSED.txt`; adoption-checklist: `LICENSING.md`. Indtil processen er færdig, må CMPCT ikke beskrives som endeligt udgivet under Apache-2.0.
