#!/usr/bin/env python3
from __future__ import annotations

"""Fair CMPCT-vs-ZIP benchmark layers.

The harness has two jobs:

* compare CMPCT and ordinary ZIP at equivalent process boundaries;
* support a release-gate mode where two CMPCT engine revisions consume the *same exact corpus tree*.

`CMPCT_PARITY_CORPUS_ROOT` activates the second property. The harness then treats that tree as immutable
input and only resets its own output directory. This lets the candidate harness drive both the base and
candidate engines without letting corpus randomness, timestamps, or an older harness revision pollute
the comparison.
"""

import json
import os
import shutil
import statistics
import subprocess
import sys
import time
import zipfile
from pathlib import Path

from cmpct.builder import Builder
from cmpct.reader import CMPCT

import universal_bench as universal

HERE = Path(__file__).resolve().parent
WORK = HERE / "_parity_work"
CORP = WORK / "corpora"
OUT = WORK / "out"
ZIP_CLI_HELPER = HERE / "zip_cli_helper.py"
REPS = int(os.environ.get("CMPCT_PARITY_REPS", "3"))
EXTERNAL_CORPUS = os.environ.get("CMPCT_PARITY_CORPUS_ROOT")


def _median(fn, reps: int = REPS) -> float:
    values = []
    for _ in range(reps):
        t0 = time.perf_counter_ns()
        fn()
        values.append((time.perf_counter_ns() - t0) / 1_000_000_000)
    return statistics.median(values)


def _reset() -> None:
    global CORP
    shutil.rmtree(WORK, ignore_errors=True)
    OUT.mkdir(parents=True)
    if EXTERNAL_CORPUS:
        CORP = Path(EXTERNAL_CORPUS).resolve()
        if not CORP.is_dir():
            raise RuntimeError(f"CMPCT_PARITY_CORPUS_ROOT is not a directory: {CORP}")
        expected = {"tiny", "source", "media", "binary", "dedup_links", "sparse", "nested", "combined"}
        actual = {p.name for p in CORP.iterdir() if p.is_dir()}
        if not expected <= actual:
            raise RuntimeError(f"external parity corpus incomplete; missing {sorted(expected - actual)}")
        # Footnote: never rewrite an external corpus inside a release comparison. Base and candidate
        # must observe the same inodes/bytes/metadata; only benchmark output is disposable.
        return

    CORP.mkdir(parents=True)
    old_corp, old_out, old_work = universal.CORP, universal.OUT, universal.WORK
    try:
        universal.CORP, universal.OUT, universal.WORK = CORP, OUT, WORK
        universal.make_corpora()
    finally:
        universal.CORP, universal.OUT, universal.WORK = old_corp, old_out, old_work


def _zip_create(src: Path, out: Path) -> None:
    try:
        out.unlink()
    except FileNotFoundError:
        pass
    with zipfile.ZipFile(out, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6, allowZip64=True) as zf:
        for p in sorted(src.rglob("*")):
            rel = p.relative_to(src).as_posix()
            if p.is_dir():
                continue
            zf.write(p, rel)


def _zip_extract(archive: Path, dest: Path) -> None:
    shutil.rmtree(dest, ignore_errors=True)
    dest.mkdir()
    with zipfile.ZipFile(archive) as zf:
        zf.extractall(dest)


def _cmpct_create(src: Path, out: Path) -> None:
    try:
        out.unlink()
    except FileNotFoundError:
        pass
    Builder(src).build(out)


def _cmpct_extract(archive: Path, dest: Path) -> None:
    shutil.rmtree(dest, ignore_errors=True)
    dest.mkdir()
    with CMPCT(archive) as ar:
        ar.extractall(dest, metadata=False)


def _run_cli(args: list[str], env: dict[str, str] | None = None) -> None:
    result = subprocess.run(args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, env=env)
    if result.returncode:
        raise RuntimeError((args, result.returncode))


def _cmpct_cli_create(src: Path, out: Path) -> None:
    try:
        out.unlink()
    except FileNotFoundError:
        pass
    env = os.environ.copy()
    env["CMPCT_DEFLATE_REUSE_MIN"] = "65536"
    _run_cli([sys.executable, "-m", "cmpct", "create", str(src), str(out)], env)


