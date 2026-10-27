# Archivo en frío: evaluación de árboles repetidos

**Estado: experimento local; NO-GO para sustituir el archivo operativo.** No es una promesa comercial,
un benchmark público del producto ni una autorización para borrar originales. La fuente privada no se
versiona: este documento sólo conserva agregados. Los nombres, destinos de enlaces, contenidos y hashes
individuales permanecen en el directorio de trabajo local.

## Resultado y límites

Inventario completo: **378,283 archivos regulares, 28,792 directorios, 4,748 enlaces simbólicos**;
**4,821,269,202 B** lógicos. Por SHA-256 hay **21,920 contenidos únicos / 368,775,494 B**. La diferencia
es redundancia exacta potencial, no ahorro comprimido probado. No hay contenedores ZIP/WHL: se descartó
esa hipótesis antes de implementar una optimización específica.

La comparación usa procesos nuevos, caché del sistema sin controlar y una repetición exploratoria.
RSS significa el máximo de los picos individuales de los hijos, **no** memoria agregada simultánea.
No se afirma una mejora temporal estable con esta muestra. La creación usa cuatro trabajadores.

<!-- COLD_RESULTS -->
Medición del 2026-10-27. **CMPCT aquí es una ejecución diagnóstica con backend sustituido**, no el
paquete genuino. “Antes” significa r24 con el fix de audio; el main original sin ese fix no tiene
un archivo completo medido. Ambas variantes parten del mismo archivo y conservan los mismos metadatos.

| Variante | Archivo B | Crear s / RSS KiB | Extraer todo s / RSS KiB | Un miembro s / RSS KiB | Hashes completos |
|---|---:|---:|---:|---:|---|
| CMPCT fijo, diagnóstico | 170,786,966 | 224.840 / 1,829,360 | 65.389 / 1,247,408 | 25.415 / 426,172 | 378,283/378,283 |
| Índice largo, investigación diagnóstica | 166,305,380 | 224.840 + 80.760 / máx. 1,829,360 | 103.557 / 1,250,816 | 5.662 / 427,428 | 378,283/378,283 |
| tar + zstd -19 --long=31 -T4 | 184,019,152 | 1,284.590 / 3,803,044 | 20.137 / 2,102,244 | 5.225 / 2,102,244 | 378,283/378,283 |
| tar + zstd -19 -T4 | 1,629,725,194 | 3,397.081 / 696,372 | 17.518 / 13,796 | 7.327 / 13,596 | 378,283/378,283 |
| CMPCT con runtime genuino | ? | ? | ? | ? | no ejecutado |

El manifiesto final de la fuente coincide con el inicial, y ambos launchers usaron el mismo inventario.
El miembro seleccionado tiene 4,321 B y coincide byte a byte en las cuatro variantes completadas.
El RSS de crear la variante es el máximo de dos procesos sucesivos, no una medición de creación
integrada; la duración suma explícitamente crear y reescribir. El prototipo ahorra **4,481,586 B**
frente a su base y **17,713,772 B** frente al flujo largo en esta corrida diagnóstica.

**Veredicto frente a tar largo, por eje:** tamaño menor en el diagnóstico; creación observada más corta, pendiente de
repetición genuina; extracción completa observada más lenta; sin ventaja medida de latencia selectiva
frente al tar largo; menor RSS observado. La diferencia de 25.415 a 5.662 s entre lectores que expanden
exactamente el mismo índice lógico impide atribuir esa bajada al mecanismo sin repetir y aislar carga.
Frente a tar normal, ambas variantes diagnósticas usan más RSS de creación y extracción; tar normal
restaura el árbol más rápido pero ocupa mucho más. No se cumplen aún la aceptación con el paquete real
ni la meta conjunta de tamaño y ventaja selectiva frente al tar largo.
<!-- /COLD_RESULTS -->

La restauración se coteja con un manifiesto independiente: SHA-256 de **cada** archivo regular, conjunto
exacto de rutas/tipos/directorios y bytes de cada destino de enlace. No se certifican UID/GID, xattrs,
topología de hardlinks ni fidelidad completa de metadatos mediante ese cotejo. Ambos formatos usan sus
valores predeterminados; no se fuerza fsync. La extracción de un miembro tar recorre el flujo hasta el
final y verifica su checksum; no se permite que una salida temprana oculte un fallo del decodificador.

## #538: disponibilidad del audio

El extra `audio` ya estaba declarado en `pyproject.toml`; faltaba tratar su ausencia como rechazo de una
candidata del encoder. `wavflac_compress` comprueba primero la estructura WAV y, si faltan los módulos o
libsndfile, permite competir a los códecs genéricos. No captura errores inesperados ni cambia el decoder.

La batería `tests/test_optional_audio.py` reproduce en la base los fallos de numpy, soundfile y
libsndfile, más la importación innecesaria en un falso WAV. En la base: cinco métodos, un fallo y tres
errores (dos subcasos de importación). Después: cinco métodos pasan con un doble Zlib y también con el
adaptador diagnóstico Zstd del sistema. **La aceptación con el núcleo empaquetado no se ha ejecutado.**

