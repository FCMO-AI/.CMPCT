#!/usr/bin/env python3
"""J24G53e: after-timing r24/ZIP native provenance, not a timing/performance proof.

Run only *after* all four original ABBA phases. This observer starts fresh
probes on the same runner, so cannot retroactively certify timed child imports.
It gives a physical binary owner, SHA-256 and Linux memory-map discriminator.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

SCHEMA = "cmpct-j24g53e-post-abba-native-runtime-v1"

# Kept independent from CMPCT imports in the controller. Fresh child runs from
# the original benchmark cwd with the same PYTHONPATH mechanism as ABBA.
PROBE = r'''
import hashlib, json, os, subprocess, sys
from pathlib import Path

root = Path(sys.argv[1]).resolve(strict=True)
package_dir = root / "src" / "cmpct"

def sha256(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for part in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(part)
    return h.hexdigest()

def assert_owned(module):
    actual = Path(module.__file__).resolve(strict=True)
    if actual.parent != package_dir:
        raise RuntimeError("wrong Python source owner for " + module.__name__ + ": " + str(actual))
    if Path(module.__file__).is_symlink():
        raise RuntimeError("symlink Python source member: " + str(module.__file__))
    repo_path = "src/cmpct/" + actual.name
    git_bytes = subprocess.check_output(["git", "-C", str(root), "show", "HEAD:" + repo_path], timeout=15)
    direct_hash = sha256(actual)
    if direct_hash != hashlib.sha256(git_bytes).hexdigest():
        raise RuntimeError("dirty source member differs from Git HEAD: " + repo_path)
    return {"name": actual.name, "sha256": direct_hash}

import cmpct
from cmpct import builder, reader, native_codec, codec
sources = {name: assert_owned(mod) for name,mod in (
    ("package", cmpct), ("builder", builder), ("reader", reader),
    ("codec", codec), ("native_codec", native_codec))}
selected_path = Path(native_codec._library_path())
loaded_path = Path(native_codec._core._name)
if selected_path.is_symlink() or loaded_path.is_symlink():
    raise RuntimeError("symlink native library ownership is not admitted")
lib_declared = selected_path.resolve(strict=True)
lib_loaded = loaded_path.resolve(strict=True)
if lib_declared != lib_loaded:
    raise RuntimeError("ctypes loaded library differs from package library selector")
if lib_loaded.parent != package_dir or lib_loaded.is_symlink():
    raise RuntimeError("native library escaped package source ownership")
if not lib_loaded.is_file():
    raise RuntimeError("native library was removed")
stat = lib_loaded.stat()
# Linux-specific live mapping; pathname alone cannot prove the same inode is loaded.
if not Path("/proc/self/maps").is_file():
    raise RuntimeError("Linux /proc/self/maps unavailable; no post-exec native claim")
matching = []
for line in Path("/proc/self/maps").read_text().splitlines():
    parts = line.split(None, 5)
    if len(parts) != 6 or parts[5] != str(lib_loaded):
        continue
    try:
        major, minor = (int(v, 16) for v in parts[3].split(":"))
        if (os.makedev(major, minor), int(parts[4])) == (stat.st_dev, stat.st_ino):
            matching.append(parts[1])
    except (ValueError, OverflowError):
        continue
if not matching:
    raise RuntimeError("ctypes native binary not mapped under declared device/inode")
if not any("x" in p for p in matching):
    raise RuntimeError("native binary has no executable mapping")
print(json.dumps({
    "source": sources,
    "native": {"file": lib_loaded.name, "sha256": sha256(lib_loaded),
               "bytes": stat.st_size, "dev": stat.st_dev, "inode": stat.st_ino,
               "mapped_regions": len(matching), "has_executable_mapping": True},
    "python_version": sys.version.split()[0], "pid": os.getpid(),
}, sort_keys=True))
'''


def expected_git_head(root: Path, expected: str) -> str:
    actual = subprocess.check_output(
        ["git", "-C", str(root), "rev-parse", "HEAD"], text=True, timeout=10
    ).strip()
    if actual != expected:
        raise ValueError(f"wrong source HEAD {root.name}: {actual} != {expected}")
    return actual


def run_probe(root: Path, cwd: Path) -> dict:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(root / "src")
    env["PYTHONNOUSERSITE"] = "1"
    # Match the benchmark's cwd and PYTHONPATH, but never run timed operations.
    child = subprocess.run(
        [sys.executable, "-c", PROBE, str(root)], cwd=cwd, env=env,
        text=True, capture_output=True, timeout=40,
    )
    if child.returncode:
        raise RuntimeError(
            f"native provenance probe failed for {root.name}: {child.returncode}\n"
            f"stdout={child.stdout[:1000]}\nstderr={child.stderr[-3000:]}"
        )
    return json.loads(child.stdout)


def attest(candidate: Path, base: Path, candidate_sha: str, base_sha: str,
           base_receipt: Path) -> dict:
    candidate = candidate.resolve(strict=True)
    base = base.resolve(strict=True)
    if candidate == base:
        raise ValueError("candidate and base resolve to the same source tree")
    expected_git_head(candidate, candidate_sha)
    expected_git_head(base, base_sha)
    base_native = json.loads(base_receipt.read_text())
    if base_native.get("source_commit") != base_sha:
        raise ValueError("base-native materialization receipt source mismatch")
    result = {"schema": SCHEMA, "claim_scope": "post_ABBA_fresh_process_only",
              "candidate_sha": candidate_sha, "base_sha": base_sha,
              "base": run_probe(base, candidate / "benchmarks"),
              "candidate": run_probe(candidate, candidate / "benchmarks")}
    if result["base"]["native"]["sha256"] != base_native.get("native_sha256"):
        raise ValueError("base native loaded binary disagrees with materialized wheel receipt")
    result["controls"] = {
        "base_matches_materialized_native_sha": True,
        "same_native_binary_sha256": (result["base"]["native"]["sha256"]
                                      == result["candidate"]["native"]["sha256"]),
        "same_python_source_hashes": {
            k: result["base"]["source"][k]["sha256"] == result["candidate"]["source"][k]["sha256"]
            for k in result["base"]["source"]
        },
    }
    return result


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--candidate", required=True, type=Path)
    p.add_argument("--base", required=True, type=Path)
    p.add_argument("--candidate-sha", required=True)
    p.add_argument("--base-sha", required=True)
    p.add_argument("--base-receipt", required=True, type=Path)
    p.add_argument("--output", required=True, type=Path)
    a = p.parse_args()
    result = attest(a.candidate, a.base, a.candidate_sha, a.base_sha, a.base_receipt)
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"schema": SCHEMA, "controls": result["controls"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
