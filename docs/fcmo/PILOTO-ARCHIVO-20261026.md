# Piloto de archivo local — 2026-10-26

Medición exploratoria de árboles concretos; no es evidencia pública de CMPCT ni base de una promesa comercial.
`tar + zstd -19 -T4` crea un tar sólido: extraer un miembro obliga a descomprimir el flujo completo. CMPCT mide `range` del archivo mediano seleccionado (lectura completa del miembro), no una submuestra.

CMPCT runtime probe: **disponible** (OK; sin bloqueador secundario observado).

| Corpus | Original (bytes) | CMPCT / tar (bytes) | Create pared CMPCT / tar (s; RSS KiB) | Extract pared CMPCT / tar (s; RSS KiB) | Byte-exact CMPCT / tar | Selectivo CMPCT / tar (s) | Veredicto comparativo |
|---|---:|---:|---|---|---|---|---|
| bundles | 85471511 | 85320094 / 81967369 | 0.802 s; 473432 KiB / 13.02 s; 417252 KiB | 0.239 s; 131888 KiB / 0.08 s; 13504 KiB | sí / sí | 0.087 / 0.042 | CMPCT pierde |
| logs-texto | 1081863092 | 143989190 / 65014889 | 10.397 s; 1820612 KiB / 83.873 s; 579928 KiB | 2.765 s; 1238240 KiB / 1.183 s; 13588 KiB | sí / sí | 0.075 / 0.951 | CMPCT pierde |
| codigo-entorno | 617908216 | None / 242234031 | 25.656 s; 694000 KiB / 152.085 s; 681648 KiB | no medido / 1.812 s; 13592 KiB | no medido / sí | no medido / 0.861 | no evaluable: CMPCT runtime no disponible |

## Veredicto

Los ejes se valoran por separado: tamaño, pared/RSS de creación y extracción, exactitud y lectura selectiva. Un timeout o runtime ausente no equivale a pérdida ni a empate. Los corpus con round trip fallido son incomparables hasta tomar una instantánea estable.

Para decidir adopción en archivo de carriles y simulacros de restauración parcial B2 (límite 512 MB/día), CMPCT sólo es candidato si el registro contiene tamaño menor o igual, round trip exacto y una ventaja útil de acceso selectivo; esta corrida aislada no prueba la política diaria de descargas ni sustituye un simulacro de restauración real.

## Alcance y límites

Los datos y fallos completos están en `piloto-20261026.json`. Los archivos temporales, incluidos logs, se eliminaron automáticamente. Las mediciones incluyen arranque de proceso; RSS es el máximo reportado por GNU time para el proceso/hijo observado, no la suma de todo el árbol de procesos. `tar` conserva el árbol como flujo sólido; CMPCT extrae el árbol completo para la comprobación integral.

## Lectura del integrador (Claude, 2026-10-26)
- Corrida fuera del sandbox (venv con núcleo nativo compilado desde este checkout; logs = copia congelada por enlaces duros
  de los archivos con más de 1 día).
- **Tamaño:** zstd -19 gana: en logs, CMPCT ocupa 2.2× más (144 MB frente a 65 MB); en bundles git ya comprimidos queda casi igual (+4 %).
- **Velocidad:** CMPCT crea 8–16× más rápido (logs 10 s frente a 84 s; bundles 0.8 s frente a 13 s) y saca un archivo suelto 12× más
  rápido en logs (0.08 s frente a 0.95 s). Usa 3× más memoria al crear.
- **Exactitud:** las dos herramientas restauran todo byte a byte idéntico donde CMPCT corrió.
- **Defecto encontrado:** `cmpct create` aborta con un árbol que contiene audio si faltan `numpy` y luego `soundfile`
  (codec.py `_audio_modules`); ninguna de las dos está declarada en `pyproject.toml` (sólo msgpack). Debería degradar al
  códec genérico o declararlas como extra. Por eso el corpus código+entorno no tiene medición CMPCT.
- **Adopción en FCMO:** para archivo en frío (disco, B2) sigue zstd -19. CMPCT sólo es candidato donde pesan la velocidad
  de creación y la extracción de un archivo suelto (simulacros de restauración parcial), una vez corregido el defecto.
  Se mide de nuevo cuando salga una versión con ese arreglo.