## Palanca investigada y falsador

Un oráculo adicional compiló el chunker nativo existente **sólo en scratch**, sin activarlo en el
encoder medido. En 39 archivos grandes únicos (91,340,487 B), 11 elegibles para cortes nativos,
los chunks únicos pasaron de 86,310,581 a 85,511,333 B: **799,248 B de reutilización cruda adicional**.
La reconstrucción fue exacta. No es tamaño de archivo comprimido, ni una comparación de creación,
ni evidencia de una rama CDC completa; no se escaló a una afirmación de producto.

La deduplicación global de contenido ya existe en r24. No se atribuye la pérdida del piloto a su
ausencia: aquella muestra y este árbol son distintos. En este árbol, la base diagnóstica ya ocupa
menos que tar largo; falta confirmar eso con el núcleo genuino. La oportunidad observada aquí es el
índice repetido, no una supuesta ausencia de deduplicación global.
El experimento `experiments/cold_index_window.py` cambia únicamente la compresión de las dos copias del
índice: prueba `zstd -19 --long=31`, cobra ambas copias y conserva **todos** los bytes originales si no
reduce el archivo completo. No cambia gramática, hashes, datos físicos ni la política del encoder.

La ablación privada del mismo índice, con CLI y entrada por pipe en ambos controles, fue:
nivel 12 **4,274,116 B**, nivel 19 **3,219,043 B**, nivel 19 largo **1,845,480 B**. El
índice base de la biblioteca ocupa **4,086,273 B**: biblioteca y CLI por pipe no tienen
idéntico framing/parámetros de entrada, por lo que el contraste causal de ventana es **19 vs 19 largo**.
En el corpus pequeño público la ventaja de ventana sobre 19 normal fue sólo siete bytes por índice.

El falsador y la ablación están fijados en `research/cold_index_window_prereg.md`: comparar nivel 12,
nivel 19 y nivel 19 con ventana larga; si el 19 normal explica el ahorro, no se acredita una ventaja
causal de ventana larga. La reescritura costó 80.760 s / 1,201,740 KiB en este diagnóstico. La compatibilidad de
recursos del reader genuino y la latencia estable de apertura siguen pendientes. Ganar bytes no cierra esa deuda. La recuperación desde cola no autoriza reescribir una primaria
dañada; el prototipo rechaza journals, basura al final y salidas existentes.

El adaptador `benchmarks/diagnostic_zstd_adapter.py` usa **Zstd 1.5.7 ambiental** y MessagePack ya instalado
o el vendorizado por pip. En esta ejecución, MessagePack usó `pip._vendor.msgpack.fallback`, **Python
puro**; tampoco se midió su extensión C normal. Por eso no se atribuye la latencia observada al reader
del producto ni se propone otra gramática para resolverla antes de repetir. El adaptador no instala
nada, no modifica el paquete y **no sustituye** el núcleo propio
fijado a Zstd 1.5.5 para una promoción. Reproducción explícita sin el runtime genuino (sólo diagnóstico). Para la comparación completa,
añadir `--diagnostic-runtime` al harness; el agregado queda marcado y cada proceso usa el adaptador.
Para el experimento sintético del índice:

```sh
TMPDIR="$PWD/.scratch" python3 benchmarks/diagnostic_zstd_adapter.py --script \
  benchmarks/cold_index_window_bench.py .scratch/index-public-diagnostic
```

Para ensayar la reescritura con el runtime genuino ya disponible:

```sh
PYTHONPATH=src python3 experiments/cold_index_window.py .scratch/base.cmpct .scratch/candidato.cmpct
```

El corpus sintético conserva sus datos diagnósticos en
`benchmarks/history/2026-10-27-cold-index-diagnostic.json`; no es evidencia de rendimiento del paquete.
Los agregados locales completos están separados en
`benchmarks/history/2026-10-27-cold-tree-local-signal.json`, sin identidad ni fingerprint de la fuente
privada. El agregado local de tar describía por error el formato predeterminado como PAX; los comandos
usaron GNU tar con su formato GNU predeterminado. El registro exportado corrige esa descripción, no la
operación medida.

## Reproducción pública y aceptación pendiente

```sh
python3 benchmarks/cold_tree_corpus.py .scratch/public-tree --seed 20261027 --stages 4 --files 256
TMPDIR="$PWD/.scratch" python3 benchmarks/cold_archive_bench.py \
  .scratch/public-tree .scratch/public-measurement --repetitions 3 --cmpct-src "$PWD/src"
```

Usar el **mismo árbol congelado** para base y candidato. La receta genera duplicados exactos, pequeñas
ediciones, inserciones en un archivo grande, texto y contenedores ya empaquetados; no reutiliza ningún
archivo privado. Los resultados privados sólo sirven como señales internas.

Análogo grande por agregados (receta suministrada, no ejecutada en esta sesión):

