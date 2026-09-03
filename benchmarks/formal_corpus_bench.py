#!/usr/bin/env python3
from __future__ import annotations

"""Benchmark CMPCT v0.29 on established public lossless-compression corpora.

This harness deliberately separates *corpus authority* from *compressor execution*.  The workflow
that invokes it downloads and validates canonical corpus bytes; this file only consumes an immutable
manifest and measures real container output, wall time, peak RSS, and lossless round trips.

The result is intentionally not collapsed into a single score. Compression ratio, encode speed,
decode speed, memory and archive semantics are different axes; hiding them behind one weighted number
would make it too easy to tune the benchmark rather than improve the format.
"""

import argparse
import hashlib
import json
import os
import platform
import shlex
import shutil
import statistics
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any


TIME_BIN = Path("/usr/bin/time")
DEFAULT_TIMEOUT = int(os.environ.get("CMPCT_FORMAL_TIMEOUT", "3600"))


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def tree_manifest(root: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for p in sorted(x for x in root.rglob("*") if x.is_file()):
        rows.append({
            "path": p.relative_to(root).as_posix(),
            "bytes": p.stat().st_size,
            "sha256": sha256_file(p),
        })
    return rows


def logical_bytes(root: Path) -> int:
    return sum(row["bytes"] for row in tree_manifest(root))


def checked_tool_version(argv: list[str]) -> str | None:
    if shutil.which(argv[0]) is None:
        return None
    try:
        p = subprocess.run(argv, check=False, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                           text=True, timeout=20)
        return (p.stdout or "").strip().splitlines()[0][:300]
    except Exception as exc:  # pragma: no cover - environment reporting must never kill a benchmark.
        return f"version-query-failed: {exc}"


def timed_run(
    argv: list[str],
    *,
    cwd: Path | None = None,
    stdout_path: Path | None = None,
    capture_stdout: bool = False,
    env: dict[str, str] | None = None,
    timeout: int = DEFAULT_TIMEOUT,
) -> dict[str, Any]:
    """Run one compressor/decompressor and collect GNU-time wall/RSS evidence.

    Footnote: timing the actual CLI boundary, instead of importing competitors into Python, makes
    startup, container writing, checksum work and normal command-line behavior part of the measurement.
    That is exactly what a user pays when replacing ZIP with CMPCT.
    """
    if not TIME_BIN.exists():
        raise RuntimeError("/usr/bin/time is required for formal benchmark telemetry")
    with tempfile.NamedTemporaryFile(prefix="cmpct-formal-time-", delete=False) as tf:
        timing_path = Path(tf.name)
    out_handle = None
    try:
        if stdout_path is not None:
            stdout_path.parent.mkdir(parents=True, exist_ok=True)
            out_handle = stdout_path.open("wb")
            stdout_target: Any = out_handle
        elif capture_stdout:
            stdout_target = subprocess.PIPE
        else:
            stdout_target = subprocess.DEVNULL
        full = [str(TIME_BIN), "-f", "%e %M", "-o", str(timing_path), *argv]
        t0 = time.perf_counter()
        p = subprocess.run(
            full,
            cwd=str(cwd) if cwd else None,
            env=env,
            stdout=stdout_target,
            stderr=subprocess.PIPE,
            timeout=timeout,
        )
        python_wall = time.perf_counter() - t0
        timing = timing_path.read_text().strip().split()
        wall_s = float(timing[0]) if len(timing) >= 1 else python_wall
        peak_rss_kib = int(timing[1]) if len(timing) >= 2 else None
        stdout = p.stdout.decode("utf-8", "replace") if capture_stdout and p.stdout is not None else ""
        stderr = p.stderr.decode("utf-8", "replace") if p.stderr else ""
        if p.returncode:
            raise RuntimeError(
                f"command failed rc={p.returncode}: {shlex.join(argv)}\n{stderr[-4000:]}"
            )
        return {
            "wall_s": wall_s,
            "python_wall_s": python_wall,
            "peak_rss_kib": peak_rss_kib,
            "stdout": stdout,
            "stderr_tail": stderr[-2000:],
        }
    finally:
        if out_handle is not None:
            out_handle.close()
        timing_path.unlink(missing_ok=True)


def shell_pipeline(script: str) -> list[str]:
    return ["bash", "-o", "pipefail", "-lc", script]


def deterministic_tar_pipeline(src: Path, compressor: str, archive: Path) -> list[str]:
    qsrc = shlex.quote(str(src))
    qout = shlex.quote(str(archive))
    # Footnote: tar metadata is normalized so tar-based competitors are not charged for random runner
    # timestamps/ownership. CMPCT is likewise run in reproducible mode. The archive bytes therefore
    # measure compression/container policy rather than whichever UID GitHub happened to allocate.
    tar = f"tar --sort=name --mtime='@0' --owner=0 --group=0 --numeric-owner -C {qsrc} -cf - ."
    return shell_pipeline(f"{tar} | {compressor} > {qout}")


def deterministic_tar_extract(archive: Path, decompressor: str, dest: Path) -> list[str]:
    qarc = shlex.quote(str(archive))
    qdest = shlex.quote(str(dest))
    return shell_pipeline(f"{decompressor} < {qarc} | tar -C {qdest} -xf -")


def assert_roundtrip(src: Path, dest: Path, label: str) -> None:
    expected = tree_manifest(src)
    actual = tree_manifest(dest)
    if expected != actual:
        raise RuntimeError(f"lossless round-trip mismatch for {label}")


def run_cmpct(src: Path, out: Path, extract: Path, env: dict[str, str]) -> dict[str, Any]:
    create = timed_run(
        [sys.executable, "-m", "cmpct", "create", str(src), str(out), "--workers", "1", "--reproducible"],
        capture_stdout=True,
        env=env,
    )
    try:
        build = json.loads(create["stdout"])
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"CMPCT create did not emit build JSON: {create['stdout'][-2000:]}") from exc
    verify = timed_run([sys.executable, "-m", "cmpct", "verify", str(out)], env=env)
    extract.mkdir(parents=True, exist_ok=True)
    decode = timed_run(
        [sys.executable, "-m", "cmpct", "extract", str(out), str(extract), "--no-metadata"], env=env
    )
    assert_roundtrip(src, extract, "cmpct")
    return {
        "bytes": out.stat().st_size,
        "create": create,
        "extract": decode,
        "verify": verify,
        "cmpct_build": build,
    }


