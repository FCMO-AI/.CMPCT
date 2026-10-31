#!/usr/bin/env python3
"""J24I70: physical A/B/C cross-owner Reader court. Research only; no shipping changes.

The source of each Reader is identified at runtime. J24G90 physical Builder/Writer
controls are imported from a separate, exact-SHA reference checkout of #853.
"""
from __future__ import annotations

import hashlib
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
import tracemalloc

ROOT = Path(__file__).resolve().parents[1]
REFERENCE = ROOT / "_reference_j24g91"
sys.path.insert(0, str(REFERENCE / "research"))
sys.path.insert(0, str(ROOT / "research"))

from cmpct.reader import CMPCT
from cmpct.validation import preflight_archive
from j24g73_reader_open import FactoredCMPCT
from j24g74_owned_decoder_court import OwnedCMPCT
from j24g90_terminal_checkpoint import make_court, check_semantics, index_fingerprint
from j24g91_delete_reader_checkpoint import OwnedDeleteCMPCT

PRODUCT_MAIN = "80c358f8824ec1b20d349c92ed94c898090969b0"
PARENT = "347a62b443bf7c880ed2b86af5d8be7159ee2480"
REFERENCE_HEAD = "129edec976efe8bb604584517de39553487fec34"
PREREG = "9b2cf6ab6d02eee9ead8e58ab1d733ee2aedb9d5"
PRIMARY_READER_BLOB = "29a8be64f3acfb027750351c6a567fd82cf7dc97"
REFERENCE_READER_BLOB = "e716233403dabd0966863c45635e18fa5ac6afb8"
CASES = (4096, 8192)
LABELS = ("public", "factored", "owned", "delete_only")
CLASSES = {
    "public": CMPCT, "factored": FactoredCMPCT,
    "owned": OwnedCMPCT, "delete_only": OwnedDeleteCMPCT,
}
EXPECTED_ROUTES = {
    "A": {"factored": "factored", "owned": "owned-fresh-decoder",
          "delete_only": "onepass-owned-delete"},
    "B": {"factored": "checkpoint", "owned": "checkpoint", "delete_only": "checkpoint"},
    "C": {"factored": "factored", "owned": "owned-fresh-decoder",
          "delete_only": "onepass-owned-delete"},
}


def git(root: Path, *args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=root, text=True).strip()


def source_identity() -> dict:
    assert git(ROOT, "rev-parse", "HEAD:src/cmpct/reader.py") == PRIMARY_READER_BLOB
    assert git(REFERENCE, "rev-parse", "HEAD") == REFERENCE_HEAD
    assert git(REFERENCE, "rev-parse", "HEAD:src/cmpct/reader.py") == REFERENCE_READER_BLOB
    assert git(ROOT, "merge-base", PARENT, "HEAD") == PARENT
    assert git(ROOT, "merge-base", PREREG, "HEAD") == PREREG
    assert Path(sys.modules["cmpct.reader"].__file__).resolve().is_relative_to(ROOT / "src")
    assert Path(sys.modules["j24g90_terminal_checkpoint"].__file__).resolve().is_relative_to(
        REFERENCE / "research")
    return {
        "head": git(ROOT, "rev-parse", "HEAD"), "parent": PARENT, "prereg": PREREG,
        "reference_head": REFERENCE_HEAD, "published_main": PRODUCT_MAIN,
        "reader_git_blob": PRIMARY_READER_BLOB,
        "reference_reader_git_blob": REFERENCE_READER_BLOB,
        "instrument_blob": git(ROOT, "rev-parse", "HEAD:research/j24i70_cross_owner_reader.py"),
        "control_blob": git(REFERENCE, "rev-parse", "HEAD:research/j24g90_terminal_checkpoint.py"),
        "delete_control_blob": git(REFERENCE, "rev-parse", "HEAD:research/j24g91_delete_reader_checkpoint.py"),
        "owned_control_blob": git(ROOT, "rev-parse", "HEAD:research/j24g74_owned_decoder_court.py"),
    }


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def check_all_readers(case, n: int) -> dict:
    expected = case["expected"]
    expected_names = set(expected)
    outcome = {}
    # Strict preflight is mandatory for the inputs; do not confuse it with
    # four-fold independent proof of the physical archive.
    for label, path in case["paths"].items():
        preflight_archive(path)
        variants = {}
        for name, klass in CLASSES.items():
            with klass(path) as ar:
                assert ar.delta_depth == (0 if label == "B" else 63), (name, label, ar.delta_depth)
                assert set(ar.by) == expected_names, (name, label, "names")
                assert index_fingerprint(ar.index) == case["index_sha256"], (name, label, "index")
                assert ar.verify() == len(expected), (name, label, "verify")
                for member, expected_sha in expected.items():
                    assert hashlib.sha256(ar.read(member)).hexdigest() == expected_sha, (
                        name, label, member)
                route = getattr(ar, "_research_route", None)
                if name != "public":
                    assert route == EXPECTED_ROUTES[label][name], (name, label, route)
                variants[name] = {
                    "member_count": len(ar.by),
                    "index_sha256": index_fingerprint(ar.index),
                    "delta_depth": ar.delta_depth,
                    "route": route,
                    "verified_members": len(expected),
                }
        outcome[label] = variants
    assert len(expected) == n - 63
    return outcome