```sh
python3 benchmarks/cold_tree_corpus.py .scratch/public-large --seed 20261027 \
  --stages 4 --files 94500 --block-bytes 12288 --copies-per-object 6 \
  --event-multiplier 8 --files-per-dir 13 --links-per-stage 1187
```

Produce 378,056 archivos regulares, 29,084 directorios y 4,748 enlaces de destino neutral, con copias dentro de cada instantánea,
ediciones entre instantáneas y tamaño lógico del orden de 4.8 GB. Son dimensiones del generador,
no una medición ejecutada ni una réplica de la distribución privada. Para cotejar sus enlaces
intencionadamente no resolubles, el harness necesita `--trusted-source-links`. Los contenedores añadidos
son controles de generalidad que no estaban presentes en la fuente privada.

```sh
# Con el runtime CMPCT genuino ya disponible; SOURCE y WORK son variables del operador.
TMPDIR="$PWD/.scratch" python3 benchmarks/cold_archive_bench.py "$SOURCE" "$WORK" \
  --repetitions 3 --cmpct-src "$PWD/src" --trusted-source-links
PYTHONPATH=src python3 -m unittest discover -s tests -p test_optional_audio.py
PYTHONPATH=src python3 -m unittest discover -s tests -p test_cold_index_window.py
python3 tools/check_performance_regression.py --base "$BASE_PARITY" --candidate "$CANDIDATE_PARITY"
```

El comprobador de regresión requiere dos registros `cmpct-zip-parity-v1` genuinos. No se convierten
registros diagnósticos o de tar a ese esquema para aparentar una puerta verde.

## Comprobaciones locales

| Comando | Resultado observado |
|---|---|
| `python3 benchmarks/diagnostic_zstd_adapter.py --test discover -s tests -p test_optional_audio.py -v` | 5 métodos pasan, diagnóstico; rojo observado primero en la base |
| `python3 -m unittest discover -s tests -p test_cold_archive_bench.py -v` | 6 métodos pasan; oráculo, generación y fallos del pipeline |
| `python3 benchmarks/diagnostic_zstd_adapter.py --test discover -s tests -p test_cold_index_window.py -v` | 5 métodos pasan, diagnóstico; sin skips en este entorno |
| Harness público con `--engines cmpct --diagnostic-runtime --trusted-source-links` | Creación/restauración/miembro exactos; 36 archivos y 4 enlaces neutros; fuente estable |
| `PYTHONPATH=src python3 -m unittest discover -s tests -p test_optional_audio.py` | No ejecuta la batería: falta msgpack antes de cargar tests |
| `python3 -m pytest -q` | No ejecuta la suite: pytest ausente; conteo completo no disponible |
| `cargo build --offline --locked --release --manifest-path native/cmpct-core/Cargo.toml` | No compila: flate2 ausente de la caché offline |
| `python3 tools/check_performance_regression.py` | Exit 2: faltan los registros auténticos base/candidato requeridos; NO es una puerta aprobada |

Las tres primeras baterías usan `TMPDIR` dentro de scratch y no acreditan el runtime nativo propio.
Los guardas de superficie, versión y estructura del dossier se registran en el PR; sólo prueban sus
contratos estáticos. No hay una afirmación de suite completa verde.

## Receta de uso

```sh
cmpct create "$SOURCE" .scratch/respaldo.cmpct --workers 4
cmpct verify .scratch/respaldo.cmpct
# Para una fuente sin enlaces externos, la política segura predeterminada:
cmpct extract .scratch/respaldo.cmpct .scratch/restaurado
# El árbol conocido evaluado aquí contiene enlaces externos: restaurar en otro destino nuevo
# sólo después de comprobar que ningún enlace es padre de un miembro (lo hace el harness):
cmpct extract .scratch/respaldo.cmpct .scratch/restaurado-con-enlaces --unsafe-symlinks
# Miembro individual: cat entrega sus bytes; extract sólo admite el árbol completo.
cmpct cat .scratch/respaldo.cmpct 'directorio/archivo' > .scratch/archivo-restaurado
# Alternativa equivalente con salida explícita, conociendo el tamaño completo del miembro:
cmpct range .scratch/respaldo.cmpct 'directorio/archivo' 0 "$MEMBER_BYTES" -o .scratch/archivo-restaurado
```

No existe `cmpct extract archive destino miembro`: no se inventa esa interfaz. La política segura
rechaza enlaces absolutos y con `..`; el árbol local contiene esos casos. Sólo para una fuente original
conocida, el harness acepta `--trusted-source-links`, comprueba que ningún enlace es padre de otro
miembro y usa la opción existente `--unsafe-symlinks`. Nunca se sigue el destino de esos enlaces al
cotejar hashes. Esa excepción no es una receta para archivos recibidos de terceros.

**EN JUEGO:** integridad del archivo operativo → **EVIDENCIA EXIGIDA:** restauración integral, semántica
de enlaces explícita y comparación repetida con el paquete real → **EVIDENCIA QUE HAY:** inventario,
pruebas aisladas y medición exploratoria → **NO-GO** para adopción o borrado. Ética: NO_MATERIAL; datos
locales, sin publicación ni envío a proveedores.
