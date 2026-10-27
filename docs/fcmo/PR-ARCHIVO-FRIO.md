# Preserve generic creation without audio extras and investigate cold-tree index context

**Borrador. Closes #538 al fusionar, después de verificar con el runtime genuino.**
No fusionar ni promover el prototipo de índice como política canónica con esta evidencia.

## Problem and baseline

La creación r24 intenta importar numpy/soundfile al considerar WAV-FLAC y aborta si faltan los extras.
El extra `audio` ya estaba declarado; declararlo de nuevo no arreglaría la ruta mínima. Base técnica:
`80c358f8` (main; el commit local siguiente sólo añade documentación). El caso de archivo frío además exige comparar datos completos, acceso individual y RSS
frente a dos flujos tar+Zstd-19: normal y `--long=31`, ambos `-T4`.

## Insight and hypothesis

La disponibilidad de una candidata reversible del encoder no debe decidir la disponibilidad de los
códecs genéricos. Se captura únicamente la carga opcional fallida; no errores de datos ni del decoder.
El experimento separado pregunta si las dos copias del índice pierden reutilización entre subárboles
distantes. Su **disproof** está en `research/cold_index_window_prereg.md`: sin ahorro completo o si el
nivel 19 normal explica el resultado, no se acredita la hipótesis de ventana larga.

## Alternatives considered

Declarar el extra ya existente deja el fallo sin arreglar. Ocultar toda excepción en el encoder o
decoder podría esconder corrupción y se rechaza. La deduplicación exacta entre archivos ya existe;
el inventario no justifica reinventarla. La hipótesis de contenedores se descartó porque el árbol no
tiene ZIP/WHL. El oráculo del chunker CDC existente encontró 799,248 B adicionales de reutilización cruda en 91.3 MB
de archivos grandes únicos; no se confundió ese inventario con ahorro de un archivo completo.
CDC y semejanza de profundidad uno siguen siendo alternativas para contenido editado;
no se movieron otras ramas ni se relabelaron gramáticas de investigación como producto canónico.

## Evidence

`tests/test_optional_audio.py`: cinco métodos, con ausencia de numpy y de soundfile como subcasos.
Se observaron rojos en la base: un fallo y tres errores; después pasan con doble Zlib y adaptador
diagnóstico Zstd. `tests/test_cold_archive_bench.py`: seis métodos, oráculo independiente de hashes,
fallos de cualquier hijo y rechazo de pivotes de enlaces. `tests/test_cold_index_window.py`: cinco
métodos, conservación de datos físicos y metadatos decodificados con la CLI Zstd independiente,
fallback de archivo completo, salida existente, cola extra y primaria dañada.

Mediciones, tabla, límites y recetas: `docs/fcmo/ARCHIVO-FRIO-20261026.md`.
Registro sintético público: `benchmarks/history/2026-10-27-cold-index-diagnostic.json`.
Señal local agregada, separada de los benchmarks públicos del producto:
`benchmarks/history/2026-10-27-cold-tree-local-signal.json`.
Los datos privados, sus nombres, hashes y logs no están versionados. El cuerpo de este documento
es el texto de PR preparado localmente; no se abrió, envió ni fusionó ningún PR.

Comprobaciones estáticas: `tools/check_public_surface.py`,
`tools/check_version_discipline.py --base-sha 32d288d6` y
`tools/check_pr_evidence.py --base-sha 32d288d6 --event .scratch/pr-event.json`.
Las tres pasan en esta rama (dossier en borrador); son comprobaciones estáticas. El integrador debe
repetirlas sobre la base pública limpia, además de las puertas reales pendientes.

## Losses, ambiguity and negative evidence

El entorno no incluye msgpack, pytest ni el núcleo CMPCT propio. La compilación offline falla por
`flate2` ausente en caché. Las ejecuciones con Zstd 1.5.7 del sistema y MessagePack vendorizado por pip
son diagnósticas; MessagePack usó el fallback Python puro, sin la extensión C normal. No se atribuye
su latencia al producto. No acreditan el runtime fijado a Zstd 1.5.5 ni su puerta de cero bytes. Una repetición,
caché no controlada y carga concurrente impiden afirmar una ventaja temporal estable.
La muestra sintética sólo ahorra 1,248 B: no es un avance material de tamaño por sí sola.
En el diagnóstico privado el índice ahorra 4,481,586 B, pero extraer todo pasó de 65.389 a
103.557 s y el miembro individual tardó 5.662 s frente a 5.225 s del tar largo. Las muestras
no cierran la meta conjunta ni prueban si la diferencia persiste con el runtime genuino.
Tar normal ocupa 1,629,725,194 B, crea en 3,397.081 s, extrae en 17.518 s y lee el miembro en
7.327 s. Su RSS de creación, 696,372 KiB, es menor que el de ambas variantes diagnósticas CMPCT;
sus picos de extracción y lectura individual son también menores. Se preservan esos ejes perdidos.

