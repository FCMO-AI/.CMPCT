#!/usr/bin/env python3
from __future__ import annotations

"""Symmetric CMPCT competitive benchmark matrix.

This harness complements ``zip_parity_bench.py``. It measures only like-for-like archive operations
and preserves every competitor that is actually installed on the runner. Missing external tools are
reported rather than silently dropped from the result schema.

Competitors:
- CMPCT revision-24 reference CLI (create/extract) and native CLI when available (list/read);
- ZIP/Deflate through Python's mature ``zipfile`` implementation;
- 7z/LZMA2 through ``7z``/``7zz`` when installed;
- tar+zstd through system ``tar`` + ``zstd`` when installed.

The output records every raw repetition, tool version, archive size and exact operation semantics.
Creation is never included inside extraction/list/read timings. Fresh-process operations stay
fresh-process for every format.
"""

import argparse
import hashlib
import json
import os
import platform
import shutil
import statistics
import subprocess
import sys
import tempfile
import time
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
NATIVE = ROOT / "native/cmpct-core/target/release/cmpct-native"
ZIP_HELPER = HERE / "zip_cli_helper.py"


def _run(cmd: list[str], *, cwd: Path | None = None, stdout=None) -> subprocess.CompletedProcess:
    return subprocess.run(
        cmd,
        cwd=cwd,
        stdout=subprocess.DEVNULL if stdout is None else stdout,
        stderr=subprocess.PIPE,
        check=False,
    )


def _must(cmd: list[str], *, cwd: Path | None = None, stdout=None) -> None:
    result = _run(cmd, cwd=cwd, stdout=stdout)
    if result.returncode:
        raise RuntimeError(f"command failed ({result.returncode}): {cmd!r}\n{result.stderr.decode(errors='replace')}")


def _tool_version(cmd: list[str]) -> str | None:
    if shutil.which(cmd[0]) is None:
        return None
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, check=False)
    if result.returncode:
        return None
    return result.stdout.splitlines()[0].strip() if result.stdout else "available"


def _timed(fn, reps: int) -> dict:
    raw = []
    for _ in range(reps):
        t0 = time.perf_counter_ns()
        fn()
        raw.append((time.perf_counter_ns() - t0) / 1_000_000_000)
    return {
        "raw_s": raw,
        "median_s": statistics.median(raw),
        "min_s": min(raw),
        "max_s": max(raw),
    }


def _tree_hash(root: Path) -> str:
    h = hashlib.sha256()
    for path in sorted(p for p in root.rglob("*") if p.is_file()):
        rel = path.relative_to(root).as_posix().encode()
        data = path.read_bytes()
        h.update(len(rel).to_bytes(4, "little"))
        h.update(rel)
        h.update(len(data).to_bytes(8, "little"))
        h.update(data)
    return h.hexdigest()


def _logical_bytes(root: Path) -> int:
    return sum(p.stat().st_size for p in root.rglob("*") if p.is_file())


def _largest_member(root: Path) -> tuple[str, bytes]:
    files = [p for p in root.rglob("*") if p.is_file()]
    if not files:
        raise RuntimeError("benchmark corpus contains no regular files")
    path = max(files, key=lambda p: p.stat().st_size)
    return path.relative_to(root).as_posix(), path.read_bytes()