def one_open(path: Path, label: str) -> dict:
    klass = CLASSES[label]
    # Windows process CPU clocks have coarse scheduling quanta: batch enough genuine
    # full Reader opens to avoid a zero CPU median for the checkpoint control.
    # This changes neither archive semantics nor any official performance gate.
    batch = 16 if sys.platform == "win32" else 1
    t0 = time.perf_counter_ns()
    c0 = time.process_time_ns()
    routes = set()
    for _ in range(batch):
        with klass(path) as ar:
            assert len(ar.files) > 0
            if label != "public":
                routes.add(getattr(ar, "_research_route", "UNKNOWN"))
    if label != "public":
        assert len(routes) == 1, (label, routes)
    return {
        "wall_ns": (time.perf_counter_ns() - t0) / batch,
        "cpu_ns": (time.process_time_ns() - c0) / batch,
        "batch": batch,
        "route": next(iter(routes)) if routes else None,
    }


def time_variants(case: dict) -> dict:
    measured = {}
    for file_label, path in case["paths"].items():
        for name in LABELS:
            one_open(path, name)
        samples = []
        # Rotations prevent a fixed time-of-day position from selecting a winner.
        for block in range(2):
            for shift in range(4):
                order = LABELS[shift:] + LABELS[:shift]
                if block == 1:
                    order = tuple(reversed(order))
                for name in order:
                    samples.append({
                        "block": block, "shift": shift, "order": list(order),
                        "variant": name, **one_open(path, name),
                    })
        assert len(samples) == 32
        median = {
            metric: {name: statistics.median(
                s[metric] for s in samples if s["variant"] == name)
                for name in LABELS}
            for metric in ("wall_ns", "cpu_ns")
        }
        block_medians = {
            str(block): {
                name: statistics.median(s["wall_ns"] for s in samples
                                        if s["block"] == block and s["variant"] == name)
                for name in LABELS
            }
            for block in range(2)
        }
        measured[file_label] = {
            "raw": samples, "medians": median, "block_wall_medians": block_medians,
        }
    wall = {k: v["medians"]["wall_ns"] for k, v in measured.items()}
    cpu = {k: v["medians"]["cpu_ns"] for k, v in measured.items()}
    ratios = {
        "public_A_over_owned_A_wall": wall["A"]["public"] / wall["A"]["owned"],
        "public_A_over_delete_A_wall": wall["A"]["public"] / wall["A"]["delete_only"],
        "owned_A_over_public_B_wall": wall["A"]["owned"] / wall["B"]["public"],
        "delete_A_over_public_B_wall": wall["A"]["delete_only"] / wall["B"]["public"],
        "owned_A_over_delete_A_wall": wall["A"]["owned"] / wall["A"]["delete_only"],
        "public_A_over_owned_A_cpu": cpu["A"]["public"] / cpu["A"]["owned"],
        "owned_A_over_public_B_cpu": cpu["A"]["owned"] / cpu["B"]["public"],
    }
    return {"files": measured, "ratios": ratios}


def traced_peak(path: Path) -> dict:
    values = {}
    for label in LABELS:
        peaks = []
        for _ in range(2):
            tracemalloc.start()
            tracemalloc.reset_peak()
            one_open(path, label)
            peaks.append(tracemalloc.get_traced_memory()[1])
            tracemalloc.stop()
        values[label] = peaks
    return values