def _cmpct_cli_extract(archive: Path, dest: Path) -> None:
    shutil.rmtree(dest, ignore_errors=True)
    dest.mkdir()
    _run_cli([sys.executable, "-m", "cmpct", "extract", str(archive), str(dest), "--no-metadata"])


def _zip_cli_create(src: Path, out: Path) -> None:
    try:
        out.unlink()
    except FileNotFoundError:
        pass
    # Footnote: the helper has no CMPCT import, so ZIP pays only its own interpreter + zipfile startup.
    # This prevents a superficially "fair" subprocess benchmark from secretly loading our package on
    # ZIP's side and gifting CMPCT an artificial CLI win.
    _run_cli([sys.executable, str(ZIP_CLI_HELPER), "create", str(src), str(out)])


def _zip_cli_extract(archive: Path, dest: Path) -> None:
    shutil.rmtree(dest, ignore_errors=True)
    dest.mkdir()
    _run_cli([sys.executable, str(ZIP_CLI_HELPER), "extract", str(archive), str(dest)])


def _timed_layer(name: str, src: Path, layer: str) -> dict:
    ca = OUT / f"{name}.{layer}.cmpct"
    za = OUT / f"{name}.{layer}.zip"
    cex = OUT / f"extract-{name}-{layer}-cmpct"
    zex = OUT / f"extract-{name}-{layer}-zip"

    if layer == "library":
        cc = lambda: _cmpct_create(src, ca)
        zc = lambda: _zip_create(src, za)
        ce = lambda: _cmpct_extract(ca, cex)
        ze = lambda: _zip_extract(za, zex)
    elif layer == "cli":
        cc = lambda: _cmpct_cli_create(src, ca)
        zc = lambda: _zip_cli_create(src, za)
        ce = lambda: _cmpct_cli_extract(ca, cex)
        ze = lambda: _zip_cli_extract(za, zex)
    else:
        raise ValueError(layer)

    c_create = _median(cc)
    z_create = _median(zc)
    # Create once more immediately before extraction so every extraction layer operates on the same
    # encoder settings and a fully committed archive after the timed creation repetitions.
    cc()
    zc()
    c_extract = _median(ce)
    z_extract = _median(ze)

    return {
        "cmpct": {
            "bytes": ca.stat().st_size,
            "create_s_median": c_create,
            "extract_s_median": c_extract,
        },
        "zip": {
            "bytes": za.stat().st_size,
            "create_s_median": z_create,
            "extract_s_median": z_extract,
        },
    }


def run() -> dict:
    _reset()
    names = ["tiny", "source", "media", "binary", "dedup_links", "sparse", "nested", "combined"]
    result = {
        "schema": "cmpct-zip-parity-v1",
        "repetitions": REPS,
        "timing_statistic": "median",
        "cache_semantics": "warm/ordinary filesystem cache; no cache dropping between repetitions",
        "integrity_semantics": {
            "cmpct": "normal reader/extractor integrity checks",
            "zip": "Python zipfile normal CRC behavior",
        },
        "filesystem_semantic_mismatch": (
            "CMPCT preserves links/sparse/uid-gid/xattrs in the archive; this Python ZIP baseline "
            "dereferences symlinks and does not preserve the richer filesystem semantics."
        ),
        "corpus_semantics": (
            "external immutable corpus shared by base/candidate" if EXTERNAL_CORPUS
            else "deterministic corpus generated by benchmarks/universal_bench.py"
        ),
        "corpora": {},
    }

    for name in names:
        print(f"PARITY {name}", flush=True)
        src = CORP / name
        result["corpora"][name] = {
            "logical_bytes": universal.logical_bytes(src),
            "library": _timed_layer(name, src, "library"),
            "cli": _timed_layer(name, src, "cli"),
        }
        (OUT / "zip-parity.partial.json").write_text(json.dumps(result, indent=2))

    (OUT / "zip-parity.json").write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2))
    return result


if __name__ == "__main__":
    run()
