<div align="center">
  <a href="https://fcmo-ai.github.io/.CMPCT/?lang=es-419">
    <img src="../../.github/assets/repository-hero.svg" width="100%" alt="CMPCT — Los formatos de archivo hicieron las paces con el compromiso. CMPCT no.">
  </a>

  <br>

  **Un proyecto de archivo/contenedor sin pérdida de propósito general, diseñado para hacer avanzar juntos los bytes almacenados, el acceso selectivo, la integridad, la recuperación y la portabilidad.**

  <br>

  **[Sitio web](https://fcmo-ai.github.io/.CMPCT/?lang=es-419)** · **[Laboratorio en el navegador](https://fcmo-ai.github.io/.CMPCT/?lang=es-419#lab)** · **[Benchmarks](../BENCHMARKS.md)** · **[Formato](../FORMAT.md)** · **[Roadmap](../ROADMAP.md)** · **[Entrada para agentes](../CURRENT_STATE.md)**

  <sub>núcleo v0.29.0 · formato canónico r24 · superficie 0.29.k · pre-1.0</sub>
</div>

> **Traducción curada.** Esta es una adaptación semántica versionada del README humano. [`README.md`](../../README.md) en inglés sigue siendo la autoridad canónica. Los números, rutas, nombres de formatos y límites de evidencia se preservan deliberadamente. Esta traducción no se etiqueta como revisada por un humano bilingüe mientras esa revisión no haya ocurrido.

---

> **El rendimiento es el contrato de cada versión.** La investigación puede descubrir un compromiso incómodo. Una versión promovida no puede ocultarlo: la regresión determinista del tamaño de archivo tiene **tolerancia de 0 bytes**, una regresión de velocidad confirmada fuera del margen de ruido documentado del mismo runner bloquea la promoción y los workloads perdedores permanecen como evidencia pública.

## Por qué existe CMPCT

| | CMPCT intenta mejorar esto |
|---|---|
| **Bytes almacenados** | Usar identidad exacta, representaciones conscientes del contenido y reutilización acotada de relaciones en vez de tratar cada archivo como un flujo de bytes sin relación. |
| **Acceso selectivo** | Leer el objeto o rango solicitado sin convertir todo el archivo en un evento obligatorio de descompresión. |
| **Integridad + recuperación** | Mantener verificaciones, metadatos redundantes y rutas de salvamento como comportamiento ejecutable del lector, no como prosa de recuperación ante desastres. |
| **Fidelidad del sistema de archivos** | Preservar enlaces, archivos dispersos, metadatos y semántica de actualización esperados de un contenedor moderno de propósito general. |
| **Interoperabilidad** | Mantener el contrato canónico lector/escritor, la exportación ZIP, el trabajo del núcleo nativo y las puertas de portabilidad separados de la gramática experimental. |
| **Calidad de evidencia** | Derivar las afirmaciones públicas de registros reproducibles versionados, conservar las derrotas y rechazar el teatro de benchmarks. |

CMPCT no es «Zstd con otra extensión» ni se conforma con ganar en una carpeta elegida a mano. El objetivo es un archivo predeterminado más fuerte en **tamaño, velocidad, acceso aleatorio, fidelidad, integridad, recuperación, actualizaciones y semántica moderna de almacenamiento**, sin trasladar silenciosamente el costo a otro lugar.

## Última frontera verificada

**Proyecto v0.29.0 — Mosaic / Residual Program Packing** hace avanzar el motor experimental verificado mientras el formato canónico que se distribuye permanece en **revisión 24**.

| Evidencia de investigación v0.29 | Resultado |
|---|---:|
| Portafolio portátil heredado de la frontera | **137,501,815 B** |
| Base directa v0.28 | 137,550,416 B |
| Ahorro exacto | **48,601 B (0.035333%)** |
| Workloads portátiles | **15** |
| Mejorados / regresados | **2 / 0** |
| Fallbacks exactos a v0.28 | **13 / 15** |
| Suites de mecanismos hostiles | **4.407362% más pequeño**, 9 mejorados / 0 regresados en 18 workloads |
| Scheduler hostil fijo | **182.454 s → 97.944 s mediana (-46.318%)**, archivo seleccionado idéntico a nivel de bytes |

En el agregado determinista hostil a la semejanza de 724 archivos / 93,526,384 bytes, el intento aceptado #5 almacena **47,147,764 B**. En ese mismo árbol, ZPAQ método 5 almacena 47,062,639 B, tar+Zstd-19 sólido 47,065,652 B, 7z/LZMA2 47,430,343 B, Borg 76,461,311 B y ZIP/Deflate-9 76,690,799 B.

Estas filas son **comparaciones emparejadas de bytes almacenados, no afirmaciones de paridad semántica**. Los archivos sólidos, repositorios de respaldo y CMPCT exponen compromisos distintos de lectura selectiva, actualización, integridad y recuperación. El registro durable de la versión está en [`docs/releases/v0.29.0.md`](../releases/v0.29.0.md); la evidencia legible por máquina vive en [`benchmarks/history/`](../../benchmarks/history/).

### Producción vs frontera

| Autoridad | Estado actual | Significado |
|---|---|---|
| **Lector/escritor canónico** | **formato r24** | Lo que escribe `python -m cmpct create` y lo que deben entender los lectores canónicos. |
| **Frontera de investigación** | **CMPNX11 / v0.29.0** | Motor experimental Mosaic + Residual Program Packing; no es sintaxis canónica r24. |
| **Superficie pública** | **0.29.k** | Presentación del repositorio/sitio/docs; no altera la semántica del archivo ni consume una versión del núcleo. |
| **Licencia** | **Apache-2.0 propuesta** | Solo propuesta. Todavía no es una concesión pública finalizada. |

## Qué puede hacer CMPCT hoy

Las capacidades actuales del prototipo canónico revisión 24 incluyen:

- deduplicación dirigida por contenido;
- almacenamiento adaptativo Zstandard y raw;
- diccionarios Zstd y paquetes micro-solid para bosques de archivos diminutos;
- chunking definido por contenido para archivos grandes que evolucionan;
- lecturas rápidas por rango de bytes y decodificación paralela de chunks;
- preservación de hardlinks, symlinks y archivos dispersos;
- captura de UID/GID y atributos extendidos cuando están disponibles;
- virtualización de ZIP/WHL anidados cuando la regeneración exacta resulta rentable;
- transformación PCM-WAV sin pérdida cuando realmente gana;
- reutilización de Deflate raw para exportación rápida a ZIP heredado;
- verificaciones CRC32 en ruta caliente más verificación fuerte SHA-256;
- índices redundantes al inicio/final y registros de blobs autodescriptivos para salvamento;
- journal transaccional append-only para actualizar/eliminar/renombrar;
- exportación bajo demanda a ZIP Deflate ordinario para compatibilidad heredada;
- creación reproducible opcional y codificación paralela determinista de candidatos.

La línea de investigación v0.29 además explora y mide:

- unidades de semejanza acotadas tipo FastCDC y búsqueda de similitud multibanda;
- deltas COPY/LITERAL de profundidad 1 medidos;
- colocación Mosaic multiraíz acotada;
- Residual Program Packing para grupos de recetas delta relacionadas;
- fallback exacto al portafolio v0.28 cuando la nueva representación no gana;
- límites de localidad/recursos para planes físicos seleccionados;
- precompresión DEFLATE exacta opcional mediante un puente fijado y memory-safe;
- registros físicos autenticados con Merkle y recuperación de cola autenticada;
- fuentes remotas estrictas por rango que no pueden descargar silenciosamente archivos completos;
- scheduling paralelo byte-idéntico del portafolio para el motor de investigación v0.29 aceptado.

Estos mecanismos experimentales permanecen fuera del lector canónico hasta superar de forma independiente integración de formato, conformidad, hardening, paridad nativa, recuperación y portabilidad.

La regla importante es **selección guiada por contenido, no folclore guiado por extensiones**. Si una representación especializada es más lenta o más grande para los bytes reales, CMPCT no debería usarla.

## Inicio rápido

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

La creación canónica CLI en un proceso nuevo es serial deliberadamente salvo que se indique `--workers N`. La puerta de versión v0.28 encontró que arrancar el thread pool podía costar ~10 ms en un árbol multimedia pequeño mientras el trabajo de biblioteca apenas cambiaba. La API `Builder` en proceso conserva creación paralela determinista por defecto, donde los callers pueden amortizar ese costo y los workloads grandes mostraron ganancias materiales.

Para el chunker nativo opcional definido por contenido en Linux:

```bash
cc -O3 -shared -fPIC native/cmpct_cdc.c -o src/cmpct/libcmpct_cdc.so
```

El lector **no** depende de ese helper. Acelera la selección de fronteras durante la creación; las fronteras de chunk se registran explícitamente en disco.

## La posición de rendimiento

Los candidatos a versión numérica del núcleo se comparan contra su base directa antes de publicarse. La regla es asimétrica porque tamaño y tiempo tienen física de medición distinta:

- **tamaño del archivo:** entrada y semántica del encoder idénticas nunca pueden producir un archivo mayor; tolerancia **0 bytes**;
- **velocidad de crear/extraer:** base y candidato corren en el mismo runner con medianas repetidas; una ralentización confirmada fuera del margen relativo+absoluto documentado bloquea la versión;
- **evidencia de benchmark:** cada versión numérica debe registrar un benchmark público nuevo, no dejarlo únicamente en CI;
- **corpora:** workloads perdedores/adversariales permanecen visibles. Eliminar el caso que contradice el titular no mejora un benchmark.

Consulta [`docs/PERFORMANCE_RELEASE_GATE.md`](../PERFORMANCE_RELEASE_GATE.md) para la política normativa y [`docs/BREAKTHROUGH_REHABILITATION.md`](../BREAKTHROUGH_REHABILITATION.md) para el protocolo que preserva investigación de alto potencial mientras paga deuda de regresión antes de promoverla.

## Orden de lectura para un agente nuevo

Un agente de código/investigación sin contexto previo de CMPCT debería leer, en orden:

1. `docs/AGI_ENGINEERING_STANDARD.md` — ratchet de calidad, falsabilidad y jerarquía de evidencia;
2. `README.md` — misión y forma del proyecto;
3. `AGENTS.md` — reglas obligatorias de desarrollo, benchmark y versionado;
4. `docs/CURRENT_STATE.md` — handoff sin historial de chat y frontera inmediata;
5. la nota aplicable más reciente en `docs/releases/` — último hito numérico;
6. `docs/PERFORMANCE_RELEASE_GATE.md` — contrato anti-regresión;
7. `docs/BREAKTHROUGH_REHABILITATION.md` — preservación de breakthroughs y deuda de regresión;
8. `docs/FORMAT.md` — contrato actual r24 en disco;
9. `docs/HISTORY.md` — historia sobreviviente con procedencia privada generalizada;
10. `docs/ENTROPYGRAPH.md`, `docs/ENTROPYGRAPH_II_CAMPAIGN.md` y `docs/MOSAIC_V029_CAMPAIGN.md` — linaje de investigación y frontera actual;
11. `docs/HARDENING.md` — estado frente a parsers/recursos hostiles;
12. `docs/PORTABILITY.md` y `docs/NATIVE_CORE.md` — integración de producto y núcleo compartido;
13. `docs/RESEARCH_LOG.md` — ideas fallidas y conclusiones experimentales;
14. `docs/BENCHMARKS.md` y `benchmarks/history/` — semántica y registros públicos;
15. `docs/PUBLIC_SURFACE.md` — límite de divulgación pública;
16. `docs/ROADMAP.md` — trabajo restante antes de 1.0.

Un agente nuevo no debería necesitar chats privados, corpora privados ni contexto de proyectos no relacionados para continuar de forma segura.

## Mapa del repositorio

- `src/cmpct/` — implementación de referencia canónica r24.
- `src/cmpct/resemblance.py` — primitivas reutilizables y acotadas de similitud/delta.
- `experiments/entropygraph_v025.py` — motor histórico CMPNX5 y linaje de fallback heredado.
- `experiments/entropygraph_v028.py` — motor de investigación EntropyGraph II CMPNX8.
- `experiments/entropygraph_v029_release.py` — entrada estable v0.29 y superficie de scheduler byte-idéntica.
- `benchmarks/universal_bench.py` — generador determinista del corpus canónico heterogéneo.
- `benchmarks/zip_parity_bench.py` — harness justo CMPCT/ZIP de paridad y release gate.
- `benchmarks/neutral_hostile_corpus_v1.py` — suite determinista neutral/hostil.
- `benchmarks/resemblance_hostile_corpus_v1.py` — suite de ataque de versiones desplazadas/falsos vecinos/boundary churn.
- `benchmarks/mosaic_v029_generalization_bench.py` — puerta de generalización portátil v0.29.
- `benchmarks/mosaic_v029_structural_competitors.py` — comparación estructural cross-format emparejada.
- `benchmarks/history/` — registros públicos durables legibles por máquina.
- `fuzz/` — ataques a recursos/parsers canónicos, de grafo y delta.
- `tools/check_performance_regression.py` — verificador de regresión contra base directa.
- `tools/check_version_discipline.py` — disciplina núcleo-vs-superficie.
- `tools/check_pr_evidence.py` — gate de dossier de evidencia para PRs materiales.
- `SURFACE_REVISION` — revisión alfabética de presentación/proceso (`x.x.a`, `x.x.b`, …).
- `docs/PERFORMANCE_RELEASE_GATE.md` — política normativa de rendimiento.
- `docs/releases/` — una nota por versión numérica.
- `site/` — sitio centrado en rendimiento, adaptadores de evidencia y Browser Lab local.
- `native/cmpct_cdc.c` — acelerador nativo opcional para chunking definido por contenido.
- `native/preflate-bridge/` — puente experimental DEFLATE exacto fijado.
- `native/cmpct-core/` — núcleo de lectura compartido memory-safe y ABI C.
- `docs/CURRENT_STATE.md` — handoff/frontera para desarrollador o agente sin contexto.
- `docs/FORMAT.md` — contrato e invariantes en disco.
- `docs/HISTORY.md` — linaje de formato/diseño.
- `docs/ENTROPYGRAPH.md` — investigación generalizada de representaciones de grafo.
- `docs/ENTROPYGRAPH_II_CAMPAIGN.md` — mapa falsable de v0.28.
- `docs/MOSAIC_V029_CAMPAIGN.md` — campaña Mosaic v0.29 y gates falsables.
- `docs/RESEARCH_LOG.md` — decisiones, ideas fallidas y conclusiones.
- `docs/PRINCIPLES.md` — reglas contra overfitting a corpus.
- `docs/BENCHMARKS.md` — disciplina e interpretación de benchmarks.
- `docs/PUBLIC_SURFACE.md` — límites de la superficie pública.
- `docs/ROADMAP.md` — bloqueos antes de un 1.0 defendible.
- `tests/` — regresiones de formato, round-trip, semejanza, localidad estricta y reproducibilidad.

## Sitio web

El sitio en vivo está diseñado para **crear impacto primero, demostrar la afirmación después y ganarse la confianza al final**. Sus cifras principales, escalera de competidores, matriz de workloads, derrotas y estado del núcleo se generan a partir del historial de benchmarks versionado, no de porcentajes de marketing mantenidos a mano.

Para v0.29 el adaptador público expone la frontera Mosaic / Residual Program Packing aceptada y mantiene ZIP/Deflate, 7z/LZMA2, tar/Zstd sólido, ZPAQ y Borg bajo sus nombres reales. Un esquema de UI obsoleto no puede renombrar un competidor solo para mantener lleno un titular viejo.

El sitio separa deliberadamente:

- **frontera de investigación** — los resultados experimentales más fuertes verificados actualmente;
- **paridad canónica** — el reader/writer ejecutable r24 frente a ZIP en límites equivalentes de biblioteca y procesos CLI nuevos;
- **revisión de superficie** — el hito actual de presentación del sitio/docs/repositorio, sin autoridad sobre la semántica ni la verdad del benchmark.

El sitio puede ser visual y retóricamente agresivo. No puede difuminar esos límites ni inventar una victoria. `main` publica mediante Pages solo después de superar verificaciones de superficie pública, coherencia de datos, revisión de superficie, JavaScript y compatibilidad del Browser Lab.

**Abrir:** https://fcmo-ai.github.io/.CMPCT/?lang=es-419

## Disciplina de versiones

CMPCT no usa la versión numérica como contador de commits. Hay tres ejes distintos:

1. **Versión numérica del núcleo (`MAJOR.MINOR.PATCH`)** — reservada para una mejora material de CMPCT: capacidad del motor/archivo, compresión o velocidad, confiabilidad, recuperación, portabilidad/interoperabilidad u otra mejora de producto. Tras v0.27.1, el avance normal mueve `MAJOR.MINOR` y usa `PATCH=0` para compatibilidad de empaquetado.
2. **Revisión de superficie (`MAJOR.MINOR.LETTER`)** — animación/diseño del sitio, documentación, presentación del repositorio, ergonomía de workflows y trabajo no relacionado con el formato. Este hito es **`0.29.k`**. No cambia por sí solo `pyproject.toml` ni requiere un benchmark sintético.
3. **Revisión del formato en disco** — cambia solo cuando los lectores necesitan nueva gramática/semántica de almacenamiento. El formato ejecutable canónico sigue en **r24**.

Una versión del núcleo puede mejorar política del encoder, velocidad, confiabilidad o interoperabilidad sin cambiar la revisión en disco, pero debe ganarse el número con evidencia durable. Una investigación también puede avanzar la línea del proyecto manteniendo bytes experimentales explícitamente no canónicos. Un rediseño del sitio/repositorio puede ser valioso sin fingir que CMPCT se convirtió en una nueva versión del formato.

CI rechaza incrementos numéricos que no toquen rutas del motor/archivo, exige notas y evidencia de benchmark para versiones numéricas, valida la línea alfabética de superficie y mantiene esas preocupaciones separadas del gate de regresión de rendimiento.

## Historia de desarrollo y procedencia de benchmarks

El proyecto empezó como una secuencia de experimentos Seekable-Zstd, indexed-Zstd, adaptive-framing y familia ZIP antes de convertirse en el formato CMPCT nativo y consciente del contenido. Se conserva la historia técnica, pero las identidades de corpora privados, artefactos privados y procedencia de proyectos no relacionados no forman parte del registro público.

El historial público de benchmarks debe ser reproducible de forma independiente o generarse a partir de entradas públicas/sintéticas deliberadas. Los corpora privados pueden seguir siendo señales locales útiles, pero sus nombres, hashes, rutas, contenido y procedencia no son evidencia pública.

Los datos históricos **no** son automáticamente una garantía universal de rendimiento. El proyecto registra ambiente, límites de proceso y diferencias semánticas, y conserva workloads perdedores en vez de reescribir la historia alrededor del resultado más bonito.

## Regla de superficie pública

CMPCT debe sostenerse por sí mismo. El repositorio y sitio no deben requerir ni exponer proyectos internos no relacionados, datos privados de clientes, corpora privados, información personal, transcripciones de chat, credenciales, nombres privados de artefactos ni enlaces de sistemas privados. Consulta `docs/PUBLIC_SURFACE.md` para la regla exigible.

## Canonicidad

Este repositorio sustituye prototipos CMPCT y scripts de benchmark locales a chats. Los cambios de formato, benchmarks, experimentos, sitio y decisiones de diseño deben aterrizar aquí, pero no reciben el mismo marcador de versión. El progreso material del motor/archivo gana una versión numérica; sitio, documentación y presentación usan `SURFACE_REVISION`; la investigación puede seguir explícitamente experimental hasta ser promovida. Código experimental no puede afirmar soporte canónico hasta integrarse al reader/writer de referencia y su superficie de conformidad.

## Licencia

Apache License 2.0 es la **licencia propuesta actualmente**, no la licencia final adoptada. El repositorio contiene el texto propuesto sin modificar en `LICENSE-APACHE-2.0-PROPOSED.txt` y una lista explícita de adopción en `LICENSING.md`. Hasta completar ese proceso, no debe representarse CMPCT como finalmente publicado bajo Apache-2.0.

Nota: el hero del repositorio es deliberadamente evergreen y no contiene porcentajes de benchmark ni números de versión; los valores con carga de evidencia permanecen en texto derivado del registro de la versión actual, donde pueden revisarse y actualizarse sin convertir la ilustración en autoridad obsoleta. Las notas históricas y los registros de benchmark no se reescriben para ajustarse a políticas nuevas. La regla de versiones escasas se aplica hacia adelante para preservar un rastro de auditoría honesto.