def _prepare_corpus(dst: Path, seed: int, mib: int) -> None:
    # Deterministic mixed corpus: compressible source/text, repeated binary structure, already-
    # compressed-like pseudo-random data, and many tiny files. It is intentionally not tuned to CMPCT.
    import random

    rng = random.Random(seed)
    (dst / "src").mkdir(parents=True)
    (dst / "tiny").mkdir()
    text = ("def transform(value):\n    return (value * 2654435761) & 0xffffffff\n" * 4096).encode()
    (dst / "src/module.py").write_bytes(text)
    for i in range(512):
        (dst / "tiny" / f"item-{i:04d}.txt").write_text(f"row={i}\nkind={i % 17}\n")
    block = bytes((i * 29 + i // 7) & 0xFF for i in range(64 * 1024))
    target = max(1, mib) * 1024 * 1024
    with (dst / "structured.bin").open("wb") as f:
        while f.tell() < target:
            f.write(block[: min(len(block), target - f.tell())])
    random_bytes = bytearray(target // 2)
    for i in range(len(random_bytes)):
        random_bytes[i] = rng.randrange(256)
    (dst / "random.bin").write_bytes(random_bytes)


def _reset_dir(path: Path) -> None:
    shutil.rmtree(path, ignore_errors=True)
    path.mkdir(parents=True)


def _cmpct(src: Path, work: Path, reps: int) -> dict:
    archive = work / "data.cmpct"
    dest = work / "cmpct-out"
    member, expected = _largest_member(src)
    env = os.environ.copy()

    def create():
        archive.unlink(missing_ok=True)
        _must([sys.executable, "-m", "cmpct", "create", str(src), str(archive)])

    create_t = _timed(create, reps)
    create()

    def extract():
        _reset_dir(dest)
        _must([sys.executable, "-m", "cmpct", "extract", str(archive), str(dest), "--no-metadata"])

    extract_t = _timed(extract, reps)
    extract()
    assert _tree_hash(dest) == _tree_hash(src)

    result = {
        "archive_bytes": archive.stat().st_size,
        "create": create_t,
        "extract": extract_t,
        "member": member,
    }

    if NATIVE.exists():
        def list_native():
            _must([str(NATIVE), "list", str(archive)])

        def read_native():
            proc = subprocess.run(
                [str(NATIVE), "read", str(archive), member],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )
            if proc.returncode:
                raise RuntimeError(proc.stderr.decode(errors="replace"))
            if proc.stdout != expected:
                raise RuntimeError("cmpct-native member output differs from source")

        result["list"] = _timed(list_native, reps)
        result["read_member"] = _timed(read_native, reps)
        result["read_surface"] = "cmpct-native fresh process"
    else:
        result["native_unavailable"] = True
    return result


def _zip(src: Path, work: Path, reps: int) -> dict:
    archive = work / "data.zip"
    dest = work / "zip-out"
    member, expected = _largest_member(src)

    def create():
        archive.unlink(missing_ok=True)
        _must([sys.executable, str(ZIP_HELPER), "create", str(src), str(archive)])

    create_t = _timed(create, reps)
    create()

    def extract():
        _reset_dir(dest)
        _must([sys.executable, str(ZIP_HELPER), "extract", str(archive), str(dest)])

    extract_t = _timed(extract, reps)
    extract()
    assert _tree_hash(dest) == _tree_hash(src)

    def list_zip():
        code = "import sys,zipfile; z=zipfile.ZipFile(sys.argv[1]); [i.filename for i in z.infolist()]"
        _must([sys.executable, "-c", code, str(archive)])

    def read_zip():
        code = "import sys,zipfile; sys.stdout.buffer.write(zipfile.ZipFile(sys.argv[1]).read(sys.argv[2]))"
        proc = subprocess.run(
            [sys.executable, "-c", code, str(archive), member],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        if proc.returncode:
            raise RuntimeError(proc.stderr.decode(errors="replace"))
        if proc.stdout != expected:
            raise RuntimeError("ZIP member output differs from source")

    return {
        "archive_bytes": archive.stat().st_size,
        "create": create_t,
        "extract": extract_t,
        "list": _timed(list_zip, reps),
        "read_member": _timed(read_zip, reps),
        "member": member,
        "read_surface": "Python zipfile fresh process",
    }


def _seven_zip(src: Path, work: Path, reps: int, exe: str) -> dict:
    archive = work / "data.7z"
    dest = work / "7z-out"
    member, expected = _largest_member(src)

    def create():
        archive.unlink(missing_ok=True)
        _must([exe, "a", "-t7z", "-mx=5", str(archive), "."], cwd=src)

    create_t = _timed(create, reps)
    create()

    def extract():
        _reset_dir(dest)
        _must([exe, "x", "-y", f"-o{dest}", str(archive)])

    extract_t = _timed(extract, reps)
    extract()
    assert _tree_hash(dest) == _tree_hash(src)

    def list_7z():
        _must([exe, "l", "-slt", str(archive)])

    def read_7z():
        proc = subprocess.run(
            [exe, "x", "-so", str(archive), member],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        if proc.returncode:
            raise RuntimeError(proc.stderr.decode(errors="replace"))
        if proc.stdout != expected:
            raise RuntimeError("7z member output differs from source")

    return {
        "archive_bytes": archive.stat().st_size,
        "create": create_t,
        "extract": extract_t,
        "list": _timed(list_7z, reps),
        "read_member": _timed(read_7z, reps),
        "member": member,
        "read_surface": f"{exe} fresh process",
    }


def _tar_zstd(src: Path, work: Path, reps: int) -> dict:
    archive = work / "data.tar.zst"
    dest = work / "tarzstd-out"
    member, _ = _largest_member(src)

    def create():
        archive.unlink(missing_ok=True)
        # Use one external pipeline per repetition. The shell is avoided so argv/process semantics are
        # explicit; tar streams to zstd exactly once.
        tar = subprocess.Popen(["tar", "-C", str(src), "-cf", "-", "."], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        zstd = subprocess.run(["zstd", "-q", "-3", "-o", str(archive)], stdin=tar.stdout, stderr=subprocess.PIPE, check=False)
        assert tar.stdout is not None
        tar.stdout.close()
        tar_rc = tar.wait()
        if tar_rc or zstd.returncode:
            raise RuntimeError("tar+zstd creation failed")

    create_t = _timed(create, reps)
    create()

    def extract():
        _reset_dir(dest)
        zstd = subprocess.Popen(["zstd", "-q", "-dc", str(archive)], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        tar = subprocess.run(["tar", "-C", str(dest), "-xf", "-"], stdin=zstd.stdout, stderr=subprocess.PIPE, check=False)
        assert zstd.stdout is not None
        zstd.stdout.close()
        zstd_rc = zstd.wait()
        if zstd_rc or tar.returncode:
            raise RuntimeError("tar+zstd extraction failed")

    extract_t = _timed(extract, reps)
    extract()
    assert _tree_hash(dest) == _tree_hash(src)
    return {
        "archive_bytes": archive.stat().st_size,
        "create": create_t,
        "extract": extract_t,
        "member": member,
        "selective_access": "not measured: tar+zstd requires stream traversal and is not semantically symmetric",
    }


def run(reps: int, seed: int, mib: int, output: Path) -> dict:
    with tempfile.TemporaryDirectory(prefix="cmpct-competitive-") as td:
        work = Path(td)
        src = work / "corpus"
        src.mkdir()
        _prepare_corpus(src, seed, mib)

        seven = shutil.which("7zz") or shutil.which("7z")
        tools = {
            "python": sys.version.split()[0],
            "cmpct_native": str(NATIVE) if NATIVE.exists() else None,
            "7z": _tool_version([seven, "i"]) if seven else None,
            "tar": _tool_version(["tar", "--version"]),
            "zstd": _tool_version(["zstd", "--version"]),
        }
        result = {
            "schema": "cmpct-competitive-matrix-v1",
            "source_commit_env": os.environ.get("GITHUB_SHA"),
            "format_revision": 24,
            "environment": {
                "platform": platform.platform(),
                "machine": platform.machine(),
                "python": sys.version,
                "tools": tools,
            },
            "corpus": {
                "generator": "competitive_matrix_bench.py deterministic mixed v1",
                "seed": seed,
                "target_structured_mib": mib,
                "logical_bytes": _logical_bytes(src),
                "tree_sha256": _tree_hash(src),
            },
            "repetitions": reps,
            "timing": "fresh process for every CLI operation; warm ordinary filesystem cache; creation excluded from read/extract timing",
            "semantics": {
                "cmpct_extract": "normal CMPCT extraction with metadata restoration disabled for byte-tree parity",
                "zip_extract": "Python zipfile extraction; regular-file byte-tree parity",
                "seven_zip_extract": "7z extraction; regular-file byte-tree parity",
                "tar_zstd_extract": "streaming tar+zstd extraction; regular-file byte-tree parity",
                "selective_reads": "measured only for random-access formats; tar+zstd is explicitly excluded",
            },
            "formats": {},
            "unavailable": [],
        }
        result["formats"]["cmpct"] = _cmpct(src, work, reps)
        result["formats"]["zip_deflate"] = _zip(src, work, reps)
        if seven:
            result["formats"]["7z_lzma2"] = _seven_zip(src, work, reps, seven)
        else:
            result["unavailable"].append("7z_lzma2: install 7zz or 7z")
        if shutil.which("tar") and shutil.which("zstd"):
            result["formats"]["tar_zstd"] = _tar_zstd(src, work, reps)
        else:
            result["unavailable"].append("tar_zstd: install tar and zstd")

        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(result, indent=2) + "\n")
        return result


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--reps", type=int, default=int(os.environ.get("CMPCT_COMPETITIVE_REPS", "5")))
    ap.add_argument("--seed", type=int, default=2401)
    ap.add_argument("--mib", type=int, default=8)
    ap.add_argument("--output", type=Path, default=ROOT / "benchmarks/history/competitive-latest.json")
    args = ap.parse_args()
    if args.reps < 3:
        raise SystemExit("at least three repetitions are required")
    result = run(args.reps, args.seed, args.mib, args.output)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
