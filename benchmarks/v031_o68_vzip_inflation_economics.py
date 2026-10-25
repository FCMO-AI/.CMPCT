#!/usr/bin/env python3
"""O68 source-exact, research-only deferred VZIP inflation economics.

A fresh installed interpreter is the observation unit. The opaque arm patches
only the imported recipe entrypoint to select the already-existing fallback;
it is an oracle, not a new shipping product or format.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import resource
import statistics
import subprocess
import sys
import tempfile
import time
import zipfile
from pathlib import Path

SIZES = (64 * 1024, 4 * 1024 * 1024, 16 * 1024 * 1024)
REPS = 3


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def fixture(directory: Path, logical_size: int) -> tuple[Path, str]:
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / "nested.zip"
    info = zipfile.ZipInfo("repeated-data.bin", (1980, 1, 1, 0, 0, 0))
    info.compress_type = zipfile.ZIP_DEFLATED
    # Exactly one real deflate member, fixed bytes and fixed metadata.
    with zipfile.ZipFile(path, "w") as z:
        z.writestr(info, b"A" * logical_size, compress_type=zipfile.ZIP_DEFLATED, compresslevel=6)
    with zipfile.ZipFile(path) as z:
        assert z.read("repeated-data.bin") == b"A" * logical_size
    return path, digest(path.read_bytes())


def worker(args: argparse.Namespace) -> None:
    import cmpct.builder as builder_module
    from cmpct.builder import Builder
    from cmpct.codec import S_VZIP, S_BLOB
    from cmpct.reader import CMPCT

    original_path = Path(args.root) / "nested.zip"
    raw = original_path.read_bytes()
    before_hash = digest(raw)
    if args.mode == "opaque":
        # Research-only representation control. Same input bytes, file names,
        # metadata, Builder, codecs and archive-level verification.
        builder_module.make_vzip_recipe = lambda *_a, **_kw: None

    out = Path(args.output)
    b = Builder(Path(args.root), workers=1, reproducible=True, reproducible_epoch_ns=0)
    t0 = time.perf_counter_ns()
    c0 = time.process_time_ns()
    b.build(out)
    build_cpu = time.process_time_ns() - c0
    build_wall = time.perf_counter_ns() - t0
    method = b.files[0][6][0]
    with CMPCT(out) as rd:
        assert rd.read("nested.zip") == raw
        assert rd.verify() >= 1

    assert digest(original_path.read_bytes()) == before_hash, "source bytes changed"
    assert method == (S_VZIP if args.mode == "virtual" else S_BLOB), (
        f"unexpected representation {method} under {args.mode}"
    )
    print(json.dumps({
        "mode": args.mode, "source_sha256": before_hash,
        "physical_zip_bytes": len(raw), "storage_kind": method,
        "archive_bytes": out.stat().st_size,
        "archive_sha256": digest(out.read_bytes()),
        "build_wall_ns": build_wall, "build_cpu_ns": build_cpu,
        "maxrss_kib_linux": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        "python": sys.version.split()[0],
    }, sort_keys=True))


def court() -> None:
    import cmpct.builder as module
    import cmpct.codec as codec
    from importlib.metadata import version

    base = Path(tempfile.mkdtemp(prefix="cmpct-o68-"))
    cases = []
    for n in SIZES:
        root = base / str(n) / "input"
        path, source_sha = fixture(root, n)
        assert path.stat().st_size < 64 * 1024
        shape = {"inflated_bytes": n, "physical_zip_bytes": path.stat().st_size,
                 "source_sha256": source_sha, "observations": []}
        # Three paired ABBA-like blocks, reversing arms between blocks.
        for rep in range(REPS):
            order = ("virtual", "opaque") if rep % 2 == 0 else ("opaque", "virtual")
            for mode in order:
                out = base / str(n) / f"{mode}-{rep}.cmpct"
                cmd = [sys.executable, str(Path(__file__).resolve()),
                       "--worker", "--root", str(root), "--output", str(out), "--mode", mode]
                child = subprocess.run(cmd, text=True, capture_output=True, timeout=45, check=False)
                if child.returncode:
                    raise RuntimeError(
                        f"real installed subprocess failed ({mode}/{n}/rep={rep}): "
                        f"{child.returncode}\n{child.stdout[-1500:]}\n{child.stderr[-4000:]}"
                    )
                rec = json.loads(child.stdout.strip().splitlines()[-1])
                assert rec["source_sha256"] == source_sha
                rec["rep"] = rep
                shape["observations"].append(rec)
        by = {m: [x for x in shape["observations"] if x["mode"] == m]
              for m in ("virtual", "opaque")}
        assert all(len(xs) == REPS for xs in by.values())
        assert len({x["archive_sha256"] for x in by["virtual"]}) == 1
        assert len({x["archive_sha256"] for x in by["opaque"]}) == 1
        median = lambda m, key: statistics.median(x[key] for x in by[m])
        shape["summary"] = {
            "virtual_create_wall_ms": median("virtual", "build_wall_ns") / 1e6,
            "opaque_create_wall_ms": median("opaque", "build_wall_ns") / 1e6,
            "virtual_create_cpu_ms": median("virtual", "build_cpu_ns") / 1e6,
            "opaque_create_cpu_ms": median("opaque", "build_cpu_ns") / 1e6,
            "virtual_archive_bytes": by["virtual"][0]["archive_bytes"],
            "opaque_archive_bytes": by["opaque"][0]["archive_bytes"],
            "inflation_ratio": n / path.stat().st_size,
        }
        shape["summary"]["cpu_ratio_virtual_over_opaque"] = (
            shape["summary"]["virtual_create_cpu_ms"] /
            max(shape["summary"]["opaque_create_cpu_ms"], 0.000001)
        )
        cases.append(shape)

    report = {
        "experiment": "O68",
        "evidence_scope": "one-host real installed source-bound research oracle",
        "expected_source_codec_blob": "dc3446b0eed82edfba9380e3885a20aa45577899",
        "expected_source_builder_blob": "382e60983bf1e8e7595ea7112f3a5553dc33dcc0",
        "installed_cmpct_version": version("cmpct"),
        "module_builder": str(Path(module.__file__).resolve()),
        "module_codec": str(Path(codec.__file__).resolve()),
        "cases": cases,
    }
    assert "/src/cmpct/" not in str(Path(module.__file__).resolve()), (
        "expected independently installed source, not checkout"
    )
    output = Path(os.environ.get("CMPCT_O68_REPORT", "o68-raw.json"))
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    for row in cases:
        print(json.dumps({"inflated_bytes": row["inflated_bytes"], **row["summary"]}, sort_keys=True))
    print(f"O68_SAMPLES={sum(len(c['observations']) for c in cases)} O68_RECEIPT={output}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--worker", action="store_true")
    parser.add_argument("--root")
    parser.add_argument("--output")
    parser.add_argument("--mode", choices=["virtual", "opaque"])
    opt = parser.parse_args()
    if opt.worker:
        worker(opt)
    else:
        court()
