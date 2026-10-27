# cmpct-fcmo

- Ejecutar la batería con el runtime CMPCT genuino (núcleo propio con Zstd 1.5.5 y MessagePack normal),
  sin adaptador diagnóstico: `tests/test_optional_audio.py`, `tests/test_cold_archive_bench.py` y
  `tests/test_cold_index_window.py`; después, la suite completa.
- Repetir la comparación sobre un único árbol congelado con tres repeticiones y generar el par de
  registros release-parity auténticos para `tools/check_performance_regression.py`. Las mediciones
  con Zstd 1.5.7 ambiental no acreditan promoción, tiempos estables ni equivalencia de bytes al paquete.
- La copia pública del brief heredado se generalizó conservando sus requisitos técnicos: el guard
  encontró dos referencias operativas preexistentes. Antes de publicar la rama, revisar también el
  historial alcanzable: corregir el árbol actual no elimina la procedencia privada del commit base.
  No publicar esta línea de historia. Aplicar y revisar `.scratch/public-safe.patch` (diff neto desde
  el main público `80c358f8`) sobre una línea limpia; no se reescribió historia ni se tocaron otras ramas.
- Mantener la propuesta en borrador; no borrar originales ni promover el experimento de índice sin
  cerrar exactitud, recursos del reader nativo, rendimiento y política de enlaces de restauración.

# cmpct-ci565

- `nested-abba`: decidir el contrato de `.github/workflows/v030-r24-nested-create-abba.yml`.
  Su premisa exige builder/codec idénticos a main; #538 requiere cambiar codec. Se conservan ambos
  el fix y la aserción. Un nuevo diagnóstico debe acreditar sus propios controles de identidad,
  vinculación y rendimiento; no se autoriza simplemente quitar la aserción ni ocultar el fix en hooks.
- `evidence`: devolver el PR #565 a borrador o producir toda la evidencia pendiente antes de marcarlo
  listo. `docs/fcmo/PR-ARCHIVO-FRIO.md` conserva sus cuatro casillas abiertas; no se cambió el estado
  remoto porque este carril es offline.
- Materializar el núcleo propio del checkout base antes del primer brazo de tiny ABBA mediante
  `tools/materialize_performance_base_native.py`, con recibo de propiedad del árbol base. La instalación
  editable del candidato no prepara el otro árbol. El workflow nested tendrá la misma necesidad
  al superar su bloqueo previo. No sustituir el núcleo por Zstd ambiental.
- Campaña CMPCT: reconciliar manifiesto rolling/loader estricto (nueve jobs), los cuatro rojos de
  suite heredados y la evidencia pública de versión. Corregir el dominio de recibos RSS entre productor
  y consumidor (36 llamadas de ambos motores frente a una expectativa de 18), sin debilitar aserciones.
  Resolver además el falso ZIP y el contexto de construcción/lectura de perfiles de investigación.
- Repetir main y candidato con el mismo runtime y árbol antes de cerrar las atribuciones provisionales
  de tamaño y create. Ejecutar pytest y la carga real de cmpct_core con y sin audio: aquí faltan pytest,
  MessagePack normal, extras de audio y núcleo; cargo offline no encuentra flate2. Ver `docs/fcmo/CI-565.md`.
