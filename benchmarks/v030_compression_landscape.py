from __future__ import annotations

"""Reference-only broad compression landscape for the frozen CMPCT v0.30 corpus.

This benchmark deliberately does *not* change the v0.30 release contract. ZIP/Deflate-9 and
solid Zstd-19 remain the release comparators. The formats here are scientific/reference
points that show where the exact shipping CMPCT candidate sits in the wider lossless
compression landscape.

Every available format:
- receives the exact same normalized 15 workload trees used by v030_external_competitors;
- pays deterministic tar/container construction inside create time where applicable;
- extracts through its real decoder;
- must reproduce the exact logical tree SHA-256 before receiving a result;
- records tool/version identity and never turns an unavailable optional codec into a pass.

No selective-read equivalence is claimed for solid stream archives or ZPAQ.
"""

import argparse
import bz2
import gzip
import hashlib
import json
import lzma
from pathlib import Path
import shutil
import subprocess
import tarfile
import tempfile
import time

from benchmarks import v030_external_competitors as B
from benchmarks import v030_release_generalization as GENERAL


def _version(exe: str | None, args: list[str] | None = None) -> str | None:
    if exe is None:
        return None
    probes = [args or ["--version"], ["-V"], ["-version"]]
    for probe in probes:
        try:
            cp = subprocess.run([exe, *probe], check=False, text=True, capture_output=True, timeout=10)
            text = (cp.stdout or cp.stderr).strip().splitlines()
            if text:
                return text[0][:240]
        except Exception:
            pass
    return Path(exe).name


def _deterministic_tar(stage: Path, tar_path: Path) -> None:
    with tarfile.open(tar_path, "w", format=tarfile.PAX_FORMAT) as tf:
        for path in B._files(stage):
            rel = path.relative_to(stage).as_posix()
            raw = path.read_bytes()
            info = tarfile.TarInfo(rel)
            info.size = len(raw)
            info.mtime = B.NORMALIZED_MTIME
            info.mode = 0o644
            info.uid = 0
            info.gid = 0
            info.uname = ""
            info.gname = ""
            import io
            tf.addfile(info, io.BytesIO(raw))


def _extract_tar(tar_path: Path, extracted: Path) -> None:
    extracted.mkdir(parents=True, exist_ok=True)
    with tarfile.open(tar_path, "r") as tf:
        root = extracted.resolve()
        for member in tf.getmembers():
            target = (extracted / member.name).resolve()
            if target != root and root not in target.parents:
                raise RuntimeError("generated tar contains unsafe path")
        tf.extractall(extracted)


def _python_stream(stage: Path, archive: Path, extracted: Path, work: Path, codec: str, level: int) -> dict:
    tar_path = work / f"{codec}-{level}.tar"
    started = time.perf_counter()
    _deterministic_tar(stage, tar_path)
    raw = tar_path.read_bytes()
    if codec == "gzip":
        payload = gzip.compress(raw, compresslevel=level, mtime=0)
    elif codec == "bzip2":
        payload = bz2.compress(raw, compresslevel=level)
    elif codec == "xz":
        payload = lzma.compress(raw, format=lzma.FORMAT_XZ, preset=level)
    else:
        raise ValueError(codec)
    archive.write_bytes(payload)
    create_s = time.perf_counter() - started

    started = time.perf_counter()
    payload = archive.read_bytes()
    if codec == "gzip":
        decoded = gzip.decompress(payload)
    elif codec == "bzip2":
        decoded = bz2.decompress(payload)
    else:
        decoded = lzma.decompress(payload, format=lzma.FORMAT_XZ)
    decoded_tar = work / f"decoded-{codec}-{level}.tar"
    decoded_tar.write_bytes(decoded)
    _extract_tar(decoded_tar, extracted)
    extract_s = time.perf_counter() - started
    return {"available": True, "archive_bytes": archive.stat().st_size, "create_s": create_s, "extract_s": extract_s,
            "tool": f"python-{codec}", "version": None}


