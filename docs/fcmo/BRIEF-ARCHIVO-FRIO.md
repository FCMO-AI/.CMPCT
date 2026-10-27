# Carril cmpct-fcmo — CMPCT para el archivo en frío de FCMO (2026-10-26)

Objetivo operativo: evaluar CMPCT para reducir el espacio de árboles repetidos y permitir restauración selectiva. Esta copia pública conserva el alcance técnico sin atribuciones personales ni coordenadas privadas.

## Lee primero
- `AGENTS.md` de este repo completo (orientación, regla de benchmarks, regla de release de rendimiento, dossier de PR material). Manda sobre este brief donde choquen.
- `AGENT_HUB.md`: orientación pública y acceso opcional al Hub.
- `docs/fcmo/PILOTO-ARCHIVO-20261026.md`: el piloto de hoy. zstd -19 ganó en tamaño (logs: CMPCT 144 MB vs 65 MB); CMPCT creó 8–16× más rápido y extrajo un archivo suelto 12× más rápido; `create` aborta con audio sin numpy/soundfile (issue #538).

## El problema real
El disco raíz del servidor FCMO está al 89 % (428 de 503 GB). La mayor parte son árboles casi idénticos: etapas de promoción nocturna (~1.4 GB cada una, decenas), copias de runtime, worktrees de carriles, logs. Queremos guardarlos en frío ocupando lo mínimo y poder sacar un archivo suelto sin descomprimir todo. Hoy el rival es `tar | zstd -19 --long=31 -T4` (la ventana larga ya deduplica entre árboles parecidos).

## Corpus (sólo lectura, local, NUNCA se versiona ni se publica)
Fuente local indicada mediante la variable `SOURCE` — 4 instantáneas reales, 4.5 GB aparentes, 378 283 archivos, ya sin configuraciones ni llaves. En el repo sólo entran cifras agregadas y la receta para regenerar un corpus sintético análogo (público). Ningún nombre de archivo, ruta ni contenido del corpus en commits, PR ni issues.

## Entregables (commits en esta rama; El integrador empuja y abre el PR contra `main` de FCMO-AI/.CMPCT; nadie fusiona sin la campaña CMPCT)
1. **#538 arreglado**: sin numpy/soundfile, `create` degrada al códec genérico (o el extra se declara en `pyproject.toml` y la ruta sin extra sigue funcionando). Prueba que se pone roja si vuelve. Cierra #538 en el PR.
2. **Medición honesta en el corpus**: CMPCT (main y, si aplica, la mejor rama de investigación con CDC/dedup) frente a `tar|zstd -19 --long=31 -T4` y `tar|zstd -19 -T4`: tamaño, pared y RSS de creación, extracción completa, extracción de un archivo suelto, round trip byte a byte. Ejes por separado, sin escalar a un puntaje.
3. **Mejora que mueva la frontera en este caso de uso**: encuentra por qué CMPCT pierde en tamaño en árboles casi duplicados (¿no deduplica entre archivos? ¿ventana corta? ¿por archivo en vez de sólido por grupos?) e implementa la palanca de mayor valor dentro de las reglas del repo (experimento con falsador, sin regresión de 0 bytes en el contrato vigente; si es investigación, márcalo como tal). Meta: tamaño ≤ zstd --long en el corpus conservando la ventaja de acceso selectivo. Si no se alcanza, el PR dice el resultado nulo con números y la siguiente palanca.
4. `docs/fcmo/ARCHIVO-FRIO-20261026.md`: tabla, veredicto por eje y la receta exacta para que FCMO lo use (`cmpct create …` y `cmpct extract …` de un miembro).

## Aceptación (corre y reporta)
- Las pruebas del repo que toque tu cambio, más `python3 tools/check_performance_regression.py` y `tools/check_pr_evidence.py` si aplican al PR.
- Round trip exacto en el corpus completo (hash de cada archivo).
- Texto del PR con el dossier que pide `AGENTS.md` en `docs/fcmo/PR-ARCHIVO-FRIO.md`.

## Prohibido
Secretos, red, tocar otras ramas o PR ajenos, fusionar, escribir fuera de este worktree y de `.scratch/` de este worktree (ignorado), borrar nada del corpus. Contexto propio < 240K: corre scripts en vez de leer salidas largas.

## Reporte final (≤12 líneas)
Números por eje (CMPCT antes/después vs zstd --long), qué palanca implementaste y su falsador, estado de #538, ruta del texto del PR y lo que no te convence.
