# Carril audio-538 — `create` no debe abortar por audio sin numpy/soundfile (Codex Luna) · 2026-11-05

Lee primero: `AGENTS.md` de este repo (manda; es el proyecto CMPCT, con sus propios agentes: cambia sólo lo de este
issue) y el Agent Hub `/srv/fcmo/agents/repos/FCMO-Agent-Hub/runtime/FCMO_RUNTIME_V1.txt`.
Issue 538: `python -m cmpct create <árbol con audio> x.cmpct` en un venv con sólo las dependencias declaradas aborta en
`codec.py` `_audio_modules` (ModuleNotFoundError numpy, luego soundfile).

Ya existe: el códec genérico del propio CMPCT → ADAPTAR (degradar a él). NO_WORTHY_WORK: arreglo interno de robustez.

## Qué haces (rama fix/audio-opcional-538; commits en español, sin push)
1. Prueba primero (roja antes): venv mínimo sólo con lo declarado en `pyproject`/requirements, un .wav sintético
   generado por la prueba (stdlib `wave`), `create` + extracción → bytes idénticos; y que `info` registre que el audio
   usó el códec genérico por falta de módulos.
2. Arreglo: si faltan los módulos de audio, degradar al códec genérico y registrarlo; declara además un extra `[audio]`
   con numpy y soundfile. Con los módulos presentes el comportamiento no cambia (prueba).
3. Suite del repo sin fallos nuevos frente a origin/main.

## Aceptación (pega la salida literal en el mensaje del último commit)
```sh
python3 -m venv /tmp/v538 && /tmp/v538/bin/pip install -q -e . && /tmp/v538/bin/python -m pytest -q <tu prueba>
<comando de suite del repo> 2>&1 | tail -5
git diff --stat origin/main
```
Si el sandbox no tiene red para pip, usa `--no-index` con lo que haya o dilo; Opus lo corre fuera.
Corre lo pesado con `nice -n 10`. Reporte final ≤8 líneas. Prohibido: push, secretos, tocar otras ramas o archivos ajenos
al issue, `git stash`, `git worktree prune`.
