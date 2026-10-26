#!/usr/bin/env python3
"""Measure CMPCT and solid tar+Zstandard on caller-supplied directory trees.

The harness writes all archives and restored trees beneath a private temporary
directory, never under a corpus root. A missing CMPCT runtime is recorded as an
unavailable measurement; it is never silently replaced by another codec.
"""
from __future__ import annotations

import argparse
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
import time
from zoneinfo import ZoneInfo


DEFAULT_TIMEOUT = 20 * 60


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus", action="append", required=True, metavar="NAME=DIR",
                        help="repeat once per read-only corpus; names should be non-sensitive labels")
    parser.add_argument("--python", default=sys.executable,
                        help="Python interpreter containing the CMPCT runtime (default: this interpreter)")
    parser.add_argument("--cmpct-root", type=Path, default=Path(__file__).resolve().parents[1],
                        help="CMPCT checkout root; its src/ is added to PYTHONPATH")
    parser.add_argument("--workers", type=int, default=4, choices=range(1, 5),
                        help="CMPCT create workers, capped at four (default: 4)")
    parser.add_argument("--timeout-seconds", type=int, default=DEFAULT_TIMEOUT,
                        help="per-tool timeout; timed-out stages are recorded and later stages continue")
    parser.add_argument("--output-json", type=Path, default=Path("docs/fcmo/piloto-20261026.json"))
    parser.add_argument("--output-report", type=Path, default=Path("docs/fcmo/PILOTO-ARCHIVO-20261026.md"))
    parser.add_argument("--work-parent", type=Path, default=Path("/var/tmp"),
                        help="parent for an automatically removed cmpct-piloto-* temporary directory")
    return parser.parse_args()


def parse_corpora(items: list[str]) -> list[tuple[str, Path]]:
    result: list[tuple[str, Path]] = []
    names: set[str] = set()
    for item in items:
        if "=" not in item:
            raise ValueError(f"--corpus must be NAME=DIR: {item!r}")
        name, raw_path = item.split("=", 1)
        path = Path(raw_path).expanduser().resolve(strict=True)
        if not name or name in names or not path.is_dir():
            raise ValueError(f"invalid or duplicate corpus name/path: {item!r}")
        names.add(name)
        result.append((name, path))
    return result


