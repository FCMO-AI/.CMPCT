<div align="center">
  <a href="https://fcmo-ai.github.io/.CMPCT/?lang=pt-BR"><img src="../../.github/assets/repository-hero.svg" width="100%" alt="CMPCT — Formatos de arquivo fizeram as pazes com concessões. CMPCT não."></a>

  **Um projeto de arquivo/contêiner lossless de uso geral, projetado para avançar em conjunto bytes armazenados, acesso seletivo, integridade, recuperação e portabilidade.**

  **[Site](https://fcmo-ai.github.io/.CMPCT/?lang=pt-BR)** · **[Laboratório no navegador](https://fcmo-ai.github.io/.CMPCT/?lang=pt-BR#lab)** · **[Benchmarks](../BENCHMARKS.md)** · **[Formato](../FORMAT.md)** · **[Roadmap](../ROADMAP.md)** · **[Entrada para agentes](../CURRENT_STATE.md)**

  <sub>núcleo v0.29.0 · formato canônico r24 · superfície 0.29.k · pré-1.0</sub>
</div>

> **Tradução curada.** Esta é uma adaptação semântica versionada do README voltado a pessoas. O [`README.md`](../../README.md) em inglês continua sendo a autoridade canônica. Números, caminhos, nomes de formatos e limites de evidência são preservados deliberadamente. Esta tradução não é rotulada como revisada por humano bilíngue sem que essa revisão tenha ocorrido.

---

> **Desempenho é o contrato da versão.** Pesquisa pode revelar uma troca desconfortável. Uma versão promovida não pode escondê-la: regressão determinística no tamanho do arquivo tem **tolerância de 0 bytes**, regressão de velocidade confirmada fora da margem de ruído documentada do mesmo runner bloqueia a promoção, e workloads perdedores continuam como evidência pública.

## Por que CMPCT existe

| | CMPCT tenta melhorar isto |
|---|---|
| **Bytes armazenados** | Usar identidade exata, representações conscientes do conteúdo e reutilização limitada de relações, em vez de tratar cada arquivo como um fluxo de bytes sem relação. |
| **Acesso seletivo** | Ler o objeto ou intervalo solicitado sem transformar o arquivo inteiro em uma descompressão obrigatória. |
| **Integridade + recuperação** | Manter verificações, metadados redundantes e caminhos de salvamento como comportamento real do leitor, não como promessa escrita de disaster recovery. |
| **Fidelidade do sistema de arquivos** | Preservar links, arquivos esparsos, metadados e semântica de atualização esperados de um contêiner moderno de uso geral. |
| **Interoperabilidade** | Separar o contrato canônico reader/writer, exportação ZIP, núcleo nativo e gates de portabilidade da gramática experimental. |
| **Qualidade da evidência** | Derivar alegações públicas de registros reproduzíveis versionados, preservar derrotas e rejeitar teatro de benchmark. |

CMPCT não é “Zstd com uma extensão nova” e não se satisfaz em vencer uma pasta escolhida a dedo. A meta é um arquivo padrão mais forte em **tamanho, velocidade, acesso aleatório, fidelidade, integridade, recuperação, atualizações e semântica moderna de armazenamento**, sem exportar silenciosamente o custo para outro lugar.

## Fronteira verificada mais recente

**Projeto v0.29.0 — Mosaic / Residual Program Packing** avança o motor de pesquisa verificado enquanto o formato canônico distribuído permanece na **revisão 24**.

| Evidência de pesquisa v0.29 | Resultado |
|---|---:|
| Portfólio portátil herdado da fronteira | **137,501,815 B** |
| Base direta v0.28 | 137,550,416 B |
| Economia exata | **48,601 B (0.035333%)** |
| Workloads portáteis | **15** |
| Melhorados / regredidos | **2 / 0** |
| Fallbacks exatos para v0.28 | **13 / 15** |
| Suites de mecanismos hostis | **4.407362% menor**, 9 melhorados / 0 regredidos em 18 workloads |
| Scheduler hostil fixo | **182.454 s → 97.944 s mediana (-46.318%)**, arquivo selecionado idêntico em bytes |

No agregado determinístico hostil à semelhança com 724 arquivos / 93,526,384 bytes, a tentativa aceita #5 armazena **47,147,764 B**. Na mesma árvore, ZPAQ método 5 armazena 47,062,639 B, tar+Zstd-19 sólido 47,065,652 B, 7z/LZMA2 47,430,343 B, Borg 76,461,311 B e ZIP/Deflate-9 76,690,799 B.

Essas linhas são **comparações pareadas de bytes armazenados, não alegações de paridade semântica**. Arquivos sólidos, repositórios de backup e CMPCT expõem trocas diferentes de leitura seletiva, atualização, integridade e recuperação. O registro durável é [`docs/releases/v0.29.0.md`](../releases/v0.29.0.md); a evidência legível por máquina está em [`benchmarks/history/`](../../benchmarks/history/).

### Produção vs fronteira

| Autoridade | Estado atual | Significado |
|---|---|---|
| **Reader/writer canônico** | **formato r24** | O que `python -m cmpct create` escreve e leitores canônicos precisam entender. |
| **Fronteira de pesquisa** | **CMPNX11 / v0.29.0** | Motor experimental Mosaic + Residual Program Packing; não é sintaxe canônica r24. |
| **Superfície pública** | **0.29.k** | Apresentação de repositório/site/docs; não muda semântica do arquivo nem consome versão do núcleo. |
| **Licença** | **Apache-2.0 proposta** | Apenas proposta; ainda não é a concessão pública final. |

## O que CMPCT pode fazer hoje

O protótipo canônico revisão 24 inclui:

- deduplicação endereçada por conteúdo;
- armazenamento adaptativo Zstandard e raw;
- dicionários Zstd e pacotes micro-solid para florestas de arquivos minúsculos;
- chunking definido por conteúdo para arquivos grandes em evolução;
- leitura rápida por intervalo de bytes e decode paralelo de chunks;
- preservação de hardlinks, symlinks e arquivos esparsos;
- captura de UID/GID e atributos estendidos onde disponível;
- virtualização ZIP/WHL aninhada quando regeneração exata compensa;
- transformação PCM-WAV lossless quando realmente vence;
- reutilização de Deflate raw para exportação rápida a ZIP legado;
- CRC32 no hot path mais verificação forte SHA-256;
- índices redundantes head/tail e registros de blobs autodescritivos para salvamento;
- journal append transacional para update/delete/rename;
- exportação sob demanda para ZIP Deflate comum;
- criação reproduzível opcional e codificação paralela determinística de candidatos.

A linha v0.29 também explora e mede unidades de semelhança limitadas estilo FastCDC, busca multibanda, deltas COPY/LITERAL depth-1, posicionamento Mosaic multi-root limitado, Residual Program Packing, fallback exato para v0.28 quando não há ganho, tetos de localidade/recursos, precompressão DEFLATE exata via bridge memory-safe fixada, registros Merkle autenticados, recuperação autenticada de cauda, range sources remotos estritos e scheduling paralelo byte-idêntico do portfólio aceito.

Esses mecanismos de pesquisa ficam fora do reader canônico até passarem independentemente integração de formato, conformidade, hardening, paridade nativa, recuperação e portabilidade.

A regra central é **seleção guiada pelo conteúdo, não folclore guiado por extensão**. Se uma representação especializada é maior ou mais lenta nos bytes reais, CMPCT não deve usá-la.

## Início rápido

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

Criação CLI canônica em processo novo é serial por intenção salvo `--workers N`. O gate v0.28 mostrou que inicializar o thread pool podia custar ~10 ms em uma pequena árvore de mídia enquanto o trabalho de biblioteca quase não mudava. A API `Builder` em processo mantém criação paralela determinística por padrão, onde callers amortizam o setup e workloads grandes mostraram ganhos materiais.

Chunker nativo opcional no Linux:

```bash
cc -O3 -shared -fPIC native/cmpct_cdc.c -o src/cmpct/libcmpct_cdc.so
```

O reader **não** depende dele. Ele acelera a seleção de fronteiras durante a criação; as fronteiras de chunk ficam registradas no disco.

## A posição de desempenho

Candidatos a release numérica do núcleo são medidos contra sua base direta. A regra é assimétrica porque tamanho e tempo têm física de medição diferente:

- **tamanho:** entrada + semântica do encoder idênticas nunca podem ficar maiores; tolerância **0 bytes**;
- **velocidade de criar/extrair:** base e candidato rodam no mesmo runner com medianas repetidas; desaceleração confirmada fora da margem relativa+absoluta bloqueia a release;
- **evidência:** toda release numérica precisa versionar um novo registro público, não deixar o resultado apenas no CI;
- **corpora:** workloads perdedores/adversariais permanecem visíveis. Apagar o caso que contradiz o headline não melhora benchmark.

Veja [`docs/PERFORMANCE_RELEASE_GATE.md`](../PERFORMANCE_RELEASE_GATE.md) e [`docs/BREAKTHROUGH_REHABILITATION.md`](../BREAKTHROUGH_REHABILITATION.md).

## Ordem de leitura para novo agente

1. `docs/AGI_ENGINEERING_STANDARD.md` — qualidade, falseabilidade e hierarquia de evidência;
2. `README.md` — missão e forma do projeto;
3. `AGENTS.md` — regras obrigatórias;
4. `docs/CURRENT_STATE.md` — handoff sem histórico;
5. nota aplicável mais nova em `docs/releases/`;
6. `docs/PERFORMANCE_RELEASE_GATE.md`;
7. `docs/BREAKTHROUGH_REHABILITATION.md`;
8. `docs/FORMAT.md` — contrato r24;
9. `docs/HISTORY.md`;
10. `docs/ENTROPYGRAPH.md`, `docs/ENTROPYGRAPH_II_CAMPAIGN.md`, `docs/MOSAIC_V029_CAMPAIGN.md`;
11. `docs/HARDENING.md`;
12. `docs/PORTABILITY.md` e `docs/NATIVE_CORE.md`;
13. `docs/RESEARCH_LOG.md`;
14. `docs/BENCHMARKS.md` e `benchmarks/history/`;
15. `docs/PUBLIC_SURFACE.md`;
16. `docs/ROADMAP.md`.

Um agente novo não deve precisar de chat privado, corpora privados ou contexto de projeto não relacionado.

## Mapa do repositório

`src/cmpct/` contém a implementação canônica r24; `src/cmpct/resemblance.py` as primitivas de similaridade/delta; `experiments/entropygraph_v025.py`, `entropygraph_v028.py` e `entropygraph_v029_release.py` preservam a linhagem de pesquisa; `benchmarks/` contém corpora e gates determinísticos, com registros duráveis em `benchmarks/history/`; `fuzz/` ataca recursos e parsers; `tools/check_*` aplica disciplina de performance/versão/evidência; `site/` contém o site e Browser Lab; `native/` contém aceleradores e o núcleo compartilhado; `docs/` contém contratos, campanhas, histórico, benchmarks, superfície pública e roadmap; `tests/` contém regressões de formato, round-trip, semelhança, localidade estrita e reproducibilidade.

## Site

O site ao vivo foi desenhado para **causar impacto primeiro, provar a afirmação depois e conquistar confiança por último**. Números principais, ladder de concorrentes, matriz de workloads, derrotas e estado do núcleo vêm do histórico de benchmark versionado, não de porcentagens de marketing mantidas à mão.

Para v0.29, o adaptador público expõe a fronteira aceita Mosaic / Residual Program Packing e mantém ZIP/Deflate, 7z/LZMA2, tar/Zstd sólido, ZPAQ e Borg sob seus nomes reais. Ele separa deliberadamente **fronteira de pesquisa**, **paridade canônica** e **revisão de superfície**. O site pode ser agressivo visual e retoricamente; não pode borrar essas fronteiras nem inventar vitória.

**Abrir:** https://fcmo-ai.github.io/.CMPCT/?lang=pt-BR

## Disciplina de versão

Há três eixos:

1. **Versão numérica do núcleo (`MAJOR.MINOR.PATCH`)** — somente para ganho material do produto; após v0.27.1, avanço normal move `MAJOR.MINOR` e mantém `PATCH=0` para compatibilidade de empacotamento.
2. **Revisão de superfície (`MAJOR.MINOR.LETTER`)** — site, docs, apresentação e ergonomia; atual **`0.29.k`**. Não altera sozinho `pyproject.toml` nem exige benchmark sintético.
3. **Revisão on-disk** — muda apenas quando leitores precisam de nova gramática/semântica. O formato canônico segue **r24**.

CI rejeita bumps numéricos sem mudanças no motor/arquivo, exige nota + benchmark correspondente para releases numéricas, valida a linha alfabética da superfície e mantém tudo separado do gate de regressão.

## História, proveniência e superfície pública

CMPCT evoluiu de experimentos Seekable-Zstd, indexed-Zstd, adaptive-framing e família ZIP até o formato nativo content-aware. O histórico técnico é preservado, mas identidades de corpora privados, artefatos privados e procedência de projetos não relacionados não entram no registro público.

Histórico público de benchmark deve ser reproduzível independentemente ou usar entradas públicas/sintéticas deliberadas. Dados históricos **não** são garantia universal: ambiente, limites de processo, diferenças semânticas e workloads perdedores ficam registrados.

CMPCT deve se sustentar sozinho. Repositório e site não podem exigir ou expor projetos internos não relacionados, dados privados de clientes, corpora privados, informação pessoal, transcrições de chat, credenciais, nomes privados de artefato ou links de sistemas privados. Veja `docs/PUBLIC_SURFACE.md`.

## Canonicidade

Este repositório substitui protótipos e scripts CMPCT locais a chats. Mudanças de formato, benchmarks, experimentos, site e decisões de design devem chegar aqui, mas usam marcadores diferentes: progresso material do motor ganha release numérica; site/docs/apresentação usam `SURFACE_REVISION`; pesquisa pode continuar explicitamente experimental até promoção. Código experimental não pode alegar suporte canônico sem integração ao reader/writer de referência e à superfície de conformidade.

## Licença

Apache License 2.0 é a **licença atualmente proposta**, não a licença final adotada. O texto proposto sem modificações está em `LICENSE-APACHE-2.0-PROPOSED.txt` e o checklist de adoção em `LICENSING.md`. Até esse processo terminar, CMPCT não deve ser apresentado como finalmente publicado sob Apache-2.0.

Nota: o hero do repositório é propositalmente evergreen e não contém porcentagens nem números de release. Valores com autoridade de evidência permanecem em texto derivado do registro atual, e histórico não é reescrito para combinar com políticas novas.