def run_zip(src: Path, out: Path, extract: Path) -> dict[str, Any]:
    # `-X` removes host-specific extra fields. `.` keeps path semantics while avoiding an arbitrary
    # temporary root directory name in the archive.
    create = timed_run(["zip", "-q", "-9", "-X", "-r", str(out), "."], cwd=src)
    extract.mkdir(parents=True, exist_ok=True)
    decode = timed_run(["unzip", "-qq", str(out), "-d", str(extract)])
    assert_roundtrip(src, extract, "zip")
    return {"bytes": out.stat().st_size, "create": create, "extract": decode}


def run_7z(src: Path, out: Path, extract: Path) -> dict[str, Any]:
    create = timed_run([
        "7z", "a", "-bd", "-bso0", "-bsp0", "-t7z", "-mx=9", "-m0=lzma2", "-ms=on", str(out), "."
    ], cwd=src)
    extract.mkdir(parents=True, exist_ok=True)
    decode = timed_run(["7z", "x", "-bd", "-bso0", "-bsp0", "-y", f"-o{extract}", str(out)])
    assert_roundtrip(src, extract, "7z")
    return {"bytes": out.stat().st_size, "create": create, "extract": decode}


def single_file(src: Path) -> Path | None:
    files = [p for p in src.rglob("*") if p.is_file()]
    return files[0] if len(files) == 1 else None


def run_stream_or_tar(
    name: str,
    src: Path,
    out: Path,
    extract: Path,
    *,
    compress_single: list[str],
    decompress_single: list[str],
    tar_compressor: str,
    tar_decompressor: str,
) -> dict[str, Any]:
    one = single_file(src)
    extract.mkdir(parents=True, exist_ok=True)
    if one is not None:
        create_argv = [x.format(input=str(one), output=str(out)) for x in compress_single]
        if "{stdout}" in create_argv:
            raise AssertionError("internal benchmark specification error")
        # gzip/bzip2/xz use stdout in order to suppress source-name/timestamp metadata where possible.
        if name in {"gzip-9", "bzip2-9", "xz-9e"}:
            create = timed_run(create_argv, stdout_path=out)
        else:
            create = timed_run(create_argv)
        restored = extract / one.name
        dec_argv = [x.format(input=str(out), output=str(restored)) for x in decompress_single]
        if name in {"gzip-9", "bzip2-9", "xz-9e"}:
            decode = timed_run(dec_argv, stdout_path=restored)
        else:
            decode = timed_run(dec_argv)
    else:
        create = timed_run(deterministic_tar_pipeline(src, tar_compressor, out))
        decode = timed_run(deterministic_tar_extract(out, tar_decompressor, extract))
    assert_roundtrip(src, extract, name)
    return {"bytes": out.stat().st_size, "create": create, "extract": decode}