def extract_exact(path: Path, expected: dict[str, str], cls: type[CMPCT]) -> dict:
    with tempfile.TemporaryDirectory(prefix="j24i70-extract-") as dest:
        start = time.perf_counter_ns()
        with cls(path) as archive:
            archive.extractall(Path(dest), metadata=False)
        wall = time.perf_counter_ns() - start
        leaves = sorted(p for p in Path(dest).rglob("*") if p.is_file())
        assert len(leaves) == len(expected)
        for file in leaves:
            rel = file.relative_to(dest).as_posix()
            assert hashlib.sha256(file.read_bytes()).hexdigest() == expected[rel]
        return {"members": len(leaves), "wall_ns": wall, "byte_identity": True}


def main() -> None:
    output = Path(os.environ.get("J24I70_EVIDENCE", "evidence/j24i70"))
    output.mkdir(parents=True, exist_ok=True)
    receipt = {
        "schema": "cmpct-j24i70-cross-owner-v1", "status": "RUNNING",
        "host": platform.platform(), "platform": sys.platform,
        "source": source_identity(), "product_credit": 0, "cases": {},
        "unmeasured": ["cold-disk open", "fresh-process peak RSS", "native Rust parity",
                       "mixed xattr/hardlink mutation", "arbitrary-reader release"],
    }
    try:
        with tempfile.TemporaryDirectory(prefix="j24i70-physical-") as scratch:
            for n in CASES:
                case = make_court(Path(scratch), n)
                semantics = check_all_readers(case, n)
                timings = time_variants(case)
                traced = traced_peak(case["paths"]["A"])
                extraction = {
                    "public_A": extract_exact(case["paths"]["A"], case["expected"], CMPCT),
                    "owned_A": extract_exact(case["paths"]["A"], case["expected"], OwnedCMPCT),
                    "public_B": extract_exact(case["paths"]["B"], case["expected"], CMPCT),
                }
                copied = {}
                for key, path in case["paths"].items():
                    to = output / f"{n}-{key}.cmpct"
                    shutil.copyfile(path, to)
                    assert digest(to) == case["physical"][key]["sha256"]
                    copied[key] = {"relative": to.name, "size": to.stat().st_size,
                                   "sha256": digest(to)}
                r = timings["ratios"]
                tests = {
                    "owned_speedup_at_least_2": r["public_A_over_owned_A_wall"] >= 2.0,
                    "owned_within_1p5_checkpoint": r["owned_A_over_public_B_wall"] <= 1.50,
                    "cpu_sign_consistent": r["public_A_over_owned_A_cpu"] > 1.0,
                    "checkpoint_byte_tax_positive": case["checkpoint_extra_bytes"] > 0,
                }
                receipt["cases"][str(n)] = {
                    "members": len(case["expected"]),
                    "physical": case["physical"],
                    "copied": copied,
                    "checkpoint_extra_bytes": case["checkpoint_extra_bytes"],
                    "checkpoint_overhead_ratio": case["checkpoint_overhead_ratio"],
                    "generation_seconds": case["generation_seconds"],
                    "semantics": semantics, "timings": timings,
                    "traced_peak_A": traced, "extraction": extraction,
                    "predictions": tests,
                }
        receipt["hypothesis"] = {
            "all_semantics_passed": True,
            "owned_narrow_checkpoint_economics": all(
                c["predictions"]["owned_speedup_at_least_2"] and
                c["predictions"]["owned_within_1p5_checkpoint"] and
                c["predictions"]["cpu_sign_consistent"]
                for c in receipt["cases"].values()),
        }
        receipt["status"] = "PASS"  # PASS = experiment safely executed, NOT H1 success.
    except BaseException as exc:
        receipt["status"] = "FAIL"
        receipt["error"] = {"type": type(exc).__name__, "message": str(exc)}
        raise
    finally:
        target = output / "receipt.json"
        target.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
        print("J24I70_RESULT", json.dumps({
            "status": receipt["status"], "hypothesis": receipt.get("hypothesis"),
            "ratios": {n: c["timings"]["ratios"] for n, c in receipt["cases"].items()},
        }, sort_keys=True))


if __name__ == "__main__":
    if len(sys.argv) != 1:
        raise SystemExit("No arguments accepted; source and cases are frozen.")
    main()
