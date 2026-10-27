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
