from __future__ import annotations

import argparse
import base64
import gzip
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys

import zstandard as zstd

# This file is invoked directly by Android CI (`python tests/...py`), which puts tests/ rather than the
# repository root on sys.path. Bind imports to the checked-out source tree explicitly so the generated vector
# always exercises the exact PR-head experiments package instead of depending on ambient PYTHONPATH/install state.
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from experiments import entropygraph_v030_logs_inverse_profile_v3 as LOGS


def _sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def build_vector(output: Path, work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    src = work_root / "src"
    src.mkdir(parents=True)

    zstd_plain = b"2026-08-22T06:00:00Z INFO android-logs request=alpha value=42\n" * 4096
    gzip_plain = b"2026-08-22T06:00:01Z WARN android-logs request=beta value=17\n" * 3584
    unmatched = b"2026-08-22T06:00:02Z INFO android-logs request=gamma value=99\n" * 1024

    (src / "zstd.log").write_bytes(zstd_plain)
    (src / "zstd.log.zst").write_bytes(zstd.ZstdCompressor(level=3, threads=0).compress(zstd_plain))
    (src / "gzip.log").write_bytes(gzip_plain)
    (src / "gzip.log.gz").write_bytes(gzip.compress(gzip_plain, compresslevel=6, mtime=0))
    (src / "unmatched.log").write_bytes(unmatched)
    os.link(src / "zstd.log", src / "zstd-hard.log")
    os.symlink("zstd.log", src / "zstd-link")

    archive = work_root / "v030-logs-android.cmpct"
    stats = LOGS.build(src, archive)
    verified = LOGS.strong_verify(archive)
    if not verified.get("ok"):
        raise RuntimeError(f"logs Android vector failed strong verification: {verified!r}")
    edges = stats.get("edge_detection", {})
    if int(edges.get("inverse_edges", 0)) < 2:
        raise RuntimeError(f"logs Android vector did not exercise both inverse families: {stats!r}")

    archive_raw = archive.read_bytes()
    expected_paths = sorted(path.name for path in src.iterdir())
    vector = {
        "schema": "cmpct-v030-android-logs-vector-v1",
        "profile": "cmpct-r25-logs-inverse-v1",
        "revision": 25,
        "archive_sha256": _sha256(archive_raw),
        "archive_base64": base64.b64encode(archive_raw).decode("ascii"),
        "expected_paths": expected_paths,
        "expected_entry_count": len(expected_paths),
        "regular_path": "zstd.log",
        "hardlink_path": "zstd-hard.log",
        "symlink_path": "zstd-link",
        "symlink_target": "zstd.log",
        "regular_head_base64": base64.b64encode(zstd_plain[:64]).decode("ascii"),
        "facts": {
            "strong_verify": True,
            "inverse_edges": int(edges["inverse_edges"]),
            "gzip_source_present": "gzip.log.gz" in edges.get("inverse_edge_sources", []),
            "zstd_source_present": "zstd.log.zst" in edges.get("inverse_edge_sources", []),
        },
    }
    if not vector["facts"]["gzip_source_present"] or not vector["facts"]["zstd_source_present"]:
        raise RuntimeError(f"logs Android vector missed required inverse codecs: {stats!r}")

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(vector, indent=2) + "\n", encoding="utf-8")
    return vector


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--work-root", type=Path, required=True)
    args = parser.parse_args()
    vector = build_vector(args.output, args.work_root)
    print(json.dumps({
        "schema": vector["schema"],
        "archive_sha256": vector["archive_sha256"],
        "expected_entry_count": vector["expected_entry_count"],
        "facts": vector["facts"],
    }, indent=2))


if __name__ == "__main__":
    main()