def compressor_runners() -> list[tuple[str, Any, str]]:
    return [
        ("cmpct-v0.29", run_cmpct, "cmpct"),
        ("zip-deflate-9", run_zip, "zip"),
        ("7z-lzma2-9", run_7z, "7z"),
        ("zstd-3", None, "zstd"),
        ("zstd-19", None, "zstd"),
        ("xz-9e", None, "xz"),
        ("gzip-9", None, "gzip"),
        ("bzip2-9", None, "bzip2"),
    ]


def run_external(name: str, src: Path, out: Path, extract: Path) -> dict[str, Any]:
    if name == "zstd-3":
        return run_stream_or_tar(
            name, src, out, extract,
            compress_single=["zstd", "-q", "-3", "-f", "{input}", "-o", "{output}"],
            decompress_single=["zstd", "-q", "-d", "-f", "{input}", "-o", "{output}"],
            tar_compressor="zstd -q -3 -c", tar_decompressor="zstd -q -d -c",
        )
    if name == "zstd-19":
        return run_stream_or_tar(
            name, src, out, extract,
            compress_single=["zstd", "-q", "-19", "-f", "{input}", "-o", "{output}"],
            decompress_single=["zstd", "-q", "-d", "-f", "{input}", "-o", "{output}"],
            tar_compressor="zstd -q -19 -c", tar_decompressor="zstd -q -d -c",
        )
    if name == "xz-9e":
        return run_stream_or_tar(
            name, src, out, extract,
            compress_single=["xz", "-9e", "-c", "{input}"],
            decompress_single=["xz", "-d", "-c", "{input}"],
            tar_compressor="xz -9e -c", tar_decompressor="xz -d -c",
        )
    if name == "gzip-9":
        return run_stream_or_tar(
            name, src, out, extract,
            compress_single=["gzip", "-9", "-n", "-c", "{input}"],
            decompress_single=["gzip", "-d", "-c", "{input}"],
            tar_compressor="gzip -9 -n -c", tar_decompressor="gzip -d -c",
        )
    if name == "bzip2-9":
        return run_stream_or_tar(
            name, src, out, extract,
            compress_single=["bzip2", "-9", "-c", "{input}"],
            decompress_single=["bzip2", "-d", "-c", "{input}"],
            tar_compressor="bzip2 -9 -c", tar_decompressor="bzip2 -d -c",
        )
    raise KeyError(name)


def compact_telemetry(row: dict[str, Any], logical: int) -> dict[str, Any]:
    out = {
        "bytes": row["bytes"],
        "ratio": row["bytes"] / logical if logical else None,
        "bits_per_input_byte": (row["bytes"] * 8 / logical) if logical else None,
        "create_s": row["create"]["wall_s"],
        "extract_s": row["extract"]["wall_s"],
        "create_mib_s": (logical / (1024 ** 2)) / row["create"]["wall_s"] if row["create"]["wall_s"] else None,
        "extract_mib_s": (logical / (1024 ** 2)) / row["extract"]["wall_s"] if row["extract"]["wall_s"] else None,
        "create_peak_rss_kib": row["create"]["peak_rss_kib"],
        "extract_peak_rss_kib": row["extract"]["peak_rss_kib"],
    }
    if "cmpct_build" in row:
        out["cmpct_build"] = row["cmpct_build"]
        out["verify_s"] = row["verify"]["wall_s"]
    return out


