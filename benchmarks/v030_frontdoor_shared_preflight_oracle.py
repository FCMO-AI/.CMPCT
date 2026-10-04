from __future__ import annotations

"""Exact A/B for eliminating duplicate source walks in the v0.30 product front door.

The shipping front door currently asks the logs terminal to scan the source tree and,
when logs are not admitted, C25CC01 scans the same tree again to obtain regular-file
count/logical bytes.  This oracle tests one content-agnostic scandir traversal that:

* proves the exact same >=2 logs-sidecar predicate and short-circuits immediately on
  the second proven pair; and
* when logs are not admitted, finishes that same traversal and returns the exact
  regular-file/logical-byte shape consumed by C25CC01.

This is research-only.  It changes no selector, archive byte, benchmark threshold or
release credit.  Promotion requires exact semantic agreement plus a material same-runner
saving on a C25-shaped negative-logs tree, while preserving a fast early-positive logs
path.
"""

import json
import os
from pathlib import Path
import statistics
import tempfile
import time

from experiments import entropygraph_v030_release_product as PRODUCT
from experiments import entropygraph_v030_release_product_logs_candidate as LOGS

ROUNDS = 11
MIN_NONLOGS_SPEEDUP = 0.25
MIN_NONLOGS_ABSOLUTE_SAVING_S = 0.003
MAX_LOGS_SLOWDOWN_FRACTION = 0.05
MAX_LOGS_ABSOLUTE_SLOWDOWN_S = 0.001


def shared_preflight(root: Path) -> dict:
    """Single traversal: early logs proof or exact completed C25 source shape."""
    root = Path(root)
    plain: set[str] = set()
    sidecars: dict[str, str] = {}
    paired: set[str] = set()
    regular_files = 0
    logical_bytes = 0
    scanned_regular_files = 0
    stack = [root]

    while stack:
        current = stack.pop()
        try:
            with os.scandir(current) as entries:
                batch = list(entries)
        except OSError:
            return {
                "logs_eligible": False,
                "shape": None,
                "metadata_error": True,
                "scanned_regular_files": scanned_regular_files,
                "short_circuited": False,
            }

        for entry in batch:
            try:
                if entry.is_symlink():
                    continue
                if entry.is_dir(follow_symlinks=False):
                    stack.append(Path(entry.path))
                    continue
                if not entry.is_file(follow_symlinks=False):
                    continue
                size = int(entry.stat(follow_symlinks=False).st_size)
            except OSError:
                return {
                    "logs_eligible": False,
                    "shape": None,
                    "metadata_error": True,
                    "scanned_regular_files": scanned_regular_files,
                    "short_circuited": False,
                }

            regular_files += 1
            logical_bytes += size
            scanned_regular_files += 1
            rel = Path(entry.path).relative_to(root).as_posix()

            sidecar_base = None
            for suffix in (".gz", ".zst"):
                if rel.endswith(suffix):
                    sidecar_base = rel[: -len(suffix)]
                    break

            if sidecar_base is not None:
                sidecars[rel] = sidecar_base
                if sidecar_base in plain:
                    paired.add(sidecar_base)
            else:
                plain.add(rel)
                for suffix in (".gz", ".zst"):
                    candidate = rel + suffix
                    if sidecars.get(candidate) == rel:
                        paired.add(rel)

            if len(paired) >= LOGS.MIN_SIDECAR_PAIRS:
                return {
                    "logs_eligible": True,
                    "shape": None,
                    "metadata_error": False,
                    "scanned_regular_files": scanned_regular_files,
                    "short_circuited": True,
                }

    return {
        "logs_eligible": False,
        "shape": {
            "logical_bytes": logical_bytes,
            "regular_files": regular_files,
            "average_regular_bytes": logical_bytes / max(1, regular_files),
        },
        "metadata_error": False,
        "scanned_regular_files": scanned_regular_files,
        "short_circuited": False,
    }


def current_two_pass(root: Path) -> dict:
    logs = PRODUCT._logs_streaming_source_prefilter(root)
    if bool(logs["eligible"]):
        return {"logs_eligible": True, "shape": None}
    shape = PRODUCT._c25cc01_source_shape(root)
    return {"logs_eligible": False, "shape": shape}


def _write(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload)


def _make_nonlogs(root: Path, *, files: int = 1800, size: int = 6144) -> None:
    # Deterministic high-file-count tree in the same broad source-shape regime as the
    # compact-control front door, with suffix traps but no valid sidecar pairs.
    root.mkdir(parents=True, exist_ok=True)
    for i in range(files):
        payload = bytes(((i * 17 + j * 29) & 255 for j in range(size)))
        _write(root / f"d{i % 19:02d}" / f"f-{i:05d}.bin", payload)
    _write(root / "traps" / "orphan.gz", b"not-a-pair")
    _write(root / "traps" / "orphan.zst", b"not-a-pair")