## Safety, integrity and resource accounting

El encoder declina WAV-FLAC sólo si falla su carga opcional, y la lectura FLAC sigue fallando
explícitamente sin decoder. No cambia ningún parser de producto. El experimento reutiliza preflight,
valida la primaria y la cola exactas, rechaza journals/colas extra y no sobrescribe salidas.
La reescritura cuesta CPU, memoria y una pasada extra; no se ha certificado su reader nativo.
La comprobación completa externa incluye cada archivo regular, rutas/tipos y destinos de enlaces.
La excepción de enlaces sólo restaura la fuente original conocida, sin enlaces padres de miembros.
UID/GID, xattrs y topología de hardlinks siguen fuera de la afirmación del oráculo de bytes.

## Compatibility and portability

El fix no cambia bytes cuando el extra funciona. No cambia versión, gramática r24, ABI ni política
canónica de creación. El experimento reempaqueta índices Zstd ordinarios manteniendo hashes, filas y
datos físicos; no añade un codec. Su compatibilidad de recursos, apertura, cola y plataformas requiere
verificación con el núcleo propio antes de cualquier promoción. No se inventó una opción de extracción
individual: la CLI actual la ofrece mediante `cat` o `range`, mientras `extract` restaura el árbol.

## Performance accounting

Los ejes y las cifras completas están en la tabla enlazada. La reescritura elige por **tamaño completo**
y conserva el archivo original byte a byte en empate o pérdida: esa es la propiedad local de
**quality-ratchet**, no una afirmación de haber superado la puerta de promoción del producto.
La creación después de investigar se desglosa en creación base y reescritura; no se oculta la segunda.
No se suman picos RSS de procesos como si fueran memoria agregada. Se conservan pérdidas y casos `?`.

## Public-surface check

Sólo agregados y una receta sintética aparecen en el árbol público. El guard detectó referencias
operativas heredadas en el brief; su copia pública se generalizó sin cambiar objetivos ni aceptación.
La historia alcanzable contiene el brief original: limpiar el árbol actual no purga el commit anterior.
**No publicar esta línea de historia.** El handoff incluye un parche neto local desde el main público
`80c358f8`, para aplicar y revisar sobre una línea limpia antes de publicar; no se reescribió historia
ni se accedió a servicios, cuentas o secretos.

## Completion gates

- [x] Reproducción roja antes del fix y verde después con backends de prueba declarados.
- [x] Hipótesis, alternativas y falsador registrados antes de la medición del índice.
- [x] Controles sintéticos y oráculo independiente conservados.
- [x] Datos privados y logs de trabajo fuera del índice Git.
- [ ] Batería y suite completa con el núcleo CMPCT empaquetado genuino.
- [ ] Tres repeticiones y registros auténticos de paridad base/candidato; puerta de rendimiento.
- [ ] Cierre de recursos/localidad/native/platform del experimento antes de promoverlo.
- [ ] Revisión de historia para publicación y revisión del integrador.

El PR permanece en borrador; los cuadrados pendientes son deuda real. `NEEDS.md` contiene la
continuación. `check_pr_evidence.py` sólo verifica la estructura del dossier, no esos resultados.

## Future leverage

La batería y el corpus público permiten repetir la decisión con un runtime real sin recuperar contexto
privado. La prioridad inmediata es repetir con el runtime genuino antes de atribuir costes a un parser o
introducir otro codec. En acceso selectivo, separar primero apertura/deserialización del índice de lectura del blob: ambos
archivos expanden los mismos 57.2 MB de metadatos. Una consulta acotada o un índice por regiones es una
hipótesis posterior con deuda explícita de representación, recuperación y portabilidad; aún no se
implementa. Para tamaño, la ablación permite decidir entre contexto de metadatos y semejanza de contenido
con reutilización acotada.
No se debe ampliar una familia ya nula ajustando umbrales a este corpus.