def tree_facts(root: Path) -> dict:
    files = []
    regular_bytes = 0
    for current, dirs, names in os.walk(root, followlinks=False):
        symlink_dirs = sorted(d for d in dirs if (Path(current) / d).is_symlink())
        for name in symlink_dirs:
            path = Path(current) / name
            files.append({"path": path.relative_to(root).as_posix(), "kind": "symlink", "target": os.readlink(path)})
        dirs[:] = sorted(d for d in dirs if d not in symlink_dirs)
        for name in sorted(names):
            path = Path(current) / name
            rel = path.relative_to(root).as_posix()
            st = path.lstat()
            if path.is_symlink():
                files.append({"path": rel, "kind": "symlink", "target": os.readlink(path)})
            elif path.is_file():
                files.append({"path": rel, "kind": "file", "size_bytes": st.st_size})
                regular_bytes += st.st_size
    eligible = [f for f in files if f["kind"] == "file" and f["size_bytes"] >= 64 * 1024]
    eligible.sort(key=lambda f: (f["size_bytes"], f["path"]))
    selected = eligible[len(eligible) // 2] if eligible else None
    return {"regular_file_bytes": regular_bytes, "file_count": sum(f["kind"] == "file" for f in files),
            "symlink_count": sum(f["kind"] == "symlink" for f in files), "selected_file": selected}


def manifest(root: Path) -> dict[str, tuple]:
    result = {}
    for current, dirs, names in os.walk(root, followlinks=False):
        symlink_dirs = sorted(d for d in dirs if (Path(current) / d).is_symlink())
        for name in symlink_dirs:
            path = Path(current) / name
            result[path.relative_to(root).as_posix()] = ("symlink", os.readlink(path))
        dirs[:] = sorted(d for d in dirs if d not in symlink_dirs)
        for name in sorted(names):
            path = Path(current) / name
            rel = path.relative_to(root).as_posix()
            if path.is_symlink():
                result[rel] = ("symlink", os.readlink(path))
            elif path.is_file():
                digest = hashlib.sha256()
                with path.open("rb") as stream:
                    for block in iter(lambda: stream.read(1024 * 1024), b""):
                        digest.update(block)
                result[rel] = ("file", path.stat().st_size, digest.hexdigest())
    return result


def tool_result(command: list[str], *, cwd: Path, env: dict[str, str], timeout: int,
                log_path: Path, shell: bool = False) -> dict:
    wrapped = command if shell else ["nice", "-n", "10", "/usr/bin/time", "-v", *command]
    started = time.monotonic()
    try:
        proc = subprocess.run(wrapped, cwd=cwd, env=env, text=True,
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                              timeout=timeout, shell=shell, check=False)
        elapsed = time.monotonic() - started
        log_path.write_text(proc.stdout + "\n--- STDERR ---\n" + proc.stderr, encoding="utf-8", errors="replace")
        match = re.search(r"Maximum resident set size \(kbytes\):\s*(\d+)", proc.stderr)
        return {"status": "ok" if proc.returncode == 0 else "failed", "exit_code": proc.returncode,
                "wall_seconds": round(elapsed, 3), "max_rss_kib": int(match.group(1)) if match else None}
    except subprocess.TimeoutExpired as exc:
        elapsed = time.monotonic() - started
        out = exc.stdout or ""
        err = exc.stderr or ""
        if isinstance(out, bytes): out = out.decode(errors="replace")
        if isinstance(err, bytes): err = err.decode(errors="replace")
        log_path.write_text(str(out) + "\n--- STDERR ---\n" + str(err), encoding="utf-8", errors="replace")
        return {"status": "timeout", "wall_seconds": round(elapsed, 3), "max_rss_kib": None}


def archive_size(path: Path) -> int | None:
    try:
        return path.stat().st_size
    except OSError:
        return None


def cdmx_stamp() -> str:
    return datetime.now(ZoneInfo("America/Mexico_City")).strftime("%Y-%m-%d %H:%M:%S %Z")


def exact_match(source: Path, restored: Path) -> dict:
    if not restored.is_dir():
        return {"byte_exact": False, "reason": "restored tree is missing"}
    left = manifest(source)
    right = manifest(restored)
    differing = set(left) ^ set(right)
    differing.update(k for k in set(left) & set(right) if left[k] != right[k])
    return {"byte_exact": not differing, "source_entries": len(left), "restored_entries": len(right),
            "differing_entry_count": len(differing)}


def run() -> int:
    args = parse_args()
    corpora = parse_corpora(args.corpus)
    repo = args.cmpct_root.resolve(strict=True)
    python = shutil.which(args.python) or args.python
    env = os.environ.copy()
    env["PYTHONPATH"] = os.pathsep.join(filter(None, [str(repo / "src"), env.get("PYTHONPATH", "")]))
    report = {"schema": "fcmo-cmpct-archive-pilot-v1", "started_cdmx": cdmx_stamp(),
              "limits": {"workers_max": 4, "nice": 10, "tool_timeout_seconds": args.timeout_seconds},
              "runtime": {"python": python, "python_version": sys.version.split()[0],
                          "cmpct_root_commit": subprocess.run(["git", "-C", str(repo), "rev-parse", "HEAD"],
                           text=True, capture_output=True, check=False).stdout.strip(),
                          "zstd_version": subprocess.run(["zstd", "--version"], text=True, capture_output=True,
                           check=False).stdout.strip(), "gnu_time": "/usr/bin/time -v",
                          "cmpct_runtime_probe": None}, "corpora": []}

    probe = subprocess.run([python, "-c", "import cmpct, msgpack"], cwd=repo, env=env,
                           text=True, capture_output=True, check=False)
    report["runtime"]["cmpct_runtime_probe"] = {"exit_code": probe.returncode,
        "error": (probe.stderr.strip().splitlines()[-1] if probe.returncode else None)}

    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_report.parent.mkdir(parents=True, exist_ok=True)
    args.work_parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="cmpct-piloto-", dir=args.work_parent) as tmp:
        work = Path(tmp)
        for index, (name, source) in enumerate(corpora, 1):
            facts = tree_facts(source)
            base = work / f"corpus-{index}"
            base.mkdir()
            entry = {"name": name, "regular_file_bytes": facts["regular_file_bytes"],
                     "file_count": facts["file_count"], "symlink_count": facts["symlink_count"],
                     "selected_file_bytes": facts["selected_file"]["size_bytes"] if facts["selected_file"] else None,
                     "cmpct": {}, "tar_zstd": {}}
            log_counter = 0

            def measured(key: str, command: list[str], *, shell: bool = False) -> dict:
                nonlocal log_counter
                log_counter += 1
                return tool_result(command, cwd=repo, env=env, timeout=args.timeout_seconds,
                                   log_path=base / f"{log_counter:02d}-{key}.log", shell=shell)

            cmpct_archive = base / "archive.cmpct"
            if probe.returncode:
                entry["cmpct"]["status"] = "unavailable"
                entry["cmpct"]["reason"] = report["runtime"]["cmpct_runtime_probe"]["error"]
            else:
                entry["cmpct"]["create"] = measured("cmpct-create", [python, "-m", "cmpct", "create",
                    str(source), str(cmpct_archive), "--workers", str(args.workers)])
                entry["cmpct"]["archive_bytes"] = archive_size(cmpct_archive)
                if entry["cmpct"]["create"]["status"] == "ok":
                    entry["cmpct"]["verify"] = measured("cmpct-verify", [python, "-m", "cmpct", "verify", str(cmpct_archive)])
                    target = base / "cmpct-restored"
                    entry["cmpct"]["extract"] = measured("cmpct-extract", [python, "-m", "cmpct", "extract",
                        str(cmpct_archive), str(target)])
                    entry["cmpct"]["roundtrip"] = exact_match(source, target) if entry["cmpct"]["extract"]["status"] == "ok" else {"byte_exact": False, "reason": "extract failed"}
                    selected = facts["selected_file"]
                    if selected:
                        partial = base / "cmpct-selected.out"
                        entry["cmpct"]["selective"] = measured("cmpct-selective", [python, "-m", "cmpct", "range",
                            str(cmpct_archive), selected["path"], "0", str(selected["size_bytes"]), "-o", str(partial)])
                        if entry["cmpct"]["selective"]["status"] == "ok":
                            entry["cmpct"]["selective"]["byte_exact"] = partial.read_bytes() == (source / selected["path"]).read_bytes()

            zstd_archive = base / "archive.tar.zst"
            tar_create = ("nice -n 10 tar -cf - -C " + shlex.quote(str(source)) + " . | nice -n 10 zstd -19 -T4 -q -o " + shlex.quote(str(zstd_archive)))
            entry["tar_zstd"]["create"] = measured("tar-zstd-create", ["nice", "-n", "10", "/usr/bin/time", "-v",
                "bash", "-o", "pipefail", "-c", tar_create], shell=False)
            # GNU time wraps the shell and its pipeline; the recorded peak is the largest waited child RSS.
            entry["tar_zstd"]["archive_bytes"] = archive_size(zstd_archive)
            if entry["tar_zstd"]["create"]["status"] == "ok":
                (base / "tar-restored").mkdir()
                entry["tar_zstd"]["extract"] = measured("tar-zstd-extract", ["nice", "-n", "10", "/usr/bin/time", "-v",
                    "bash", "-o", "pipefail", "-c", "zstd -dc -q " + shlex.quote(str(zstd_archive)) +
                    " | tar -xf - -C " + shlex.quote(str(base / "tar-restored"))], shell=False)
                restored = base / "tar-restored"
                entry["tar_zstd"]["roundtrip"] = exact_match(source, restored) if entry["tar_zstd"]["extract"]["status"] == "ok" else {"byte_exact": False, "reason": "extract failed"}
                if "source_entries" in entry["tar_zstd"]["roundtrip"]:
                    entry["tar_zstd"]["roundtrip"]["source_entry_delta_from_start"] = entry["tar_zstd"]["roundtrip"]["source_entries"] - facts["file_count"] - facts["symlink_count"]
                selected = facts["selected_file"]
                if selected:
                    selected_path = selected["path"]
                    selective = ("zstd -dc -q " + shlex.quote(str(zstd_archive)) + " | tar -xOf - -- " +
                                 shlex.quote("./" + selected_path) + " > " + shlex.quote(str(base / "tar-selected.out")))
                    entry["tar_zstd"]["selective"] = measured("tar-zstd-selective", ["nice", "-n", "10", "/usr/bin/time", "-v",
                        "bash", "-o", "pipefail", "-c", selective], shell=False)
                    if entry["tar_zstd"]["selective"]["status"] == "ok":
                        entry["tar_zstd"]["selective"]["byte_exact"] = (base / "tar-selected.out").read_bytes() == (source / selected_path).read_bytes()
            report["corpora"].append(entry)

    report["finished_cdmx"] = cdmx_stamp()
    args.output_json.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    args.output_report.write_text(render_report(report), encoding="utf-8")
    return 0


