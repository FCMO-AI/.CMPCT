#!/usr/bin/env python3
from __future__ import annotations

"""Cross-version formal-corpus benchmark for CMPCT v0.29 and the v0.30 authoritative candidate.

The corpus acquisition lives in CI; this harness only consumes already-validated bytes.  It pins the
actual v0.29/v0.30 interpreters through environment variables so both engines see the exact same source
tree on the exact same runner.  Results remain multi-axis: bytes, ratio, wall time, throughput, memory,
verify time, and byte-for-byte round-trip integrity are all kept instead of collapsed into one score.
"""

import argparse
import hashlib
import json
import os
import shlex
import shutil
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Any

TIME_BIN = "/usr/bin/time"


def tree_manifest(root: Path) -> list[tuple[str, int, str]]:
    rows = []
    for p in sorted(x for x in root.rglob("*") if x.is_file()):
        h = hashlib.sha256()
        with p.open("rb") as fh:
            for block in iter(lambda: fh.read(1024 * 1024), b""):
                h.update(block)
        rows.append((p.relative_to(root).as_posix(), p.stat().st_size, h.hexdigest()))
    return rows


def logical_bytes(root: Path) -> int:
    return sum(row[1] for row in tree_manifest(root))


def timed(argv: list[str], *, cwd: Path | None = None, stdout_path: Path | None = None) -> dict[str, Any]:
    # Footnote: GNU time wraps the actual CLI process boundary, so interpreter startup, archive framing,
    # checksums, normal codec work, and extractor startup are all charged to the format the user runs.
    with tempfile.NamedTemporaryFile(prefix="cmpct-cross-time-", delete=False) as tf:
        stat_path = Path(tf.name)
    out = None
    try:
        if stdout_path is not None:
            stdout_path.parent.mkdir(parents=True, exist_ok=True)
            out = stdout_path.open("wb")
        full = [TIME_BIN, "-f", "%e %M", "-o", str(stat_path), *argv]
        t0 = time.perf_counter()
        p = subprocess.run(
            full,
            cwd=str(cwd) if cwd else None,
            stdout=out if out else subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=int(os.environ.get("CMPCT_CROSS_TIMEOUT", "3600")),
        )
        fallback = time.perf_counter() - t0
        if out:
            out.close(); out = None
        if p.returncode:
            raise RuntimeError(f"command failed rc={p.returncode}: {shlex.join(argv)}\n{p.stderr.decode('utf-8','replace')[-4000:]}")
        fields = stat_path.read_text().strip().split()
        return {
            "wall_s": float(fields[0]) if fields else fallback,
            "peak_rss_kib": int(fields[1]) if len(fields) > 1 else None,
            "stdout": p.stdout.decode("utf-8", "replace") if p.stdout else "",
        }
    finally:
        if out:
            out.close()
        stat_path.unlink(missing_ok=True)


def assert_roundtrip(src: Path, dest: Path, label: str) -> None:
    if tree_manifest(src) != tree_manifest(dest):
        raise RuntimeError(f"lossless round-trip mismatch: {label}")


def cmpct_runner(label: str, python: str, src: Path, out_root: Path) -> dict[str, Any]:
    archive = out_root / f"{label}.cmpct"
    dest = out_root / f"{label}-extract"
    shutil.rmtree(dest, ignore_errors=True)
    create = timed([python, "-m", "cmpct", "create", str(src), str(archive), "--workers", "1", "--reproducible"])
    verify = timed([python, "-m", "cmpct", "verify", str(archive)])
    dest.mkdir(parents=True)
    extract = timed([python, "-m", "cmpct", "extract", str(archive), str(dest), "--no-metadata"])
    assert_roundtrip(src, dest, label)
    build = json.loads(create["stdout"])
    return {"bytes": archive.stat().st_size, "create": create, "extract": extract, "verify_s": verify["wall_s"], "cmpct_build": build}


def zip_runner(src: Path, out_root: Path) -> dict[str, Any]:
    archive = out_root / "zip-deflate-9.zip"; dest = out_root / "zip-extract"
    shutil.rmtree(dest, ignore_errors=True)
    create = timed(["zip", "-q", "-9", "-X", "-r", str(archive), "."], cwd=src)
    dest.mkdir(parents=True)
    extract = timed(["unzip", "-qq", str(archive), "-d", str(dest)])
    assert_roundtrip(src, dest, "zip-deflate-9")
    return {"bytes": archive.stat().st_size, "create": create, "extract": extract}


def seven_runner(src: Path, out_root: Path) -> dict[str, Any]:
    archive = out_root / "7z-lzma2-9.7z"; dest = out_root / "7z-extract"
    shutil.rmtree(dest, ignore_errors=True)
    create = timed(["7z", "a", "-bd", "-bso0", "-bsp0", "-t7z", "-mx=9", "-m0=lzma2", "-ms=on", str(archive), "."], cwd=src)
    dest.mkdir(parents=True)
    extract = timed(["7z", "x", "-bd", "-bso0", "-bsp0", "-y", f"-o{dest}", str(archive)])
    assert_roundtrip(src, dest, "7z-lzma2-9")
    return {"bytes": archive.stat().st_size, "create": create, "extract": extract}


