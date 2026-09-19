from __future__ import annotations

"""Exact A/B for the C25CC01 source-shape preflight.

The promoted C25CC01 shipping win has only a small ZIP creation-time margin on
some runners. Before the real r24 build starts, the historical release front
door walked high-file-count trees once only to count regular files and logical
bytes, paying Path construction plus lstat for every file. This oracle keeps
that historical implementation frozen locally and compares it with the direct
``os.scandir`` traversal now used by the release product.

Research evidence only: archive bytes and selector thresholds are unchanged.
Promotion/evidence requires exact shape/prefilter parity on adversarial trees
and a meaningful same-runner speedup. A negative result remains valid evidence.
"""

import argparse
import json
import os
from pathlib import Path
import random
import stat
import statistics
import tempfile
import time

from experiments import entropygraph_v030_release_product as PRODUCT

ROUNDS = 11
MIN_RELATIVE_SPEEDUP = 0.20
MIN_ABSOLUTE_SPEEDUP_S = 0.003


def _legacy_shape(root: Path) -> dict:
    """Frozen pre-promotion os.walk + Path + lstat source-shape implementation."""
    root = Path(root)
    regular_files = 0
    logical_bytes = 0
    for dirpath, dirnames, filenames in os.walk(root, followlinks=False):
        dirnames[:] = [name for name in dirnames if not os.path.islink(Path(dirpath) / name)]
        for name in filenames:
            path = Path(dirpath) / name
            try:
                st = os.lstat(path)
            except OSError:
                continue
            if stat.S_ISREG(st.st_mode):
                regular_files += 1
                logical_bytes += int(st.st_size)
    return {
        "regular_files": regular_files,
        "logical_bytes": logical_bytes,
        "average_regular_bytes": logical_bytes / max(1, regular_files),
    }


def _scandir_shape(root: Path) -> dict:
    regular_files = 0
    logical_bytes = 0
    stack = [os.fspath(root)]
    while stack:
        directory = stack.pop()
        try:
            with os.scandir(directory) as entries:
                for entry in entries:
                    try:
                        if entry.is_symlink():
                            continue
                        if entry.is_dir(follow_symlinks=False):
                            stack.append(entry.path)
                            continue
                        st = entry.stat(follow_symlinks=False)
                    except OSError:
                        continue
                    if stat.S_ISREG(st.st_mode):
                        regular_files += 1
                        logical_bytes += int(st.st_size)
        except OSError:
            continue
    return {
        "regular_files": regular_files,
        "logical_bytes": logical_bytes,
        "average_regular_bytes": logical_bytes / max(1, regular_files),
    }


def _build_tree(root: Path) -> None:
    rng = random.Random(0xC25CC01)
    root.mkdir(parents=True, exist_ok=True)
    for d in range(12):
        directory = root / f"d{d:02d}"
        directory.mkdir()
        for i in range(128):
            size = 4096 + ((d * 131 + i * 17) % 2048)
            (directory / f"f{i:04d}.bin").write_bytes(rng.randbytes(size))
    (root / "empty").write_bytes(b"")
    (root / "tiny").write_bytes(b"x")
    try:
        (root / "file-link").symlink_to(root / "d00" / "f0000.bin")
        (root / "dir-link").symlink_to(root / "d00", target_is_directory=True)
    except (OSError, NotImplementedError):
        pass


def _time(fn, root: Path) -> tuple[dict, float]:
    started = time.perf_counter()
    result = fn(root)
    return result, time.perf_counter() - started


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--work-root", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    args.work_root.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="cmpct-c25-shape-", dir=args.work_root) as td:
        source = Path(td) / "source"
        _build_tree(source)

        samples = []
        baseline_shape = None
        candidate_shape = None
        shipping_shape = None
        for rep in range(ROUNDS):
            order = ("baseline", "candidate") if rep % 2 == 0 else ("candidate", "baseline")
            row = {}
            for name in order:
                if name == "baseline":
                    shape, elapsed = _time(_legacy_shape, source)
                    baseline_shape = shape
                else:
                    shape, elapsed = _time(_scandir_shape, source)
                    candidate_shape = shape
                row[name] = elapsed
            samples.append(row)
        shipping_shape = PRODUCT._compact_control_source_shape(source)

        assert baseline_shape is not None and candidate_shape is not None and shipping_shape is not None
        shape_exact = baseline_shape == candidate_shape == shipping_shape
        prefilter_exact = (
            PRODUCT._compact_control_source_prefilter(baseline_shape)
            == PRODUCT._compact_control_source_prefilter(candidate_shape)
            == PRODUCT._compact_control_source_prefilter(shipping_shape)
        )
        shipping_uses_candidate = shipping_shape == candidate_shape
        baseline_median = statistics.median(row["baseline"] for row in samples)
        candidate_median = statistics.median(row["candidate"] for row in samples)
        absolute = baseline_median - candidate_median
        relative = absolute / max(baseline_median, 1e-12)
        material_speedup = (
            candidate_median < baseline_median
            and absolute >= MIN_ABSOLUTE_SPEEDUP_S
            and relative >= MIN_RELATIVE_SPEEDUP
        )
        experiment_valid = shape_exact and prefilter_exact and shipping_uses_candidate
        promotion_signal = experiment_valid and material_speedup

        result = {
            "schema": "cmpct-v030-c25cc01-scandir-source-shape-v2",
            "contract": {
                "rounds": ROUNDS,
                "min_relative_speedup": MIN_RELATIVE_SPEEDUP,
                "min_absolute_speedup_s": MIN_ABSOLUTE_SPEEDUP_S,
                "archive_bytes_changed": False,
                "selector_changed": False,
                "release_credit": False,
                "baseline": "frozen-os-walk-path-lstat",
                "candidate": "os-scandir-direntry",
            },
            "baseline_shape": baseline_shape,
            "candidate_shape": candidate_shape,
            "shipping_shape": shipping_shape,
            "samples": samples,
            "median_baseline_s": baseline_median,
            "median_candidate_s": candidate_median,
            "absolute_speedup_s": absolute,
            "relative_speedup": relative,
            "gate": {
                "shape_exact": shape_exact,
                "prefilter_exact": prefilter_exact,
                "shipping_uses_candidate": shipping_uses_candidate,
                "experiment_valid": experiment_valid,
                "material_speedup": material_speedup,
                "promotion_signal": promotion_signal,
            },
        }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))
    if not experiment_valid:
        raise SystemExit("C25CC01 scandir source-shape experiment invalid")


if __name__ == "__main__":
    main()