def render_report(data: dict) -> str:
    lines = ["# Piloto de archivo local — 2026-10-26", "",
             "Medición exploratoria de árboles concretos; no es evidencia pública de CMPCT ni base de una promesa comercial.",
             "`tar + zstd -19 -T4` crea un tar sólido: extraer un miembro obliga a descomprimir el flujo completo. CMPCT mide `range` del archivo mediano seleccionado (lectura completa del miembro), no una submuestra.", "",
             f"CMPCT runtime probe: **{'disponible' if data['runtime']['cmpct_runtime_probe']['exit_code'] == 0 else 'no disponible'}** ({data['runtime']['cmpct_runtime_probe'].get('error') or 'OK'}; {data['runtime'].get('secondary_blocker_observed', 'sin bloqueador secundario observado')}).",
             "", "| Corpus | Original (bytes) | CMPCT / tar (bytes) | Create pared CMPCT / tar (s; RSS KiB) | Extract pared CMPCT / tar (s; RSS KiB) | Byte-exact CMPCT / tar | Selectivo CMPCT / tar (s) | Veredicto comparativo |", "|---|---:|---:|---|---|---|---|---|"]
    for row in data["corpora"]:
        c, z = row["cmpct"], row["tar_zstd"]
        def secs(group: dict, key: str) -> str:
            val = group.get(key, {})
            return f"{val.get('wall_seconds')} s" if val.get("wall_seconds") is not None else val.get("status", "no medido")
        def exact(group: dict) -> str:
            return "sí" if group.get("roundtrip", {}).get("byte_exact") else ("no" if "roundtrip" in group else "no medido")
        def metric(group: dict, key: str) -> str:
            val = group.get(key, {})
            if not val.get("wall_seconds"):
                return val.get("status", "no medido")
            rss = val.get("max_rss_kib")
            return f"{val['wall_seconds']} s; {rss if rss is not None else '?'} KiB"
        sel_c = c.get("selective", {}).get("wall_seconds", c.get("selective", {}).get("status", "no medido"))
        sel_z = z.get("selective", {}).get("wall_seconds", z.get("selective", {}).get("status", "no medido"))
        verdict = "no evaluable: CMPCT runtime no disponible"
        if c.get("archive_bytes") is not None and z.get("archive_bytes") is not None:
            verdict = "CMPCT gana" if c["archive_bytes"] < z["archive_bytes"] else "empate" if c["archive_bytes"] == z["archive_bytes"] else "CMPCT pierde"
        roundtrip = f"{exact(c)} / {exact(z)}"
        if z.get("roundtrip", {}).get("byte_exact") is False:
            roundtrip += f" (árbol cambió: {z['roundtrip'].get('source_entries')} vs {z['roundtrip'].get('restored_entries')} entradas)"
        lines.append(f"| {row['name']} | {row['regular_file_bytes']} | {c.get('archive_bytes', '—')} / {z.get('archive_bytes', '—')} | {metric(c, 'create')} / {metric(z, 'create')} | {metric(c, 'extract')} / {metric(z, 'extract')} | {roundtrip} | {sel_c} / {sel_z} | {verdict} |")
    lines += ["", "## Veredicto", "",
              "Los ejes se valoran por separado: tamaño, pared/RSS de creación y extracción, exactitud y lectura selectiva. Un timeout o runtime ausente no equivale a pérdida ni a empate. Los corpus con round trip fallido son incomparables hasta tomar una instantánea estable.", "",
              "Para decidir adopción en archivo de carriles y simulacros de restauración parcial B2 (límite 512 MB/día), CMPCT sólo es candidato si el registro contiene tamaño menor o igual, round trip exacto y una ventaja útil de acceso selectivo; esta corrida aislada no prueba la política diaria de descargas ni sustituye un simulacro de restauración real.", "",
              "## Alcance y límites", "",
              "Los datos y fallos completos están en `piloto-20261026.json`. Los archivos temporales, incluidos logs, se eliminaron automáticamente. Las mediciones incluyen arranque de proceso; RSS es el máximo reportado por GNU time para el proceso/hijo observado, no la suma de todo el árbol de procesos. `tar` conserva el árbol como flujo sólido; CMPCT extrae el árbol completo para la comprobación integral.", ""]
    return "\n".join(lines)


if __name__ == "__main__":
    try:
        raise SystemExit(run())
    except (OSError, ValueError) as exc:
        print(f"fcmo_piloto_archivo: {exc}", file=sys.stderr)
        raise SystemExit(2)
