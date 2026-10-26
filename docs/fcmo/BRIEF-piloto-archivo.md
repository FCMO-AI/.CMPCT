# Brief — piloto de archivo FCMO con CMPCT (carril cmpct-piloto, 2026-10-26)

Lee primero: el Agent Hub (`/srv/fcmo/agents/repos/FCMO-Agent-Hub/runtime/FCMO_RUNTIME_V1.txt`, `disciplines/RESEARCH_EVALUATION.md`),
y en este repo `AGENTS.md`, `CURRENT_STATE.md`, `BENCHMARKS.md` y el README (§Quick start). CMPCT es una frontera autónoma:
este carril NO cambia el formato, el código de `cmpct/` ni su versión; sólo mide.

## Pregunta
¿Sirve CMPCT hoy para archivar directorios fríos reales de este servidor (disco raíz al 88 %) mejor o igual que `zstd -19`
(tar | zstd -19 -T0), conservando acceso selectivo? Un nulo es un resultado válido.

## Corpus (sólo lectura; NUNCA modificar ni borrar el origen)
1. `/srv/fcmo/agents/work/lane-archive` (84 MB, bundles git)
2. `/srv/fcmo/agents/work/claudex-goal-20261001/logs` (1.2 GB, logs de texto)
3. `/var/tmp/kyrion-test/kui-staging-c07c/c11-antes` (688 MB, árbol de código + venv)

## Qué medir por corpus (salidas en un dir temporal propio bajo /var/tmp/cmpct-piloto-*, se borra al final salvo el reporte)
- tamaño original, tamaño CMPCT (`python -m cmpct create <dir> x.cmpct --workers 4`), tamaño tar+zstd -19 -T4;
- tiempo de pared y RSS máximo (`/usr/bin/time -v`) de crear y de extraer, ambos;
- ida y vuelta byte-exacta: `cmpct verify` + extracción completa y `diff -r` (o comparación sha256 por archivo) contra el origen;
- acceso selectivo: tiempo de `cmpct extract`/`range` de UN archivo mediano frente a `zstd -dc | tar -x <ese archivo>`.
Máximo 4 workers y `nice -n 10` (host compartido, ley 22). Si un corpus tarda >20 min en una herramienta, regístralo y sigue.

## Entregables (dueño exclusivo de estos archivos)
- `tools/fcmo_piloto_archivo.py` (o .sh): reproduce todo con un comando, sin rutas fijas salvo por argumentos.
- `docs/fcmo/PILOTO-ARCHIVO-20261026.md`: tabla por corpus, veredicto (gana / empata / pierde por eje), y si conviene adoptarlo
  para archivo de carriles y simulacros de restauración parcial del respaldo B2 (tope de descarga 512 MB/día).
- `docs/fcmo/piloto-20261026.json`: números crudos.

## Aceptación
`python3 tools/fcmo_piloto_archivo.py --help` funciona; el reporte y el JSON existen y coinciden; ida y vuelta byte-exacta
reportada por corpus; `git diff --stat origin/main` sólo toca los tres entregables y este brief.

## Prohibido
Secretos, tocar `cmpct/`, versiones, CI, borrar o mover algo fuera de tu dir temporal, más de 4 workers.
Reporte final ≤10 líneas: COMMITS, FINDINGS, ACCEPTANCE, UNVERIFIED, CANON (cita sólo lo que leíste de verdad).