def markdown_summary(result: dict[str, Any]) -> str:
    lines = [
        "# CMPCT v0.29 — formal corpus benchmark",
        "",
        f"Commit: `{result['provenance']['git_sha']}`",
        "",
        "Container-inclusive sizes are reported. For multi-file corpora, stream compressors are measured as deterministic tar + compressor; native ZIP/7z/CMPCT archive the tree directly.",
        "",
    ]
    for corpus, entry in result["corpora"].items():
        lines += [
            f"## {corpus}",
            "",
            f"Logical bytes: **{entry['logical_bytes']:,}**; files: **{entry['files']}**",
            "",
            "| compressor | bytes | ratio | create MiB/s | extract MiB/s | create RSS MiB |",
            "|---|---:|---:|---:|---:|---:|",
        ]
        ranked = sorted(entry["results"].items(), key=lambda kv: kv[1]["bytes"])
        for name, row in ranked:
            lines.append(
                f"| {name} | {row['bytes']:,} | {row['ratio']:.4f} | "
                f"{row['create_mib_s']:.2f} | {row['extract_mib_s']:.2f} | "
                f"{row['create_peak_rss_kib'] / 1024:.1f} |"
            )
        lines.append("")
    return "\n".join(lines)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("manifest", type=Path)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--only", action="append", default=[], help="optional corpus-name filter")
    args = ap.parse_args()

    manifest = json.loads(args.manifest.read_text())
    args.out.mkdir(parents=True, exist_ok=True)
    work = args.out / "work"
    shutil.rmtree(work, ignore_errors=True)
    work.mkdir()

    tools = {
        "python": platform.python_version(),
        "zip": checked_tool_version(["zip", "-v"]),
        "7z": checked_tool_version(["7z", "i"]),
        "zstd": checked_tool_version(["zstd", "--version"]),
        "xz": checked_tool_version(["xz", "--version"]),
        "gzip": checked_tool_version(["gzip", "--version"]),
        "bzip2": checked_tool_version(["bzip2", "--version"]),
    }
    git_sha = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    result: dict[str, Any] = {
        "schema": "cmpct-formal-corpus-v1",
        "provenance": {
            "git_sha": git_sha,
            "platform": platform.platform(),
            "machine": platform.machine(),
            "processor": platform.processor(),
            "cpu_count": os.cpu_count(),
            "tools": tools,
            "timing": "single measured CLI pass; GNU time wall + max RSS; same runner",
            "cmpct_profile": "v0.29 CLI, workers=1, reproducible metadata",
        },
        "manifest_source": manifest.get("source_notes", []),
        "corpora": {},
    }

    env = os.environ.copy()
    # Footnote: keep the shipping deflate-reuse threshold explicit in the evidence. A hidden benchmark
    # environment override would make the result impossible to reproduce from an ordinary v0.29 CLI.
    env.setdefault("CMPCT_DEFLATE_REUSE_MIN", "65536")

    for item in manifest["corpora"]:
        name = item["name"]
        if args.only and name not in args.only:
            continue
        src = Path(item["path"]).resolve()
        if not src.is_dir():
            raise RuntimeError(f"missing corpus directory: {src}")
        src_manifest = tree_manifest(src)
        logical = sum(x["bytes"] for x in src_manifest)
        if item.get("expected_logical_bytes") is not None and logical != int(item["expected_logical_bytes"]):
            raise RuntimeError(f"logical-byte mismatch for {name}: {logical} != {item['expected_logical_bytes']}")
        print(f"=== FORMAL CORPUS {name}: {logical:,} bytes / {len(src_manifest)} files ===", flush=True)
        entry = {
            "authority": item.get("authority"),
            "mode": item.get("mode", "canonical"),
            "logical_bytes": logical,
            "files": len(src_manifest),
            "source_manifest": src_manifest,
            "results": {},
        }
        result["corpora"][name] = entry

        for comp_name, runner, required_tool in compressor_runners():
            if required_tool != "cmpct" and shutil.which(required_tool) is None:
                print(f"SKIP {comp_name}: missing {required_tool}", flush=True)
                continue
            suffix = {
                "cmpct-v0.29": ".cmpct", "zip-deflate-9": ".zip", "7z-lzma2-9": ".7z",
                "zstd-3": ".zst", "zstd-19": ".zst", "xz-9e": ".xz",
                "gzip-9": ".gz", "bzip2-9": ".bz2",
            }[comp_name]
            archive = work / f"{name}-{comp_name}{suffix}"
            extracted = work / f"extract-{name}-{comp_name}"
            shutil.rmtree(extracted, ignore_errors=True)
            archive.unlink(missing_ok=True)
            print(f"  -> {comp_name}", flush=True)
            try:
                if comp_name == "cmpct-v0.29":
                    raw = run_cmpct(src, archive, extracted, env)
                elif runner is not None:
                    raw = runner(src, archive, extracted)
                else:
                    raw = run_external(comp_name, src, archive, extracted)
                entry["results"][comp_name] = compact_telemetry(raw, logical)
            finally:
                # Archives can be hundreds of MB each on enwik9. Keep only measurements so the job
                # never needs disk proportional to (corpus size × compressor count).
                archive.unlink(missing_ok=True)
                shutil.rmtree(extracted, ignore_errors=True)
            args.out.joinpath("formal-corpus.partial.json").write_text(json.dumps(result, indent=2))

    args.out.joinpath("formal-corpus.json").write_text(json.dumps(result, indent=2))
    args.out.joinpath("formal-corpus.md").write_text(markdown_summary(result))
    print(markdown_summary(result))


if __name__ == "__main__":
    main()
