<div align="center">
  <a href="https://fcmo-ai.github.io/.CMPCT/?lang=fr"><img src="../../.github/assets/repository-hero.svg" width="100%" alt="CMPCT — Les formats d’archive ont accepté les compromis. Pas CMPCT."></a>

  **Un projet d’archive/conteneur sans perte à usage général, conçu pour faire progresser ensemble les octets stockés, l’accès sélectif, l’intégrité, la récupération et la portabilité.**

  **[Site](https://fcmo-ai.github.io/.CMPCT/?lang=fr)** · **[Labo navigateur](https://fcmo-ai.github.io/.CMPCT/?lang=fr#lab)** · **[Benchmarks](../BENCHMARKS.md)** · **[Format](../FORMAT.md)** · **[Roadmap](../ROADMAP.md)** · **[Entrée agents](../CURRENT_STATE.md)**

  <sub>cœur v0.29.0 · format canonique r24 · surface 0.29.k · pré-1.0</sub>
</div>

> **Traduction éditoriale.** Cette version est une adaptation sémantique versionnée du README destiné aux humains. Le [`README.md`](../../README.md) anglais reste l’autorité canonique. Les chiffres, chemins, noms de formats et limites de preuve sont volontairement conservés. Cette traduction n’est pas présentée comme relue par un humain bilingue tant qu’une telle relecture n’a pas eu lieu.

---

> **La performance est le contrat de chaque version.** La recherche peut révéler un compromis inconfortable. Une version promue n’a pas le droit de le masquer : la régression déterministe de taille d’archive a une **tolérance de 0 octet**, une baisse de vitesse confirmée hors de la marge de bruit documentée du même runner bloque la promotion, et les workloads perdants restent des preuves publiques.

## Pourquoi CMPCT existe

| | CMPCT cherche à améliorer |
|---|---|
| **Octets stockés** | Exploiter l’identité exacte, des représentations conscientes du contenu et la réutilisation bornée des relations au lieu de traiter chaque fichier comme un flux indépendant. |
| **Accès sélectif** | Lire l’objet ou la plage demandée sans imposer une décompression de toute l’archive. |
| **Intégrité + récupération** | Faire des contrôles, métadonnées redondantes et chemins de sauvetage un comportement réel du lecteur plutôt qu’une promesse de reprise après sinistre. |
| **Fidélité du système de fichiers** | Préserver liens, fichiers clairsemés, métadonnées et sémantique de mise à jour attendus d’un conteneur moderne. |
| **Interopérabilité** | Séparer clairement contrat canonique reader/writer, export ZIP, cœur natif et gates de portabilité de la grammaire expérimentale. |
| **Qualité des preuves** | Dériver les affirmations publiques d’enregistrements reproductibles versionnés, conserver les défaites et refuser le théâtre de benchmark. |

CMPCT n’est pas « Zstd avec une nouvelle extension » et ne se satisfait pas de gagner sur un dossier choisi à la main. L’objectif est une meilleure archive par défaut sur **taille, vitesse, accès aléatoire, fidélité, intégrité, récupération, mises à jour et sémantique moderne du stockage**, sans déplacer silencieusement le coût ailleurs.

## Dernière frontière vérifiée

**Projet v0.29.0 — Mosaic / Residual Program Packing** fait progresser le moteur de recherche vérifié tandis que le format canonique livré reste en **révision 24**.

| Preuve de recherche v0.29 | Résultat |
|---|---:|
| Portefeuille portable hérité de la frontière | **137,501,815 B** |
| Base directe v0.28 | 137,550,416 B |
| Économie exacte | **48,601 B (0.035333%)** |
| Workloads portables | **15** |
| Améliorés / régressés | **2 / 0** |
| Fallbacks exacts v0.28 | **13 / 15** |
| Suites de mécanismes hostiles | **4.407362% plus petit**, 9 améliorés / 0 régressés sur 18 workloads |
| Scheduler hostile fixe | **182.454 s → 97.944 s médiane (-46.318%)**, archive sélectionnée identique octet pour octet |

Sur l’agrégat déterministe hostile à la ressemblance de 724 fichiers / 93,526,384 octets, la tentative acceptée #5 stocke **47,147,764 B**. Sur le même arbre : ZPAQ méthode 5 47,062,639 B, tar+Zstd-19 solide 47,065,652 B, 7z/LZMA2 47,430,343 B, Borg 76,461,311 B et ZIP/Deflate-9 76,690,799 B.

Ces lignes sont des **comparaisons appariées d’octets stockés, pas des affirmations de parité sémantique**. Archives solides, dépôts de sauvegarde et CMPCT exposent des compromis différents d’accès sélectif, mise à jour, intégrité et récupération. Le dossier durable est [`docs/releases/v0.29.0.md`](../releases/v0.29.0.md), les preuves machine dans [`benchmarks/history/`](../../benchmarks/history/).

### Livré vs frontière

| Autorité | État actuel | Sens |
|---|---|---|
| **Reader/writer canonique** | **format r24** | Ce que `python -m cmpct create` écrit et que les lecteurs canoniques doivent comprendre. |
| **Frontière de recherche** | **CMPNX11 / v0.29.0** | Moteur expérimental Mosaic + Residual Program Packing ; pas une syntaxe canonique r24. |
| **Surface publique** | **0.29.k** | Présentation dépôt/site/docs uniquement ; aucune autorité sur la sémantique d’archive. |
| **Licence** | **Apache-2.0 proposée** | Proposition seulement, pas encore concession publique finale. |

## Ce que CMPCT sait faire aujourd’hui

Le prototype canonique r24 inclut : déduplication adressée par contenu ; stockage adaptatif Zstandard/raw ; dictionnaires Zstd et micro-solid packs ; chunking défini par contenu ; lectures rapides par plage et decode parallèle ; préservation hardlinks/symlinks/sparse ; UID/GID/xattrs ; virtualisation ZIP/WHL imbriquée ; transformation PCM-WAV sans perte lorsqu’elle gagne ; réutilisation Deflate brute pour export ZIP ; CRC32 + SHA-256 ; index head/tail redondants et blobs auto-descriptifs ; journal transactionnel append ; export ZIP à la demande ; création reproductible optionnelle et encodage parallèle déterministe.

La ligne v0.29 explore en plus unités de ressemblance FastCDC bornées, recherche multi-bandes, deltas COPY/LITERAL profondeur 1, placement Mosaic multi-root borné, Residual Program Packing, fallback exact v0.28 lorsque la nouvelle représentation ne gagne pas, plafonds de localité/ressources, précompression DEFLATE exacte via bridge memory-safe épinglé, enregistrements Merkle authentifiés, récupération de fin authentifiée, sources range distantes strictes et scheduling parallèle byte-identique.

Ces mécanismes restent hors du reader canonique jusqu’à validation indépendante de l’intégration format, conformité, hardening, parité native, récupération et portabilité.

Règle centrale : **sélection guidée par le contenu, pas folklore guidé par l’extension**. Si une représentation spécialisée est plus lente ou plus grosse pour les octets réels, CMPCT ne doit pas l’utiliser.

## Démarrage rapide

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

La création CLI canonique dans un nouveau processus est volontairement sérielle sauf `--workers N`. Le gate v0.28 a montré que le démarrage du thread pool pouvait coûter ~10 ms sur un petit arbre média alors que le travail bibliothèque changeait à peine. L’API `Builder` en processus conserve la création parallèle déterministe par défaut, où les appels peuvent amortir ce coût.

Chunker natif optionnel Linux :

```bash
cc -O3 -shared -fPIC native/cmpct_cdc.c -o src/cmpct/libcmpct_cdc.so
```

Le reader **n’en dépend pas**. Il accélère la sélection des frontières à la création ; les frontières de chunks sont enregistrées explicitement sur disque.

## Position de performance

Les candidats numériques du cœur sont benchmarkés contre leur base directe. La règle est asymétrique car taille et temps n’ont pas la même physique de mesure :

- **taille d’archive** : mêmes données + mêmes sémantiques d’encodeur ne doivent jamais produire plus gros ; **0 octet** de tolérance ;
- **vitesse création/extraction** : base et candidat sur le même runner avec médianes répétées ; ralentissement confirmé hors marge documentée = version bloquée ;
- **preuves** : chaque release numérique doit committer un nouvel enregistrement public ;
- **corpora** : les workloads perdants/adversariaux restent visibles.

Voir [`docs/PERFORMANCE_RELEASE_GATE.md`](../PERFORMANCE_RELEASE_GATE.md) et [`docs/BREAKTHROUGH_REHABILITATION.md`](../BREAKTHROUGH_REHABILITATION.md).

## Ordre de lecture pour un nouvel agent

1. `docs/AGI_ENGINEERING_STANDARD.md` ; 2. `README.md` ; 3. `AGENTS.md` ; 4. `docs/CURRENT_STATE.md` ; 5. dernière note `docs/releases/` ; 6. `docs/PERFORMANCE_RELEASE_GATE.md` ; 7. `docs/BREAKTHROUGH_REHABILITATION.md` ; 8. `docs/FORMAT.md` ; 9. `docs/HISTORY.md` ; 10. `docs/ENTROPYGRAPH.md`, `docs/ENTROPYGRAPH_II_CAMPAIGN.md`, `docs/MOSAIC_V029_CAMPAIGN.md` ; 11. `docs/HARDENING.md` ; 12. `docs/PORTABILITY.md`, `docs/NATIVE_CORE.md` ; 13. `docs/RESEARCH_LOG.md` ; 14. `docs/BENCHMARKS.md`, `benchmarks/history/` ; 15. `docs/PUBLIC_SURFACE.md` ; 16. `docs/ROADMAP.md`.

Un agent neuf ne devrait avoir besoin ni de chats privés, ni de corpus privés, ni de contexte d’un projet sans rapport.

## Carte du dépôt

`src/cmpct/` porte l’implémentation canonique r24 ; `src/cmpct/resemblance.py` les primitives similitude/delta ; `experiments/entropygraph_v025.py`, `entropygraph_v028.py` et `entropygraph_v029_release.py` la lignée expérimentale ; `benchmarks/` les corpus/gates déterministes et `benchmarks/history/` leurs enregistrements durables ; `fuzz/` attaque les parsers/ressources ; `tools/check_*` impose les contrats ; `site/` contient le site et Browser Lab ; `native/` les accélérateurs et le cœur partagé ; `docs/` les contrats, campagnes, historique, benchmarks et roadmap ; `tests/` les régressions format/round-trip/ressemblance/localité/reproductibilité.

## Site web

Le site est conçu pour **frapper d’abord, prouver ensuite, gagner la confiance enfin**. Titres de performance, ladder de concurrents, matrice de workloads, défaites et état du cœur viennent de l’historique versionné, pas de pourcentages marketing écrits à la main. Il sépare strictement **frontière de recherche**, **parité canonique** et **révision de surface**. Il peut être visuellement agressif ; il ne peut ni brouiller ces frontières ni inventer une victoire.

**Ouvrir :** https://fcmo-ai.github.io/.CMPCT/?lang=fr

## Discipline de version

1. **Version numérique du cœur (`MAJOR.MINOR.PATCH`)** — uniquement pour un gain matériel du produit ; après v0.27.1, l’avancement normal déplace `MAJOR.MINOR` avec `PATCH=0` pour compatibilité packaging.
2. **Révision de surface (`MAJOR.MINOR.LETTER`)** — site, docs, présentation, ergonomie ; actuelle **`0.29.k`**. Elle ne modifie pas seule `pyproject.toml` et n’exige pas de benchmark synthétique.
3. **Révision on-disk** — seulement si les readers nécessitent une nouvelle grammaire/sémantique ; le canonique reste **r24**.

CI rejette les bumps numériques sans travail moteur/archive, exige release note + benchmark pour les releases numériques, valide la ligne alphabétique et sépare le tout du gate de régression.

## Histoire, provenance et surface publique

CMPCT vient d’expériences Seekable-Zstd, indexed-Zstd, adaptive-framing et famille ZIP avant le format natif content-aware. L’histoire technique reste publique, mais identités de corpus privés, artefacts privés et provenance de projets sans rapport n’en font pas partie. Les benchmarks publics doivent être reproductibles ou issus d’entrées volontairement publiques/synthétiques ; les données historiques **ne constituent pas une garantie universelle**.

CMPCT doit tenir seul. Dépôt et site ne doivent pas exiger ni exposer projets internes sans rapport, données client privées, corpus privés, informations personnelles, transcriptions de chat, identifiants, artefacts privés ou liens internes. Voir `docs/PUBLIC_SURFACE.md`.

## Canonicité

Ce dépôt remplace les prototypes et scripts CMPCT locaux aux chats. Les changements format, benchmarks, expériences, site et décisions de conception doivent atterrir ici, mais n’utilisent pas le même marqueur : progrès matériel du moteur = release numérique ; site/docs/présentation = `SURFACE_REVISION` ; recherche = explicitement expérimentale jusqu’à promotion. Un code expérimental ne peut revendiquer le support canonique avant intégration au reader/writer de référence et à la conformité.

## Licence

Apache License 2.0 est la **licence actuellement proposée**, pas encore la licence adoptée. Le texte proposé intact est dans `LICENSE-APACHE-2.0-PROPOSED.txt` et la checklist dans `LICENSING.md`. Tant que le processus n’est pas terminé, CMPCT ne doit pas être présenté comme définitivement publié sous Apache-2.0.

Note : le hero du dépôt est volontairement evergreen et ne contient ni pourcentages de benchmark ni numéros de release ; les valeurs porteuses de preuve restent du texte dérivé du dossier de release actuel, et l’historique n’est pas réécrit pour suivre les politiques futures.