def _cli_stream(stage: Path, archive: Path, extracted: Path, work: Path, codec: str, level: int) -> dict:
    exe = shutil.which(codec)
    if exe is None:
        return {"available": False, "reason": f"{codec}-not-installed"}
    tar_path = work / f"{codec}-{level}.tar"
    started = time.perf_counter()
    _deterministic_tar(stage, tar_path)
    if codec == "zstd":
        cmd = [exe, f"-{level}", "-T1", "-f", str(tar_path), "-o", str(archive)]
    elif codec == "brotli":
        cmd = [exe, f"--quality={level}", "--no-copy-stat", "--output", str(archive), str(tar_path)]
    elif codec == "lz4":
        # level 12 is the highest ordinary HC level exposed by the CLI.
        cmd = [exe, f"-{level}", "-f", str(tar_path), str(archive)]
    elif codec == "lzip":
        cmd = [exe, f"-{level}", "-f", "-o", str(archive), str(tar_path)]
    else:
        raise ValueError(codec)
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
    create_s = time.perf_counter() - started

    decoded_tar = work / f"decoded-{codec}-{level}.tar"
    started = time.perf_counter()
    if codec == "zstd":
        cmd = [exe, "-d", "-f", str(archive), "-o", str(decoded_tar)]
    elif codec == "brotli":
        cmd = [exe, "--decompress", "--output", str(decoded_tar), str(archive)]
    elif codec == "lz4":
        cmd = [exe, "-d", "-f", str(archive), str(decoded_tar)]
    elif codec == "lzip":
        cmd = [exe, "-d", "-f", "-o", str(decoded_tar), str(archive)]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
    _extract_tar(decoded_tar, extracted)
    extract_s = time.perf_counter() - started
    return {"available": True, "archive_bytes": archive.stat().st_size, "create_s": create_s, "extract_s": extract_s,
            "tool": Path(exe).name, "version": _version(exe)}