def zstd_runner(level: int, src: Path, out_root: Path) -> dict[str, Any]:
    one = [p for p in src.rglob("*") if p.is_file()]
    archive = out_root / f"zstd-{level}.zst"; dest = out_root / f"zstd-{level}-extract"
    shutil.rmtree(dest, ignore_errors=True); dest.mkdir(parents=True)
    if len(one) == 1:
        # Footnote: canonical single-file corpora such as enwik8 are given raw to stream compressors;
        # CMPCT therefore pays all of its real container overhead instead of receiving a favorable tar wrapper.
        create = timed(["zstd", "-q", f"-{level}", "-f", str(one[0]), "-o", str(archive)])
        restored = dest / one[0].name
        extract = timed(["zstd", "-q", "-d", "-f", str(archive), "-o", str(restored)])
    else:
        qsrc, qarc, qdest = map(shlex.quote, (str(src), str(archive), str(dest)))
        tar = f"tar --sort=name --mtime='@0' --owner=0 --group=0 --numeric-owner -C {qsrc} -cf - ."
        create = timed(["bash", "-o", "pipefail", "-lc", f"{tar} | zstd -q -{level} -c > {qarc}"])
        extract = timed(["bash", "-o", "pipefail", "-lc", f"zstd -q -d -c {qarc} | tar -C {qdest} -xf -"])
    assert_roundtrip(src, dest, f"zstd-{level}")
    return {"bytes": archive.stat().st_size, "create": create, "extract": extract}


def compact(row: dict[str, Any], logical: int) -> dict[str, Any]:
    result = {
        "bytes": row["bytes"],
        "ratio": row["bytes"] / logical,
        "create_s": row["create"]["wall_s"],
        "extract_s": row["extract"]["wall_s"],
        "create_mib_s": (logical / 1048576) / row["create"]["wall_s"] if row["create"]["wall_s"] else None,
        "extract_mib_s": (logical / 1048576) / row["extract"]["wall_s"] if row["extract"]["wall_s"] else None,
        "create_peak_rss_kib": row["create"]["peak_rss_kib"],
        "extract_peak_rss_kib": row["extract"]["peak_rss_kib"],
    }
    if "verify_s" in row:
        result["verify_s"] = row["verify_s"]
        result["cmpct_build"] = row["cmpct_build"]
    return result


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("manifest")
    ap.add_argument("--out", default="formal-cross-results")
    a = ap.parse_args()
    manifest = json.loads(Path(a.manifest).read_text())
    py29 = os.environ["CMPCT_V029_PYTHON"]
    py30 = os.environ["CMPCT_V030_PYTHON"]
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    result: dict[str, Any] = {
        "schema": "cmpct-formal-cross-v1",
        "v029_sha": os.environ["CMPCT_V029_SHA"],
        "v030_candidate_sha": os.environ["CMPCT_V030_SHA"],
        "v030_status": "authoritative integration candidate; not a released v0.30",
        "corpora": {},
    }
    for item in manifest["corpora"]:
        name = item["name"]; src = Path(item["path"]); logical = logical_bytes(src)
        if logical != item["expected_logical_bytes"]:
            raise RuntimeError(f"logical-byte mismatch for {name}: {logical} != {item['expected_logical_bytes']}")
        work = out / name; shutil.rmtree(work, ignore_errors=True); work.mkdir(parents=True)
        rows: dict[str, Any] = {}
        runners = [
            ("cmpct-v0.29", lambda: cmpct_runner("cmpct-v029", py29, src, work)),
            ("cmpct-v0.30-candidate", lambda: cmpct_runner("cmpct-v030", py30, src, work)),
            ("zip-deflate-9", lambda: zip_runner(src, work)),
            ("zstd-3", lambda: zstd_runner(3, src, work)),
            ("zstd-19", lambda: zstd_runner(19, src, work)),
            ("7z-lzma2-9", lambda: seven_runner(src, work)),
        ]
        for label, fn in runners:
            print(f"BENCH {name} :: {label}", flush=True)
            rows[label] = compact(fn(), logical)
            print(json.dumps({"corpus": name, "compressor": label, **rows[label]}, sort_keys=True), flush=True)
        result["corpora"][name] = {"logical_bytes": logical, "files": len(tree_manifest(src)), "results": rows}
        (out / "formal-cross.partial.json").write_text(json.dumps(result, indent=2))
    (out / "formal-cross.json").write_text(json.dumps(result, indent=2))
    print("RESULT_JSON=" + json.dumps(result, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