def _make_logs(root: Path, *, ordinary: int = 12000) -> None:
    root.mkdir(parents=True, exist_ok=True)
    _write(root / "00-a.log", b"a")
    _write(root / "00-a.log.gz", b"ga")
    _write(root / "00-b.log", b"b")
    _write(root / "00-b.log.zst", b"zb")
    for i in range(ordinary):
        _write(root / "bulk" / f"f-{i:05d}.bin", bytes((i & 255,)))


def _shape_equal(a: dict | None, b: dict | None) -> bool:
    if a is None or b is None:
        return a is b
    return (
        int(a["logical_bytes"]) == int(b["logical_bytes"])
        and int(a["regular_files"]) == int(b["regular_files"])
        and abs(float(a["average_regular_bytes"]) - float(b["average_regular_bytes"])) < 1e-12
    )


def _timed(fn, root: Path) -> float:
    started = time.perf_counter()
    fn(root)
    return time.perf_counter() - started


def _rotated(root: Path) -> dict:
    current_samples: list[float] = []
    shared_samples: list[float] = []
    for i in range(ROUNDS):
        if i % 2:
            shared_samples.append(_timed(shared_preflight, root))
            current_samples.append(_timed(current_two_pass, root))
        else:
            current_samples.append(_timed(current_two_pass, root))
            shared_samples.append(_timed(shared_preflight, root))
    c = statistics.median(current_samples)
    s = statistics.median(shared_samples)
    return {
        "rounds": ROUNDS,
        "current_samples_s": current_samples,
        "shared_samples_s": shared_samples,
        "current_median_s": c,
        "shared_median_s": s,
        "absolute_saving_s": c - s,
        "speedup_fraction": (c - s) / max(c, 1e-12),
        "slowdown_fraction": (s - c) / max(c, 1e-12),
    }


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="cmpct-v030-shared-preflight-") as td:
        base = Path(td)
        nonlogs = base / "nonlogs"
        logs = base / "logs"
        _make_nonlogs(nonlogs)
        _make_logs(logs)

        current_nonlogs = current_two_pass(nonlogs)
        shared_nonlogs = shared_preflight(nonlogs)
        current_logs = current_two_pass(logs)
        shared_logs = shared_preflight(logs)

        correctness = {
            "nonlogs_logs_equal": current_nonlogs["logs_eligible"] == shared_nonlogs["logs_eligible"],
            "nonlogs_shape_equal": _shape_equal(current_nonlogs["shape"], shared_nonlogs["shape"]),
            "logs_logs_equal": current_logs["logs_eligible"] == shared_logs["logs_eligible"],
            "logs_shared_short_circuit": bool(shared_logs["short_circuited"]),
            "logs_shared_shape_omitted_after_proof": shared_logs["shape"] is None,
            "no_metadata_error": not bool(shared_nonlogs["metadata_error"]) and not bool(shared_logs["metadata_error"]),
        }
        nonlogs_perf = _rotated(nonlogs)
        logs_perf = _rotated(logs)

    exact = all(correctness.values())
    nonlogs_material = (
        nonlogs_perf["speedup_fraction"] >= MIN_NONLOGS_SPEEDUP
        and nonlogs_perf["absolute_saving_s"] >= MIN_NONLOGS_ABSOLUTE_SAVING_S
    )
    logs_safe = (
        logs_perf["slowdown_fraction"] <= MAX_LOGS_SLOWDOWN_FRACTION
        and (logs_perf["shared_median_s"] - logs_perf["current_median_s"]) <= MAX_LOGS_ABSOLUTE_SLOWDOWN_S
    )
    promotion_signal = exact and nonlogs_material and logs_safe
    result = {
        "experiment": "v030-frontdoor-shared-preflight-v1",
        "research_only": True,
        "selector_change": False,
        "release_credit": False,
        "correctness": correctness,
        "nonlogs_performance": nonlogs_perf,
        "logs_performance": logs_perf,
        "requirements": {
            "minimum_nonlogs_speedup_fraction": MIN_NONLOGS_SPEEDUP,
            "minimum_nonlogs_absolute_saving_s": MIN_NONLOGS_ABSOLUTE_SAVING_S,
            "maximum_logs_slowdown_fraction": MAX_LOGS_SLOWDOWN_FRACTION,
            "maximum_logs_absolute_slowdown_s": MAX_LOGS_ABSOLUTE_SLOWDOWN_S,
        },
        "experiment_valid": exact,
        "promotion_signal": promotion_signal,
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if exact else 1


if __name__ == "__main__":
    raise SystemExit(main())
