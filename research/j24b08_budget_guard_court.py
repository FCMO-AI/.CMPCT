#!/usr/bin/env python3
"""J24B08 preregistered installed-Reader extraction economics.

Research only. This script must not edit either Reader or its release benchmark.
Usage: python research/j24b08_budget_guard_court.py --out j24b08-evidence
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import inspect
import json
import os
from pathlib import Path
import platform
import shutil
import statistics
import subprocess
import sys
import tempfile
import time

from cmpct.builder import Builder
from cmpct.codec import K_DIR, K_FILE
from cmpct.reader import CMPCT as CandidateCMPCT

RELEASE = "80c358f8824ec1b20d349c92ed94c898090969b0"
RELEASE_READER = "e716233403dabd0966863c45635e18fa5ac6afb8"
PARENT = "adcf38cb5be022567c1faf6538aefeef2f6b72de"
PARENT_READER = "20f6e257a07a61a4c1aebe23ae23e4109d6c41c8"


def git(*args: str, input_bytes: bytes | None = None) -> bytes:
    return subprocess.run(
        ["git", *args], input=input_bytes, check=True, stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    ).stdout.strip()


def git_bytes(ref: str, name: str) -> bytes:
    return subprocess.run(
        ["git", "show", f"{ref}:{name}"], check=True, stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    ).stdout


def git_blob(data: bytes) -> str:
    return git("hash-object", "--stdin", input_bytes=data).decode()


def identity_check() -> dict:
    head = git("rev-parse", "HEAD").decode()
    if git("merge-base", "--is-ancestor", PARENT, "HEAD") != b"":
        # git returns no stdout on successful ancestry check.
        raise AssertionError("unexpected merge-base output")
    old = git_bytes(RELEASE, "src/cmpct/reader.py")
    expected = git_bytes("HEAD", "src/cmpct/reader.py")
    assert git_blob(old) == RELEASE_READER
    assert git_blob(expected) == PARENT_READER, "candidate Reader modified after owner pin"
    installed_path = Path(inspect.getfile(CandidateCMPCT))
    installed = installed_path.read_bytes()
    # Git checkout on Windows may translate the actual working-tree bytes to CRLF.
    # Normalization is *only* for text-source identity; retain both raw digests.
    normalized = installed.replace(b"\r\n", b"\n")
    assert normalized == expected, "installed candidate differs from exact Git source"
    assert git("rev-parse", f"HEAD:src/cmpct/builder.py") == git(
        "rev-parse", f"{RELEASE}:src/cmpct/builder.py"
    ), "Builder changed between direct competitors"
    assert git("rev-parse", f"HEAD:src/cmpct/codec.py") == git(
        "rev-parse", f"{RELEASE}:src/cmpct/codec.py"
    ), "codec changed between direct competitors"
    return {
        "head": head,
        "release": RELEASE,
        "release_reader_blob": git_blob(old),
        "candidate_parent": PARENT,
        "candidate_reader_blob": git_blob(expected),
        "installed_reader_sha256_raw": hashlib.sha256(installed).hexdigest(),
        "installed_reader_sha256_normalized": hashlib.sha256(normalized).hexdigest(),
        "git_reader_sha256": hashlib.sha256(expected).hexdigest(),
        "installed_source_path": str(installed_path),
        "platform": platform.platform(),
        "python": platform.python_version(),
    }


def load_historical(temp: Path):
    raw = git_bytes(RELEASE, "src/cmpct/reader.py")
    path = temp / "_j24b08_historical_reader.py"
    path.write_bytes(raw)
    spec = importlib.util.spec_from_file_location(
        "cmpct._j24b08_historical_reader", str(path)
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    assert module.CMPCT is not CandidateCMPCT
    return module.CMPCT


def data_at(n: int, i: int) -> bytes:
    return hashlib.sha256(f"J24B08:{n}:{i:06d}".encode()).digest() * 3


def tree_digest(root: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(root.rglob("*.bin")):
        rel = path.relative_to(root).as_posix().encode()
        value = path.read_bytes()
        digest.update(len(rel).to_bytes(4, "big") + rel)
        digest.update(len(value).to_bytes(8, "big"))
        digest.update(hashlib.sha256(value).digest())
    return digest.hexdigest()


def build_geometry(root: Path, n: int, evidence: Path) -> dict:
    source = root / f"tree-{n}"
    source.mkdir()
    for i in range(n):
        (source / f"{i:06d}.bin").write_bytes(data_at(n, i))
    archive = evidence / f"source-{n}.cmpct"
    Builder(source, workers=1, reproducible=True).build(archive)
    assert archive.is_file()
    return {
        "files": n,
        "payload_total": n * 96,
        "tree_sha256": tree_digest(source),
        "archive_path": str(archive),
        "archive_sha256": hashlib.sha256(archive.read_bytes()).hexdigest(),
        "archive_bytes": archive.stat().st_size,
    }


def one_extract(cls, source: dict, destination: Path, max_bytes):
    archive = Path(source["archive_path"])
    t0 = time.perf_counter_ns()
    c0 = time.process_time_ns()
    reader = cls(archive)
    t1 = time.perf_counter_ns()
    c1 = time.process_time_ns()
    try:
        assert len([x for x in reader.files if x[1] != K_DIR]) == source["files"]
        start = time.perf_counter_ns()
        cpu_start = time.process_time_ns()
        reader.extractall(destination, metadata=False, max_bytes=max_bytes)
        end = time.perf_counter_ns()
        cpu_end = time.process_time_ns()
    finally:
        reader.close()
    # Crucially, hashing and cleanup are OUTSIDE the measured extract operation.
    assert len(list(destination.glob("*.bin"))) == source["files"]
    assert tree_digest(destination) == source["tree_sha256"], "output byte parity lost"
    return {
        "open_wall_ns": t1 - t0,
        "open_cpu_ns": c1 - c0,
        "extract_wall_ns": end - start,
        "extract_cpu_ns": cpu_end - cpu_start,
        "output_sha256": tree_digest(destination),
        "output_files": source["files"],
    }


def micro_scan() -> dict:
    # Only a causal component; *not* a replacement for real Reader proof.
    rows = [(f"{i:06d}", K_FILE, 0, 0, 96, b"", []) for i in range(100_000)]

    def base():
        return sum(x[4] for x in rows if x[1] != K_DIR)

    def candidate():
        total = 0
        for row in rows:
            declared = row[4]
            if type(declared) is not int or declared < 0:
                raise IOError("invalid nonnegative logical size")
            if row[1] != K_DIR:
                total += declared
        return total

    samples = {"base": [], "candidate": []}
    for turn in range(8):
        order = ["base", "candidate", "candidate", "base"]
        if turn % 2:
            order.reverse()
        for arm in order:
            t0, c0 = time.perf_counter_ns(), time.process_time_ns()
            result = base() if arm == "base" else candidate()
            t1, c1 = time.perf_counter_ns(), time.process_time_ns()
            assert result == 9_600_000
            samples[arm].append({"wall_ns": t1 - t0, "cpu_ns": c1 - c0})
    return {
        "class": "source_equivalent_component_only_not_product",
        "rows": len(rows),
        "raw": samples,
        "median_wall_ns": {
            arm: statistics.median(x["wall_ns"] for x in raw)
            for arm, raw in samples.items()
        },
    }


def run(out: Path) -> dict:
    out.mkdir(parents=True, exist_ok=True)
    identity = identity_check()
    with tempfile.TemporaryDirectory(prefix="cmpct-j24b08-") as temp_str:
        temp = Path(temp_str)
        baseline_cls = load_historical(temp)
        geometries = [
            build_geometry(temp, n, out) for n in (128, 4096)
        ]
        cells = []
        for g in geometries:
            for budget_mode in ("none", "exact"):
                budget = None if budget_mode == "none" else g["payload_total"]
                raw = []
                for repeat in range(4):
                    order = ["base", "candidate", "candidate", "base"]
                    if repeat % 2:
                        order.reverse()
                    for step, arm in enumerate(order):
                        destination = temp / f"output-{g['files']}-{budget_mode}-{repeat}-{step}"
                        cls = baseline_cls if arm == "base" else CandidateCMPCT
                        result = one_extract(cls, g, destination, budget)
                        raw.append({"arm": arm, "repeat": repeat,
                                    "step": step, "budget_mode": budget_mode, **result})
                        shutil.rmtree(destination)
                grouped = {
                    a: [r for r in raw if r["arm"] == a]
                    for a in ("base", "candidate")
                }
                assert all(len(x) == 8 for x in grouped.values())
                med = {
                    a: {field: statistics.median(r[field] for r in members)
                        for field in (
                            "open_wall_ns", "open_cpu_ns",
                            "extract_wall_ns", "extract_cpu_ns",
                        )}
                    for a, members in grouped.items()
                }
                base_w = med["base"]["extract_wall_ns"]
                cand_w = med["candidate"]["extract_wall_ns"]
                delta_ms = (cand_w - base_w) / 1e6
                ratio = cand_w / base_w
                # A recorded negative is scientific evidence, not a CI failure.
                confirmed_gate_signal = ratio > 1.05 and delta_ms > 3
                cells.append({
                    "files": g["files"],
                    "budget_mode": budget_mode,
                    "budget": budget,
                    "raw": raw,
                    "median": med,
                    "candidate_over_base_wall_ratio": ratio,
                    "candidate_minus_base_wall_ms": delta_ms,
                    "confirmed_release_gate_signal_on_this_experimental_cell":
                        confirmed_gate_signal,
                })
        receipt = {
            "schema": "cmpct-j24b08-economics-v1",
            "classification": "installed_reader_research_not_release_gate",
            "identity": identity,
            "geometries": geometries,
            "cells": cells,
            "micro": micro_scan(),
            "important_negative": (
                "This performance court does NOT repair #693's proven nonnegative "
                "hardlink quota undercount, verify semantic signed owner lengths, "
                "or approve a v0.31 release."
            ),
        }
        # Archive paths are directory-relative in final receipt.
        for g in receipt["geometries"]:
            g["archive_path"] = Path(g["archive_path"]).name
        (out / "receipt.json").write_text(
            json.dumps(receipt, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        print("J24B08_RECEIPT=" + json.dumps({
            "source": identity["head"],
            "cells": [
                {"files": c["files"], "budget_mode": c["budget_mode"],
                 "ratio": c["candidate_over_base_wall_ratio"],
                 "delta_ms": c["candidate_minus_base_wall_ms"],
                 "gate_signal": c["confirmed_release_gate_signal_on_this_experimental_cell"]}
                for c in cells
            ],
        }, sort_keys=True))
        return receipt


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--out", default="j24b08-evidence")
    args = p.parse_args()
    run(Path(args.out))