def _seven_zip_variant(stage: Path, archive: Path, extracted: Path, method: str) -> dict:
    exe = shutil.which("7z") or shutil.which("7zz")
    if exe is None:
        return {"available": False, "reason": "7z-not-installed"}
    if method == "lzma2":
        method_args = ["-m0=lzma2", "-mx=9", "-ms=on"]
    elif method == "ppmd":
        method_args = ["-m0=PPMd", "-mx=9", "-ms=on"]
    else:
        raise ValueError(method)
    started = time.perf_counter()
    cp = subprocess.run([exe, "a", "-t7z", *method_args, str(archive), "."], cwd=stage,
                        check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if cp.returncode != 0:
        return {"available": False, "reason": f"7z-{method}-unsupported"}
    create_s = time.perf_counter() - started
    extracted.mkdir(parents=True)
    started = time.perf_counter()
    subprocess.run([exe, "x", str(archive), f"-o{extracted}", "-y"], check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
    extract_s = time.perf_counter() - started
    return {"available": True, "archive_bytes": archive.stat().st_size, "create_s": create_s, "extract_s": extract_s,
            "tool": Path(exe).name, "version": _version(exe)}


def _zpaq_method(stage: Path, archive: Path, extracted: Path, method: int) -> dict:
    exe = shutil.which("zpaq")
    if exe is None:
        return {"available": False, "reason": "zpaq-not-installed"}
    rels = [path.relative_to(stage).as_posix() for path in B._files(stage)]
    started = time.perf_counter()
    subprocess.run([exe, "a", str(archive), *rels, "-method", str(method)], cwd=stage,
                   check=True, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
    create_s = time.perf_counter() - started
    extracted.mkdir(parents=True)
    started = time.perf_counter()
    subprocess.run([exe, "x", str(archive), "-to", str(extracted)], cwd=stage,
                   check=True, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
    extract_s = time.perf_counter() - started
    return {"available": True, "archive_bytes": archive.stat().st_size, "create_s": create_s, "extract_s": extract_s,
            "tool": Path(exe).name, "version": _version(exe)}


def _specs(outputs: Path):
    return (
        ("cmpct_v030", lambda s, a, e, w: B._cmpct(s, a, e), outputs / "candidate.cmpct", outputs / "cmpct-out"),
        ("zip_deflate9", lambda s, a, e, w: B._zip(s, a, e), outputs / "archive.zip", outputs / "zip-out"),
        ("zstd_1_solid", lambda s, a, e, w: _cli_stream(s, a, e, w, "zstd", 1), outputs / "zstd1.tar.zst", outputs / "zstd1-out"),
        ("zstd_3_solid", lambda s, a, e, w: _cli_stream(s, a, e, w, "zstd", 3), outputs / "zstd3.tar.zst", outputs / "zstd3-out"),
        ("zstd_9_solid", lambda s, a, e, w: _cli_stream(s, a, e, w, "zstd", 9), outputs / "zstd9.tar.zst", outputs / "zstd9-out"),
        ("zstd_19_solid", lambda s, a, e, w: _cli_stream(s, a, e, w, "zstd", 19), outputs / "zstd19.tar.zst", outputs / "zstd19-out"),
        ("gzip_9_solid", lambda s, a, e, w: _python_stream(s, a, e, w, "gzip", 9), outputs / "gzip9.tar.gz", outputs / "gzip9-out"),
        ("bzip2_9_solid", lambda s, a, e, w: _python_stream(s, a, e, w, "bzip2", 9), outputs / "bzip9.tar.bz2", outputs / "bzip9-out"),
        ("xz_6_solid", lambda s, a, e, w: _python_stream(s, a, e, w, "xz", 6), outputs / "xz6.tar.xz", outputs / "xz6-out"),
        ("xz_9_solid", lambda s, a, e, w: _python_stream(s, a, e, w, "xz", 9), outputs / "xz9.tar.xz", outputs / "xz9-out"),
        ("brotli_6_solid", lambda s, a, e, w: _cli_stream(s, a, e, w, "brotli", 6), outputs / "br6.tar.br", outputs / "br6-out"),
        ("brotli_11_solid", lambda s, a, e, w: _cli_stream(s, a, e, w, "brotli", 11), outputs / "br11.tar.br", outputs / "br11-out"),
        ("lz4_hc12_solid", lambda s, a, e, w: _cli_stream(s, a, e, w, "lz4", 12), outputs / "lz4hc.tar.lz4", outputs / "lz4hc-out"),
        ("lzip_9_solid", lambda s, a, e, w: _cli_stream(s, a, e, w, "lzip", 9), outputs / "lzip9.tar.lz", outputs / "lzip9-out"),
        ("7z_lzma2_max_solid", lambda s, a, e, w: _seven_zip_variant(s, a, e, "lzma2"), outputs / "lzma2.7z", outputs / "lzma2-out"),
        ("7z_ppmd_max_solid", lambda s, a, e, w: _seven_zip_variant(s, a, e, "ppmd"), outputs / "ppmd.7z", outputs / "ppmd-out"),
        ("zpaq_method3", lambda s, a, e, w: _zpaq_method(s, a, e, 3), outputs / "method3.zpaq", outputs / "zpaq3-out"),
        ("zpaq_method5", lambda s, a, e, w: _zpaq_method(s, a, e, 5), outputs / "method5.zpaq", outputs / "zpaq5-out"),
    )


def _one(label: str, source: Path, work: Path) -> dict:
    expected_tree = B._tree(source)
    with tempfile.TemporaryDirectory(prefix="cmpct-v030-landscape-", dir=work) as td:
        td_path = Path(td)
        stage = B._normalized_stage(source, td_path)
        outputs = td_path / "outputs"
        outputs.mkdir()
        formats = {}
        for name, function, archive, extracted in _specs(outputs):
            try:
                result = function(stage, archive, extracted, outputs)
            except (subprocess.CalledProcessError, OSError, RuntimeError, ValueError) as exc:
                result = {"available": False, "reason": f"error:{type(exc).__name__}:{exc}"[:300]}
            if result.get("available"):
                B._verify_extracted(extracted, expected_tree, name)
                result["tree_verified"] = True
            formats[name] = result
        return {"label": label, "tree_sha256": expected_tree, "formats": formats}


def _pareto(rows: list[dict], names: list[str]) -> dict[str, dict]:
    points = {}
    for name in names:
        measured = [row["formats"][name] for row in rows if row["formats"][name].get("available")]
        if len(measured) != len(rows):
            continue
        points[name] = {
            "archive_bytes": sum(int(x["archive_bytes"]) for x in measured),
            "create_s": sum(float(x["create_s"]) for x in measured),
            "extract_s": sum(float(x["extract_s"]) for x in measured),
        }
    for name, point in points.items():
        dominated_by = []
        for other, op in points.items():
            if other == name:
                continue
            no_worse = op["archive_bytes"] <= point["archive_bytes"] and op["create_s"] <= point["create_s"]
            strict = op["archive_bytes"] < point["archive_bytes"] or op["create_s"] < point["create_s"]
            if no_worse and strict:
                dominated_by.append(other)
        point["size_create_pareto"] = not dominated_by
        point["dominated_by"] = sorted(dominated_by)
    return points


def _markdown(result: dict) -> str:
    lines = [
        "# CMPCT v0.30 broad compression landscape",
        "",
        "> Reference-only evidence. ZIP/Deflate-9 and solid Zstd-19 remain the v0.30 release comparators.",
        "",
        f"Candidate: `{result['candidate_sha']}`",
        "",
        "## 15-workload aggregate",
        "",
        "| Format | Bytes | Create s | Extract s | Size/create Pareto |",
        "|---|---:|---:|---:|:---:|",
    ]
    ranked = sorted(result["aggregate"].items(), key=lambda kv: (kv[1]["archive_bytes"], kv[1]["create_s"]))
    for name, row in ranked:
        lines.append(f"| `{name}` | {row['archive_bytes']:,} | {row['create_s']:.3f} | {row['extract_s']:.3f} | {'yes' if row['size_create_pareto'] else 'no'} |")
    lines += ["", "## Per-workload size/create results", ""]
    names = list(result["formats"])
    for row in result["rows"]:
        lines += [f"### `{row['label']}`", "", "| Format | Bytes | Create s | Extract s |", "|---|---:|---:|---:|"]
        available = [(name, row["formats"][name]) for name in names if row["formats"][name].get("available")]
        for name, item in sorted(available, key=lambda kv: (int(kv[1]["archive_bytes"]), float(kv[1]["create_s"]))):
            lines.append(f"| `{name}` | {int(item['archive_bytes']):,} | {float(item['create_s']):.3f} | {float(item['extract_s']):.3f} |")
        lines.append("")
    return "\n".join(lines) + "\n"


def run(work_root: Path, candidate_sha: str) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)
    accepted = GENERAL._accepted_v029_rows()
    neutral = GENERAL.V029._load(GENERAL.V029.ROOT / "benchmarks" / "neutral_hostile_corpus_v1.py", "cmpct_v030_landscape_neutral")
    hostile = GENERAL.V029._load(GENERAL.V029.ROOT / "benchmarks" / "resemblance_hostile_corpus_v1.py", "cmpct_v030_landscape_hostile")
    repair = GENERAL.V029._load(GENERAL.V029.REPAIR_PATH, "cmpct_v030_landscape_repair")
    repair.install_generation_hooks(neutral)
    rows = []
    for suite, builder, root in (("neutral_hostile_v1", neutral, work_root / "neutral"), ("resemblance_hostile_v1", hostile, work_root / "hostile")):
        builder.build(root)
        if suite == "neutral_hostile_v1":
            repair.normalize_root(root)
        for workload in sorted(path for path in root.iterdir() if path.is_dir()):
            key = (suite, workload.name)
            if B._tree(workload) != accepted[key]["tree_sha256"]:
                raise RuntimeError(f"landscape source drift: {suite}/{workload.name}")
            row = _one(f"{suite}/{workload.name}", workload, work_root)
            row["suite"] = suite
            row["name"] = workload.name
            rows.append(row)
            print(json.dumps({"label": row["label"], "complete": sum(1 for x in row["formats"].values() if x.get("available"))}), flush=True)

    names = [name for name, *_ in _specs(Path("unused"))]
    aggregate = _pareto(rows, names)
    return {
        "schema": "cmpct-v030-compression-landscape-v1",
        "candidate_sha": candidate_sha,
        "contract": {
            "workloads": 15,
            "release_gate_impact": "none-reference-only",
            "release_comparators": ["zip_deflate9", "zstd_19_solid"],
            "all_available_rows_tree_verified": True,
            "solid_stream_note": "tar construction and extraction are charged; no selective-read equivalence claim",
        },
        "formats": names,
        "rows": rows,
        "aggregate": aggregate,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-landscape-work"))
    parser.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-compression-landscape.json"))
    parser.add_argument("--markdown", type=Path, default=Path("benchmark-artifacts/v030-compression-landscape.md"))
    parser.add_argument("--candidate-sha", default="unknown")
    args = parser.parse_args()
    result = run(args.work_root, args.candidate_sha)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    args.markdown.write_text(_markdown(result), encoding="utf-8")
    print(json.dumps({"candidate_sha": result["candidate_sha"], "aggregate": result["aggregate"]}, indent=2), flush=True)


if __name__ == "__main__":
    main()
