#!/usr/bin/env python3
"""Frozen falsifier for ONE-G0.2 fused authentication observation.

This benchmark does not touch the Genesis 15-workload gate.  It compares two builders for
the exact same authenticated research archive representation and asks whether consuming
already-read payload bytes for AuthTree construction removes the redundant source pass
without exporting material CPU or semantic cost.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
import os
from pathlib import Path
import statistics
import tempfile
import time

from experiments.one.archive_envelope import CHUNK_BYTES
from experiments.one.authenticated_archive_envelope import AUTH_LEAF_BYTES, build_authenticated_archive, open_authenticated_archive
from experiments.one.fused_authenticated_archive import build_authenticated_archive_fused

REPETITIONS = 11
MEDIAN_CPU_MAX = 1.05
WORST_CPU_MAX = 1.15


def _pattern(length: int, salt: int) -> bytes:
    block = bytes(((i * 37 + salt * 19 + (i >> 3)) & 255) for i in range(4096))
    return (block * ((length + len(block) - 1) // len(block)))[:length]


def _write_shape(root: Path, shape: str) -> dict[str, bytes]:
    if shape == "single_32k":
        payloads = {"data.bin": _pattern(32 * 1024, 1)}
    elif shape == "single_256k":
        payloads = {"data.bin": _pattern(256 * 1024 + 73, 2)}
    elif shape == "single_cross_chunk":
        payloads = {"data.bin": _pattern(CHUNK_BYTES + AUTH_LEAF_BYTES * 3 + 137, 3)}
    elif shape == "multi_medium":
        payloads = {
            "a.bin": _pattern(192 * 1024 + 11, 4),
            "b.bin": _pattern(224 * 1024 + 29, 5),
            "c.bin": _pattern(320 * 1024 + 47, 6),
        }
    elif shape == "mixed":
        (root / "nested").mkdir()
        payloads = {
            "empty.bin": b"",
            "tiny.bin": b"ONE-fused-auth",
            "nested/medium.bin": _pattern(257 * 1024 + 31, 7),
            "large.bin": _pattern(CHUNK_BYTES + AUTH_LEAF_BYTES * 2 + 97, 8),
        }
    else:  # pragma: no cover
        raise AssertionError(shape)

    for rel, data in payloads.items():
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    if shape == "mixed":
        try:
            os.symlink("../tiny.bin", root / "nested" / "link-to-tiny")
        except (OSError, NotImplementedError):
            pass
    return payloads


def _time_build(fn, root: Path) -> tuple[int, int, bytes, object]:
    cpu0 = time.process_time_ns()
    wall0 = time.perf_counter_ns()
    wire, stats = fn(root)
    wall = time.perf_counter_ns() - wall0
    cpu = time.process_time_ns() - cpu0
    return cpu, wall, wire, stats


def _requests(length: int) -> list[tuple[int, int]]:
    out = [(0, 0)]
    if length == 0:
        return out
    out.extend([
        (0, min(64, length)),
        (max(0, length // 2 - 31), min(127, length - max(0, length // 2 - 31))),
        (max(0, length - min(257, length)), min(257, length)),
    ])
    if length > AUTH_LEAF_BYTES:
        out.append((AUTH_LEAF_BYTES - 31, min(127, length - (AUTH_LEAF_BYTES - 31))))
    if length > CHUNK_BYTES:
        out.append((CHUNK_BYTES - 31, min(127, length - (CHUNK_BYTES - 31))))
    return out


def _row(root: Path, shape: str, payloads: dict[str, bytes]) -> dict:
    # Establish exact representation and reopen/selective parity outside the timed samples.
    baseline_wire, baseline_stats = build_authenticated_archive(root)
    candidate_wire, candidate_stats = build_authenticated_archive_fused(root)
    if candidate_wire != baseline_wire:
        raise AssertionError(f"{shape}: candidate wire differs from baseline")
    if candidate_stats.source_reread_bytes != 0:
        raise AssertionError(f"{shape}: candidate retained authentication-only reread")
    logical = sum(len(data) for data in payloads.values())
    if baseline_stats.source_reread_bytes != logical:
        raise AssertionError(f"{shape}: baseline reread accounting drifted")
    if candidate_stats.logical_file_bytes != logical:
        raise AssertionError(f"{shape}: candidate logical-byte accounting drifted")

    baseline_open = open_authenticated_archive(baseline_wire)
    candidate_open = open_authenticated_archive(candidate_wire)
    if baseline_open.list_paths() != candidate_open.list_paths():
        raise AssertionError(f"{shape}: reopened path set differs")
    selective_checks = 0
    max_cone = 0
    for rel, expected in payloads.items():
        if candidate_open.read_file(rel) != expected or baseline_open.read_file(rel) != expected:
            raise AssertionError(f"{shape}/{rel}: full reconstruction mismatch")
        for start, length in _requests(len(expected)):
            base_data, base_sel = baseline_open.read_range(rel, start, length)
            cand_data, cand_sel = candidate_open.read_range(rel, start, length)
            if cand_data != base_data or cand_data != expected[start:start + length]:
                raise AssertionError(f"{shape}/{rel}: selective bytes mismatch")
            if cand_sel != base_sel:
                raise AssertionError(f"{shape}/{rel}: selective accounting/geometry mismatch")
            selective_checks += 1
            max_cone = max(max_cone, cand_sel.cone_bytes)

    baseline_cpu: list[int] = []
    candidate_cpu: list[int] = []
    baseline_wall: list[int] = []
    candidate_wall: list[int] = []
    for rep in range(REPETITIONS):
        # Alternate order so page-cache/thermal ordering does not systematically favor one arm.
        order = ("baseline", "candidate") if rep % 2 == 0 else ("candidate", "baseline")
        for arm in order:
            if arm == "baseline":
                cpu, wall, wire, stats = _time_build(build_authenticated_archive, root)
                if wire != baseline_wire or stats.source_reread_bytes != logical:
                    raise AssertionError(f"{shape}: timed baseline semantics/accounting drift")
                baseline_cpu.append(cpu); baseline_wall.append(wall)
            else:
                cpu, wall, wire, stats = _time_build(build_authenticated_archive_fused, root)
                if wire != baseline_wire or stats.source_reread_bytes != 0:
                    raise AssertionError(f"{shape}: timed candidate semantics/accounting drift")
                candidate_cpu.append(cpu); candidate_wall.append(wall)

    base_cpu_med = statistics.median(baseline_cpu)
    cand_cpu_med = statistics.median(candidate_cpu)
    base_wall_med = statistics.median(baseline_wall)
    cand_wall_med = statistics.median(candidate_wall)
    return {
        "shape": shape,
        "logical_file_bytes": logical,
        "regular_files": candidate_stats.regular_files,
        "wire_bytes": len(candidate_wire),
        "wire_sha256": sha256(candidate_wire).hexdigest(),
        "wire_exact": True,
        "auth_manifest_delta_bytes": candidate_stats.auth_manifest_delta_bytes,
        "raw_auth_index_bytes": candidate_stats.raw_auth_index_bytes,
        "baseline_total_source_payload_read_bytes": logical + baseline_stats.source_reread_bytes,
        "candidate_total_source_payload_read_bytes": logical,
        "baseline_authentication_only_reread_bytes": baseline_stats.source_reread_bytes,
        "candidate_authentication_only_reread_bytes": candidate_stats.source_reread_bytes,
        "source_payload_read_ratio": logical / (logical + baseline_stats.source_reread_bytes) if logical else 1.0,
        "candidate_extra_auth_payload_cache_bytes": 0,
        "selective_checks": selective_checks,
        "max_selective_cone_bytes": max_cone,
        "baseline_cpu_ns_median": base_cpu_med,
        "candidate_cpu_ns_median": cand_cpu_med,
        "cpu_ratio": cand_cpu_med / base_cpu_med,
        "baseline_wall_ns_median": base_wall_med,
        "candidate_wall_ns_median": cand_wall_med,
        "wall_ratio": cand_wall_med / base_wall_med,
        "baseline_cpu_ns_samples": baseline_cpu,
        "candidate_cpu_ns_samples": candidate_cpu,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="one_g02_fused_auth_observation.json")
    parser.add_argument("--evidence-head", default=os.environ.get("EVIDENCE_HEAD", ""))
    args = parser.parse_args()

    rows: list[dict] = []
    with tempfile.TemporaryDirectory(prefix="one-g02-fused-auth-") as td:
        base = Path(td)
        for shape in ("single_32k", "single_256k", "single_cross_chunk", "multi_medium", "mixed"):
            root = base / shape
            root.mkdir()
            payloads = _write_shape(root, shape)
            rows.append(_row(root, shape, payloads))

    median_cpu_ratio = statistics.median(row["cpu_ratio"] for row in rows)
    worst_cpu_ratio = max(row["cpu_ratio"] for row in rows)
    all_wire_exact = all(row["wire_exact"] for row in rows)
    all_reread_eliminated = all(row["candidate_authentication_only_reread_bytes"] == 0 for row in rows)
    all_source_halved = all(row["source_payload_read_ratio"] == (1.0 if row["logical_file_bytes"] == 0 else 0.5) for row in rows)
    cpu_pass = median_cpu_ratio <= MEDIAN_CPU_MAX and worst_cpu_ratio <= WORST_CPU_MAX
    advance = all_wire_exact and all_reread_eliminated and all_source_halved and cpu_pass

    result = {
        "experiment": "ONE-G0.2 fused authentication observation",
        "evidence_head": args.evidence_head,
        "repetitions": REPETITIONS,
        "gates": {
            "median_cpu_ratio_max": MEDIAN_CPU_MAX,
            "worst_cpu_ratio_max": WORST_CPU_MAX,
            "wire_exact_required": True,
            "authentication_only_reread_bytes_required": 0,
            "candidate_source_payload_ratio_required": 0.5,
        },
        "summary": {
            "all_wire_exact": all_wire_exact,
            "all_authentication_only_rereads_eliminated": all_reread_eliminated,
            "all_nonempty_source_payload_reads_halved": all_source_halved,
            "median_candidate_baseline_cpu_ratio": median_cpu_ratio,
            "worst_candidate_baseline_cpu_ratio": worst_cpu_ratio,
            "decision": "ADVANCE_FUSED_AUTH_OBSERVATION" if advance else "HOLD_FUSED_AUTH_OBSERVATION",
        },
        "rows": rows,
    }
    Path(args.output).write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result["summary"], indent=2, sort_keys=True))
    return 0 if advance else 2


if __name__ == "__main__":
    raise SystemExit(main())
