#!/usr/bin/env python3
"""J24P15: source-bound same-runner, same-tree upstream 7-Zip version court.

RESEARCH ONLY. No CMPCT engine or release comparator is invoked or changed.
Every process execution is a real create/extract, with a byte-identical manifest.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import random
import re
import shutil
import subprocess
import sys
import time
import zipfile

SOURCE_EPOCH = 315532800  # 1980-01-01 UTC; portability and archive metadata control.
FAMILIES = ("small_config", "incompressible", "nested_deflate", "shared_blocks", "mixed_records")
ASSET_SHA256 = {
    "26.03": "dc99eff5008f1ab79bd7084c68513701547a808a89502bf4133683535ab3c695",
    "26.05": "22cf82fcc6eb7474f1d5bb4f02c0f8ebd573a718089d6833dc30f8350a3b232e",
}
COMMAND_FLAGS = ["a", "-t7z", "-m0=lzma2", "-mx=9", "-ms=on"]
RUN_ORDER = ("26.03", "26.05", "26.05", "26.03") * 2  # Four raw runs / version; ABBA x2.


def h(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def deterministic_bytes(tag: str, length: int) -> bytes:
    """Stable SHA256 counter stream. Generated inputs are research controls, not secret corpora."""
    seed = tag.encode("utf-8")
    return b"".join(hashlib.sha256(seed + i.to_bytes(4, "little")).digest()
                    for i in range((length + 31) // 32))[:length]


def write(root: Path, name: str, data: bytes) -> None:
    target = root / name
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(data)


def build_family(root: Path, family: str) -> None:
    root.mkdir(parents=True)
    if family == "small_config":
        for i in range(192):
            raw = {
                "owner": f"service_{i % 8:02}",
                "route": f"/v3/{i % 11}/resource",
                "priority": i % 5,
                "rules": ["allow", "deny", "rewrite", "retain"] * 8,
                "stable": "public-structural-control" * 22,
            }
            write(root, f"config/{i // 24:02}/service_{i:04}.json",
                  json.dumps(raw, sort_keys=True, separators=(",", ":")).encode() + b"\n")
    elif family == "incompressible":
        for i in range(4):
            write(root, f"chunks/{i:02}.bin",
                  deterministic_bytes(f"J24P15-high-entropy-{i}", 256 * 1024))
    elif family == "nested_deflate":
        for i in range(16):
            target = root / f"office/batch_{i:02}.zip"
            target.parent.mkdir(parents=True, exist_ok=True)
            with zipfile.ZipFile(target, "w") as z:
                for j in range(5):
                    info = zipfile.ZipInfo(f"data/{j:02}.txt", (1980, 1, 1, 0, 0, 0))
                    info.compress_type = zipfile.ZIP_DEFLATED
                    info.external_attr = (0o100644 << 16)
                    z.writestr(info, (f"field={j} phase={i%4}\n".encode() * 2000)
                               + deterministic_bytes(f"nested-{i%4}-{j}", 8192),
                               compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
    elif family == "shared_blocks":
        common = [deterministic_bytes(f"shared-segment-{k}", 64 * 1024)
                  for k in range(5)]
        for i in range(12):
            unique = deterministic_bytes(f"unique-tail-{i}", 64 * 1024)
            write(root, f"assets/v{i:02}.bin",
                  common[i % 5] + common[(i + 1) % 5] + common[2] + unique)
    elif family == "mixed_records":
        for i in range(12):
            csv_lines = ["key,category,value,comment"]
            log_lines = []
            records = []
            for j in range(320):
                key = f"event-{i:02}-{j:04}"
                csv_lines.append(f"{key},{j % 13},{(j*j)%10003},bucket-{i%4}")
                log_lines.append(f"2026-10-31T00:{j%60:02}:00Z INFO bucket={i%4} event={key} state=ok")
                records.append({"key": key, "tags": ["alpha", "beta", "gamma"],
                                "bucket": i % 4, "metric": (j * 7) % 101})
            write(root, f"logs/{i:02}.log", ("\n".join(log_lines) + "\n").encode())
            write(root, f"tables/{i:02}.csv", ("\n".join(csv_lines) + "\n").encode())
            write(root, f"json/{i:02}.json",
                  json.dumps(records, sort_keys=True, separators=(",", ":")).encode())
    else:
        raise ValueError("unrecognized family")

    # Normalizing names, timestamps, and modes removes avoidable source confounding.
    for path in sorted(root.rglob("*"), reverse=True):
        if path.is_symlink():
            raise AssertionError("unexpected generated symlink")
        path.chmod(0o755 if path.is_dir() else 0o644)
        os.utime(path, (SOURCE_EPOCH, SOURCE_EPOCH))
    os.utime(root, (SOURCE_EPOCH, SOURCE_EPOCH))


def manifest(root: Path) -> list[dict]:
    result = []
    for path in sorted(root.rglob("*")):
        if path.is_symlink():
            raise AssertionError("symlink in regular-file-only court")
        if path.is_file():
            result.append({"path": path.relative_to(root).as_posix(),
                           "size": path.stat().st_size, "sha256": h(path.read_bytes())})
    if not result:
        raise AssertionError("zero source files")
    return result


def tree_sha(rows: list[dict]) -> str:
    return h(json.dumps(rows, sort_keys=True, separators=(",", ":")).encode())


def binary_facts(exe: Path, version: str) -> dict:
    exe = exe.resolve(strict=True)
    if not exe.is_file():
        raise AssertionError(f"{exe}: not a regular executable")
    info = subprocess.run([str(exe), "i"], check=True, capture_output=True, text=True).stdout
    if not re.search(r"\b" + re.escape(version) + r"\b", info[:4096]):
        raise AssertionError(f"wrong 7-Zip executable version {version}: {info[:120]!r}")
    return {"version": version, "path": str(exe), "binary_sha256": h(exe.read_bytes()),
            "identity_line": next((s for s in info.splitlines() if "7-Zip" in s), info.splitlines()[0])}


def one(exe: Path, stage: Path, archive: Path, extracted: Path, expected: list[dict]) -> dict:
    if archive.exists() or extracted.exists():
        raise AssertionError("research run reused an output")
    args = [str(exe), *COMMAND_FLAGS, str(archive), "."]
    t0 = time.perf_counter_ns()
    subprocess.run(args, cwd=stage, check=True, capture_output=True)
    create_ns = time.perf_counter_ns() - t0
    if not archive.is_file():
        raise AssertionError("7-Zip returned success without producing an archive")
    args_extract = [str(exe), "x", str(archive), f"-o{extracted}", "-y"]
    t0 = time.perf_counter_ns()
    subprocess.run(args_extract, check=True, capture_output=True)
    extract_ns = time.perf_counter_ns() - t0
    got = manifest(extracted)
    if got != expected:
        raise AssertionError("decoded tree differs: " + str({"expected": tree_sha(expected),
                                                         "actual": tree_sha(got)}))
    return {"archive_bytes": archive.stat().st_size, "archive_sha256": h(archive.read_bytes()),
            "create_wall_ns": create_ns, "extract_wall_ns": extract_ns,
            "extracted_tree_sha256": tree_sha(got)}


def run(old: Path, new: Path, work: Path, head: str) -> dict:
    if not re.fullmatch(r"[0-9a-f]{40}", head):
        raise ValueError("source commit must be exact 40-character hex")
    if work.exists():
        raise ValueError("work-root already exists; never reuse source/output state")
    work.mkdir(parents=True)
    tools = {"26.03": old, "26.05": new}
    facts = {k: binary_facts(v, k) for k, v in tools.items()}
    output = {"schema": "cmpct-j24p15-upstream-7zip-delta-v1", "source_commit": head,
              "research_credit": True, "product_credit": False,
              "command_flags": COMMAND_FLAGS, "order": RUN_ORDER,
              "python": sys.version, "platform": platform.platform(),
              "tools": facts, "asset_sha256": ASSET_SHA256, "families": []}
    for family in FAMILIES:
        stage = work / family / "input"
        build_family(stage, family)
        expected = manifest(stage)
        family_result = {"family": family, "source_tree_sha256": tree_sha(expected),
                         "source_members": len(expected),
                         "source_logical_bytes": sum(e["size"] for e in expected),
                         "runs": []}
        for i, version in enumerate(RUN_ORDER):
            run_root = work / family / f"{i:02}-{version}"
            run_root.mkdir()
            sample = one(tools[version], stage, run_root / "out.7z",
                         run_root / "extract", expected)
            family_result["runs"].append({"order_index": i, "version": version, **sample})
        output["families"].append(family_result)
        print(json.dumps({"family": family, "source_sha256": family_result["source_tree_sha256"],
                          "sizes": [(r["version"], r["archive_bytes"]) for r in family_result["runs"]]},
                         separators=(",", ":")), flush=True)
    return output


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--old", required=True, type=Path)
    p.add_argument("--new", required=True, type=Path)
    p.add_argument("--work-root", required=True, type=Path)
    p.add_argument("--out", required=True, type=Path)
    p.add_argument("--source-head", required=True)
    a = p.parse_args()
    data = run(a.old, a.new, a.work_root, a.source_head)
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(data, sort_keys=True, indent=2) + "\n")
    print(json.dumps({"receipt": str(a.out), "families": len(data["families"]),
                      "per_version_runs": len(FAMILIES) * RUN_ORDER.count("26.03")},
                     separators=(",", ":")))


if __name__ == "__main__":
    main()
